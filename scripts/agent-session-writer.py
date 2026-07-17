#!/usr/bin/env python3
"""
agent-session-writer.py — PostToolUse/Stop hook for all CortexOS agents.

Fires after every tool call. Accumulates a session buffer in /tmp/,
then flushes to /opt/openclaw/second-brain/raw/ AND to CortexOS memory
(SPEC-COS-16) on Claude Code Stop.

Canonical source: /opt/cortexos/scripts/agent-session-writer.py (this repo).
Wired GLOBALLY in /root/.claude/settings.json's PostToolUse/Stop hooks —
NOT per-agent .md frontmatter (that was this docstring's original, incorrect
install instruction; per-agent .md files here don't support inline hooks
config, and as of 2026-07-17 zero of 330 agent files referenced this script
at all — it had never actually run). One settings.json edit covers every
agent since they all share the same root-level Claude Code config.

Usage (called by Claude Code hook infrastructure):
  python3 agent-session-writer.py [--flush]
  - Without --flush: accumulate tool event to session buffer (PostToolUse)
  - With --flush: write buffer to second brain + CortexOS, then clear (Stop)

Agent identity: read from the hook's stdin JSON `.metadata.agent` /
`.metadata.venture` first (the channel notify-mattermost.sh already uses),
falling back to CLAUDE_TOOL_NAME/CLAUDE_AGENT_NAME env vars if stdin doesn't
carry it. The env-var-only approach this script originally used had never
been verified to actually populate in this harness.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

BRAIN_RAW = Path("/opt/openclaw/second-brain/raw")
SESSION_DIR = Path(tempfile.gettempdir()) / "cortex-session-buffers"
SESSION_DIR.mkdir(exist_ok=True)

# SPEC-COS-16 — direct write path to CortexOS memory. Internal-only
# (localhost, not the public Traefik route). Reads the shared write token
# straight from the server-local .env rather than requiring every one of
# 329 agent environments to have it individually exported.
CORTEXOS_MEMORY_URL = "http://localhost:8200/api/v1/memory"
CORTEXOS_ENV_FILE = Path("/opt/cortexos/.env")

# Tools that carry knowledge worth capturing
KNOWLEDGE_TOOLS = {
    "Write", "Edit", "Bash", "WebFetch", "WebSearch",
    "Agent", "mcp__", "TodoWrite",
}

# Tools to skip (too noisy, no semantic value)
SKIP_TOOLS = {"Read", "Glob", "Grep", "ScheduleWakeup", "AskUserQuestion"}


def _read_hook_stdin() -> dict:
    """
    Claude Code hooks receive a JSON payload on stdin (this is how
    notify-mattermost.sh gets `.metadata.agent`/`.metadata.venture` — a
    more reliable channel than the CLAUDE_AGENT_NAME env var, which per
    this script's own original docstring is only set "if set in agent
    config" — i.e. not guaranteed). Read once, defensively.
    """
    try:
        if sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _session_id(hook_input: dict) -> str:
    return (
        hook_input.get("session_id")
        or os.environ.get("CLAUDE_SESSION_ID")
        or "unknown-session"
    )


def _agent_name(hook_input: dict) -> str:
    metadata = hook_input.get("metadata") or {}
    return (
        metadata.get("agent")
        or hook_input.get("agent_name")
        or os.environ.get("CLAUDE_AGENT_NAME")
        or os.environ.get("USER")
        or "unknown-agent"
    )


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


def accumulate(hook_input: dict) -> None:
    """Add current tool call to session buffer."""
    tool_name = hook_input.get("tool_name") or os.environ.get("CLAUDE_TOOL_NAME", "")
    if not tool_name or not _is_knowledge_bearing(tool_name):
        return

    tool_input = hook_input.get("tool_input")
    if tool_input is None:
        try:
            tool_input = json.loads(os.environ.get("CLAUDE_TOOL_INPUT", "{}"))
        except json.JSONDecodeError:
            tool_input = {}

    tool_result = hook_input.get("tool_response") or os.environ.get("CLAUDE_TOOL_RESULT", "")
    insight = _extract_insight(tool_name, tool_input, tool_result)
    if not insight:
        return

    session_id = _session_id(hook_input)
    buffer_file = SESSION_DIR / f"{session_id}.jsonl"
    entry = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
        "tool": tool_name,
        "insight": insight,
        "agent": _agent_name(hook_input),
    }
    with buffer_file.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def _agent_write_token() -> str | None:
    try:
        for line in CORTEXOS_ENV_FILE.read_text().splitlines():
            if line.startswith("AGENT_WRITE_TOKEN="):
                token = line.split("=", 1)[1].strip()
                return token or None
    except OSError:
        pass
    return None


def _post_to_cortexos(agent_name: str, content: str) -> None:
    """
    Push the session summary straight into CortexOS memory. Best-effort —
    a CortexOS outage must never break the agent session, so any failure
    here is logged and swallowed. The file written by flush() above is the
    fallback of record regardless of whether this succeeds.
    """
    token = _agent_write_token()
    if not token:
        return

    body = json.dumps({
        "content": content[:8000],
        "memory_type": "episodic",
        "category": "session-summary",
    }).encode("utf-8")
    req = urllib.request.Request(
        CORTEXOS_MEMORY_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Agent-Name": agent_name,
            "Content-Type": "application/json",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except (urllib.error.URLError, OSError) as exc:
        print(f"agent-session-writer: cortexos write failed: {exc}", file=sys.stderr)


def flush(hook_input: dict) -> None:
    """Write session buffer to second brain raw dir."""
    session_id = _session_id(hook_input)
    agent_name = _agent_name(hook_input)
    venture = (hook_input.get("metadata") or {}).get("venture") or _venture_from_agent(agent_name)
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

    summary_text = "\n".join(lines) + "\n"

    # Write to venture-scoped raw dir (fallback of record)
    venture_raw = BRAIN_RAW / venture
    venture_raw.mkdir(parents=True, exist_ok=True)
    out_file = venture_raw / f"{agent_name}-{date_str}-{time_str}.md"
    out_file.write_text(summary_text)

    # SPEC-COS-16 — also write live, in addition to the file above.
    _post_to_cortexos(agent_name, summary_text)

    # Cleanup buffer
    buffer_file.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--flush", action="store_true",
                        help="Flush session buffer to second brain (call on Stop hook)")
    args = parser.parse_args()

    hook_input = _read_hook_stdin()

    if args.flush:
        flush(hook_input)
    else:
        accumulate(hook_input)


if __name__ == "__main__":
    main()
