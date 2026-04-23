from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

from config import DATABASE_PATH
from tools import TOOL_REGISTRY

_jobstore_url = f"sqlite:///{DATABASE_PATH}"
_scheduler = BackgroundScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=_jobstore_url)}
)
_scheduler.start()


def _fire_reminder(chat_id: str, message: str) -> None:
    from tools.whatsapp import send_reply
    send_reply(chat_id, f"⏰ תזכורת: {message}")


def create_reminder(chat_id: str, remind_at_iso: str, message: str) -> str:
    """Schedule a reminder to be sent at remind_at_iso (ISO 8601)."""
    run_at = datetime.fromisoformat(remind_at_iso)
    job = _scheduler.add_job(
        _fire_reminder,
        "date",
        run_date=run_at,
        args=[chat_id, message],
    )
    return f"תזכורת נקבעה ל-{run_at.strftime('%d/%m/%Y %H:%M')} | מזהה: {job.id}"


def list_reminders(chat_id: str) -> str:
    """List all pending reminders for this chat."""
    jobs = [
        j for j in _scheduler.get_jobs()
        if j.args and j.args[0] == chat_id
    ]
    if not jobs:
        return "אין תזכורות פעילות."
    lines = []
    for j in jobs:
        run_time = j.next_run_time.strftime("%d/%m/%Y %H:%M") if j.next_run_time else "?"
        lines.append(f"• {run_time} — {j.args[1]} (מזהה: {j.id})")
    return "\n".join(lines)


def cancel_reminder(reminder_id: str) -> str:
    """Cancel a reminder by its ID."""
    job = _scheduler.get_job(reminder_id)
    if not job:
        return f"לא מצאתי תזכורת עם מזהה {reminder_id}."
    job.remove()
    return "התזכורת בוטלה."


TOOL_REGISTRY["schedule_reminder"] = {
    "schema": {
        "name": "schedule_reminder",
        "description": "קבע תזכורת שתישלח בזמן מסוים.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "chat_id will be filled by the framework; leave empty",
                },
                "remind_at_iso": {
                    "type": "string",
                    "description": "מתי לשלוח את התזכורת, בפורמט ISO 8601. לדוגמה: 2026-04-23T15:00:00",
                },
                "message": {
                    "type": "string",
                    "description": "תוכן התזכורת",
                },
            },
            "required": ["chat_id", "remind_at_iso", "message"],
        },
    },
    "fn": create_reminder,
}

TOOL_REGISTRY["list_reminders"] = {
    "schema": {
        "name": "list_reminders",
        "description": "הצג את כל התזכורות הפעילות.",
        "input_schema": {
            "type": "object",
            "properties": {
                "chat_id": {
                    "type": "string",
                    "description": "chat_id will be filled by the framework; leave empty",
                },
            },
            "required": ["chat_id"],
        },
    },
    "fn": list_reminders,
}

TOOL_REGISTRY["cancel_reminder"] = {
    "schema": {
        "name": "cancel_reminder",
        "description": "בטל תזכורת לפי מזהה.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reminder_id": {
                    "type": "string",
                    "description": "מזהה התזכורת (מהרשימה)",
                },
            },
            "required": ["reminder_id"],
        },
    },
    "fn": cancel_reminder,
}
