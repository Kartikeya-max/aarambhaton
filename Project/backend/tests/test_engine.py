"""Engine tests. Run:  python -m unittest discover -s tests -v

Mirrors the deck's test goal: every planted error is caught, the clean bill stays green,
and weak matches are shown as "could not verify" rather than guessed.
"""
import io
import unittest
from pathlib import Path

from app.engine import ReviewEngine, normalize_accreditation
from app.parsers import ParseError, extract_summary_text, parse_bill
from app.reference_data import load_reference_data
from app.textutils import parse_amount

SAMPLES = Path(__file__).resolve().parent.parent / "samples"
SUMMARY = (SAMPLES / "visit_summary.txt").read_text()


def review(name: str, summary: str = SUMMARY, accreditation: str = "nabh"):
    bill = parse_bill(name, (SAMPLES / name).read_bytes())
    return ENGINE.review(bill, plan_name="Test", accreditation=accreditation, summary_text=summary)


def csv_bill(rows: str):
    header = "date,code,description,category,quantity,rate,amount\n"
    return parse_bill("x.csv", (header + rows).encode())


ENGINE = ReviewEngine(load_reference_data())


class PlantedErrors(unittest.TestCase):
    def test_clean_bill_is_all_green(self):
        r = review("clean_bill.csv")
        self.assertEqual(r.issues_found, 0, [(i.description, i.reason) for i in r.items if i.reason])
        self.assertEqual(r.potential_savings, 0)
        self.assertEqual(r.total_billed, 37940)
        self.assertTrue(all(i.status == "matched" for i in r.items))
        self.assertTrue(r.is_demo)  # sample reference data in use

    def flagged(self, r):
        return [i for i in r.items if i.status == "needs_review"]

    def test_arithmetic_error(self):
        r = review("planted_arithmetic.csv")
        (item,) = self.flagged(r)
        self.assertIn("Quantity × rate", item.reason)
        self.assertEqual(item.excess, 90)

    def test_duplicate_item(self):
        r = review("planted_duplicate.csv")
        (item,) = self.flagged(r)
        self.assertEqual(item.rule, "duplicate")
        self.assertTrue(item.uncertain)  # a repeat can be legitimate
        self.assertIn("same date", item.reason)

    def test_drug_above_mrp(self):
        r = review("planted_drug_mrp.csv")
        (item,) = self.flagged(r)
        self.assertEqual(item.rule, "drug_mrp")
        self.assertEqual(item.reference_amount, 95.0)
        self.assertEqual(item.excess, 55.0)

    def test_cghs_overcharge(self):
        r = review("planted_cghs_rate.csv")
        (item,) = self.flagged(r)
        self.assertEqual(item.rule, "cghs_rate")
        self.assertEqual(item.reference_amount, 150)
        self.assertEqual(r.potential_savings, 450)
        self.assertFalse(item.uncertain)


class MatchingBehaviour(unittest.TestCase):
    def test_unknown_item_is_could_not_verify_not_an_accusation(self):
        r = ENGINE.review(csv_bill("2026-11-03,,Surgical consumables kit,,1,,6200"), plan_name="t")
        (item,) = r.items
        self.assertEqual((item.status, item.uncertain, item.reference_amount), ("needs_review", True, None))
        self.assertEqual(r.potential_savings, 0)  # unverified items never count as savings

    def test_conflicting_drug_strength_does_not_match(self):
        r = ENGINE.review(csv_bill("2026-11-03,,Paracetamol 650mg tablet,drug,10,2.00,20.00"), plan_name="t")
        (item,) = r.items
        self.assertEqual(item.rule, "unverified")

    def test_close_amount_within_tolerance_is_not_flagged(self):
        r = ENGINE.review(csv_bill("2026-11-02,D-1201,Complete blood count,,1,,185"), plan_name="t")  # 2.8% over
        self.assertEqual(r.issues_found, 0)

    def test_accreditation_changes_reference_rate(self):
        row = "2026-11-02,D-1201,Complete blood count,,1,,180"
        nabh = ENGINE.review(csv_bill(row), plan_name="t", accreditation="nabh")
        non = ENGINE.review(csv_bill(row), plan_name="t", accreditation="non_nabh")
        self.assertEqual((nabh.issues_found, non.issues_found), (0, 1))
        self.assertEqual(non.items[0].reference_amount, 153)

    def test_code_mismatch_suggests_better_item(self):
        r = ENGINE.review(csv_bill("2026-11-03,D-1201,Laparoscopic appendectomy,,1,,31500"), plan_name="t")
        item = r.items[0]
        self.assertEqual(item.rule, "code_mismatch")
        self.assertEqual(item.suggested_code, "D-3312")

    def test_visit_summary_conflict(self):
        row = "2026-11-03,D-3310,Appendectomy (open),,1,,22000"
        with_summary = ENGINE.review(csv_bill(row), plan_name="t", summary_text=SUMMARY)
        without = ENGINE.review(csv_bill(row), plan_name="t")
        self.assertEqual(with_summary.items[0].rule, "summary_conflict")
        self.assertEqual(with_summary.items[0].suggested_code, "D-3312")
        self.assertEqual(without.issues_found, 0)


class BillTotals(unittest.TestCase):
    def test_total_mismatch_warns_and_adjustments_count(self):
        ok = csv_bill("2026-11-02,,Complete blood count,,1,,180\n,,Discount,,,,-30\n,,Total,,,,150")
        self.assertEqual(len(ok.lines), 1)
        r = ENGINE.review(ok, plan_name="t")
        self.assertEqual(r.warnings, [])
        bad = csv_bill("2026-11-02,,Complete blood count,,1,,180\n,,Total,,,,999")
        self.assertEqual(len(ENGINE.review(bad, plan_name="t").warnings), 1)

    def test_item_starting_with_total_is_still_an_item(self):
        b = csv_bill("2026-11-02,,Total knee replacement,,1,,150000")
        self.assertEqual(len(b.lines), 1)


class Parsing(unittest.TestCase):
    def test_amounts(self):
        self.assertEqual(parse_amount("₹1,20,000.50"), 120000.5)
        self.assertEqual(parse_amount("Rs. 500/-"), 500)
        self.assertEqual(parse_amount("(250)"), -250)
        self.assertIsNone(parse_amount("nan"))
        self.assertIsNone(parse_amount("abc"))

    def test_flexible_headers_and_semicolons(self):
        b = parse_bill("b.csv", b"Particulars;Qty;Charges\nComplete blood count;1;Rs. 180\n")
        self.assertEqual((b.lines[0].description, b.lines[0].amount), ("Complete blood count", 180))

    def test_missing_columns_gives_helpful_error(self):
        with self.assertRaises(ParseError):
            parse_bill("b.csv", b"foo,bar\n1,2\n")

    def test_images_are_rejected_clearly(self):
        with self.assertRaisesRegex(ParseError, "not supported yet"):
            parse_bill("bill.jpg", b"\xff\xd8")

    def test_image_visit_summary_is_skipped_with_warning(self):
        text, warnings = extract_summary_text("s.png", b"x")
        self.assertEqual(text, "")
        self.assertEqual(len(warnings), 1)

    def test_accreditation_values(self):
        self.assertEqual(normalize_accreditation("Non-NABH"), "non_nabh")
        self.assertEqual(normalize_accreditation(None), "nabh")
        with self.assertRaises(ValueError):
            normalize_accreditation("platinum")


class PdfParsing(unittest.TestCase):
    def _pdf(self, build):
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        build(c)
        c.save()
        return buf.getvalue()

    def test_text_pdf_is_read(self):
        try:
            import pdfplumber, reportlab  # noqa: F401
        except ImportError:
            self.skipTest("pdfplumber/reportlab not installed")

        def draw(c):
            y = 780
            for line in ["Description Qty Rate Amount",
                         "Complete blood count 1 180 180",
                         "Chest X-ray PA view 1 2400 2400",
                         "Bill No 12345"]:
                c.drawString(50, y, line)
                y -= 20

        bill = parse_bill("b.pdf", self._pdf(draw))
        self.assertEqual([l.amount for l in bill.lines], [180, 2400])
        r = ENGINE.review(bill, plan_name="t")
        self.assertEqual([i.status for i in r.items], ["matched", "needs_review"])
        self.assertTrue(any("PDF" in w for w in r.warnings))

    def test_blank_pdf_is_reported_as_scanned(self):
        try:
            import pdfplumber, reportlab  # noqa: F401
        except ImportError:
            self.skipTest("pdfplumber/reportlab not installed")
        with self.assertRaisesRegex(ParseError, "scanned"):
            parse_bill("b.pdf", self._pdf(lambda c: None))


if __name__ == "__main__":
    unittest.main()
