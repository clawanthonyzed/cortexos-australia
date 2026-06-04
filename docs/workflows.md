# Workflows

Workflows connect multiple agents, tools, and human approvals into automated pipelines.

---

## Core Concepts

### Nodes

A node is a single step in a workflow. Each node has:

- **Type**: what kind of step it is (see node types below)
- **Config**: parameters specific to that node type
- **Inputs**: data it receives from upstream nodes
- **Outputs**: data it passes to downstream nodes

### Edges

Edges connect nodes. An edge means "when node A completes, send its output to node B."

Edges can be:
- **Unconditional**: always execute node B after node A
- **Conditional**: execute node B only if a condition on node A's output is true

### Conditions

Conditions evaluate node output. Examples:
- `output.score >= 9.5` — pass QC check
- `output.status == "approved"` — human approved
- `output.word_count > 500` — content is long enough
- `output.contains("error")` — error detection

---

## Node Types

| Type | Purpose |
|------|---------|
| `agent` | Execute an agent with a goal |
| `condition` | Branch based on output value |
| `approval` | Pause and wait for human response |
| `tool` | Run a tool directly (no LLM) |
| `transform` | Map / filter / reduce data |
| `trigger` | Workflow entry point (manual, schedule, webhook) |
| `output` | Workflow exit point (emit result) |

---

## Building Workflows in the UI

### Step 1: Open the Workflow Editor

Go to **Workflows** → **New Workflow**.

You'll see a blank canvas with a **Trigger** node pre-placed.

### Step 2: Configure the Trigger

Click the Trigger node and choose:
- **Manual**: users run it from the dashboard
- **Schedule**: cron expression (e.g., `0 9 * * 1-5` = weekdays at 9am)
- **Webhook**: external system POSTs to `/api/v1/workflows/{id}/trigger`

### Step 3: Add Nodes

Click **+ Add Node** in the toolbar. Drag it onto the canvas. Configure it in the right panel.

**Agent node configuration:**
```
Agent:  [select from dropdown]
Goal:   Write a 1000-word blog post about {{input.topic}}
Inputs: topic (from trigger)
```

Use `{{variable}}` to reference data from upstream nodes.

### Step 4: Connect Nodes

Click and drag from a node's output port to another node's input port. A blue edge appears.

For conditional edges: right-click the edge → **Add condition** → enter expression.

### Step 5: Test the Workflow

Click **Run Test** in the toolbar. Enter test inputs. Watch nodes execute in real-time on the canvas (green = running, tick = done, red = error).

### Step 6: Activate

Toggle **Active** in the top-right. The workflow is now live.

---

## Workflow Templates

### Content Production Pipeline

```
Trigger (manual: topic)
    │
    ▼
Research Agent
    │  output: research_notes
    ▼
Writer Agent (goal: "Write article based on {{research_notes}}")
    │  output: draft
    ▼
QC Agent (goal: "Score this draft: {{draft}}")
    │
    ├─→ [score < 9.5] ──→ Writer Agent (revise) ──→ QC Agent
    │
    └─→ [score ≥ 9.5] ──→ Output (article ready)
```

### Daily Finance Digest

```
Trigger (schedule: 0 8 * * *)
    │
    ▼
Finance Agent (goal: "Summarise yesterday's revenue and expenses")
    │  output: finance_summary
    ▼
Writer Agent (goal: "Format {{finance_summary}} as executive email")
    │  output: email_body
    ▼
Tool: Send Email (to: ceo@company.com, body: {{email_body}})
    │
    ▼
Output
```

### Product Launch Sequence

```
Trigger (webhook: product_data)
    │
    ▼
[Parallel fan-out]
    ├─→ Writer Agent (blog post)
    ├─→ Writer Agent (email sequence)
    └─→ Writer Agent (social media captions)
    │
    ▼
[Merge: collect all 3 outputs]
    │
    ▼
Approval Gate (human reviews all 3 pieces)
    │
    ├─→ [rejected] ──→ Notify user, stop
    │
    └─→ [approved] ──→ Tool: Publish (blog + email + social)
    │
    ▼
Output
```

---

## Human Approval Gates

An approval node pauses the workflow and sends a notification to a designated reviewer.

**Configuration:**

```json
{
  "type": "approval",
  "reviewers": ["user@example.com"],
  "message": "Please review the draft before publishing: {{input.draft}}",
  "timeout_hours": 48,
  "on_timeout": "reject"
}
```

**Reviewer experience:**

1. Email notification with summary and preview
2. Reviewer opens CortexOS → **Approvals** tab
3. Reviews full content in side panel
4. Clicks **Approve** or **Reject** (with optional comment)
5. Workflow continues or stops based on decision

**Timeout behaviour:**

| `on_timeout` | What happens |
|-------------|-------------|
| `reject` | Workflow stops, task marked failed |
| `approve` | Workflow continues as if approved |
| `escalate` | Sends to next reviewer in list |

---

## Scheduling Workflows

Use standard cron syntax in the trigger configuration.

```
┌──────── minute (0–59)
│ ┌────── hour (0–23)
│ │ ┌──── day of month (1–31)
│ │ │ ┌── month (1–12)
│ │ │ │ ┌ day of week (0–7, Sunday=0 or 7)
│ │ │ │ │
* * * * *
```

**Common schedules:**

| Schedule | Cron |
|---------|------|
| Every day at 8am | `0 8 * * *` |
| Weekdays at 9am | `0 9 * * 1-5` |
| Every hour | `0 * * * *` |
| Every Monday at 7am | `0 7 * * 1` |
| First day of month | `0 9 1 * *` |

Scheduled workflows run in the Celery beat scheduler. Timezone is configurable per workflow (default: UTC).

---

## Workflow Data Model

```json
{
  "id": "wf_01abc",
  "name": "Content Production",
  "description": "Research → Write → QC loop",
  "trigger": {
    "type": "manual",
    "input_schema": {
      "topic": { "type": "string", "required": true },
      "target_length": { "type": "integer", "default": 1000 }
    }
  },
  "nodes": [
    {
      "id": "n1",
      "type": "agent",
      "agent_id": "agent_research",
      "goal": "Research the topic: {{trigger.topic}}",
      "position": { "x": 100, "y": 100 }
    },
    {
      "id": "n2",
      "type": "agent",
      "agent_id": "agent_writer",
      "goal": "Write a {{trigger.target_length}}-word article using: {{n1.output}}",
      "position": { "x": 100, "y": 300 }
    }
  ],
  "edges": [
    { "from": "trigger", "to": "n1" },
    { "from": "n1", "to": "n2" }
  ],
  "is_active": true,
  "created_at": "2026-06-02T00:00:00Z"
}
```
