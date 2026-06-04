# CortexOS Architecture

---

## System Overview

CortexOS is a multi-layer agentic operating system. Each layer has a single responsibility.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Users / External Systems                        │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTPS / WSS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Traefik (Reverse Proxy / TLS)                     │
│              Rate limiting · Security headers · ACME certs               │
└───────┬───────────────────────────┬─────────────────────────────────────┘
        │                           │
        ▼                           ▼
┌───────────────────┐   ┌───────────────────────────────────────────────┐
│   Next.js         │   │              FastAPI Backend                   │
│   Frontend        │   │                                               │
│   (React/TS)      │   │  ┌─────────────┐  ┌──────────────────────┐   │
│                   │   │  │  REST API   │  │  WebSocket / SSE     │   │
│  · Dashboard      │   │  │  /api/v1/   │  │  Real-time updates   │   │
│  · Agent studio   │   │  └──────┬──────┘  └──────────┬───────────┘   │
│  · Workflow editor│   │         │                     │               │
│  · Finance view   │   │  ┌──────▼─────────────────────▼───────────┐  │
│                   │   │  │           Service Layer                  │  │
└───────────────────┘   │  │  AgentService · TaskService             │  │
                        │  │  WorkflowService · MemoryService        │  │
                        │  │  FinanceService · AuthService           │  │
                        │  └──────────────────┬──────────────────────┘  │
                        │                     │                          │
                        │  ┌──────────────────▼──────────────────────┐  │
                        │  │           Agent Execution Engine         │  │
                        │  │                                         │  │
                        │  │  ┌────────────┐  ┌────────────────────┐│  │
                        │  │  │ BaseAgent  │  │  Tool Registry     ││  │
                        │  │  │ · plan()   │  │  · web_search      ││  │
                        │  │  │ · act()    │  │  · read_file       ││  │
                        │  │  │ · reflect()│  │  · run_code        ││  │
                        │  │  └────────────┘  │  · call_api        ││  │
                        │  │                  │  · mcp_*           ││  │
                        │  │  ┌────────────┐  └────────────────────┘│  │
                        │  │  │  LLM Layer │                         │  │
                        │  │  │ · Anthropic│                         │  │
                        │  │  │ · OpenAI   │                         │  │
                        │  │  │ · Gemini   │                         │  │
                        │  │  │ · OpenRtr  │                         │  │
                        │  │  └────────────┘                         │  │
                        │  └─────────────────────────────────────────┘  │
                        └───────────────────────────────────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌──────────────────┐    ┌───────────────────────┐   ┌──────────────────┐
│  PostgreSQL 16   │    │   Redis 7              │   │  Celery Workers  │
│  + pgvector      │    │                        │   │                  │
│                  │    │  · Task queue          │   │  · Async tasks   │
│  · Users         │    │  · Session cache       │   │  · Scheduled     │
│  · Agents        │    │  · Rate limit state    │   │    workflows     │
│  · Tasks         │    │  · Pub/sub for WS      │   │  · Integration   │
│  · Workflows     │    │  · Agent short-term    │   │    syncs         │
│  · Finance       │    │    memory              │   │  · Background    │
│  · Audit logs    │    │                        │   │    processing    │
│  · Embeddings    │    └───────────────────────┘   └──────────────────┘
│    (pgvector)    │
└──────────────────┘
          │
          ▼
┌──────────────────┐    ┌───────────────────────┐   ┌──────────────────┐
│    Neo4j 5.24    │    │  Langfuse              │   │  External APIs   │
│    + APOC        │    │  (LLM Observability)   │   │                  │
│                  │    │                        │   │  · Anthropic     │
│  · Entity graph  │    │  · Traces              │   │  · OpenAI        │
│  · Relationships │    │  · Generations         │   │  · Etsy          │
│  · Agent memory  │    │  · Cost tracking       │   │  · Gumroad       │
│    (Graphiti)    │    │  · Prompt versions     │   │  · GitHub        │
└──────────────────┘    └───────────────────────┘   └──────────────────┘
```

---

## Data Flow Diagrams

### User Triggers an Agent Task

```
User (browser)
    │
    │  POST /api/v1/tasks
    ▼
FastAPI → TaskService.create_task()
    │
    ├─→ Save task to PostgreSQL (status=pending)
    ├─→ Push task_id to Redis queue
    └─→ Return task_id to user (202 Accepted)

WebSocket (ws://localhost:8000/ws/{task_id})
    │
    │  User subscribes to task_id
    ▼
Celery Worker picks up task_id from Redis
    │
    ├─→ Load agent config from PostgreSQL
    ├─→ Inject memory context from Redis + Neo4j
    │
    ▼
AgentExecutionEngine.run(task)
    │
    ├─→ LLM call (Anthropic/OpenAI) → plan steps
    │     └─→ Langfuse traces every token
    │
    ├─→ Execute tools (search, API calls, code)
    │
    ├─→ LLM reflects on results
    │
    ├─→ Persist memory:
    │     ├─→ Short-term: Redis (TTL 24h)
    │     ├─→ Long-term: PostgreSQL
    │     ├─→ Embeddings: pgvector
    │     └─→ Graph: Neo4j via Graphiti
    │
    ├─→ Update task status in PostgreSQL
    └─→ Publish result to Redis pub/sub
          └─→ WebSocket pushes update to browser
```

### Workflow Execution

```
Workflow trigger (schedule / manual / webhook)
    │
    ▼
WorkflowEngine.execute(workflow_id)
    │
    ├─→ Load workflow DAG from PostgreSQL
    ├─→ Identify root nodes (no dependencies)
    │
    ▼
For each node in topological order:
    │
    ├─→ [agent_node]    → dispatch to AgentExecutionEngine
    ├─→ [condition_node] → evaluate condition, branch
    ├─→ [approval_node] → pause, notify human, await response
    ├─→ [tool_node]     → run tool directly (no LLM)
    └─→ [transform_node] → map/filter/reduce data
    │
    ├─→ Pass outputs to downstream nodes
    └─→ On completion: emit workflow.completed event
```

---

## Agent Execution Lifecycle

```
CREATE
  └─→ Validate config schema
  └─→ Assign default tools based on agent type
  └─→ Create agent record in PostgreSQL

ACTIVATE (task received)
  └─→ Load agent config
  └─→ Inject system prompt + persona
  └─→ Fetch memory context:
        ├─→ Redis: recent conversation history (last 20 turns)
        ├─→ PostgreSQL: long-term facts
        ├─→ pgvector: semantically similar past tasks (top-k)
        └─→ Neo4j: entity relationships relevant to task

PLAN
  └─→ LLM call: "Given context + tools available, plan steps"
  └─→ Output: ordered list of (tool, args) pairs
  └─→ Validate all tools are available

ACT (loop until done or max_steps)
  └─→ Execute next tool call
  └─→ Capture result
  └─→ LLM: "Given result, continue or stop?"
  └─→ If stop: produce final answer
  └─→ Langfuse traces each step

REFLECT
  └─→ LLM: "What did I learn? What should I remember?"
  └─→ Extract entities and relationships
  └─→ Store to memory layers

CLEANUP
  └─→ Update task status
  └─→ Emit completion event
  └─→ Release any held resources
```

---

## Memory System Architecture

CortexOS uses a four-layer memory system. Each layer optimises for a different access pattern.

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY SYSTEM                                 │
│                                                                 │
│  Layer 1: Working Memory (Redis, TTL 24h)                       │
│  ─────────────────────────────────────────────────────────────  │
│  What: Current conversation, active task state, tool results    │
│  Why:  Sub-millisecond reads. Lost on TTL — intentional.        │
│  Key pattern: agent:{id}:context:{task_id}                      │
│                                                                 │
│  Layer 2: Episodic Memory (PostgreSQL)                          │
│  ─────────────────────────────────────────────────────────────  │
│  What: Completed task transcripts, decisions, outcomes          │
│  Why:  Durable. Queryable by time, agent, outcome.              │
│  Table: agent_memories (id, agent_id, content, created_at)      │
│                                                                 │
│  Layer 3: Semantic Memory (PostgreSQL + pgvector)               │
│  ─────────────────────────────────────────────────────────────  │
│  What: Embedded facts, documents, knowledge chunks              │
│  Why:  Similarity search. "Find tasks like this one."           │
│  Table: memory_embeddings (id, content, embedding vector(1536)) │
│  Index: IVFFlat for fast ANN queries                            │
│                                                                 │
│  Layer 4: Graph Memory (Neo4j via Graphiti)                     │
│  ─────────────────────────────────────────────────────────────  │
│  What: Entities, relationships, causal chains                   │
│  Why:  "Who does this agent know? What caused this outcome?"    │
│  Nodes: Agent, Entity, Concept, Task, Outcome                   │
│  Edges: KNOWS, CAUSED, RELATED_TO, WORKED_ON, PRODUCED          │
└─────────────────────────────────────────────────────────────────┘
```

**Memory injection at task start:**

1. Working memory (Redis): immediate context, last N turns
2. Episodic (PostgreSQL): last 5 relevant completed tasks for this agent
3. Semantic (pgvector): top-5 similar tasks by embedding cosine similarity
4. Graph (Neo4j): entities mentioned in task + their 1-hop neighbours

Total injected context budget: 8,000 tokens (configurable per agent).

---

## MCP Integration Pattern

CortexOS supports the Model Context Protocol for extending agent tool capabilities.

```
Agent needs tool "fetch_webpage"
    │
    ▼
Tool Registry lookup
    │
    ├─→ [built-in tool]: execute directly
    │
    └─→ [MCP tool]: route to MCP handler
          │
          ├─→ Connect to MCP server (stdio or SSE)
          ├─→ Send tools/call request
          ├─→ Receive result
          └─→ Return to agent as tool output
```

**MCP servers** are configured per-agent in the agent config JSON:

```json
{
  "mcp_servers": [
    {
      "name": "filesystem",
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    },
    {
      "name": "brave-search",
      "type": "sse",
      "url": "http://mcp-brave:8080/sse"
    }
  ]
}
```

Each MCP server's tools are automatically registered in the tool registry when the agent is activated.
