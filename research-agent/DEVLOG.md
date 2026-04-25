# DEVLOG

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
