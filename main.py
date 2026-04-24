import importlib
from pathlib import Path

from fastapi import FastAPI, Request

import config
import database
from config import DATABASE_PATH, SPEC
from tools.whatsapp import send_reply

# Ensure data directory exists before any module tries to open the DB
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

database.init_db()

# Wire tools that are available without external auth
importlib.import_module("tools.reminders")

# Wire Google tools (require GOOGLE_* env vars)
if config.GOOGLE_REFRESH_TOKEN:
    importlib.import_module("tools.google_calendar")
    importlib.import_module("tools.gmail")

app = FastAPI()

_AUTHORIZED = {
    c["phone_e164"] for c in SPEC["audience"].get("authorized_contacts", [])
}
_ANSWER_GROUPS = SPEC["audience"].get("answer_groups", False)
_IS_WHITELIST = SPEC["audience"].get("mode") == "whitelist"


def _sender_phone(chat_id: str) -> str:
    return chat_id.replace("@c.us", "").replace("@g.us", "")


@app.get("/health")
async def health():
    return {"status": "ok", "bot": SPEC["identity"]["name"], "version": 1}


@app.post("/webhook/green-api")
async def webhook(request: Request):
    body = await request.json()

    if body.get("typeWebhook") != "incomingMessageReceived":
        return {"ok": True}

    id_message = body.get("idMessage", "")
    if database.is_processed(id_message):
        return {"ok": True}
    database.mark_processed(id_message)

    sender_data = body.get("senderData", {})
    chat_id: str = sender_data.get("chatId", "")
    sender_name: str = sender_data.get("senderName", "")

    if chat_id.endswith("@g.us") and not _ANSWER_GROUPS:
        return {"ok": True}

    if _IS_WHITELIST:
        phone = _sender_phone(chat_id)
        if phone not in _AUTHORIZED:
            return {"ok": True}

    msg_data = body.get("messageData", {})
    msg_type = msg_data.get("typeMessage", "")

    if msg_type == "textMessage":
        text = msg_data.get("textMessageData", {}).get("textMessage", "").strip()
    elif msg_type in ("extendedTextMessage", "quotedMessage"):
        text = (
            msg_data.get("extendedTextMessageData", {}).get("text", "")
            or msg_data.get("textMessageData", {}).get("textMessage", "")
        ).strip()
    else:
        return {"ok": True}

    if not text:
        return {"ok": True}

    from agent import handle_message
    reply = handle_message(chat_id, sender_name, text)
    send_reply(chat_id, reply)

    return {"ok": True}
