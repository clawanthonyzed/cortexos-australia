#!/usr/bin/env python3
"""Build the EmpireOS Resources catalog (2026-10-10).

Runs on the host (cron) because only the host can see `claude mcp list`, docker, Ollama and /root/CLAUDE.md.
Writes /opt/openclaw/orchestration/resources_catalog.json, which the backend serves read-only at
GET /api/v1/resources. Never writes anywhere else.
"""
import json
import re
import shutil
import socket
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SKILLS = Path("/opt/openclaw/shared/skills")
OUT = Path("/opt/openclaw/orchestration/resources_catalog.json")
CLAUDE_MD = Path("/root/CLAUDE.md")

CATEGORY_RULES = [
    ("Scraping", r"scrap|crawl|browser|web.?fetch|harvest|playwright|selenium|spider|webclaw|firecrawl|apify"),
    ("Financial Analytics", r"financ|trading|trade|quant|stock|market data|hedge|portfolio|invest|crypto|polymarket|kronos|qlib|dexter|account|tax|budget"),
    ("Media & Content", r"video|image|audio|music|voice|speech|tts|podcast|photo|animation|youtube|instagram|content|writ|book|kdp|design|art|lofi|lo-fi|comic|character|thumbnail|subtitle|ghibli"),
    ("Storage", r"memory|knowledge|graph|vault|database|storage|notes|obsidian|rag|vector|index|sync|backup|bookmark"),
    ("Business & Marketing", r"seo|marketing|affiliate|sales|crm|email|newsletter|business|ecommerce|etsy|amazon|reseller|brand|ads|lead"),
    ("Dev Tools", r"code|coding|dev|git|test|debug|cli|api|sdk|framework|agent|claude|mcp|deploy|docker|sandbox|lint|repo|engineer|security|bug"),
]


def categorise(text):
    t = text.lower()
    for cat, rx in CATEGORY_RULES:
        if re.search(rx, t):
            return cat
    return "AI & Automation"


def clean(s, n=220):
    s = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)|\[([^\]]*)\]\([^)]*\)|[*_`#>|]", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return (s[: n - 1] + "…") if len(s) > n else s


def describe(d):
    sk = d / "SKILL.md"
    if sk.exists():
        m = re.search(r"^description:\s*(.+)$", sk.read_text(errors="ignore")[:4000], re.M)
        if m:
            return clean(m.group(1).strip("\"' "))
    for name in ("README.md", "readme.md", "README.rst", "README"):
        f = d / name
        if f.exists():
            for line in f.read_text(errors="ignore")[:12000].splitlines():
                l = clean(line.strip(), 400)
                ascii_ratio = sum(c.isascii() for c in l) / max(len(l), 1)
                if (len(l) > 40 and len(l.split()) >= 7 and ascii_ratio > 0.95
                        and not line.strip().startswith(("#", "!", "[!", "<", "|", "```", "---", "=", "http", ">"))
                        and not re.search(r"badge|shields\.io|https?://\S+$|^\W", l, re.I)):
                    return clean(l)
    return "Installed skill. No description file found."


def assignments():
    """Map normalised tool names to 'ASSIGNED TO' text from the root CLAUDE.md skill lists."""
    out = {}
    if not CLAUDE_MD.exists():
        return out
    for line in CLAUDE_MD.read_text(errors="ignore").splitlines():
        m = re.match(r"\s*-\s+\*\*([^*]+)\*\*.*?ASSIGNED TO:\s*([^\n]+)", line)
        if m:
            who = re.split(r"\.\s|\. ?$", m.group(2).strip())[0].strip(" .")
            for name in re.split(r"[+/,]| and ", m.group(1)):
                out[re.sub(r"[^a-z0-9]", "", name.lower())] = who
    return out


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def port_open(port):
    with socket.socket() as s:
        s.settimeout(1.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def run(cmd, timeout=90):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def main():
    assign = assignments()
    res = []

    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir() and not p.name.startswith(".")):
        desc = describe(d)
        users = next((v for k, v in assign.items() if k and (k == norm(d.name) or (len(k) > 4 and k in norm(d.name)))), "Any agent (on demand)")
        res.append({"name": d.name, "kind": "Skill", "category": categorise(d.name + " " + desc),
                    "description": desc, "users": users, "status": "Active", "location": str(d)})

    # Command-line tools agents rely on (verified present, not assumed).
    tools = [
        ("crawl4ai", "Scraping", "Headless Chromium crawler with stealth mode. First escalation when a site returns 403 or a Cloudflare block (Anti-Block Protocol).", "All agents (dforge-harvester, researchers)", ["python3", "-c", "import crawl4ai"]),
        ("yt-dlp", "Media & Content", "Downloads video or audio from YouTube and 1,000+ sites for analysis.", "Kai, Cruz, Murray", ["which", "yt-dlp"]),
        ("ffmpeg", "Media & Content", "Converts, trims and transcodes audio and video.", "Kai, Sol, Cruz, Murray", ["which", "ffmpeg"]),
        ("gh (GitHub CLI)", "Dev Tools", "Creates repos, commits, PRs and releases on GitHub. All venture files are stored there.", "All managers", ["which", "gh"]),
        ("graphify", "Storage", "Turns a codebase into a searchable knowledge graph.", "Einstein, Theodore, Turing", ["which", "graphify"]),
    ]
    for name, cat, desc, users, probe in tools:
        ok = subprocess.run(probe, capture_output=True).returncode == 0
        res.append({"name": name, "kind": "Tool", "category": cat, "description": desc, "users": users,
                    "status": "Active" if ok else "Offline", "location": "server"})

    # MCP servers (live health from the Claude Code registry).
    mcp_desc = {
        "memory": ("Storage", "Long-term knowledge graph memory shared across sessions.", "Theodore, Einstein"),
        "codegraph": ("Dev Tools", "Code knowledge graph: finds functions and links fast with far fewer file reads.", "All developers"),
        "headroom": ("AI & Automation", "Compresses long context so agents use fewer tokens.", "All agents"),
        "tavily": ("Scraping", "Web search API built for AI agents.", "Researchers"),
        "sequential-thinking": ("AI & Automation", "Forces step-by-step reasoning on hard problems.", "All agents"),
        "excel": ("Financial Analytics", "Reads and writes Excel workbooks.", "Harper, Cruz, Theodore"),
        "opensandbox": ("Dev Tools", "Runs untrusted code safely in an isolated sandbox.", "Turing, Hex"),
        "firecrawl": ("Scraping", "Website crawl and clean-text extraction (MCP wrapper).", "Researchers"),
        "n8n-mcp": ("AI & Automation", "Lets agents build and inspect n8n workflows.", "Harper, Scout"),
        "markdownify-mcp": ("Media & Content", "Converts web pages, PDFs and documents into Markdown.", "Researchers"),
        "playwright": ("Scraping", "Drives a real browser: click, type, screenshot.", "Idea Lobster, QA"),
    }
    for line in run(["claude", "mcp", "list"], 120).splitlines():
        m = re.match(r"^([\w.-]+):\s.*-\s*(✓|✗)\s*(.+)$", line.strip())
        if m:
            cat, desc, users = mcp_desc.get(m.group(1), ("AI & Automation", "MCP server registered with Claude Code.", "Any agent"))
            res.append({"name": m.group(1), "kind": "MCP server", "category": cat, "description": desc, "users": users,
                        "status": "Active" if m.group(2) == "✓" else "Offline", "location": "server (claude mcp)"})

    # AI models and routes.
    free_chain = ["nvidia/nemotron-3-super-120b-a12b:free", "liquid/lfm-2.5-2.6b:free", "google/gemma-4-31b-it:free", "nvidia/nemotron-3.5-lightning:free"]
    gate_ok, hub_ok = port_open(8900), port_open(8400)
    res.append({"name": "Spending Gate (free route)", "kind": "AI route", "category": "AI & Automation",
                "description": "Routes agent work to $0 models first (x-gate-tier: free) and blocks paid calls without approval. About 50 free calls/day before OpenRouter rate-limits (resets 08:00 AWST).",
                "users": "All agents via the A2A executor", "status": "Free tier" if gate_ok else "Offline", "location": "port 8900"})
    for m in free_chain:
        res.append({"name": m, "kind": "AI model", "category": "AI & Automation",
                    "description": "Free OpenRouter model in the Spending Gate fallback chain (A$0.00).",
                    "users": "All agents (free route)", "status": "Free tier", "location": "OpenRouter"})
    try:
        tags = json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3))["models"]
        for t in tags:
            n = t["name"]
            if not re.match(r"^(llama|nomic|qwen|mistral|gemma|phi|deepseek|glm|kimi|minimax)", n):
                continue  # skip unrecognised/test models
            local = not n.endswith(":cloud")
            res.append({"name": f"Ollama {n}", "kind": "AI model", "category": "AI & Automation",
                        "description": ("Runs on our own server (CPU). Last fallback in the free chain." if local else "Ollama cloud model, reached through the local Ollama service.")
                        if "embed" not in n else "Turns text into vectors for semantic search.",
                        "users": "Free route fallback, embeddings", "status": "Active" if local else "Free tier", "location": "Ollama :11434"})
    except Exception:
        res.append({"name": "Ollama", "kind": "AI model", "category": "AI & Automation", "description": "Local model server.",
                    "users": "Free route fallback", "status": "Offline", "location": ":11434"})
    res.append({"name": "A2A hub + executor", "kind": "AI route", "category": "AI & Automation",
                "description": "Agent-to-agent task hub: managers dispatch work to named agents, mirrored onto EmpireOS Tasks.",
                "users": "Idea Lobster, all managers", "status": "Active" if hub_ok else "Offline", "location": "port 8400"})

    # Databases and storage.
    running = set(run(["docker", "ps", "--format", "{{.Names}}"]).split())
    dbs = [
        ("PostgreSQL (EmpireOS)", "cortexos-postgres-1", "Main EmpireOS database: agents, ventures, tasks, finance, memories."),
        ("Neo4j knowledge graph", "cortexos-neo4j-1", "Graph database behind the Knowledge Graph tab."),
        ("Redis (EmpireOS)", "cortexos-redis-1", "Fast cache and job queue for EmpireOS background workers."),
        ("Redis (empire)", "empire_redis", "Cache and queue for empire automation services."),
    ]
    for name, container, desc in dbs:
        res.append({"name": name, "kind": "Database", "category": "Storage", "description": desc, "users": "EmpireOS, all agents",
                    "status": "Active" if container in running else "Offline", "location": container})
    vault = Path("/opt/openclaw/second-brain")
    notes = sum(1 for _ in vault.rglob("*.md")) if vault.exists() else 0
    res.append({"name": "Second Brain vault", "kind": "Database", "category": "Storage",
                "description": f"The empire's shared notes ({notes:,} Markdown notes), synced to GitHub every 30 minutes. Readable on the Second Brain tab.",
                "users": "All agents", "status": "Active" if notes else "Offline", "location": str(vault)})

    kinds = {}
    for r in res:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    OUT.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "counts": kinds, "total": len(res), "resources": res}, indent=1, ensure_ascii=False))
    print(f"catalog: {len(res)} resources {kinds}")


if __name__ == "__main__":
    main()
