from datetime import datetime, timezone

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
    return build("calendar", "v3", credentials=creds)


def list_events(time_min_iso: str, time_max_iso: str) -> str:
    """List calendar events between two ISO-8601 timestamps."""
    try:
        svc = _service()
        result = svc.events().list(
        calendarId="primary",
        timeMin=time_min_iso,
        timeMax=time_max_iso,
        singleEvents=True,
        orderBy="startTime",
        maxResults=20,
    ).execute()

        events = result.get("items", [])
        if not events:
            return "אין אירועים בטווח הזמן שביקשת."

        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))
            summary = e.get("summary", "(ללא כותרת)")
            location = e.get("location", "")
            loc_str = f" | {location}" if location else ""
            lines.append(f"• {start[:16].replace('T', ' ')} — {summary}{loc_str}")
        return "\n".join(lines)
    except Exception as e:
        return f"שגיאה בגישה ליומן: {type(e).__name__}: {e}"


def create_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> str:
    """Create a new calendar event."""
    svc = _service()
    body = {
        "summary": summary,
        "start": {"dateTime": start_iso, "timeZone": "Asia/Jerusalem"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Jerusalem"},
    }
    if description:
        body["description"] = description

    event = svc.events().insert(calendarId="primary", body=body).execute()
    return f"נקבע: {summary} ב-{start_iso[:16].replace('T', ' ')} (מזהה: {event['id'][:8]})"


def delete_event(event_id: str) -> str:
    """Delete a calendar event by ID."""
    svc = _service()
    svc.events().delete(calendarId="primary", eventId=event_id).execute()
    return f"האירוע בוטל."


TOOL_REGISTRY["list_calendar_events"] = {
    "schema": {
        "name": "list_calendar_events",
        "description": "הצג אירועים ביומן Google בין שתי נקודות זמן.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min_iso": {"type": "string", "description": "תחילת הטווח, ISO 8601, לדוגמה 2026-04-24T00:00:00+03:00"},
                "time_max_iso": {"type": "string", "description": "סוף הטווח, ISO 8601"},
            },
            "required": ["time_min_iso", "time_max_iso"],
        },
    },
    "fn": list_events,
}

TOOL_REGISTRY["create_calendar_event"] = {
    "schema": {
        "name": "create_calendar_event",
        "description": "צור אירוע חדש ביומן Google.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "כותרת האירוע"},
                "start_iso": {"type": "string", "description": "שעת התחלה ISO 8601"},
                "end_iso": {"type": "string", "description": "שעת סיום ISO 8601"},
                "description": {"type": "string", "description": "תיאור אופציונלי"},
            },
            "required": ["summary", "start_iso", "end_iso"],
        },
    },
    "fn": create_event,
}

TOOL_REGISTRY["delete_calendar_event"] = {
    "schema": {
        "name": "delete_calendar_event",
        "description": "בטל אירוע ביומן לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_id": {"type": "string", "description": "מזהה האירוע"},
            },
            "required": ["event_id"],
        },
    },
    "fn": delete_event,
}
