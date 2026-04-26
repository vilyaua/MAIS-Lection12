# DEVLOG

## 2026-04-26 — Resilience & production hardening (v0.1.2)

- A2A client timeout: 120s → 300s to handle slow web searches
- Supervisor tools: graceful fallbacks on A2A timeout/error
  - Planner: returns minimal plan
  - Researcher: returns timeout message
  - Critic: auto-approves with note
- Recursion limits tightened: critic 30→15, researcher 50→30
- Supervisor prompt: always call `save_report` even on errors, add ⚠️ Limitations section
- Re-uploaded updated supervisor prompt to Langfuse

## 2026-04-26 — Langfuse v4 API fix (v0.1.1)

- Fixed `CallbackHandler` for Langfuse SDK v4: `session_id`/`user_id`/`tags` now
  passed via `metadata` dict in config, not constructor args
- Fixed import: `langfuse.callback` → `langfuse.langchain`
- Added 4 LLM-as-a-Judge evaluators in Langfuse UI:
  - answer-relevancy (numeric 0–1)
  - report-completeness (boolean)
  - faithfulness (numeric 0–1)
  - conciseness (categorical: concise/adequate/verbose)
- Switched models from gpt-5.5/5.4-mini to gpt-4.1/4.1-mini for cost efficiency

## 2026-04-25 — Initial scaffold (v0.1.0)

- Based on hw09 A2A architecture (no MCP, no ACP)
- `a2a_server.py` — A2A server with 3 skills using local @tool functions
- `a2a_client.py` — a2a-sdk client with 120s timeout (from hw09)
- `tools.py` — plain @tool functions (web_search, read_url, knowledge_search, save_report)
- `langfuse_prompts.py` — loads all prompts from Langfuse via `get_prompt(name, label="production")`
- `upload_prompts.py` — one-time script to seed 4 prompts into Langfuse
- `supervisor.py` — A2A-only delegation + Langfuse prompt loading
- `main.py` — CLI REPL with Langfuse `CallbackHandler` (session_id + user_id)
- `app.py` — Web UI with Langfuse tracing per request
- `config.py` — settings with Langfuse env vars, no hardcoded prompts
- `docker-compose.yml` — 2 services: a2a (:8904), web (:8000)
- Agents: planner, researcher, critic — all load prompts from Langfuse
