"""Turns an uploaded bill (CSV or text-based PDF) into a ParsedBill."""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime
from typing import Optional

from .models import BillLine, ParsedBill
from .textutils import parse_amount


class ParseError(ValueError):
    """The file could not be read as a bill. The message is safe to show the user."""


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".heic")

_COLUMN_NAMES = {
    "description": {"description", "item", "itemname", "itemdescription", "particulars",
                    "service", "servicename", "name", "procedure", "details"},
    "amount": {"amount", "totalamount", "total", "billedamount", "charge", "charges",
               "netamount", "lineamount", "amountinr", "amountrs"},
    "unit_price": {"rate", "unitprice", "unitrate", "priceperunit", "price"},
    "quantity": {"quantity", "qty", "units", "days", "nos"},
    "code": {"code", "cghscode", "procedurecode", "itemcode"},
    "date": {"date", "servicedate", "billdate", "chargedate", "dateofservice"},
    "category": {"category", "type", "itemtype", "head", "department"},
}

_SUBTOTAL = re.compile(r"^\s*sub\s*-?\s*total.*$", re.I)
_TOTAL = re.compile(
    r"^\s*(grand\s+total|total(\s+(bill|amount|payable|charges|due))?|"
    r"net\s+(payable|amount|bill)(\s+amount)?|amount\s+payable|bill\s+total)\s*:?\s*$",
    re.I,
)
_ADJUSTMENT = re.compile(
    r"\b(discount|advance|deposit|round(ing)?[\s-]*off|gst|cgst|sgst|igst|service\s+tax)\b", re.I
)
_PDF_NOISE = re.compile(
    r"\b(bill|invoice|receipt|uhid|ip|mr|reg|registration)\s*(no|number|#)\b|phone|mobile|page\s+\d", re.I
)
_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d %b %Y", "%d-%b-%Y")


def _header_key(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (h or "").lower())


def _norm_date(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _map_columns(header: list[str]) -> dict[str, int]:
    cols: dict[str, int] = {}
    for i, h in enumerate(header):
        key = _header_key(h)
        for field_name, names in _COLUMN_NAMES.items():
            if field_name not in cols and key in names:
                cols[field_name] = i
    return cols


def _rows_to_bill(rows: list[list[str]]) -> ParsedBill:
    header_idx, cols = None, {}
    for i, row in enumerate(rows[:15]):
        mapped = _map_columns(row)
        if "description" in mapped and ("amount" in mapped or "unit_price" in mapped):
            header_idx, cols = i, mapped
            break
    if header_idx is None:
        raise ParseError(
            "Could not find the bill's columns. The file needs a header row with an item "
            "description column (e.g. 'Description') and an amount column (e.g. 'Amount')."
        )

    header_desc = _header_key(rows[header_idx][cols["description"]])
    bill = ParsedBill(lines=[])

    for r_no, row in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        def cell(name: str) -> str:
            i = cols.get(name)
            return row[i].strip() if i is not None and i < len(row) else ""

        desc = " ".join(cell("description").split())
        if not desc or _header_key(desc) == header_desc:  # blank, or a repeated header row
            continue
        if _SUBTOTAL.match(desc):
            continue

        amount, unit = parse_amount(cell("amount")), parse_amount(cell("unit_price"))
        qty = parse_amount(cell("quantity"))

        if _TOTAL.match(desc):
            bill.stated_total = amount if amount is not None else unit
            continue
        if amount is None and unit is not None:
            amount = round(unit * (qty if qty and qty > 0 else 1.0), 2)
        if amount is None:
            bill.warnings.append(f"Row {r_no} ('{desc}') has no amount and was skipped.")
            continue
        if amount < 0 or _ADJUSTMENT.search(desc):
            bill.adjustments.append((desc, amount))
            continue

        bill.lines.append(
            BillLine(
                row=r_no,
                description=desc,
                amount=amount,
                quantity=qty if qty and qty > 0 else 1.0,
                unit_price=unit,
                code=cell("code") or None,
                date=_norm_date(cell("date")),
                category=cell("category") or None,
            )
        )

    if not bill.lines:
        raise ParseError("No bill items were found in the file.")
    return bill


def _parse_csv(content: bytes) -> ParsedBill:
    text = _decode(content)
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    rows = [r for r in csv.reader(io.StringIO(text), dialect) if any(c.strip() for c in r)]
    return _rows_to_bill(rows)


def _import_pdfplumber():
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        raise ParseError("PDF support is not installed on the server (pip install pdfplumber).") from exc
    return pdfplumber


def _line_to_row(line: str) -> Optional[list[str]]:
    line = re.sub(r"(₹|\bRs\b\.?|\bINR\b)\s*", "", line, flags=re.I).strip()
    tokens = line.split()
    nums: list[str] = []
    while tokens and len(nums) < 3 and parse_amount(tokens[-1]) is not None:
        nums.insert(0, tokens.pop())
    if not tokens or not nums or sum(c.isalpha() for c in " ".join(tokens)) < 3:
        return None
    desc = " ".join(tokens)
    if _PDF_NOISE.search(desc):
        return None
    if len(nums) == 3:
        qty, rate, amount = nums
    elif len(nums) == 2 and re.fullmatch(r"\d{1,3}", nums[0]):
        qty, rate, amount = nums[0], "", nums[1]
    else:
        qty, rate, amount = "", "", nums[-1]
    return [desc, qty, rate, amount]


def _parse_pdf(content: bytes) -> ParsedBill:
    pdfplumber = _import_pdfplumber()
    table_rows: list[list[str]] = []
    text_lines: list[str] = []
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                for table in page.extract_tables() or []:
                    table_rows.extend([(c or "").replace("\n", " ").strip() for c in r] for r in table)
                text_lines.extend((page.extract_text() or "").splitlines())
    except Exception as exc:
        raise ParseError("This PDF could not be opened. Please check the file or try a CSV.") from exc

    if not any(ln.strip() for ln in text_lines) and not table_rows:
        raise ParseError(
            "This PDF has no readable text (it looks scanned). Scanned bills and photos "
            "are not supported yet; please upload a CSV or a text-based PDF."
        )
    if table_rows:
        try:
            bill = _rows_to_bill(table_rows)
            bill.warnings.append("Bill was read from a PDF table. Please check the items match your bill.")
            return bill
        except ParseError:
            pass

    rows = [["description", "quantity", "rate", "amount"]]
    rows += [r for r in (_line_to_row(ln) for ln in text_lines) if r]
    bill = _rows_to_bill(rows)
    bill.warnings.append("Bill was read from PDF text. Please check the items match your bill.")
    return bill


def parse_bill(filename: str, content: bytes) -> ParsedBill:
    name = (filename or "").lower()
    if name.endswith(".csv"):
        return _parse_csv(content)
    if name.endswith(".pdf"):
        return _parse_pdf(content)
    if name.endswith(IMAGE_EXTENSIONS):
        raise ParseError(
            "Photos and scanned images of bills are not supported yet. "
            "Please upload the bill as a CSV or a text-based PDF."
        )
    raise ParseError("Unsupported bill file type. Please upload a CSV or PDF.")


def extract_summary_text(filename: str, content: bytes) -> tuple[str, list[str]]:
    """Text of the visit summary, plus any warnings. Never raises: the summary is optional help."""
    name = (filename or "").lower()
    if name.endswith(IMAGE_EXTENSIONS):
        return "", ["The visit summary is an image and could not be read, so it was not used."]
    if name.endswith(".pdf"):
        try:
            pdfplumber = _import_pdfplumber()
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        except Exception:
            return "", ["The visit summary PDF could not be read, so it was not used."]
        if not text.strip():
            return "", ["The visit summary PDF has no readable text, so it was not used."]
        return text, []
    return _decode(content), []
