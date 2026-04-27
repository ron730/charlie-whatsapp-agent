from datetime import datetime
import zoneinfo

from config import SPEC


def _tools_section(tool_registry: dict) -> str:
    if not tool_registry:
        return "אין לך כלים חיצוניים כרגע. ענה מהידע שלך בלבד."
    lines = ["יש לך הכלים הבאים:"]
    for name, td in tool_registry.items():
        desc = td["schema"].get("description", "")
        lines.append(f"- `{name}`: {desc}")
    return "\n".join(lines)


def build_system_prompt(tool_registry: dict) -> str:
    identity = SPEC["identity"]
    audience = SPEC["audience"]
    scope = SPEC["scope"]
    knowledge = SPEC["knowledge"]
    extras = SPEC.get("extras", {})

    authorized = audience.get("authorized_contacts", [])
    authorized_names = ", ".join(c["name"] for c in authorized)

    in_scope = "، ".join(scope["in_scope"])
    out_of_scope = "، ".join(scope["out_of_scope"])

    length_note = {
        "short": "ענה בקצרה — 1-2 משפטים. אל תתפרש.",
        "medium": "ענה בבינוני — כמה משפטים לפי הצורך.",
        "long": "ענה בפירוט כאשר נדרש.",
    }.get(extras.get("response_length", "short"), "ענה בקצרה.")

    now = datetime.now(zoneinfo.ZoneInfo("Asia/Jerusalem"))
    date_str = now.strftime("%A, %d/%m/%Y, %H:%M")

    prompt = f"""אתה {identity['name']}, עוזר אישי חברי ושימושי.
כעת: {date_str} (שעון ישראל)


## זהות וסגנון
{identity['tone_description']}. דבר בגוף ראשון, בעברית, בטון חברי וקרוב. אל תהיה רשמי.
{length_note}

## מי אתה עונה לו
אתה עוזר אישי של {authorized_names}. אתה עונה רק להודעות ממנו.
אם מגיעה הודעה ממישהו אחר, תגיד בנימוס שאתה עוזר אישי פרטי ואינך יכול לעזור.

## מה בתחום שלך
אתה עוזר ב: {in_scope}.
אתה לא עוסק ב: {out_of_scope}.
אם שואלים אותך משהו מחוץ לתחום, תגיד: "{scope['out_of_scope_response']}"

## מידע על {authorized_names}
{knowledge.get('static_knowledge', '')}

## כלים
{_tools_section(tool_registry)}

כאשר אתה משתמש בכלי — חכה לתוצאה לפני שאתה עונה. אם כלי נכשל, אמור זאת בפשטות.
"""

    if "request_human_handoff" in tool_registry:
        prompt += "\nאם המשתמש מבקש לדבר עם בן אדם, השתמש בכלי `request_human_handoff`."

    return prompt.strip()
