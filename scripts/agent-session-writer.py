#!/usr/bin/env python3
"""
agent-session-writer.py — PostToolUse hook for all CortexOS agents.

Fires after every tool call. Accumulates a session buffer in /tmp/,
then flushes to /opt/openclaw/second-brain/raw/ on Claude Code Stop.

Install: add to every agent .md file's PostToolUse hooks section:
  hooks:
    PostToolUse:
      - name: Second Brain Capture
        matcher: ".*"
        command: python3 /opt/openclaw/second-brain/agent-session-writer.py

Usage (called by Claude Code hook infrastructure):
  python3 agent-session-writer.py [--flush]
  - Without --flush: accumulate tool event to session buffer
  - With --flush: write buffer to second brain raw dir and clear

Environment variables set by Claude Code:
  CLAUDE_TOOL_NAME, CLAUDE_TOOL_INPUT, CLAUDE_TOOL_RESULT (JSON strings)
  CLAUDE_SESSION_ID, CLAUDE_AGENT_NAME (if set in agent config)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

BRAIN_RAW = Path("/opt/openclaw/second-brain/raw")
SESSION_DIR = Path(tempfile.gettempdir()) / "cortex-session-buffers"
SESSION_DIR.mkdir(exist_ok=True)

# Tools that carry knowledge worth capturing
KNOWLEDGE_TOOLS = {
    "Write", "Edit", "Bash", "WebFetch", "WebSearch",
    "Agent", "mcp__", "TodoWrite",
}

# Tools to skip (too noisy, no semantic value)
SKIP_TOOLS = {"Read", "Glob", "Grep", "ScheduleWakeup", "AskUserQuestion"}


def _session_id() -> str:
    return os.environ.get("CLAUDE_SESSION_ID", "unknown-session")


def _agent_name() -> str:
    return os.environ.get("CLAUDE_AGENT_NAME", os.environ.get("USER", "unknown-agent"))


def _venture_from_agent(agent_name: str) -> str:
    """Best-effort map from agent name to venture slug."""
    name_lower = agent_name.lower()
    venture_map = {
        "maren": "bloom-and-bub", "finn": "bloom-and-bub", "zoe": "bloom-and-bub",
        "wren": "handwritten-book", "atlas": "kdp-colouring-books",
        "kai": "lo-fi-engine", "murray": "ambient-escapes",
        "harper": "affiliate-empire", "callum": "the-footnote",
        "quant": "polymarket-tracker", "neve": "sage-ai", "sol": "sage-ai",
        "remy": "mapdrop", "geo": "mapdrop", "lena": "mapdrop",
        "scout": "domain-flipping", "bondi": "meal-plan-cart",
        "levi": "scroll-and-stone", "wonder": "weekly-wonder",
        "ellis": "wantsyoutoknow", "orbit": "cortexos", "helix": "cortexos",
        "lyra": "cortexos", "bolt": "cortexos", "hex": "cortexos",
        "cruz": "cudan-studio", "jordan": "cudan-studio",
        "kira": "cudan-studio", "maya": "cudan-studio",
        "einstein": "empire", "theodore": "empire", "felix": "empire",
        "nexus": "empire", "turing": "empire",
    }
    for key, venture in venture_map.items():
        if name_lower.startswith(key):
            return venture
    return "empire"


def _is_knowledge_bearing(tool_name: str) -> bool:
    if tool_name in SKIP_TOOLS:
        return False
    if any(tool_name.startswith(prefix) for prefix in KNOWLEDGE_TOOLS):
        return True
    return False


def _extract_insight(tool_name: str, tool_input: dict, tool_result: str) -> str | None:
    """Extract a concise insight string from a tool call, or None if not interesting."""
    if tool_name == "Write":
        path = tool_input.get("file_path", "")
        return f"Wrote file: {path}"
    if tool_name == "Edit":
        path = tool_input.get("file_path", "")
        old = str(tool_input.get("old_string", ""))[:80]
        return f"Edited {path}: changed '{old}...'"
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))[:120]
        result_snippet = str(tool_result)[:200].replace("\n", " ")
        return f"Ran: {cmd} → {result_snippet}"
    if tool_name == "WebFetch":
        url = tool_input.get("url", "")
        return f"Fetched: {url}"
    if tool_name == "WebSearch":
        query = tool_input.get("query", "")
        return f"Searched: {query}"
    if tool_name == "Agent":
        desc = tool_input.get("description", "")
        return f"Spawned agent: {desc}"
    if tool_name == "TodoWrite":
        todos = tool_input.get("todos", [])
        completed = [t["content"] for t in todos if t.get("status") == "completed"]
        if completed:
            return f"Completed tasks: {'; '.join(completed[:3])}"
    return None


def accumulate() -> None:
    """Add current tool call to session buffer."""
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    if not tool_name or not _is_knowledge_bearing(tool_name):
        return

    try:
        tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))
    except json.JSONDecodeError:
        tool_input = {}

    tool_result = os.environ.get("CLAUDE_TOOL_RESULT", "")
    insight = _extract_insight(tool_name, tool_input, tool_result)
    if not insight:
        return

    session_id = _session_id()
    buffer_file = SESSION_DIR / f"{session_id}.jsonl"
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "tool": tool_name,
        "insight": insight,
        "agent": _agent_name(),
    }
    with buffer_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def flush() -> None:
    """Write session buffer to second brain raw dir."""
    session_id = _session_id()
    agent_name = _agent_name()
    venture = _venture_from_agent(agent_name)
    buffer_file = SESSION_DIR / f"{session_id}.jsonl"

    if not buffer_file.exists():
        return

    entries = []
    with buffer_file.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not entries:
        buffer_file.unlink(missing_ok=True)
        return

    # Build a readable session summary
    date_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    time_str = datetime.now(tz=timezone.utc).strftime("%H%M%S")
    lines = [
        f"# Agent Session: {agent_name}",
        f"Date: {date_str}",
        f"Venture: {venture}",
        f"Session ID: {session_id}",
        f"Tool calls captured: {len(entries)}",
        "",
        "## Actions Taken",
    ]
    for e in entries:
        lines.append(f"- [{e['ts']}] {e['tool']}: {e['insight']}")

    # Write to venture-scoped raw dir
    venture_raw = BRAIN_RAW / venture
    venture_raw.mkdir(parents=True, exist_ok=True)
    out_file = venture_raw / f"{agent_name}-{date_str}-{time_str}.md"
    out_file.write_text("\n".join(lines) + "\n")

    # Cleanup buffer
    buffer_file.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flush", action="store_true",
                        help="Flush session buffer to second brain (call on Stop hook)")
    args = parser.parse_args()

    if args.flush:
        flush()
    else:
        accumulate()


if __name__ == "__main__":
    main()
