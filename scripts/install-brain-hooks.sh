#!/usr/bin/env bash
# install-brain-hooks.sh — Patch all 329 agent .md files with Second Brain capture hooks.
#
# Safe to run repeatedly (idempotent). Skips agents already patched.
# Backs up original .md to .md.bak before first patch.
#
# Usage:
#   bash /opt/openclaw/second-brain/install-brain-hooks.sh [--dry-run]
#
# Prereqs:
#   - Python 3 at /usr/bin/python3
#   - agent-session-writer.py at /opt/openclaw/second-brain/agent-session-writer.py
#   - Agent .md files at /root/.claude/agents/

set -euo pipefail

AGENTS_DIR="/root/.claude/agents"
WRITER="/opt/openclaw/second-brain/agent-session-writer.py"
DRY_RUN="${1:-}"
PATCHED=0
SKIPPED=0
ERRORS=0

# Hook block we inject — YAML-safe (ASCII only)
HOOK_BLOCK='
hooks:
  PostToolUse:
    - name: "Second Brain Capture"
      matcher: ".*"
      command: "python3 /opt/openclaw/second-brain/agent-session-writer.py"
  Stop:
    - command: "python3 /opt/openclaw/second-brain/agent-session-writer.py --flush"'

echo "[install-brain-hooks] Scanning $AGENTS_DIR..."

for md_file in "$AGENTS_DIR"/*.md; do
    [ -f "$md_file" ] || continue
    agent_name=$(basename "$md_file" .md)

    # Skip if already patched
    if grep -q "agent-session-writer.py" "$md_file" 2>/dev/null; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    if [ "$DRY_RUN" = "--dry-run" ]; then
        echo "  [DRY RUN] Would patch: $agent_name"
        PATCHED=$((PATCHED + 1))
        continue
    fi

    # Backup
    cp "$md_file" "${md_file}.bak"

    # Append hook block at end of file (after existing content)
    # Use python3 to safely append — avoids shell heredoc quoting issues
    python3 - "$md_file" "$agent_name" <<'PYEOF'
import sys
path = sys.argv[1]
agent = sys.argv[2]

content = open(path).read()

hook_section = f"""
## Auto-injected: Second Brain Capture Hooks

```yaml
hooks:
  PostToolUse:
    - name: "Second Brain Capture"
      matcher: ".*"
      command: "CLAUDE_AGENT_NAME={agent} python3 /opt/openclaw/second-brain/agent-session-writer.py"
  Stop:
    - command: "CLAUDE_AGENT_NAME={agent} python3 /opt/openclaw/second-brain/agent-session-writer.py --flush"
```
"""

if "agent-session-writer.py" not in content:
    with open(path, "a") as f:
        f.write(hook_section)
    print(f"  Patched: {agent}")
else:
    print(f"  Already patched (concurrent check): {agent}")
PYEOF

    PATCHED=$((PATCHED + 1))
done

echo ""
echo "[install-brain-hooks] Complete."
echo "  Patched: $PATCHED"
echo "  Skipped (already done): $SKIPPED"
echo "  Errors: $ERRORS"

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo ""
    echo "  (No changes made — dry run)"
fi
