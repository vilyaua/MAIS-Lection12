# CLAUDE.md — MAIS Lection 12: Langfuse Observability

## Goal

Add Langfuse observability to the multi-agent research system. Base on hw09 A2A architecture (no MCP, no ACP).

## What Changes from hw09

| hw09 | hw12 |
|------|------|
| No observability | Every run traced in Langfuse with full call tree |
| System prompts hardcoded in `config.py` | All prompts loaded from Langfuse Prompt Management |
| No automated quality eval | LLM-as-a-Judge evaluators auto-score traces |
| MCP servers for tools | Tools as plain `@tool` functions (no MCP) |
| ACP + A2A dual protocol | A2A only (a2a-sdk) |

## Architecture

```
User (REPL / Web UI)
  │
  ▼
Supervisor (local create_agent, LangGraph + Langfuse CallbackHandler)
  ├── delegate_to_planner   ──► A2A :8904 ──► Planner Agent  ──► tools (web_search, knowledge_search)
  ├── delegate_to_researcher ──► A2A :8904 ──► Research Agent ──► tools (web_search, read_url, knowledge_search)
  ├── delegate_to_critic    ──► A2A :8904 ──► Critic Agent   ──► tools (web_search, read_url, knowledge_search)
  └── save_report           ──► local @tool (HITL gated)
```

All LLM calls, tool calls, and sub-agent delegations appear as spans under one Langfuse trace.

## Project Layout

```
MAIS-Lection12/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore
├── homework-lesson-12/              # assignment spec (read-only)
└── research-agent/
    ├── main.py                      # REPL + HITL + Langfuse trace init
    ├── app.py                       # FastAPI web UI + Langfuse trace init
    ├── supervisor.py                # Supervisor with CallbackHandler
    ├── a2a_client.py                # A2A client (from hw09, httpx timeout=120s)
    ├── a2a_server.py                # A2A server with 3 skills on :8904
    ├── agents/
    │   ├── __init__.py
    │   ├── planner.py               # Planner Agent
    │   ├── research.py              # Research Agent
    │   └── critic.py                # Critic Agent
    ├── tools.py                     # @tool functions: web_search, read_url, knowledge_search, save_report
    ├── schemas.py                   # ResearchPlan, CritiqueResult
    ├── config.py                    # Settings (NO hardcoded prompts — loaded from Langfuse)
    ├── langfuse_prompts.py          # get_prompt() wrappers for all agent prompts
    ├── retriever.py                 # Hybrid retrieval (from hw08)
    ├── ingest.py                    # PDF ingestion (from hw08)
    ├── requirements.txt
    ├── Dockerfile
    ├── docker-compose.yml
    ├── VERSION
    ├── DEVLOG.md
    ├── .env.example
    ├── .env                         # OPENAI_API_KEY + LANGFUSE_* keys — NEVER commit
    ├── data/                        # PDFs for RAG
    ├── screenshots/                 # 4 Langfuse UI screenshots
    └── test_queries.txt
```

## What to Bring from hw09

### Keep (A2A path only)
- `a2a_server.py` — AgentExecutor with 3 skills, Starlette on :8904
- `a2a_client.py` — a2a-sdk client with httpx timeout=120s
- `supervisor.py` — A2A delegation only (remove ACP code, remove `AGENT_PROTOCOL` toggle)
- `agents/` — planner, researcher, critic definitions
- `schemas.py`, `retriever.py`, `ingest.py`
- `app.py`, `main.py`
- `docker-compose.yml` — keep: search-mcp → remove, a2a + web only

### Drop
- `acp_server.py`, `acp_client.py` — no ACP
- `mcp_servers/`, `mcp_utils.py` — no MCP
- ACP-related code in supervisor.py (`_delegate_acp`, `PatchedACPClient` imports)
- `AGENT_PROTOCOL` config and toggle logic

### Add back from hw08
- `tools.py` — `web_search`, `read_url`, `knowledge_search`, `save_report` as plain `@tool` functions

## Key Implementation Details

### 1. Langfuse Tracing

Use `CallbackHandler` from `langfuse.callback` for LangChain/LangGraph integration:

```python
from langfuse.callback import CallbackHandler

handler = CallbackHandler(
    session_id=session_id,
    user_id=user_id,
    tags=["research-agent"],
)

# Pass to create_agent invocations
supervisor.invoke(input, config={"callbacks": [handler], ...})
```

Each A2A agent (planner, researcher, critic) should also create its own `CallbackHandler` span nested under the parent trace.

### 2. Session & User Tracking

- `session_id` — unique per conversation session (UUID, reused across turns)
- `user_id` — identifier for the user (e.g., "cli-user" or from web session)
- Both passed via `CallbackHandler` constructor

### 3. Prompt Management

**All system prompts loaded from Langfuse** — zero hardcoded prompts in Python code.

Upload to Langfuse UI (Prompts → + New prompt, label `production`):
- `supervisor-prompt` — Supervisor system prompt (template var: `{{max_revisions}}`)
- `planner-prompt` — Planner system prompt
- `researcher-prompt` — Researcher system prompt
- `critic-prompt` — Critic system prompt (template var: `{{current_date}}`)

Load in code:
```python
from langfuse import Langfuse

langfuse = Langfuse()

def get_system_prompt(name: str, **variables) -> str:
    prompt = langfuse.get_prompt(name, label="production")
    return prompt.compile(**variables)
```

`langfuse_prompts.py` — single module with `get_system_prompt()` used by all agents and supervisor.

### 4. LLM-as-a-Judge (Langfuse UI)

Set up 2 evaluators in Langfuse UI (LLM-as-a-Judge → Evaluators → + Set up evaluator):

**Evaluator 1: Answer Relevancy** (numeric, 0-1)
- Template: "Rate how relevant the output is to the input query. Score 0-1."
- Variables: `{{input}}`, `{{output}}`

**Evaluator 2: Report Completeness** (boolean)
- Template: "Does the output contain a structured report with sections, sources, and conclusion?"
- Variables: `{{input}}`, `{{output}}`

### 5. Screenshots

4 screenshots in `screenshots/`:
1. Trace tree — expanded trace showing supervisor → planner → researcher → critic
2. Session — Sessions tab showing grouped traces
3. Evaluator scores — trace Scores tab with auto-scores
4. Prompt management — Prompts tab showing all 4 prompts

## Docker Compose Services

```yaml
services:
  a2a:          # A2A server :8904 (planner, researcher, critic)
  web:          # FastAPI web UI :8000
  ingest:       # One-off PDF ingestion (profile: tools)
  supervisor:   # Interactive CLI REPL (profile: cli)
```

No MCP or ACP services.

## Dependencies (new vs hw09)

```
langfuse                          # Langfuse SDK (tracing + prompt management)
a2a-sdk[http-server]>=1.0.0      # A2A server + client
```

Drop from hw09: `acp-sdk`, `fastmcp`, `langchain-mcp-adapters`, uvicorn pin.
Keep: langchain, langgraph, faiss-cpu, rank_bm25, sentence-transformers, ddgs, trafilatura.

## Environment Variables

```
OPENAI_API_KEY=sk-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
MODEL_POWERFUL=openai:gpt-4.1
MODEL_FAST=openai:gpt-4.1-mini
```

## Build Order

1. Copy hw09 `research-agent/` as base
2. Remove MCP/ACP code, keep A2A only
3. Add `tools.py` from hw08 (plain @tool functions)
4. Add `langfuse` to requirements
5. Upload 4 system prompts to Langfuse UI
6. Create `langfuse_prompts.py` — load prompts via `get_prompt()`
7. Replace hardcoded prompts in agents + supervisor with Langfuse calls
8. Add `CallbackHandler` to supervisor and agent invocations
9. Add `session_id` + `user_id` to traces
10. Set up 2 LLM-as-a-Judge evaluators in Langfuse UI
11. Run 3-5 queries, verify traces in Langfuse
12. Take 4 screenshots

## Requirements Checklist

- [ ] Tracing: every run → Langfuse trace with full tree (LLM, tools, sub-agents)
- [ ] Session & User: traces grouped by session_id, tagged with user_id
- [ ] Prompt Management: all system prompts from Langfuse (zero hardcoded)
- [ ] LLM-as-a-Judge: 2 evaluators (different score types) auto-scoring traces
- [ ] Screenshots: 4 screenshots in `screenshots/`
- [ ] No MCP servers — tools as plain @tool functions
- [ ] No ACP — A2A only for agent-to-agent communication

## Do NOT

- Commit `.env` or API keys
- Hardcode any system prompts in Python files
- Use MCP or ACP — A2A only
- Skip session_id/user_id on traces
- Forget to label prompts as `production` in Langfuse
