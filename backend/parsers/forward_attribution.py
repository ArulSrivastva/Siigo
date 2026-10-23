"""
Forwarded Content & Attribution Parser
Detects when a Tier 0 (Owner) or Tier 1 (Staff) message contains forwarded
content from an external party.
Prevents elevation-of-privilege attacks where forwarding an external message
could accidentally inherit the forwarder's high trust tier!
"""
import re
from typing import Tuple
from tests.gold_dataset.schema import TrustTier

# Patterns indicating forwarded email or quoted WhatsApp
FORWARD_PATTERNS = [
    r"-{3,}\s*Forwarded message\s*-{3,}",
    r"Begin forwarded message:",
    r"From:\s*([^\n<]+)",
    r"---------- Forwarded message ---------",
    r"\[Forwarded from ([^\]]+)\]",
    r"^>\s*([^\n]+)"
]

def parse_forwarded_content(raw_text: str, forwarder_tier: TrustTier) -> Tuple[str, TrustTier, str]:
    """
    Analyzes raw message text.
    If forwarded content is detected from an external vendor,
    downgrades effective trust tier to TrustTier.EXTERNAL (Tier 2).
    Returns (cleaned_content, effective_trust_tier, original_sender_attribution)
    """
    for pat in FORWARD_PATTERNS:
        match = re.search(pat, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Forwarded external content detected!
            sender = match.group(1).strip() if match.groups() else "External Quoted Source"
            return raw_text, TrustTier.EXTERNAL, f"Quoted/Forwarded from {sender}"

    return raw_text, forwarder_tier, "Direct Author"
