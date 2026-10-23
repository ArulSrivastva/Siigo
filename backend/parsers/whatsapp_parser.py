"""
WhatsApp .txt Export Ingestion Parser
Handles standard Indian WhatsApp export formats:
- "[25/10/26, 11:15:30 AM] Author: message" (iOS / bracketed format)
- "25/10/26, 11:15 am - Author: message" (Android / dash format)
- "25/10/2026, 11:15 - Author: message" (24-hour format)
- Multi-line message continuation
- System messages filtering ("Messages and calls are end-to-end encrypted", media omitted, etc.)
"""
import re
import datetime
from typing import List, Optional
from pydantic import BaseModel
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

class ParsedWhatsAppMessage(BaseModel):
    timestamp_ist: datetime.datetime
    author_name: str
    content: str
    raw_header: str

# Regex patterns matching standard WhatsApp timestamps
# 1. Bracketed format: [25/10/26, 11:15:30 AM] or [25/10/2026, 11:15:30]
PAT_BRACKET = re.compile(
    r"^\[(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\]\s+([^:]+):\s+(.*)$"
)

# 2. Dash format: 25/10/26, 11:15 am - Author: text
PAT_DASH = re.compile(
    r"^(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[APap][Mm])?)\s+-\s+([^:]+):\s+(.*)$"
)

SYSTEM_PHRASES = [
    "Messages and calls are end-to-end encrypted",
    "<Media omitted>",
    "image omitted",
    "video omitted",
    "audio omitted",
    "sticker omitted",
    "Contact card omitted",
    "This message was deleted",
    "You deleted this message"
]

def parse_ist_timestamp(date_str: str, time_str: str) -> datetime.datetime:
    """Parses date/time strings commonly found in Indian WhatsApp exports."""
    # Standardize separators
    clean_date = date_str.replace(".", "/").replace("-", "/")
    parts = clean_date.split("/")
    if len(parts) == 3:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        if year < 100:
            year += 2000
    else:
        now = datetime.datetime.now(IST)
        day, month, year = now.day, now.month, now.year

    time_clean = time_str.strip()
    is_pm = "pm" in time_clean.lower()
    is_am = "am" in time_clean.lower()
    time_digits = re.sub(r"[^\d:]", "", time_clean)
    time_parts = [int(p) for p in time_digits.split(":")]

    hour = time_parts[0]
    minute = time_parts[1] if len(time_parts) > 1 else 0
    second = time_parts[2] if len(time_parts) > 2 else 0

    if is_pm and hour < 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0

    return datetime.datetime(year, month, day, hour, minute, second, tzinfo=IST)

def parse_whatsapp_txt(file_content: str) -> List[ParsedWhatsAppMessage]:
    """
    Parses full WhatsApp chat export text into structured messages.
    Supports multi-line messages and filters WhatsApp system alerts.
    """
    lines = file_content.splitlines()
    parsed_messages: List[ParsedWhatsAppMessage] = []

    current_msg: Optional[ParsedWhatsAppMessage] = None

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        # Try match bracket pattern
        m_bracket = PAT_BRACKET.match(clean_line)
        m_dash = PAT_DASH.match(clean_line) if not m_bracket else None
        match = m_bracket or m_dash

        if match:
            date_part, time_part, author_part, text_part = match.groups()
            author_clean = author_part.strip()
            text_clean = text_part.strip()

            # Ignore system announcements
            if any(phrase in text_clean for phrase in SYSTEM_PHRASES):
                current_msg = None
                continue

            dt = parse_ist_timestamp(date_part, time_part)
            current_msg = ParsedWhatsAppMessage(
                timestamp_ist=dt,
                author_name=author_clean,
                content=text_clean,
                raw_header=line[:len(line) - len(text_clean)].strip()
            )
            parsed_messages.append(current_msg)
        else:
            # Continuation of previous message
            if current_msg:
                # Append multi-line content
                current_msg.content += "\n" + clean_line

    return parsed_messages
