import anthropic

import database
from config import API_KEY, LLM_MODEL, MAX_HISTORY
from prompt import build_system_prompt
from tools import TOOL_REGISTRY

_client = anthropic.Anthropic(api_key=API_KEY)

FRAMEWORK_INJECTED_CHAT_ID = {
    "schedule_reminder",
    "list_reminders",
    "cancel_reminder",
    # wa-connect appends: "request_human_handoff"
}

MAX_TOOL_ITERATIONS = 5


def _run_tool(tool_use, chat_id: str) -> str:
    name = tool_use.name
    if name not in TOOL_REGISTRY:
        return f"כלי לא מוכר: {name}"

    tool_def = TOOL_REGISTRY[name]
    tool_input = dict(tool_use.input or {})

    if name in FRAMEWORK_INJECTED_CHAT_ID:
        tool_input["chat_id"] = chat_id

    try:
        result = tool_def["fn"](**tool_input)
        return str(result)
    except Exception as e:
        return f"שגיאה בהפעלת הכלי {name}: {e}"


def handle_message(chat_id: str, sender_name: str, message_text: str) -> str:
    database.append(chat_id, "user", message_text)
    history = database.tail(chat_id, MAX_HISTORY)

    system_prompt = build_system_prompt(TOOL_REGISTRY)
    tools = [td["schema"] for td in TOOL_REGISTRY.values()]

    messages = history[:-1]  # all but last (we'll add user message fresh)
    messages.append({"role": "user", "content": message_text})

    for _ in range(MAX_TOOL_ITERATIONS):
        kwargs = {
            "model": LLM_MODEL,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = _client.messages.create(**kwargs)

        if response.stop_reason == "end_turn":
            reply = _extract_text(response)
            database.append(chat_id, "assistant", reply)
            return reply

        if response.stop_reason == "tool_use":
            tool_results = []
            assistant_content = response.content

            for block in assistant_content:
                if block.type == "tool_use":
                    result = _run_tool(block, chat_id)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            continue

        break

    reply = "סליחה, לא הצלחתי לעבד את הבקשה. נסה שוב."
    database.append(chat_id, "assistant", reply)
    return reply


def _extract_text(response) -> str:
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return "."
