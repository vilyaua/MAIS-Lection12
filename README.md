# MAIS-Lection12

## Homework: Langfuse Observability for Multi-Agent Research System

Adds Langfuse tracing, prompt management, and LLM-as-a-Judge evaluation to the multi-agent research system. Based on hw09 A2A architecture (no MCP, no ACP).

### What's New vs Lesson 9

| Lesson 9 | Lesson 12 |
|----------|-----------|
| No observability | Every run traced in Langfuse with full call tree |
| System prompts hardcoded in `config.py` | All prompts loaded from Langfuse Prompt Management |
| No automated quality eval | LLM-as-a-Judge evaluators auto-score traces |
| MCP servers for tools | Tools as plain `@tool` functions (no MCP) |
| ACP + A2A dual protocol | A2A only |

### Project Structure

- **`homework-lesson-12/`** — Original homework spec (read-only)
- **`research-agent/`** — Implementation
- **`CLAUDE.md`** — Implementation guide and specifications

### Quick Start

```bash
cd research-agent
pip install -r requirements.txt
cp .env.example .env   # add OPENAI_API_KEY + LANGFUSE_* keys

# 1. Upload prompts to Langfuse (one-time)
python upload_prompts.py

# 2. Ingest documents
python ingest.py

# 3. Start A2A server
python a2a_server.py          # :8904

# 4. Run supervisor REPL
python main.py
```

### Docker

```bash
cd research-agent
cp .env.example .env   # add OPENAI_API_KEY + LANGFUSE_* keys
docker compose build
docker compose --profile tools run --rm ingest
docker compose up                                    # starts A2A + Web UI
docker compose --profile cli run --rm supervisor     # interactive REPL (optional)
```

Services: `a2a` (:8904), `web` (:8000).

### Langfuse Setup

1. Register at [us.cloud.langfuse.com](https://us.cloud.langfuse.com)
2. Create project, get API keys
3. Add keys to `.env`
4. Run `python upload_prompts.py` to seed prompts
5. Set up LLM-as-a-Judge evaluators in Langfuse UI

### LLM-as-a-Judge Evaluators

4 evaluators configured in Langfuse:

| Evaluator | Score Type | Purpose |
|-----------|-----------|---------|
| answer-relevancy | numeric (0–1) | Does the output address the query? |
| report-completeness | boolean | Is the report well-structured with all required sections? |
| faithfulness | numeric (0–1) | Are claims grounded in cited sources? |
| conciseness | categorical | Is the output concise, adequate, or verbose? |

### Resilience

- A2A client timeout: 300s
- Graceful fallbacks on agent timeout/error (critic auto-approves, planner returns minimal plan)
- Tightened recursion limits to prevent excessive search loops
- Supervisor always calls `save_report` even on degraded results (with ⚠️ Limitations section)

See [`CLAUDE.md`](CLAUDE.md) for full architecture and implementation details.
