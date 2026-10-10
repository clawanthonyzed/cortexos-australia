"""Seed 6 real empire workflows into CortexOS database."""
from __future__ import annotations
import asyncio
import json
import uuid

import asyncpg

DATABASE_URL = "postgresql://cortexos:Clawanthonyzed2026!@postgres:5432/cortexos"

WORKFLOWS = [
    {
        "name": "Daily Empire Health Check",
        "description": "Every morning 7am AWST: sentinel reads MASTER-DASH, felix checks email, posts summary to Mattermost #general",
        "trigger_type": "scheduled",
        "cron_expression": "0 23 * * *",
        "status": "active",
        "config_json": {},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Sentinel: Read MASTER-DASH", "agent": "sentinel", "nodeType": "agent"}},
                {"id": "n2", "type": "agent", "position": {"x": 250, "y": 180}, "data": {"label": "Felix: Check Email Flags", "agent": "felix", "nodeType": "agent"}},
                {"id": "n3", "type": "agent", "position": {"x": 250, "y": 310}, "data": {"label": "Post Summary to #general", "agent": "felix", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"},
            ],
        },
        "steps": [
            {"name": "Sentinel reads MASTER-DASH", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "sentinel", "task": "Read MASTER-DASH.md and report empire status: active ventures, blockers, revenue alerts"}},
            {"name": "Felix checks email for urgent flags", "step_type": "agent_node", "order": 1, "node_id": "n2",
             "config_json": {"agent": "felix", "task": "Check empire email inbox for urgent flags, payment notifications, or client messages"}},
            {"name": "Post summary to Mattermost #general", "step_type": "agent_node", "order": 2, "node_id": "n3",
             "config_json": {"agent": "felix", "task": "Post empire health summary to Mattermost #general channel"}},
        ],
    },
    {
        "name": "New Product Launch Loop",
        "description": "Bloom & Bub: maren creates listing copy, zoe QC checks (min 9.5/10), pass -> Etsy, fail -> loop back with feedback",
        "trigger_type": "manual",
        "status": "active",
        "cron_expression": None,
        "config_json": {},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Maren: Create Listing Copy", "agent": "maren", "nodeType": "agent"}},
                {"id": "n2", "type": "agent", "position": {"x": 250, "y": 180}, "data": {"label": "Zoe: QC Check (min 9.5/10)", "agent": "zoe", "nodeType": "agent"}},
                {"id": "n3", "type": "condition", "position": {"x": 250, "y": 310}, "data": {"label": "Score >= 9.5?", "nodeType": "condition"}},
                {"id": "n4", "type": "agent", "position": {"x": 450, "y": 440}, "data": {"label": "Post to Etsy", "agent": "maren", "nodeType": "agent"}},
                {"id": "n5", "type": "agent", "position": {"x": 50, "y": 440}, "data": {"label": "Revise with Feedback", "agent": "maren", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"},
                {"id": "e3-4", "source": "n3", "target": "n4", "label": "pass"},
                {"id": "e3-5", "source": "n3", "target": "n5", "label": "fail"},
                {"id": "e5-1", "source": "n5", "target": "n1", "label": "retry"},
            ],
        },
        "steps": [
            {"name": "Maren creates listing copy", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "maren", "task": "Create Etsy product listing: title, description, 13 tags, 5 photos brief for new Bloom & Bub product"}},
            {"name": "Zoe QC check", "step_type": "agent_node", "order": 1, "node_id": "n2",
             "config_json": {"agent": "zoe", "task": "Score listing copy on 10-point scale. Minimum pass score: 9.5. Output: score, pass/fail, specific feedback"}},
            {"name": "Score gate (9.5 threshold)", "step_type": "condition_node", "order": 2, "node_id": "n3",
             "config_json": {"condition": "score >= 9.5", "on_pass": "n4", "on_fail": "n5", "max_retries": 3}},
            {"name": "Post to Etsy", "step_type": "agent_node", "order": 3, "node_id": "n4",
             "config_json": {"agent": "maren", "task": "Submit approved listing to Etsy via API"}},
            {"name": "Revise with Zoe feedback", "step_type": "agent_node", "order": 4, "node_id": "n5",
             "config_json": {"agent": "maren", "task": "Revise listing based on Zoe QC feedback, then loop back to QC"}},
        ],
    },
    {
        "name": "Weekly Revenue Report",
        "description": "Every Monday: pull revenue from Gumroad + Etsy + LemonSqueezy, compare vs MASTER-DASH targets, generate summary, post to #revenue",
        "trigger_type": "scheduled",
        "cron_expression": "0 23 * * 0",
        "status": "active",
        "config_json": {},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Pull Revenue: Gumroad + Etsy + LS", "agent": "felix", "nodeType": "agent"}},
                {"id": "n2", "type": "agent", "position": {"x": 250, "y": 180}, "data": {"label": "Compare vs MASTER-DASH Targets", "agent": "sentinel", "nodeType": "agent"}},
                {"id": "n3", "type": "agent", "position": {"x": 250, "y": 310}, "data": {"label": "Generate Weekly PDF Summary", "agent": "sentinel", "nodeType": "agent"}},
                {"id": "n4", "type": "agent", "position": {"x": 250, "y": 440}, "data": {"label": "Post to Mattermost #revenue", "agent": "felix", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"},
                {"id": "e3-4", "source": "n3", "target": "n4"},
            ],
        },
        "steps": [
            {"name": "Pull revenue from all platforms", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "felix", "task": "Fetch weekly revenue totals from Gumroad, Etsy, and LemonSqueezy APIs. Sum by venture."}},
            {"name": "Compare vs MASTER-DASH targets", "step_type": "agent_node", "order": 1, "node_id": "n2",
             "config_json": {"agent": "sentinel", "task": "Read MASTER-DASH revenue targets. Compare actual vs target for each venture. Flag gaps > 20%."}},
            {"name": "Generate weekly summary", "step_type": "agent_node", "order": 2, "node_id": "n3",
             "config_json": {"agent": "sentinel", "task": "Generate structured weekly revenue summary: total, by-venture breakdown, vs target, highlights, flags"}},
            {"name": "Post to #revenue channel", "step_type": "agent_node", "order": 3, "node_id": "n4",
             "config_json": {"agent": "felix", "task": "Post formatted weekly revenue report to Mattermost #revenue channel"}},
        ],
    },
    {
        "name": "Agent Onboarding Loop",
        "description": "Standard new agent onboarding: nexus creates .md, deploys to server, updates WORKFORCE.md, posts to #new-hires, rebuilds registry",
        "trigger_type": "manual",
        "status": "active",
        "cron_expression": None,
        "config_json": {},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Nexus: Create Agent .md File", "agent": "nexus", "nodeType": "agent"}},
                {"id": "n2", "type": "agent", "position": {"x": 250, "y": 180}, "data": {"label": "Deploy to /root/.claude/agents/", "agent": "nexus", "nodeType": "agent"}},
                {"id": "n3", "type": "agent", "position": {"x": 250, "y": 310}, "data": {"label": "Update WORKFORCE.md", "agent": "nexus", "nodeType": "agent"}},
                {"id": "n4", "type": "agent", "position": {"x": 250, "y": 440}, "data": {"label": "Post to Mattermost #new-hires", "agent": "nexus", "nodeType": "agent"}},
                {"id": "n5", "type": "agent", "position": {"x": 250, "y": 570}, "data": {"label": "Rebuild registry.json", "agent": "nexus", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"},
                {"id": "e3-4", "source": "n3", "target": "n4"},
                {"id": "e4-5", "source": "n4", "target": "n5"},
            ],
        },
        "steps": [
            {"name": "Nexus creates agent .md file", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "nexus", "task": "Create agent .md file with: name, venture, responsibilities, tools, skills, communication rules. Use standard template."}},
            {"name": "Deploy to server agents dir", "step_type": "agent_node", "order": 1, "node_id": "n2",
             "config_json": {"agent": "nexus", "task": "Deploy agent .md file to /root/.claude/agents/ on server via SSH"}},
            {"name": "Update WORKFORCE.md", "step_type": "agent_node", "order": 2, "node_id": "n3",
             "config_json": {"agent": "nexus", "task": "Add agent entry to /opt/openclaw/WORKFORCE.md under correct venture section"}},
            {"name": "Post to #new-hires", "step_type": "agent_node", "order": 3, "node_id": "n4",
             "config_json": {"agent": "nexus", "task": "Post new hire announcement to Mattermost #new-hires channel with agent name, venture, and responsibilities"}},
            {"name": "Rebuild registry.json", "step_type": "agent_node", "order": 4, "node_id": "n5",
             "config_json": {"agent": "nexus", "task": "Run build_registry.py to rebuild /opt/openclaw/orchestration/registry.json with new agent included"}},
        ],
    },
    {
        "name": "Content QC Loop",
        "description": "Empire-wide QC gate: zoe scores content (9.5/10), fail -> back to originating agent with feedback, loop max 3 attempts",
        "trigger_type": "event",
        "status": "active",
        "cron_expression": None,
        "config_json": {"event_trigger": "task_complete", "max_retries": 3},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Zoe: Score Content (9.5/10 target)", "agent": "zoe", "nodeType": "agent"}},
                {"id": "n2", "type": "condition", "position": {"x": 250, "y": 180}, "data": {"label": "Score >= 9.5? Attempts <= 3?", "nodeType": "condition"}},
                {"id": "n3", "type": "agent", "position": {"x": 450, "y": 310}, "data": {"label": "Deliver Approved Content", "agent": "zoe", "nodeType": "agent"}},
                {"id": "n4", "type": "agent", "position": {"x": 50, "y": 310}, "data": {"label": "Return to Agent with Feedback", "agent": "zoe", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3", "label": "pass"},
                {"id": "e2-4", "source": "n2", "target": "n4", "label": "fail"},
                {"id": "e4-1", "source": "n4", "target": "n1", "label": "retry"},
            ],
        },
        "steps": [
            {"name": "Zoe scores content", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "zoe", "task": "Score content on 10-point QC rubric: accuracy, tone, SEO, completeness, brand alignment. Output: score/10, pass/fail, line-level feedback"}},
            {"name": "QC gate (9.5 threshold, 3 max attempts)", "step_type": "condition_node", "order": 1, "node_id": "n2",
             "config_json": {"condition": "score >= 9.5 AND attempts <= 3", "on_pass": "n3", "on_fail": "n4"}},
            {"name": "Deliver approved content", "step_type": "agent_node", "order": 2, "node_id": "n3",
             "config_json": {"agent": "zoe", "task": "Mark content as QC-approved and deliver to requesting agent or venture"}},
            {"name": "Send feedback to originating agent", "step_type": "agent_node", "order": 3, "node_id": "n4",
             "config_json": {"agent": "zoe", "task": "Send structured feedback to originating agent: what failed, specific fixes needed, re-attempt counter"}},
        ],
    },
    {
        "name": "Cudan Studio Booking Loop",
        "description": "Webhook from Squarespace booking form: cruz receives inquiry, jordan checks calendar, kira drafts confirmation, send + add to calendar",
        "trigger_type": "webhook",
        "status": "active",
        "cron_expression": None,
        "config_json": {"webhook_source": "squarespace_booking_form"},
        "graph_json": {
            "nodes": [
                {"id": "n1", "type": "agent", "position": {"x": 250, "y": 50}, "data": {"label": "Cruz: Receive Booking Inquiry", "agent": "cruz", "nodeType": "agent"}},
                {"id": "n2", "type": "agent", "position": {"x": 250, "y": 180}, "data": {"label": "Jordan: Check Calendar Availability", "agent": "jordan", "nodeType": "agent"}},
                {"id": "n3", "type": "condition", "position": {"x": 250, "y": 310}, "data": {"label": "Date Available?", "nodeType": "condition"}},
                {"id": "n4", "type": "agent", "position": {"x": 450, "y": 440}, "data": {"label": "Kira: Draft Confirmation Email", "agent": "kira", "nodeType": "agent"}},
                {"id": "n5", "type": "agent", "position": {"x": 50, "y": 440}, "data": {"label": "Cruz: Send Alternatives", "agent": "cruz", "nodeType": "agent"}},
                {"id": "n6", "type": "agent", "position": {"x": 450, "y": 570}, "data": {"label": "Send Confirmation + Add to Calendar", "agent": "jordan", "nodeType": "agent"}},
            ],
            "edges": [
                {"id": "e1-2", "source": "n1", "target": "n2"},
                {"id": "e2-3", "source": "n2", "target": "n3"},
                {"id": "e3-4", "source": "n3", "target": "n4", "label": "available"},
                {"id": "e3-5", "source": "n3", "target": "n5", "label": "unavailable"},
                {"id": "e4-6", "source": "n4", "target": "n6"},
            ],
        },
        "steps": [
            {"name": "Cruz receives booking inquiry", "step_type": "agent_node", "order": 0, "node_id": "n1",
             "config_json": {"agent": "cruz", "task": "Parse webhook payload from Squarespace: client name, requested date/time, studio type, contact details"}},
            {"name": "Jordan checks calendar", "step_type": "agent_node", "order": 1, "node_id": "n2",
             "config_json": {"agent": "jordan", "task": "Check Cudan Studio calendar for requested date/time availability"}},
            {"name": "Availability gate", "step_type": "condition_node", "order": 2, "node_id": "n3",
             "config_json": {"condition": "date_available == true", "on_pass": "n4", "on_fail": "n5"}},
            {"name": "Kira drafts confirmation email", "step_type": "agent_node", "order": 3, "node_id": "n4",
             "config_json": {"agent": "kira", "task": "Draft warm confirmation email with: booking details, deposit instructions, studio address, what to bring"}},
            {"name": "Send alternatives if unavailable", "step_type": "agent_node", "order": 4, "node_id": "n5",
             "config_json": {"agent": "cruz", "task": "Reply to client with 3 alternative available dates and invite them to re-book"}},
            {"name": "Send confirmation + add to calendar", "step_type": "agent_node", "order": 5, "node_id": "n6",
             "config_json": {"agent": "jordan", "task": "Send Kira confirmation email to client and add booking to Cudan Studio Google Calendar"}},
        ],
    },
]


async def seed():
    conn = await asyncpg.connect(DATABASE_URL)
    seeded = 0
    try:
        for wf in WORKFLOWS:
            existing = await conn.fetchval(
                "SELECT id FROM workflows WHERE name = $1", wf["name"]
            )
            if existing:
                print(f"SKIP (exists): {wf['name']}")
                continue

            wf_id = str(uuid.uuid4())
            steps = wf.pop("steps", [])
            config_json = wf.pop("config_json", {})

            await conn.execute(
                """
                INSERT INTO workflows (id, name, description, graph_json, trigger_type, cron_expression,
                                       status, config_json, run_count, success_count, failure_count,
                                       created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0, 0, 0, NOW(), NOW())
                """,
                wf_id,
                wf["name"],
                wf.get("description", ""),
                json.dumps(wf["graph_json"]),
                wf["trigger_type"],
                wf.get("cron_expression"),
                wf.get("status", "active"),
                json.dumps(config_json),
            )

            for i, step in enumerate(steps):
                step_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO workflow_steps (id, workflow_id, name, description, step_type,
                                               config_json, "order", next_steps_json, node_id,
                                               created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                    """,
                    step_id,
                    wf_id,
                    step["name"],
                    step.get("description", ""),
                    step.get("step_type", "agent_node"),
                    json.dumps(step.get("config_json", {})),
                    step.get("order", i),
                    "[]",
                    step.get("node_id"),
                )

            print(f"SEEDED: {wf['name']} ({len(steps)} steps)")
            seeded += 1
    finally:
        await conn.close()

    print(f"\nDone: {seeded} workflows seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
