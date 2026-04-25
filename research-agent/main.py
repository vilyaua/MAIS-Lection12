"""REPL with HITL interrupt/resume loop + Langfuse tracing.

Requires A2A server to be running first.
Usage: python main.py
"""

import logging
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage
from langfuse.callback import CallbackHandler
from langgraph.types import Command, Interrupt

from config import APP_VERSION, Settings
from supervisor import supervisor

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("logs/supervisor.log", maxBytes=5_000_000, backupCount=3),
    ],
)
logger = logging.getLogger("supervisor")

settings = Settings()

USER_ID = "cli-user"
SESSION_ID = str(uuid.uuid4())


def _create_langfuse_handler(session_id: str, trace_name: str = "research-query") -> CallbackHandler:
    """Create a Langfuse CallbackHandler with session and user tracking."""
    return CallbackHandler(
        session_id=session_id,
        user_id=USER_ID,
        trace_name=trace_name,
        tags=["research-agent", "cli"],
    )


def _print_header():
    print(f"Multi-Agent Research System v{APP_VERSION} (A2A + Langfuse)")
    print(f"Model: {settings.model_powerful} / {settings.model_fast}")
    print(f"A2A: :{settings.a2a_port} | Session: {SESSION_ID[:8]}")
    print("Type 'exit' to quit.\n" + "-" * 60)


def _format_tool_call(msg):
    if not isinstance(msg, AIMessage) or not msg.tool_calls:
        return None
    lines = []
    for tc in msg.tool_calls:
        name = tc.get("name", "?")
        args = tc.get("args", {})
        if name == "save_report":
            arg_str = args.get("filename", "")
        elif "request" in args:
            arg_str = (
                args["request"][:80] + "..."
                if len(args.get("request", "")) > 80
                else args.get("request", "")
            )
        elif "findings" in args:
            arg_str = args["findings"][:80] + "..."
        else:
            arg_str = str(args)[:80]
        lines.append(f"  >> {name}({arg_str})")
    return "\n".join(lines)


def _handle_interrupt(interrupts: list[Interrupt], thread_id: str, langfuse_handler: CallbackHandler) -> None:
    """Handle HITL interrupt from HumanInTheLoopMiddleware."""
    for intr in interrupts:
        payload = intr.value
        action_requests = payload.get("action_requests", [])
        review_configs = payload.get("review_configs", [])

        decisions = []
        for i, action in enumerate(action_requests):
            tool_name = action.get("name", "unknown")
            tool_args = action.get("arguments", action.get("args", {}))

            print("\n" + "=" * 60)
            print("  ACTION REQUIRES APPROVAL")
            print("=" * 60)
            print(f"  Tool:     {tool_name}")
            if tool_name == "save_report":
                print(f"  Filename: {tool_args.get('filename', '?')}")
                content_preview = tool_args.get("content", "")
                if content_preview:
                    print(f"  Preview:\n{content_preview[:500]}")
            else:
                print(f"  Args: {str(tool_args)[:300]}")
            print("=" * 60)

            allowed = ["approve", "edit", "reject"]
            if i < len(review_configs):
                allowed = review_configs[i].get("allowed_decisions", allowed)

            while True:
                choice = input(f"\n  {' / '.join(allowed)}: ").strip().lower()
                if choice in allowed:
                    break
                print(f"  Please enter one of: {', '.join(allowed)}")

            if choice == "approve":
                print("  Approved!")
                decisions.append({"type": "approve"})
            elif choice == "edit":
                feedback = input("  Your feedback: ").strip()
                print(f"  Sending feedback to Supervisor: {feedback}")
                decisions.append(
                    {"type": "edit", "edited_action": {**action, "feedback": feedback}}
                )
            else:
                input("  Reason (optional): ").strip()
                decisions.append({"type": "reject"})

        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": 100,
            "callbacks": [langfuse_handler],
        }
        result = supervisor.invoke(
            Command(resume={"decisions": decisions}),
            config=config,
        )
        _check_and_handle(result, thread_id, langfuse_handler)


def _check_and_handle(result: dict, thread_id: str, langfuse_handler: CallbackHandler):
    interrupts = result.get("__interrupt__", [])
    if interrupts:
        _handle_interrupt(interrupts, thread_id, langfuse_handler)
    else:
        _print_final_messages(result)


def _print_final_messages(result: dict):
    messages = result.get("messages", [])
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            print(f"\nAgent: {msg.content}")


def _stream_and_handle(thread_id: str, input_data: dict, langfuse_handler: CallbackHandler) -> None:
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 100,
        "callbacks": [langfuse_handler],
    }

    for chunk in supervisor.stream(input_data, config=config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            if node_name == "__interrupt__":
                _handle_interrupt(node_output, thread_id, langfuse_handler)
                return

            if node_output is None:
                continue
            messages = node_output.get("messages", [])
            for msg in messages:
                tool_info = _format_tool_call(msg) if isinstance(msg, AIMessage) else None
                if tool_info:
                    print(tool_info)

                if isinstance(msg, ToolMessage):
                    content = msg.content
                    if len(content) > 200:
                        content = content[:200] + "..."
                    print(f"  <- {content}")

                if (
                    isinstance(msg, AIMessage)
                    and msg.content
                    and not getattr(msg, "tool_calls", None)
                ):
                    print(f"\nAgent: {msg.content}")


def main():
    _print_header()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        thread_id = str(uuid.uuid4())
        langfuse_handler = _create_langfuse_handler(SESSION_ID, trace_name=user_input[:80])
        _stream_and_handle(
            thread_id,
            {"messages": [("user", user_input)]},
            langfuse_handler,
        )


if __name__ == "__main__":
    main()
