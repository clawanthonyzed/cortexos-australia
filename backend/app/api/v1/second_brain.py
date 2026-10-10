"""Second Brain reader API (2026-10-10).

Read-only view of /opt/openclaw/second-brain (mounted read-only into the backend) so the
EmpireOS "Second Brain" tab can browse and read notes. Never writes. Paths are resolved and
must stay inside the vault; only .md/.txt notes are served; DB dumps, git internals and
scripts are hidden.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.rbac import Permission, require_permission
from app.models.user import User

router = APIRouter()

ROOT = Path("/opt/openclaw/second-brain").resolve()
NOTE_EXT = {".md", ".txt"}
HIDDEN_DIRS = {".git", "backups", "__pycache__", "node_modules", ".obsidian"}
MAX_NOTE_BYTES = 2_000_000


def _safe(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise HTTPException(status_code=400, detail={"error": "Path is outside the Second Brain"})
    if any(part in HIDDEN_DIRS for part in p.relative_to(ROOT).parts):
        raise HTTPException(status_code=404, detail={"error": "Not found"})
    return p


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _walk(d: Path) -> dict[str, Any]:
    folders, notes = [], []
    try:
        entries = sorted(os.scandir(d), key=lambda e: e.name.lower())
    except OSError:
        entries = []
    for e in entries:
        if e.name.startswith(".") or e.name in HIDDEN_DIRS or e.is_symlink():
            continue  # symlinks can point outside the vault (CLAUDE.md -> /root/CLAUDE.md)
        if e.is_dir(follow_symlinks=False):
            sub = _walk(Path(e.path))
            if sub["count"]:
                folders.append(sub)
        elif Path(e.name).suffix.lower() in NOTE_EXT:
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            notes.append({"name": e.name, "path": str(Path(e.path).relative_to(ROOT)),
                          "size": st.st_size, "modified": _iso(st.st_mtime)})
    count = len(notes) + sum(f["count"] for f in folders)
    latest = max([n["modified"] for n in notes] + [f["latest"] for f in folders if f["latest"]], default=None)
    return {"name": d.name if d != ROOT else "second-brain", "path": "" if d == ROOT else str(d.relative_to(ROOT)),
            "count": count, "latest": latest, "folders": folders, "notes": notes}


@router.get("/tree", tags=["second-brain"])
async def second_brain_tree(current_user: User = Depends(require_permission(Permission.MEMORY_READ))) -> dict[str, Any]:
    """Folder tree of every note (no content)."""
    return _walk(ROOT)


@router.get("/note", tags=["second-brain"])
async def second_brain_note(
    path: str = Query(..., min_length=1),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """One note's full text."""
    p = _safe(path)
    if not p.is_file() or p.suffix.lower() not in NOTE_EXT:
        raise HTTPException(status_code=404, detail={"error": "Note not found"})
    st = p.stat()
    if st.st_size > MAX_NOTE_BYTES:
        raise HTTPException(status_code=413, detail={"error": "Note is too large to display"})
    return {"path": str(p.relative_to(ROOT)), "name": p.name, "size": st.st_size, "modified": _iso(st.st_mtime),
            "content": p.read_text(errors="replace")}


@router.get("/search", tags=["second-brain"])
async def second_brain_search(
    q: str = Query(..., min_length=2, max_length=100),
    current_user: User = Depends(require_permission(Permission.MEMORY_READ)),
) -> dict[str, Any]:
    """Case-insensitive full-text search; returns up to 50 notes with a matching line."""
    needle = q.lower()
    hits: list[dict[str, Any]] = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [n for n in dirnames if n not in HIDDEN_DIRS and not n.startswith(".")]
        for fn in filenames:
            if Path(fn).suffix.lower() not in NOTE_EXT:
                continue
            fp = Path(dirpath) / fn
            try:
                if fp.stat().st_size > MAX_NOTE_BYTES:
                    continue
                text = fp.read_text(errors="replace")
            except OSError:
                continue
            low = text.lower()
            i = low.find(needle)
            if i < 0 and needle not in fn.lower():
                continue
            start = text.rfind("\n", 0, max(i, 0)) + 1 if i >= 0 else 0
            end = text.find("\n", i) if i >= 0 else -1
            hits.append({"path": str(fp.relative_to(ROOT)), "name": fn,
                         "snippet": text[start:end if end > 0 else start + 200][:200].strip()})
            if len(hits) >= 50:
                return {"query": q, "results": hits, "truncated": True}
    return {"query": q, "results": hits, "truncated": False}
