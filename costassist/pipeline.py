"""The four-stage investigation pipeline.

    question --1--> QueryPlan --2--> CostAnalysis --3--> runbook chunks --4--> Investigation
              plan            pandas over CUR     vector search with      LLM (or offline)
                                                  role + service filter   synthesis

Role-based isolation is applied twice: cost rows are scoped to the caller's
team (engineers) and runbook chunks are filtered by `allowed_roles` inside the
vector store query. All retrieved text passes through the PII filter before it
is sent to the LLM or returned.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, replace
from datetime import date

import pandas as pd

from .analysis import CostAnalysis, analyze
from .embeddings import Embedder, get_embedder
from .knowledge import Chunk, load_knowledge
from .llm import ChatLLM, llm_from_env
from .pii import redact
from .query import QueryPlan, plan
from .vectorstore import Filter, Hit, VectorStore, get_store

ROLES = {"engineer", "finance", "admin"}


class AccessDenied(Exception):
    pass


@dataclass
class Requester:
    role: str
    team: str | None = None

    def __post_init__(self):
        if self.role not in ROLES:
            raise ValueError(f"unknown role {self.role!r}")
        if self.role == "engineer" and not self.team:
            raise ValueError("engineers must be scoped to a team")


@dataclass
class Investigation:
    question: str
    plan: QueryPlan
    analysis: CostAnalysis
    sources: list[dict]
    root_cause: str | None
    answer: str
    actions: list[str]
    timings_ms: dict[str, float] = field(default_factory=dict)
    llm_cost_usd: float = 0.0
    redactions: dict[str, int] = field(default_factory=dict)

    @property
    def latency_ms(self) -> float:
        return sum(self.timings_ms.values())

    def to_dict(self) -> dict:
        return {
            "question": self.question,
            "team": self.plan.team,
            "window": [str(self.plan.window_start), str(self.plan.window_end)],
            "total_baseline_daily": self.analysis.total_baseline_daily,
            "total_window_daily": self.analysis.total_window_daily,
            "drivers": [d.to_dict() for d in self.analysis.drivers],
            "root_cause": self.root_cause,
            "answer": self.answer,
            "actions": self.actions,
            "sources": self.sources,
            "timings_ms": self.timings_ms,
            "latency_ms": round(self.latency_ms, 1),
            "llm_cost_usd": round(self.llm_cost_usd, 5),
            "redactions": self.redactions,
        }


def _strip_region(usage_type: str) -> str:
    return re.sub(r"^[A-Z]{2,4}\d?-", "", usage_type)


SYSTEM_PROMPT = """You are a FinOps engineer investigating an AWS cost anomaly.
Use ONLY the cost analysis and runbook excerpts provided. Cite runbooks by their [doc_id].
Return JSON: {"summary": str, "root_cause": one of CATEGORIES, "actions": [str, ...]}.
If the evidence is insufficient, say so in the summary and set root_cause to "unknown"."""


class CostInvestigator:
    def __init__(
        self,
        cur: pd.DataFrame,
        chunks: list[Chunk] | None = None,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
        llm: ChatLLM | None = None,
        today: date | None = None,
        k: int = 4,
        retrieval_mode: str = "driver",
    ):
        self.cur = cur
        self.today = today or cur["date"].max().date()
        self.embedder = embedder or get_embedder()
        self.store = store or get_store(dim=self.embedder.dim)
        self.llm = llm if llm is not None else llm_from_env()
        self.k = k
        if retrieval_mode not in ("driver", "question"):
            raise ValueError("retrieval_mode must be 'driver' or 'question'")
        self.retrieval_mode = retrieval_mode
        chunks = chunks if chunks is not None else load_knowledge()
        self.categories = sorted({c.metadata.get("category") for c in chunks} - {None, "general"})
        self.store.upsert(chunks, self.embedder.embed([f"{c.title}\n{c.section}\n{c.text}" for c in chunks]))

    # ---------------------------------------------------------------- stages
    def _plan(self, question: str, who: Requester) -> QueryPlan:
        p = plan(question, self.today, sorted(self.cur["team"].unique()))
        if who.role == "engineer":
            if p.team and p.team != who.team:
                raise AccessDenied(f"engineers on '{who.team}' cannot view cost data for '{p.team}'")
            p.team = who.team
        return p

    def _retrieve(self, question: str, analysis: CostAnalysis, who: Requester) -> list[Hit]:
        top = analysis.top
        if top is None or self.retrieval_mode == "question":  # "question" = single-stage RAG baseline
            vec = self.embedder.embed([question])[0]
            return self.store.search(vec, Filter(role=who.role), self.k)
        ut = _strip_region(top.usage_type)
        query = f"{question}\n{top.service} {ut} {ut.replace(':', ' ').replace('-', ' ')} {top.resource_id}"
        vec = self.embedder.embed([query])[0]
        hits = self.store.search(vec, Filter(role=who.role, service=top.service), self.k * 3)
        # rerank: boost runbooks whose usage-type pattern matches the top driver
        for h in hits:
            pattern = h.chunk.metadata.get("usage_type_pattern", "")
            if pattern and pattern.lower() in ut.lower():
                h.score += 0.5
        hits.sort(key=lambda h: -h.score)
        return hits[: self.k]

    def _root_cause(self, hits: list[Hit]) -> str | None:
        for h in hits:
            cat = h.chunk.metadata.get("category")
            if cat in self.categories:
                return cat
        return None

    def _offline_synthesis(self, analysis: CostAnalysis, hits: list[Hit], root: str | None) -> tuple[str, list[str]]:
        top = analysis.top
        if top is None:
            return "No cost increase was found for this scope and window.", []
        new = ", new resource first seen " + top.first_seen if top.new_resource else ""
        lines = [
            f"Daily spend went from ${analysis.total_baseline_daily:,.2f} to ${analysis.total_window_daily:,.2f} "
            f"(+${analysis.total_delta_daily:,.2f}/day).",
            f"The largest driver is {top.service} `{top.usage_type}` on `{top.resource_id}` in {top.region}: "
            f"${top.baseline_daily:,.2f} -> ${top.window_daily:,.2f} per day (+${top.delta_daily:,.2f}"
            + (f"{new})." if top.new_resource else f", {top.zscore} std devs above baseline)."),
        ]
        minor = [d for d in analysis.drivers[1:3] if d.delta_daily >= 1]
        if minor:
            others = ", ".join(f"{d.service} {_strip_region(d.usage_type)} (+${d.delta_daily:,.0f}/day)" for d in minor)
            lines.append(f"Smaller contributors: {others}.")
        if root:
            title = next(h.chunk.title for h in hits if h.chunk.metadata.get("category") == root)
            lines.append(f"This pattern matches the runbook \"{title}\" [{root}].")
        actions: list[str] = []
        for h in hits:
            if h.chunk.metadata.get("category") == root and h.chunk.section.lower().startswith(("fix", "how to confirm")):
                for line in h.chunk.text.splitlines():
                    line = line.strip()
                    if re.match(r"^(-|\d+\.)\s", line):
                        actions.append(re.sub(r"^(-|\d+\.)\s+", "", line) + f" [{h.chunk.doc_id}]")
        return " ".join(lines), actions[:6]

    def _llm_synthesis(self, question: str, analysis: CostAnalysis, hits: list[Hit], root: str | None):
        context = {
            "question": question,
            "window_daily": analysis.total_window_daily,
            "baseline_daily": analysis.total_baseline_daily,
            "top_drivers": [d.to_dict() for d in analysis.drivers],
        }
        excerpts = "\n\n".join(f"[{h.chunk.doc_id}] {h.chunk.title} - {h.chunk.section}\n{h.chunk.text}" for h in hits)
        prompt = (f"CATEGORIES: {self.categories + ['unknown']}\nRetriever suggestion: {root}\n\n"
                  f"COST ANALYSIS:\n{json.dumps(context, indent=1)}\n\nRUNBOOK EXCERPTS:\n{excerpts}")
        res = self.llm.complete(SYSTEM_PROMPT, prompt)
        try:
            data = json.loads(res.text)
            cat = data.get("root_cause")
            root = cat if cat in self.categories else root
            return data.get("summary", ""), list(data.get("actions", []))[:6], root, res.cost_usd
        except (json.JSONDecodeError, AttributeError):
            summary, actions = self._offline_synthesis(analysis, hits, root)
            return summary, actions, root, res.cost_usd

    # ------------------------------------------------------------------ run
    def investigate(self, question: str, who: Requester) -> Investigation:
        t = {}
        s = time.perf_counter()
        p = self._plan(question, who)
        t["plan"] = (time.perf_counter() - s) * 1000

        s = time.perf_counter()
        analysis = analyze(self.cur, p)
        t["analysis"] = (time.perf_counter() - s) * 1000

        s = time.perf_counter()
        hits = self._retrieve(question, analysis, who)
        redactions: dict[str, int] = {}
        clean_hits = []
        for h in hits:  # copy, so the stored chunk is never modified
            text, counts = redact(h.chunk.text)
            clean_hits.append(Hit(replace(h.chunk, text=text, metadata=dict(h.chunk.metadata)), h.score))
            for k, v in counts.items():
                redactions[k] = redactions.get(k, 0) + v
        hits = clean_hits
        root = self._root_cause(hits)
        t["retrieval"] = (time.perf_counter() - s) * 1000

        s = time.perf_counter()
        cost = 0.0
        if self.llm is not None:
            summary, actions, root, cost = self._llm_synthesis(question, analysis, hits, root)
        else:
            summary, actions = self._offline_synthesis(analysis, hits, root)
        summary, c1 = redact(summary)
        actions = [redact(a)[0] for a in actions]
        for k, v in c1.items():
            redactions[k] = redactions.get(k, 0) + v
        t["synthesis"] = (time.perf_counter() - s) * 1000

        sources = [{"doc_id": h.chunk.doc_id, "title": h.chunk.title, "section": h.chunk.section, "score": round(h.score, 3),
                    "allowed_roles": h.chunk.allowed_roles, "snippet": h.chunk.text[:400]} for h in hits]
        return Investigation(question, p, analysis, sources, root, summary, actions,
                             {k: round(v, 2) for k, v in t.items()}, cost, redactions)
