"""Loads the CGHS rate list and the drug MRP list from CSV.

Real data goes in  data/cghs_rates.csv  and  data/drug_mrp.csv.
If those files are missing, the *.sample.csv files (fictional) are used and
`ReferenceData.is_demo` is True, which makes the frontend show its "Demo" badge.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from . import config
from .textutils import parse_amount


@dataclass(frozen=True)
class CghsEntry:
    code: str
    name: str
    nabh_rate: Optional[float]
    non_nabh_rate: Optional[float]
    aliases: tuple[str, ...] = ()

    def rate(self, accreditation: str) -> Optional[float]:
        """Rate for the accreditation, falling back to the other column."""
        if accreditation == "non_nabh":
            return self.non_nabh_rate if self.non_nabh_rate is not None else self.nabh_rate
        return self.nabh_rate if self.nabh_rate is not None else self.non_nabh_rate


@dataclass(frozen=True)
class DrugEntry:
    name: str
    mrp: float  # per billed unit (tablet, ml, vial...)
    aliases: tuple[str, ...] = ()


@dataclass
class ReferenceData:
    cghs: list[CghsEntry]
    drugs: list[DrugEntry]
    is_demo: bool
    by_code: dict[str, CghsEntry] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.by_code = {e.code.upper(): e for e in self.cghs}


def _key(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (header or "").lower())


def _read_rows(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)))
    return [{_key(k): (v or "").strip() for k, v in row.items() if k} for row in reader]


def _pick(row: dict[str, str], *names: str) -> str:
    for n in names:
        if row.get(n):
            return row[n]
    return ""


def _split_aliases(value: str) -> tuple[str, ...]:
    return tuple(a.strip() for a in value.split("|") if a.strip())


def load_cghs(path: Path) -> list[CghsEntry]:
    entries: list[CghsEntry] = []
    for n, row in enumerate(_read_rows(path), start=1):
        name = _pick(row, "name", "procedure", "procedurename", "packagename", "description", "item")
        if not name:
            continue
        nabh = non_nabh = None
        for col, value in row.items():
            if "nabh" in col and "non" in col:
                non_nabh = parse_amount(value)
            elif "nabh" in col:
                nabh = parse_amount(value)
        if nabh is None and non_nabh is None:
            nabh = non_nabh = parse_amount(_pick(row, "rate", "price", "amount"))
        if nabh is None and non_nabh is None:
            continue
        code = _pick(row, "code", "procedurecode", "cghscode", "packagecode") or f"CGHS-{n}"
        entries.append(
            CghsEntry(code, name, nabh, non_nabh, _split_aliases(_pick(row, "aliases", "alias", "synonyms")))
        )
    return entries


def load_drugs(path: Path) -> list[DrugEntry]:
    entries: list[DrugEntry] = []
    for row in _read_rows(path):
        name = _pick(row, "name", "drug", "drugname", "medicine", "item")
        mrp = parse_amount(_pick(row, "mrp", "mrpperunit", "price", "ceilingprice"))
        if name and mrp is not None and mrp > 0:
            entries.append(DrugEntry(name, mrp, _split_aliases(_pick(row, "aliases", "alias", "synonyms"))))
    return entries


def load_reference_data(data_dir: Path | None = None) -> ReferenceData:
    d = Path(data_dir or config.DATA_DIR)
    cghs_real, cghs_sample = d / "cghs_rates.csv", d / "cghs_rates.sample.csv"
    drug_real, drug_sample = d / "drug_mrp.csv", d / "drug_mrp.sample.csv"

    cghs_path = cghs_real if cghs_real.exists() else cghs_sample
    drug_path = drug_real if drug_real.exists() else drug_sample
    if not cghs_path.exists():
        raise FileNotFoundError(f"No CGHS rate file found in {d} (expected cghs_rates.csv).")

    drugs = load_drugs(drug_path) if drug_path.exists() else []
    # Demo mode whenever either list is the fictional sample.
    is_demo = cghs_path == cghs_sample or (drug_path == drug_sample)
    return ReferenceData(load_cghs(cghs_path), drugs, is_demo)
