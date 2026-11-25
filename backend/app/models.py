"""Plain data classes. `to_dict()` output matches the frontend's lib/types.ts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BillLine:
    row: int  # row number in the uploaded file, for messages
    description: str
    amount: float  # line total as billed
    quantity: float = 1.0
    unit_price: Optional[float] = None
    code: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    @property
    def is_drug_category(self) -> bool:
        c = (self.category or "").lower()
        return any(k in c for k in ("drug", "medic", "pharm"))


@dataclass
class ParsedBill:
    lines: list[BillLine]
    # Discounts, GST, advances: not reviewed as items, but part of the total check.
    adjustments: list[tuple[str, float]] = field(default_factory=list)
    stated_total: Optional[float] = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class Finding:
    rule: str
    reason: str
    excess: float = 0.0  # estimated amount above the benchmark, in rupees
    uncertain: bool = False


@dataclass
class BillItem:
    id: str
    description: str
    applied_code: Optional[str]
    suggested_code: Optional[str]
    suggested_reference_item: Optional[str]
    billed_amount: float
    reference_amount: Optional[float]
    status: str  # "matched" | "needs_review"
    uncertain: bool
    reason: Optional[str]
    rule: Optional[str] = None  # extra field: id of the first rule that fired
    excess: float = 0.0  # internal; not sent to the client

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "appliedCode": self.applied_code,
            "suggestedCode": self.suggested_code,
            "suggestedReferenceItem": self.suggested_reference_item,
            "billedAmount": self.billed_amount,
            "referenceAmount": self.reference_amount,
            "status": self.status,
            "uncertain": self.uncertain,
            "reason": self.reason,
            "rule": self.rule,
        }


@dataclass
class ReviewResult:
    is_demo: bool
    plan_name: str
    total_billed: float
    potential_savings: float
    issues_found: int
    items: list[BillItem]
    warnings: list[str] = field(default_factory=list)
    accreditation: str = "nabh"

    def to_dict(self) -> dict:
        return {
            "isDemo": self.is_demo,
            "planName": self.plan_name,
            "summary": {
                "totalBilled": self.total_billed,
                "potentialSavings": self.potential_savings,
                "issuesFound": self.issues_found,
            },
            "items": [i.to_dict() for i in self.items],
            # Extra fields the current frontend ignores:
            "warnings": self.warnings,
            "accreditation": self.accreditation,
        }
