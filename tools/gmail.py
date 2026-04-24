import base64
import email as email_lib

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import config
from tools import TOOL_REGISTRY


def _service():
    creds = Credentials(
        token=None,
        refresh_token=config.GOOGLE_REFRESH_TOKEN,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
    )
    return build("gmail", "v1", credentials=creds)


def search_emails(query: str, max_results: int = 10) -> str:
    """Search emails by query (Gmail search syntax)."""
    try:
        svc = _service()
        result = svc.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
    except Exception as e:
        return f"שגיאה בגישה ל-Gmail: {type(e).__name__}: {e}"

    messages = result.get("messages", [])
    if not messages:
        return "לא נמצאו מיילים."

    lines = []
    for msg in messages[:10]:
        detail = svc.users().messages().get(
            userId="me", id=msg["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        subject = headers.get("Subject", "(ללא נושא)")
        sender = headers.get("From", "?")
        date = headers.get("Date", "")[:16]
        lines.append(f"• {date} | {sender[:30]} | {subject[:50]}")

    return "\n".join(lines)


def get_email(message_id: str) -> str:
    """Get the full body of an email by ID."""
    svc = _service()
    msg = svc.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
    subject = headers.get("Subject", "(ללא נושא)")
    sender = headers.get("From", "?")

    body = _extract_body(msg.get("payload", {}))
    return f"מאת: {sender}\nנושא: {subject}\n\n{body[:2000]}"


def _extract_body(payload: dict) -> str:
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        for part in payload["parts"]:
            result = _extract_body(part)
            if result:
                return result
    else:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    return "(לא נמצא תוכן)"


TOOL_REGISTRY["search_emails"] = {
    "schema": {
        "name": "search_emails",
        "description": "חפש מיילים ב-Gmail. תומך בסינטקס Gmail: from:, subject:, is:unread וכו'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "שאילתת חיפוש Gmail, לדוגמה: 'is:unread' או 'from:boss@company.com'"},
                "max_results": {"type": "integer", "description": "מספר מקסימלי של תוצאות (ברירת מחדל: 10)"},
            },
            "required": ["query"],
        },
    },
    "fn": search_emails,
}

TOOL_REGISTRY["get_email"] = {
    "schema": {
        "name": "get_email",
        "description": "קרא את תוכן מייל מלא לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "מזהה המייל"},
            },
            "required": ["message_id"],
        },
    },
    "fn": get_email,
}
