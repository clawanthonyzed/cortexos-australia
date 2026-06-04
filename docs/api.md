# API Reference

Base URL: `http://localhost:8000/api/v1`  
All endpoints require `Authorization: Bearer <token>` unless marked public.  
Full interactive docs: http://localhost:8000/docs (Swagger) · http://localhost:8000/redoc (ReDoc)

---

## Authentication

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "admin@cortexos.ai",
  "password": "admin"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Refresh Token

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

Revokes the current token (added to Redis blocklist).

---

## Agents API

### List agents

```http
GET /agents?page=1&limit=20&tag=research&is_active=true
```

**Response:**
```json
{
  "items": [
    {
      "id": "agent_01abc",
      "name": "Market Researcher",
      "description": "Researches market trends",
      "model": "claude-sonnet-4-5",
      "provider": "anthropic",
      "tools": ["web_search", "read_url"],
      "is_active": true,
      "tags": ["research"],
      "created_at": "2026-06-02T00:00:00Z",
      "updated_at": "2026-06-02T00:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

### Get agent

```http
GET /agents/{agent_id}
```

### Create agent

```http
POST /agents
Content-Type: application/json

{
  "name": "Market Researcher",
  "description": "Researches market trends and competitor activity",
  "system_prompt": "You are a sharp market research analyst...",
  "model": "claude-sonnet-4-5",
  "provider": "anthropic",
  "tools": ["web_search", "read_url", "extract_structured_data"],
  "max_steps": 15,
  "temperature": 0.3,
  "tags": ["research"]
}
```

### Update agent

```http
PATCH /agents/{agent_id}
Content-Type: application/json

{
  "is_active": false
}
```

### Delete agent

```http
DELETE /agents/{agent_id}
```

### Run agent (single task)

```http
POST /agents/{agent_id}/run
Content-Type: application/json

{
  "goal": "Research the top 5 competitors of Notion",
  "context": {
    "market": "project management software",
    "focus": "pricing and positioning"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "task_id": "task_01xyz",
  "status": "pending",
  "agent_id": "agent_01abc"
}
```

---

## Tasks API

### List tasks

```http
GET /tasks?agent_id=agent_01abc&status=completed&page=1&limit=20
```

**Status values:** `pending` · `running` · `completed` · `failed` · `cancelled`

### Get task

```http
GET /tasks/{task_id}
```

**Response:**
```json
{
  "id": "task_01xyz",
  "agent_id": "agent_01abc",
  "goal": "Research top 5 Notion competitors",
  "status": "completed",
  "result": "Here are the top 5 competitors...",
  "steps": [
    {
      "step": 1,
      "tool": "web_search",
      "input": {"query": "Notion competitors 2026"},
      "output": "...",
      "duration_ms": 823
    }
  ],
  "tokens_used": 4821,
  "cost_usd": 0.0145,
  "started_at": "2026-06-02T09:00:00Z",
  "completed_at": "2026-06-02T09:01:34Z"
}
```

### Cancel task

```http
POST /tasks/{task_id}/cancel
```

---

## Workflows API

### List workflows

```http
GET /workflows?is_active=true&page=1&limit=20
```

### Get workflow

```http
GET /workflows/{workflow_id}
```

### Create workflow

```http
POST /workflows
Content-Type: application/json

{
  "name": "Content Production Pipeline",
  "description": "Research → Write → QC",
  "trigger": {
    "type": "manual",
    "input_schema": {
      "topic": { "type": "string", "required": true }
    }
  },
  "nodes": [...],
  "edges": [...]
}
```

### Update workflow

```http
PATCH /workflows/{workflow_id}
Content-Type: application/json

{
  "is_active": false
}
```

### Trigger workflow manually

```http
POST /workflows/{workflow_id}/trigger
Content-Type: application/json

{
  "inputs": {
    "topic": "AI agent frameworks in 2026"
  }
}
```

**Response:** `202 Accepted`
```json
{
  "run_id": "run_01abc",
  "workflow_id": "wf_01abc",
  "status": "running"
}
```

### Get workflow run

```http
GET /workflows/{workflow_id}/runs/{run_id}
```

### List workflow runs

```http
GET /workflows/{workflow_id}/runs?status=completed&limit=20
```

### Respond to approval gate

```http
POST /workflows/{workflow_id}/runs/{run_id}/approvals/{approval_id}
Content-Type: application/json

{
  "decision": "approved",
  "comment": "Looks good, publish it."
}
```

---

## Memory API

### Search memories

```http
POST /memory/search
Content-Type: application/json

{
  "query": "Notion competitor pricing",
  "agent_id": "agent_01abc",
  "limit": 10,
  "similarity_threshold": 0.75
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "mem_01abc",
      "content": "Confluence charges $10/user/month for the standard plan...",
      "similarity": 0.91,
      "created_at": "2026-05-15T00:00:00Z",
      "source_task_id": "task_00xyz"
    }
  ]
}
```

### Get agent memory summary

```http
GET /memory/agents/{agent_id}/summary
```

Returns: total memories, recent topics, entity count in graph.

### Delete agent memories

```http
DELETE /memory/agents/{agent_id}
```

Removes all episodic memories and embeddings. Graph nodes are preserved.

---

## Finance API

### Get revenue summary

```http
GET /finance/revenue?from=2026-06-01&to=2026-06-30&venture=all
```

**Response:**
```json
{
  "period": { "from": "2026-06-01", "to": "2026-06-30" },
  "total_revenue_aud": 42500.00,
  "by_venture": {
    "bloom-and-bub": 8200.00,
    "cudan-studio": 34300.00
  },
  "by_channel": {
    "etsy": 8200.00,
    "gumroad": 15000.00,
    "direct": 19300.00
  }
}
```

### Get expense summary

```http
GET /finance/expenses?from=2026-06-01&to=2026-06-30
```

### Get P&L

```http
GET /finance/pnl?from=2026-06-01&to=2026-06-30
```

---

## WebSocket Events

Connect: `ws://localhost:8000/ws/{task_id}?token=<access_token>`

### Events emitted by server

#### `task.started`
```json
{ "event": "task.started", "task_id": "task_01xyz", "agent_id": "agent_01abc" }
```

#### `task.step`
```json
{
  "event": "task.step",
  "task_id": "task_01xyz",
  "step": 2,
  "tool": "web_search",
  "status": "running"
}
```

#### `task.step_complete`
```json
{
  "event": "task.step_complete",
  "task_id": "task_01xyz",
  "step": 2,
  "tool": "web_search",
  "output_preview": "Found 10 results about...",
  "duration_ms": 821
}
```

#### `task.thinking`
```json
{
  "event": "task.thinking",
  "task_id": "task_01xyz",
  "message": "Analysing competitor pricing data..."
}
```

#### `task.completed`
```json
{
  "event": "task.completed",
  "task_id": "task_01xyz",
  "result": "Here are the top 5 Notion competitors...",
  "tokens_used": 4821,
  "cost_usd": 0.0145
}
```

#### `task.failed`
```json
{
  "event": "task.failed",
  "task_id": "task_01xyz",
  "error": "Max steps exceeded",
  "step": 10
}
```

#### `workflow.approval_required`
```json
{
  "event": "workflow.approval_required",
  "run_id": "run_01abc",
  "approval_id": "appr_01abc",
  "node_id": "n5",
  "message": "Please review the draft before publishing",
  "content_preview": "..."
}
```

### Connecting (JavaScript)

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/${taskId}?token=${accessToken}`
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.event) {
    case 'task.step':
      console.log(`Step ${data.step}: running ${data.tool}`);
      break;
    case 'task.completed':
      console.log('Done:', data.result);
      ws.close();
      break;
    case 'task.failed':
      console.error('Failed:', data.error);
      ws.close();
      break;
  }
};
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Agent not found",
  "code": "AGENT_NOT_FOUND",
  "status": 404
}
```

| Status | Code | Meaning |
|--------|------|---------|
| 400 | `VALIDATION_ERROR` | Request body invalid |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Token valid, insufficient permissions |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource already exists (e.g. agent name) |
| 422 | `UNPROCESSABLE` | Semantic validation failed |
| 429 | `RATE_LIMITED` | Too many requests |
| 500 | `INTERNAL_ERROR` | Server error (check logs) |
