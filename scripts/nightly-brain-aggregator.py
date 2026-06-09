#!/usr/bin/env python3
"""
nightly-brain-aggregator.py — Aggregates daily agent session summaries into venture files.

Runs at 03:00 AWST (19:00 UTC) via cron:
  0 19 * * * python3 /opt/openclaw/second-brain/nightly-brain-aggregator.py >> /var/log/brain-agg.log 2>&1

What it does:
1. Reads all venture-scoped raw files from today
2. Groups by venture
3. Asks Claude Haiku to distil key facts/decisions from each venture's day
4. Appends distilled summary to ventures/[slug]/daily-[date].md
5. Posts empire-wide digest to Mattermost #intelligence channel
6. Moves processed files to raw/processed/
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone, date
from pathlib import Path
import anthropic
import httpx

# ── Config ────────────────────────────────────────────────────────────────────

BRAIN_ROOT = Path("/opt/openclaw/second-brain")
RAW_ROOT = BRAIN_ROOT / "raw"
VENTURES_ROOT = BRAIN_ROOT / "ventures"
PROCESSED_ROOT = RAW_ROOT / "processed"
PROCESSED_ROOT.mkdir(parents=True, exist_ok=True)

MATTERMOST_URL = os.environ.get("MATTERMOST_URL", "http://localhost:8065")
MATTERMOST_TOKEN = os.environ.get("MATTERMOST_TOKEN", "")
MATTERMOST_CHANNEL = "intelligence"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TODAY = date.today().isoformat()

# ── Anthropic client ──────────────────────────────────────────────────────────

_claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


def _distil(venture_slug: str, raw_text: str) -> str:
    """Use Claude Haiku to distil key knowledge from raw session files."""
    if not _claude:
        return raw_text[:2000]

    try:
        resp = _claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=800,
            messages=[{
                "role": "user",
                "content": (
                    f"Venture: {venture_slug}\n\n"
                    "Below are raw agent session logs from today. "
                    "Extract key facts, decisions made, files created, errors hit, and lessons learned. "
                    "Write 3-8 bullet points. Be specific. Skip routine tool calls. Focus on WHAT was accomplished and WHY it matters.\n\n"
                    f"{raw_text[:6000]}"
                ),
            }],
        )
        return resp.content[0].text
    except Exception as e:
        return f"[Distillation failed: {e}]\n\nRaw:\n{raw_text[:1000]}"


def _post_mattermost(text: str) -> None:
    if not MATTERMOST_TOKEN:
        return
    try:
        # Find channel ID
        headers = {"Authorization": f"Bearer {MATTERMOST_TOKEN}"}
        channels_resp = httpx.get(
            f"{MATTERMOST_URL}/api/v4/channels/name/{MATTERMOST_CHANNEL}",
            headers=headers, timeout=10
        )
        if channels_resp.status_code != 200:
            return
        channel_id = channels_resp.json().get("id")
        if not channel_id:
            return
        httpx.post(
            f"{MATTERMOST_URL}/api/v4/posts",
            headers=headers,
            json={"channel_id": channel_id, "message": text},
            timeout=10,
        )
    except Exception:
        pass


def main() -> None:
    print(f"[brain-aggregator] Starting for {TODAY}")

    # Collect raw files from today across all venture dirs
    venture_files: dict[str, list[Path]] = {}
    for venture_dir in RAW_ROOT.iterdir():
        if venture_dir.is_dir() and venture_dir.name != "processed":
            files = [
                f for f in venture_dir.glob("*.md")
                if TODAY in f.name or f.stat().st_mtime > (datetime.now().timestamp() - 86400)
            ]
            if files:
                venture_files[venture_dir.name] = files

    if not venture_files:
        print("[brain-aggregator] No new files today.")
        return

    summaries: list[str] = []

    for venture_slug, files in sorted(venture_files.items()):
        print(f"  Processing venture: {venture_slug} ({len(files)} files)")

        # Concatenate all raw content for this venture today
        raw_parts = []
        for f in files:
            raw_parts.append(f"--- {f.name} ---\n{f.read_text()}")
        raw_text = "\n\n".join(raw_parts)

        distilled = _distil(venture_slug, raw_text)

        # Append to venture daily file
        venture_dir = VENTURES_ROOT / venture_slug
        venture_dir.mkdir(parents=True, exist_ok=True)
        daily_file = venture_dir / f"daily-{TODAY}.md"
        with daily_file.open("a") as out:
            out.write(f"\n## Aggregated {TODAY} ({len(files)} sessions)\n")
            out.write(distilled)
            out.write("\n")

        summaries.append(f"**{venture_slug}**: {len(files)} sessions processed.")

        # Move raw files to processed
        for f in files:
            dest = PROCESSED_ROOT / f.name
            # Handle name collision
            if dest.exists():
                stem, suffix = f.stem, f.suffix
                dest = PROCESSED_ROOT / f"{stem}-{venture_slug}{suffix}"
            f.rename(dest)

    # Post empire digest to Mattermost
    digest_lines = [
        f"**Empire Brain Digest — {TODAY}**",
        f"{len(venture_files)} ventures active today.\n",
        *summaries,
        "\nKnowledge routed to `/opt/openclaw/second-brain/ventures/`.",
    ]
    _post_mattermost("\n".join(digest_lines))
    print(f"[brain-aggregator] Done. {len(venture_files)} ventures, digest posted.")


if __name__ == "__main__":
    main()
