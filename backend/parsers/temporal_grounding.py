"""
Deterministic Temporal Grounding Engine
Normalizes relative weekday mentions ("Thursday", "kal morning", "next Monday")
anchored to the message's ISO timestamp in Asia/Kolkata timezone.
No LLM required - pure deterministic calendar math.
"""
import re
import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Tuple

IST = ZoneInfo("Asia/Kolkata")

WEEKDAYS = {
    "monday": 0, "somwar": 0, "thingal": 0,
    "tuesday": 1, "mangalwar": 1, "sevvaai": 1,
    "wednesday": 2, "budhwar": 2, "budhan": 2,
    "thursday": 3, "guruwar": 3, "vyazhan": 3,
    "friday": 4, "shukrawar": 4, "velli": 4,
    "saturday": 5, "shaniwar": 5, "sani": 5,
    "sunday": 6, "raviwar": 6, "njaayiru": 6
}

def resolve_relative_date(text: str, anchor_dt: datetime.datetime) -> Optional[datetime.datetime]:
    """
    Scans text for relative date phrases and anchors them to anchor_dt in IST.
    Examples:
    - 'Thursday tak settle kar dunga' relative to Sunday -> upcoming Thursday 18:00 IST
    - 'Wednesday afternoon' -> upcoming Wednesday 14:00 IST
    - 'Friday morning' -> upcoming Friday 10:00 IST
    - 'kal morning' -> next day 10:00 IST
    """
    clean = text.lower()

    # 1. Check relative weekdays
    for day_name, day_idx in WEEKDAYS.items():
        if re.search(rf"\b{day_name}\b", clean):
            current_day = anchor_dt.weekday()
            days_ahead = (day_idx - current_day) % 7
            if days_ahead == 0:
                days_ahead = 7 # next week if same day

            target_date = anchor_dt.date() + datetime.timedelta(days=days_ahead)

            # Check time-of-day hints
            hour = 18 # default end of business day
            minute = 0
            if "morning" in clean or "kaalai" in clean:
                hour = 10
            elif "afternoon" in clean or "mathiyam" in clean:
                hour = 14
            elif "evening" in clean or "saayanthram" in clean:
                hour = 18

            return datetime.datetime(
                target_date.year, target_date.month, target_date.day,
                hour, minute, 0, tzinfo=IST
            )

    # 2. Check 'kal' / 'tomorrow' / 'naalaiku'
    if re.search(r"\b(kal|tomorrow|naalai|naalaiku)\b", clean):
        target_date = anchor_dt.date() + datetime.timedelta(days=1)
        hour = 10 if "morning" in clean else 18
        return datetime.datetime(target_date.year, target_date.month, target_date.day, hour, 0, 0, tzinfo=IST)

    return None
