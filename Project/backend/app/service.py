"""Glue between the HTTP layer and the engine. No web framework imports here."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from .engine import ReviewEngine, normalize_accreditation
from .parsers import ParseError, extract_summary_text, parse_bill
from .plans import plan_name
from .reference_data import load_reference_data


@lru_cache(maxsize=1)
def get_engine() -> ReviewEngine:
    return ReviewEngine(load_reference_data())


def run_review(
    *,
    plan_id: str,
    bill_name: str,
    bill_bytes: bytes,
    summary_name: Optional[str] = None,
    summary_bytes: Optional[bytes] = None,
    accreditation: Optional[str] = None,
) -> dict:
    """Returns the JSON-ready dict the frontend expects. Raises ParseError / ValueError for bad input."""
    accreditation = normalize_accreditation(accreditation)
    bill = parse_bill(bill_name, bill_bytes)

    summary_text = ""
    if summary_bytes:
        summary_text, summary_warnings = extract_summary_text(summary_name or "", summary_bytes)
        bill.warnings.extend(summary_warnings)

    result = get_engine().review(
        bill, plan_name=plan_name(plan_id), accreditation=accreditation, summary_text=summary_text
    )
    return result.to_dict()


__all__ = ["run_review", "get_engine", "ParseError"]
