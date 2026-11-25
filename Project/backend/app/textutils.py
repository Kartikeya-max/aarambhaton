"""Small text helpers shared by the parsers, loaders and matcher."""
from __future__ import annotations

import math
import re
from typing import Any, Optional

_MONEY_JUNK = re.compile(r"(?i)(₹|\brs\b\.?|\binr\b|/-)")


def parse_amount(value: Any) -> Optional[float]:
    """Parse '₹1,20,000.50', 'Rs. 500/-', '(250)', '-40' into a float.

    Returns None when the value is empty or not a number.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    s = str(value).strip()
    if not s:
        return None
    negative = (s.startswith("(") and s.endswith(")")) or s.startswith("-")
    s = _MONEY_JUNK.sub("", s)
    s = s.replace(",", "").replace(" ", "").strip("()-")
    try:
        number = float(s)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return -abs(number) if negative else number


# Abbreviations are expanded on BOTH sides of every comparison (bill text and
# reference names), so they only need to be consistent, not exhaustive.
_ABBREVIATIONS = {
    "cbc": "complete blood count",
    "usg": "ultrasound",
    "ecg": "electrocardiogram",
    "ekg": "electrocardiogram",
    "iv": "intravenous",
    "tab": "tablet",
    "tabs": "tablet",
    "cap": "capsule",
    "caps": "capsule",
    "inj": "injection",
    "lap": "laparoscopic",
    "opd": "",
}
_DROP_TOKENS = {"charges", "charge", "fee", "fees", "rs", "inr"}
_NUMBER_WITH_UNIT = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|ml|gm|g|iu|kg|l)\b")


def normalize_name(text: str) -> str:
    """Lower-case, strip punctuation/noise words, expand common abbreviations."""
    s = (text or "").lower().replace("&", " and ")
    s = re.sub(r"x[\s-]*ray", "xray", s)
    s = _NUMBER_WITH_UNIT.sub(r"\1\2", s)
    s = re.sub(r"(?<=\d)\.(?=\d)", "_", s)  # keep decimals like 0.9 as one token
    s = re.sub(r"[^a-z0-9_]+", " ", s)
    tokens: list[str] = []
    for token in s.split():
        if token in _DROP_TOKENS:
            continue
        for part in _ABBREVIATIONS.get(token, token).split():
            if part not in tokens:
                tokens.append(part)
    return " ".join(tokens)
