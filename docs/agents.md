# Agents

Agents are the core execution unit in CortexOS. Each agent is a configurable AI entity that can plan, use tools, and retain memory across tasks.

---

## What Is an Agent?

An agent is a combination of:

- **Identity**: name, description, persona, system prompt
- **Capability**: which LLM model to use, which tools are available
- **Memory**: what it remembers across tasks and how much context it injects
- **Behaviour**: max steps per task, temperature, retry policy

Agents do not hold state between tasks by default. State is externalised to the memory system (Redis + PostgreSQL + Neo4j).

---

## BaseAgent Lifecycle

Every agent — whether built-in or custom — goes through this lifecycle:

```
1. LOAD
   └─→ Load agent config from database
   └─→ Build system prompt from template + variables
   └─→ Discover available tools (built-ins + MCP)

2. PLAN
   └─→ Receive task (goal + context)
   └─→ Inject memory context (see architecture.md)
   └─→ Call LLM: produce ordered list of tool calls

3. ACT (loop, up to max_steps)
   └─→ Execute next planned tool call
   └─→ Capture output
   └─→ Call LLM: continue, re-plan, or finish?

4. REFLECT
   └─→ Summarise what was learned
   └─→ Extract entities for graph memory
   └─→ Write episodic memory entry

5. RETURN
   └─→ Emit final answer / artefacts
   └─→ Update task status
```

---

## Creating a Custom Agent

### Via the UI

1. Go to **Agents** → **New Agent**
2. Fill in name, description, and select a base template
3. Write your system prompt in the editor
4. Add tools from the tool palette
5. Click **Save** — the agent is immediately available for tasks

### Via the API

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Market Researcher",
    "description": "Researches market trends and competitor activity",
    "system_prompt": "You are a sharp market research analyst...",
    "model": "claude-sonnet-4-5",
    "provider": "anthropic",
    "tools": ["web_search", "read_url", "extract_structured_data"],
    "max_steps": 15,
    "temperature": 0.3
  }'
```

### Via config file (import)

```json
{
  "name": "Market Researcher",
  "description": "Researches market trends and competitor activity",
  "system_prompt": "You are a sharp market research analyst. You always cite sources. You prefer primary data over secondary. When researching competitors, you look for pricing, positioning, and customer sentiment.",
  "model": "claude-sonnet-4-5",
  "provider": "anthropic",
  "tools": [
    "web_search",
    "read_url",
    "extract_structured_data",
    "write_file"
  ],
  "max_steps": 15,
  "temperature": 0.3,
  "memory": {
    "short_term_ttl": 86400,
    "max_context_tokens": 8000,
    "embed_outputs": true,
    "graph_enabled": true
  },
  "mcp_servers": []
}
```

Import via: `POST /api/v1/agents/import` with the JSON body.

---

## Agent Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Display name. Must be unique per workspace. |
| `description` | string | "" | Shown in the UI agent list. |
| `system_prompt` | string | required | The agent's core instruction set. Supports `{{variable}}` templating. |
| `model` | string | `claude-sonnet-4-5` | LLM model identifier. |
| `provider` | enum | `anthropic` | `anthropic` · `openai` · `google` · `openrouter` |
| `temperature` | float | `0.7` | 0.0 = deterministic, 1.0 = creative. |
| `max_tokens` | int | `4096` | Max tokens in a single LLM response. |
| `max_steps` | int | `10` | Max tool calls per task before forced stop. |
| `tools` | string[] | `[]` | Tool IDs the agent can use. See tool registry. |
| `mcp_servers` | object[] | `[]` | MCP server configs. See architecture.md. |
| `memory.short_term_ttl` | int | `86400` | Redis TTL in seconds (default: 24h). |
| `memory.max_context_tokens` | int | `8000` | Max tokens injected from memory. |
| `memory.embed_outputs` | bool | `true` | Embed task outputs for semantic search. |
| `memory.graph_enabled` | bool | `true` | Extract entities for Neo4j graph. |
| `is_active` | bool | `true` | Inactive agents cannot receive tasks. |
| `tags` | string[] | `[]` | Freeform tags for filtering. |
| `metadata` | object | `{}` | Arbitrary key-value pairs for your use. |

---

## Default Agents

CortexOS ships with these agents. They are created during `make seed`.

### CEO Agent

**ID:** `agent_ceo`  
**Model:** `claude-opus-4-5`  
**Purpose:** High-level strategic planning, goal decomposition, cross-agent delegation.  
**Tools:** `delegate_task`, `read_file`, `write_file`, `web_search`  
**System prompt focus:** Breaks large goals into subtasks, assigns them to specialist agents, synthesises results into executive summaries.

### Research Analyst

**ID:** `agent_research`  
**Model:** `claude-sonnet-4-5`  
**Purpose:** Deep research on any topic. Produces structured reports.  
**Tools:** `web_search`, `read_url`, `extract_structured_data`, `write_file`  
**System prompt focus:** Cites sources, distinguishes primary from secondary data, flags speculation.

### Content Writer

**ID:** `agent_writer`  
**Model:** `claude-sonnet-4-5`  
**Purpose:** Produces long-form content: blog posts, product descriptions, email sequences.  
**Tools:** `web_search`, `read_file`, `write_file`, `humanize_text`  
**System prompt focus:** Matches brand voice, avoids AI-sounding patterns, optimises for the target platform.

### Finance Analyst

**ID:** `agent_finance`  
**Model:** `claude-sonnet-4-5`  
**Purpose:** Revenue tracking, expense categorisation, P&L generation.  
**Tools:** `read_file`, `write_file`, `calculate`, `query_database`  
**System prompt focus:** Precise numbers, flags anomalies, produces tables.

### QC Inspector

**ID:** `agent_qc`  
**Model:** `claude-opus-4-5`  
**Purpose:** Reviews output from other agents. Scores on a 0–10 scale. Rejects below 9.5.  
**Tools:** `read_file`, `web_search`  
**System prompt focus:** Applies stop-slop patterns, checks factual accuracy, flags vague claims.

---

## Agent Execution Patterns

### Single Agent

```
Task → Agent → Result
```

Use for: self-contained tasks. Research, content, analysis.

### Sequential Pipeline

```
Task → Agent A → Agent B → Agent C → Result
```

Use for: research → write → QC review.  
Configured as a workflow with linear edges.

### Parallel Fan-out

```
              ┌─→ Agent A (research)  ─┐
Task → Router ├─→ Agent B (competitor) ─┼─→ Synthesiser → Result
              └─→ Agent C (pricing)   ─┘
```

Use for: parallel information gathering, then synthesis.

### Human-in-the-Loop

```
Task → Agent → [APPROVAL GATE] → Agent continues → Result
                 │
                 └─→ Human reviews and approves/rejects in UI
```

Use for: high-stakes decisions (publishing content, sending emails, making purchases).

### Reflection Loop

```
Task → Agent → QC Agent → [score < 9.5] → Agent (revise) → QC → ...
                         → [score ≥ 9.5] → Result
```

Use for: ensuring quality output without manual review.
