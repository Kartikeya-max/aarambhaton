"""The rule engine: matches each bill line to reference data and applies the checks.

Rules (each one reports *why* it fired and what it was compared with):
  arithmetic     quantity x rate does not equal the line amount
  duplicate      same item, same date, same amount appears more than once
  drug_mrp       billed price per unit is above the medicine's MRP
  cghs_rate      billed amount is above the CGHS reference rate
  code_mismatch  the code printed on the bill points to a different item
  summary_conflict  the visit summary points to a different reference item
  unverified     no confident match: shown as "could not verify", never as an error
"""
from __future__ import annotations

import re
from typing import Optional

from . import config
from .ai_explanations import enrich_flagged_items
from .matcher import Candidate, NameIndex, pair_score
from .models import BillItem, BillLine, Finding, ParsedBill, ReviewResult
from .reference_data import CghsEntry, DrugEntry, ReferenceData
from .textutils import normalize_name

_ARITHMETIC_TOLERANCE = 1.0  # rupees
_TOTAL_TOLERANCE = 1.0
_GENERIC_TOKENS = {"with", "without", "and", "the", "for", "per", "day", "days", "type", "level"}


def _inr(x: float) -> str:
    return f"₹{x:,.0f}" if abs(x - round(x)) < 0.005 else f"₹{x:,.2f}"


def normalize_accreditation(value: Optional[str]) -> str:
    v = re.sub(r"[^a-z]", "", (value or config.DEFAULT_ACCREDITATION).lower())
    if v in ("", "auto"):
        v = re.sub(r"[^a-z]", "", config.DEFAULT_ACCREDITATION.lower())
    if v == "nabh":
        return "nabh"
    if v in ("nonnabh", "nonaccredited"):
        return "non_nabh"
    raise ValueError("accreditation must be 'nabh' or 'non_nabh'.")


class ReviewEngine:
    def __init__(self, reference: ReferenceData):
        self.ref = reference
        self.cghs_index = NameIndex(reference.cghs, lambda e: (e.name, *e.aliases))
        self.drug_index = NameIndex(reference.drugs, lambda e: (e.name, *e.aliases))

    # ------------------------------------------------------------------ public
    def review(
        self,
        bill: ParsedBill,
        *,
        plan_name: str,
        accreditation: str = "nabh",
        summary_text: str = "",
    ) -> ReviewResult:
        summary_tokens = set(normalize_name(summary_text).split())
        duplicates = self._find_duplicates(bill.lines)
        items = [
            self._review_line(i, line, accreditation, summary_tokens, duplicates.get(line.row))
            for i, line in enumerate(bill.lines, start=1)
        ]

        warnings = list(bill.warnings)
        ai_warning = enrich_flagged_items(items)
        if ai_warning:
            warnings.append(ai_warning)
        line_sum = sum(l.amount for l in bill.lines)
        if bill.stated_total is not None:
            expected = line_sum + sum(a for _, a in bill.adjustments)
            if abs(expected - bill.stated_total) > _TOTAL_TOLERANCE:
                warnings.append(
                    f"The total on the bill ({_inr(bill.stated_total)}) does not match the sum of its "
                    f"items and adjustments ({_inr(expected)})."
                )

        return ReviewResult(
            is_demo=self.ref.is_demo,
            plan_name=plan_name,
            total_billed=round(line_sum, 2),
            potential_savings=round(sum(i.excess for i in items), 2),
            issues_found=sum(1 for i in items if i.status == "needs_review"),
            items=items,
            warnings=warnings,
            accreditation=accreditation,
        )

    # --------------------------------------------------------------- internals
    @staticmethod
    def _find_duplicates(lines: list[BillLine]) -> dict[int, int]:
        """Maps a repeated line's row number -> row number of its first occurrence."""
        seen: dict[tuple, int] = {}
        dups: dict[int, int] = {}
        for line in lines:
            key = (normalize_name(line.description), line.date or "", round(line.amount, 2))
            if key in seen:
                dups[line.row] = seen[key]
            else:
                seen[key] = line.row
        return dups

    def _review_line(
        self,
        n: int,
        line: BillLine,
        accreditation: str,
        summary_tokens: set[str],
        duplicate_of: Optional[int],
    ) -> BillItem:
        cutoff, floor = config.MATCH_CUTOFF, config.WEAK_MATCH_FLOOR
        qty = line.quantity if line.quantity > 0 else 1.0

        cghs_c = self.cghs_index.top(line.description, 5, floor)
        drug_c = self.drug_index.top(line.description, 3, floor)
        cghs_best = cghs_c[0] if cghs_c and cghs_c[0].score >= cutoff else None
        drug_best = drug_c[0] if drug_c and drug_c[0].score >= cutoff else None
        is_drug = line.is_drug_category or (
            drug_best is not None and (cghs_best is None or drug_best.score >= cghs_best.score)
        )

        findings: list[Finding] = []
        reference: Optional[float] = None
        suggested_code = suggested_item = None

        if is_drug:
            if drug_best:
                reference, f = self._check_drug(line, qty, drug_best.entry)
                findings += f
            else:
                findings.append(Finding(
                    "unverified",
                    "No MRP reference was found for this medicine, so it could not be verified. "
                    "Check the price against the MRP printed on the pack.",
                    uncertain=True,
                ))
        elif cghs_best:
            reference, f, suggested_code, suggested_item = self._check_cghs(
                line, qty, cghs_best, accreditation, summary_tokens
            )
            findings += f
        else:
            reason = ("No matching CGHS reference item was found for this charge, so it could not be "
                      "verified. Asking the hospital for an itemised breakdown can help clarify it.")
            est_excess = 0.0
            closest_cghs = cghs_c[0] if cghs_c else None
            if closest_cghs:  # weak hint only
                suggested_code, suggested_item = closest_cghs.entry.code, closest_cghs.entry.name
                reason += " The closest reference item is shown for information only; it was not used."

            findings.append(Finding("unverified", reason, excess=est_excess, uncertain=True))

        findings += self._check_arithmetic(line, qty)
        if reference is None:
            reference = self._arithmetic_expected(line, qty)
        if duplicate_of is not None:
            findings.append(Finding(
                "duplicate",
                f"This item appears more than once on the same date (see row {duplicate_of}). "
                "That can be correct if more than one was used, so it is worth confirming with the hospital.",
                excess=line.amount, uncertain=True,
            ))

        flagged = bool(findings)
        return BillItem(
            id=f"item-{n}",
            description=line.description,
            applied_code=line.code,
            suggested_code=suggested_code,
            suggested_reference_item=suggested_item,
            billed_amount=round(line.amount, 2),
            reference_amount=round(reference, 2) if reference is not None else None,
            status="needs_review" if flagged else "matched",
            uncertain=flagged and all(f.uncertain for f in findings),
            reason=" ".join(f.reason for f in findings[:3]) if flagged else None,
            rule=findings[0].rule if flagged else None,
            excess=round(max((f.excess for f in findings), default=0.0), 2),
        )

    # ------------------------------------------------------------------ rules
    @staticmethod
    def _arithmetic_expected(line: BillLine, qty: float) -> Optional[float]:
        return qty * line.unit_price if line.unit_price is not None else None

    def _check_arithmetic(self, line: BillLine, qty: float) -> list[Finding]:
        expected = self._arithmetic_expected(line, qty)
        if expected is None or abs(expected - line.amount) <= _ARITHMETIC_TOLERANCE:
            return []
        q = f"{qty:g}"
        return [Finding(
            "arithmetic",
            f"Quantity × rate ({q} × {_inr(line.unit_price)}) is {_inr(expected)}, "
            f"but {_inr(line.amount)} is billed on this line.",
            excess=max(0.0, line.amount - expected),
        )]

    @staticmethod
    def _check_drug(line: BillLine, qty: float, drug: DrugEntry):
        mrp_total = drug.mrp * qty
        findings: list[Finding] = []
        if line.amount / qty > drug.mrp + 0.005:
            findings.append(Finding(
                "drug_mrp",
                f"Billed at {_inr(line.amount / qty)} per unit, but the MRP for '{drug.name}' is "
                f"{_inr(drug.mrp)}. Medicines are not normally sold above MRP; you can ask the "
                "pharmacy for the batch MRP, and drug overcharging can be reported to NPPA.",
                excess=line.amount - mrp_total,
            ))
        return mrp_total, findings

    def _check_cghs(self, line, qty, best: Candidate, accreditation: str, summary_tokens: set[str]):
        entry: CghsEntry = best.entry
        rate = entry.rate(accreditation)
        findings: list[Finding] = []
        suggested_code = suggested_item = None

        if rate is None:
            return None, [Finding("unverified", "The reference list has no rate for this item.", uncertain=True)], None, None

        reference = rate * qty
        if line.amount > reference * (1 + config.CGHS_TOLERANCE):
            pct = (line.amount / reference - 1) * 100
            findings.append(Finding(
                "cghs_rate",
                f"Billed {_inr(line.amount)} is {pct:.0f}% above the CGHS reference rate of "
                f"{_inr(reference)} for '{entry.name}'. You may want to ask the hospital how "
                "this charge was calculated.",
                excess=line.amount - reference,
            ))

        # Does the printed code point at a different item?
        if line.code and line.code.upper() in self.ref.by_code:
            coded = self.ref.by_code[line.code.upper()]
            if coded.code != entry.code and pair_score(
                normalize_name(line.description), normalize_name(coded.name)
            ) < 70:
                suggested_code, suggested_item = entry.code, entry.name
                findings.append(Finding(
                    "code_mismatch",
                    f"The applied code {coded.code} refers to '{coded.name}', which does not look "
                    f"like this item. A different reference item ('{entry.name}') may fit better.",
                ))

        # Does the visit summary describe a different variant than the bill?
        conflict = self._summary_conflict(line, entry, summary_tokens)
        if conflict and not suggested_code:
            suggested_code, suggested_item = conflict.code, conflict.name
            findings.append(Finding(
                "summary_conflict",
                f"The visit summary seems to describe a different variant than the bill "
                f"('{conflict.name}'). A different reference item may fit better.",
            ))
        return reference, findings, suggested_code, suggested_item

    def _summary_conflict(self, line: BillLine, best: CghsEntry, summary_tokens: set[str]) -> Optional[CghsEntry]:
        if not summary_tokens:
            return None
        best_tokens = set(normalize_name(best.name).split())
        found: Optional[tuple[float, CghsEntry]] = None
        for cand in self.cghs_index.top(best.name, 8, config.WEAK_MATCH_FLOOR):
            other: CghsEntry = cand.entry
            if other.code == best.code:
                continue
            other_tokens = set(normalize_name(other.name).split())
            extra = {t for t in other_tokens - best_tokens if len(t) >= 5 and t not in _GENERIC_TOKENS}
            mine = {t for t in best_tokens - other_tokens if len(t) >= 4 and t not in _GENERIC_TOKENS}
            # The summary mentions what the other item has, and not what this one has.
            if extra and extra <= summary_tokens and mine and not (mine & summary_tokens):
                if found is None or cand.score > found[0]:
                    found = (cand.score, other)
        return found[1] if found else None
