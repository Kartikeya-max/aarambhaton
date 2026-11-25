"""NVIDIA-powered explanations and bounded savings estimates for flagged items."""
from __future__ import annotations

import json
import logging
import math
import re
from typing import Any

import httpx

from . import config
from .models import BillItem

_API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
_BATCH_SIZE = 20
_SAVINGS_RULES = {"cghs_rate", "drug_mrp", "arithmetic"}
_LOGGER = logging.getLogger(__name__)


def enrich_flagged_items(items: list[BillItem]) -> str | None:
    """Add AI explanations and estimates without allowing unsupported savings.

    Only flagged item fields are sent; uploaded files and visit-summary text are
    never sent. The rule engine remains the fallback if NVIDIA is unavailable.
    """
    flagged = [item for item in items if item.status == "needs_review"]
    if not flagged:
        return None
    if not config.NVIDIA_API_KEY:
        return "NVIDIA AI is not configured; rule-based explanations and savings are shown. Add NVIDIA_API_KEY to the backend .env to enable it."

    failed = False
    for start in range(0, len(flagged), _BATCH_SIZE):
        batch = flagged[start : start + _BATCH_SIZE]
        try:
            results = _request_explanations(batch)
            for item in batch:
                result = results.get(item.id)
                if result is None:
                    failed = True
                    continue

                reason = result.get("reason")
                if isinstance(reason, str) and reason.strip():
                    item.reason = re.sub(r"\s+", " ", reason).strip()[:600]

                savings = _valid_amount(result.get("estimated_savings"))
                if savings is None:
                    failed = True
                    continue
                cap = _savings_cap(item)
                item.excess = round(min(savings, cap), 2)
                if item.excess > 0:
                    estimate_text = f"AI-estimated potential savings: ₹{item.excess:,.2f}."
                    item.reason = f"{item.reason or ''} {estimate_text}".strip()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in (401, 403):
                _LOGGER.warning("NVIDIA rejected the configured API credentials (HTTP %s).", status)
                return f"NVIDIA rejected the API key or its permissions (HTTP {status}); check NVIDIA_API_KEY in backend .env."
            if status == 404:
                _LOGGER.warning("NVIDIA model or endpoint was not found (HTTP 404).")
                return "NVIDIA could not find the configured model or API endpoint (HTTP 404); check NVIDIA_MODEL."
            if status == 429:
                _LOGGER.warning("NVIDIA rate-limited the request (HTTP 429).")
                return "NVIDIA rate-limited the request (HTTP 429); rule-based results are shown."
            _LOGGER.warning("NVIDIA AI request failed with HTTP %s.", status)
            return f"NVIDIA AI request failed (HTTP {status}); rule-based results are shown."
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            _LOGGER.warning("NVIDIA AI enrichment failed (%s); keeping rule-based results.", type(exc).__name__)
            failed = True

    if failed:
        return "NVIDIA AI could not process every flagged item; rule-based results are shown where AI was unavailable."
    return None


def _savings_cap(item: BillItem) -> float:
    """Only let AI estimate savings where a deterministic rule provides a cap."""
    if item.uncertain or item.rule not in _SAVINGS_RULES:
        return 0.0
    return max(0.0, item.excess)


def _request_explanations(items: list[BillItem]) -> dict[str, dict[str, Any]]:
    caps = {item.id: _savings_cap(item) for item in items}
    rows = [
        {
            "id": item.id,
            "description": item.description[:240],
            "rule": item.rule,
            "rule_reason": item.reason or "",
            "billed_amount_inr": item.billed_amount,
            "reference_amount_inr": item.reference_amount if caps[item.id] else None,
            "savings_cap_inr": caps[item.id],
            "uncertain": item.uncertain,
        }
        for item in items
    ]
    system_prompt = (
        "Explain already-flagged hospital bill items in clear, cautious language. "
        "Do not change whether an item is flagged. Use only the supplied fields; "
        "do not invent CGHS rates, MRP values, insurance rules, or facts. Do not call "
        "a charge fraudulent or illegal. Return one or two short sentences per item. "
        "Return only valid JSON with this shape: {\"items\":[{\"id\":\"...\","
        "\"reason\":\"...\",\"estimated_savings\":0.0}]}. Savings are INR and "
        "must be between zero and that item's savings_cap_inr. If the cap is zero "
        "or the item is uncertain, estimated_savings must be zero."
    )
    response = httpx.post(
        _API_URL,
        headers={"Authorization": f"Bearer {config.NVIDIA_API_KEY}"},
        json={
            "model": config.NVIDIA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps({"items": rows}, ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "max_tokens": min(4096, 256 + len(items) * 160),
            "stream": False,
        },
        timeout=45.0,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("NVIDIA returned no text content")
    parsed = json.loads(_strip_code_fence(content))
    if not isinstance(parsed, dict):
        raise ValueError("NVIDIA returned invalid JSON")
    output = parsed.get("items")
    if not isinstance(output, list):
        raise ValueError("NVIDIA returned an invalid item list")
    return {
        str(row["id"]): row
        for row in output
        if isinstance(row, dict) and "id" in row
    }


def _valid_amount(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return amount if math.isfinite(amount) and amount >= 0 else None


def _strip_code_fence(value: str) -> str:
    text = value.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    return text.strip()
