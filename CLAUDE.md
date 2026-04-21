# CLAUDE.md — MAIS Lection 12: Langfuse Observability

## Project overview
Homework 12: integrate Langfuse observability into an existing multi-agent system (MAS) from previous homeworks. The goal is tracing, session/user tracking, prompt management, and LLM-as-a-Judge online evaluation.

## Key requirements
1. **Tracing** — every MAS run creates a trace in Langfuse with full tree (LLM calls, tool calls, sub-agents nested under one parent trace). Use `@observe` decorator and `CallbackHandler` for LangChain/LangGraph.
2. **Session & User tracking** — traces grouped by `session_id`, each trace has `user_id`. Verify in Langfuse UI Sessions/Users tabs.
3. **Prompt Management** — ALL system prompts loaded from Langfuse via `get_prompt(name, label=...)` + `.compile(**vars)`. Zero hardcoded prompts in Python code. Template variables use `{{...}}` syntax.
4. **LLM-as-a-Judge** — minimum 2 evaluators (different score types: numeric/boolean/categorical) set up in Langfuse UI under LLM-as-a-Judge → Evaluators. Template variables: `{{input}}`, `{{output}}`.
5. **Screenshots** — 4 screenshots in `screenshots/` folder: trace tree, session, evaluator scores, prompt management.

## Structure
```
homework-lesson-12/
├── .env                  # Langfuse keys (LANGFUSE_SECRET_KEY, LANGFUSE_PUBLIC_KEY, LANGFUSE_BASE_URL)
├── README.md             # Full homework spec (in Ukrainian)
├── lesson-12/
│   └── lesson-12.ipynb   # Lecture notebook
└── screenshots/          # (to create) 4 Langfuse UI screenshots
```

## Tech stack
- Python, LangChain/LangGraph (from previous homework MAS)
- Langfuse Cloud (us.cloud.langfuse.com) — free tier
- Langfuse Python SDK: `langfuse`, integration via `CallbackHandler`

## Key Langfuse docs
- Tracing + LangChain integration: https://langfuse.com/docs/integrations/langchain
- Prompt Management: https://langfuse.com/docs/prompts
- LLM-as-a-Judge: https://langfuse.com/docs/scores/model-based-evals

## Conventions
- Update DEVLOG.md after every significant change.
- Bump VERSION when appropriate.
- Keep `.env` out of git (contains secrets).
- Code language: Python. Comments/docs can be in Ukrainian or English.
