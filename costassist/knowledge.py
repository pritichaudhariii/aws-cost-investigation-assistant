"""Load runbooks from markdown, parse front matter and split into chunks."""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DIR = Path(__file__).resolve().parent.parent / "knowledge"
_FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)


@dataclass
class Chunk:
    id: str
    doc_id: str
    title: str
    section: str
    text: str
    metadata: dict = field(default_factory=dict)

    @property
    def allowed_roles(self) -> list[str]:
        return self.metadata.get("allowed_roles", [])


def _front_matter(text: str) -> tuple[dict, str]:
    m = _FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    meta["allowed_roles"] = [r.strip() for r in meta.get("allowed_roles", "").split(",") if r.strip()]
    return meta, text[m.end():]


def chunk_document(path: Path, max_chars: int = 900) -> list[Chunk]:
    meta, body = _front_matter(path.read_text())
    doc_id = path.stem
    title = meta.get("title", doc_id)
    chunks: list[Chunk] = []
    # split on level-2 headings so each chunk is one coherent section
    sections = re.split(r"\n(?=## )", body)
    for sec in sections:
        sec = sec.strip()
        if not sec or sec.startswith("# ") and "\n" not in sec:
            continue
        heading = sec.splitlines()[0].lstrip("# ").strip()
        for start in range(0, len(sec), max_chars):
            piece = sec[start:start + max_chars]
            cid = hashlib.sha1(f"{doc_id}:{heading}:{start}".encode()).hexdigest()[:12]
            chunks.append(Chunk(cid, doc_id, title, heading, piece, dict(meta)))
    return chunks


def load_knowledge(directory: Path = DEFAULT_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(directory.rglob("*.md")):
        chunks.extend(chunk_document(path))
    return chunks
