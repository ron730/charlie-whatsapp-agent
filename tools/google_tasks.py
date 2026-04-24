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
    return build("tasks", "v1", credentials=creds)


def list_tasks(tasklist: str = "@default", show_completed: bool = False) -> str:
    """List tasks from Google Tasks."""
    try:
        svc = _service()
        result = svc.tasks().list(
            tasklist=tasklist,
            showCompleted=show_completed,
            showHidden=False,
            maxResults=20,
        ).execute()

        tasks = result.get("items", [])
        if not tasks:
            return "אין משימות פתוחות."

        lines = []
        for t in tasks:
            status = "✅" if t.get("status") == "completed" else "⬜"
            title = t.get("title", "(ללא כותרת)")
            due = t.get("due", "")[:10] if t.get("due") else ""
            due_str = f" (עד {due})" if due else ""
            lines.append(f"{status} {title}{due_str} [id:{t['id'][:8]}]")
        return "\n".join(lines)
    except Exception as e:
        return f"שגיאה בגישה למשימות: {type(e).__name__}: {e}"


def add_task(title: str, due_date: str = "", notes: str = "") -> str:
    """Add a new task to Google Tasks."""
    try:
        svc = _service()
        body = {"title": title, "status": "needsAction"}
        if due_date:
            body["due"] = f"{due_date}T00:00:00.000Z"
        if notes:
            body["notes"] = notes

        task = svc.tasks().insert(tasklist="@default", body=body).execute()
        return f"משימה נוספה: {title}"
    except Exception as e:
        return f"שגיאה בהוספת משימה: {type(e).__name__}: {e}"


def complete_task(task_id: str) -> str:
    """Mark a task as completed."""
    try:
        svc = _service()
        svc.tasks().patch(
            tasklist="@default",
            task=task_id,
            body={"status": "completed"}
        ).execute()
        return "המשימה סומנה כבוצעה."
    except Exception as e:
        return f"שגיאה: {type(e).__name__}: {e}"


def delete_task(task_id: str) -> str:
    """Delete a task."""
    try:
        svc = _service()
        svc.tasks().delete(tasklist="@default", task=task_id).execute()
        return "המשימה נמחקה."
    except Exception as e:
        return f"שגיאה: {type(e).__name__}: {e}"


TOOL_REGISTRY["list_tasks"] = {
    "schema": {
        "name": "list_tasks",
        "description": "הצג את רשימת המשימות של המשתמש מ-Google Tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "show_completed": {"type": "boolean", "description": "האם להציג גם משימות שבוצעו (ברירת מחדל: false)"},
            },
            "required": [],
        },
    },
    "fn": list_tasks,
}

TOOL_REGISTRY["add_task"] = {
    "schema": {
        "name": "add_task",
        "description": "הוסף משימה חדשה ל-Google Tasks.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "כותרת המשימה"},
                "due_date": {"type": "string", "description": "תאריך יעד בפורמט YYYY-MM-DD (אופציונלי)"},
                "notes": {"type": "string", "description": "הערות (אופציונלי)"},
            },
            "required": ["title"],
        },
    },
    "fn": add_task,
}

TOOL_REGISTRY["complete_task"] = {
    "schema": {
        "name": "complete_task",
        "description": "סמן משימה כבוצעה לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "מזהה המשימה (8 תווים ראשונים מהרשימה)"},
            },
            "required": ["task_id"],
        },
    },
    "fn": complete_task,
}

TOOL_REGISTRY["delete_task"] = {
    "schema": {
        "name": "delete_task",
        "description": "מחק משימה לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "מזהה המשימה"},
            },
            "required": ["task_id"],
        },
    },
    "fn": delete_task,
}
