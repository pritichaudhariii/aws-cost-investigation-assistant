"""FastAPI service.

The caller's role and team come from headers set by an upstream gateway /
identity-aware proxy (X-User-Role, X-User-Team). In production these must be
derived from a verified token, never trusted from the client directly.
"""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from .pipeline import AccessDenied, CostInvestigator, Requester
from .scenarios import build_scenario

app = FastAPI(title="AWS Cost Investigation Assistant", version="0.1.0")


class Question(BaseModel):
    question: str = Field(min_length=5, max_length=500)


@lru_cache(maxsize=1)
def investigator() -> CostInvestigator:
    path = os.environ.get("CUR_PATH")
    if path:
        from .cli import load_cur

        return CostInvestigator(load_cur(path))
    _, df = build_scenario(int(os.environ.get("DEMO_SCENARIO", "1")) - 1)
    return CostInvestigator(df)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/investigate")
def investigate(q: Question, x_user_role: str = Header(...), x_user_team: str | None = Header(default=None)) -> dict:
    try:
        who = Requester(x_user_role, x_user_team)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        return investigator().investigate(q.question, who).to_dict()
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
