# BillSatyapana backend

FastAPI service that checks a hospital bill against CGHS reference rates and drug MRPs and
returns the JSON your Next.js frontend (`lib/types.ts → ReviewResult`) already expects.
Rule-based and explainable: every flag says which rule fired and what it was compared with.
Weak matches are reported as **"could not verify"**, never as errors.

## Run it

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/docs to try it. Tests: `python -m unittest discover -s tests -v`

## Connect the frontend

In `lib/review-service.ts`, replace the body of `reviewBill`:

```ts
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function reviewBill(request: ReviewRequest): Promise<ReviewResult> {
  const formData = new FormData()
  formData.append('plan_id', request.planId)
  formData.append('bill', request.billFile)
  formData.append('visit_summary', request.visitSummaryFile)
  const response = await fetch(`${API_URL}/api/review`, { method: 'POST', body: formData })
  if (!response.ok) throw new Error('Review failed')
  return (await response.json()) as ReviewResult
}
```
CORS allows `http://localhost:3000` by default; set `CORS_ORIGINS` for your deployed frontend URL.
The frontend currently catches every error with one generic message. The backend's 422 responses
carry a readable `detail` (e.g. "scanned images are not supported yet") if you want to show it.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/review` (alias `/analyze`) | multipart: `plan_id`, `bill`, `visit_summary` (optional), `accreditation` (optional: `nabh` / `non_nabh`) |
| GET | `/api/plans` | the plan dropdown options |
| GET | `/health` | status, how many reference items are loaded, whether demo data is in use |

Response extras the current UI ignores: per-item `rule`, top-level `warnings` and `accreditation`.

## The checks

| Rule id | Fires when |
|---|---|
| `arithmetic` | quantity × rate ≠ line amount (needs both columns) |
| `duplicate` | same item, date and amount appears again (marked uncertain: repeats can be legitimate) |
| `drug_mrp` | price per unit is above the medicine's MRP |
| `cghs_rate` | billed amount is more than 5% above the CGHS rate × quantity |
| `code_mismatch` | the code on the bill belongs to a clearly different CGHS item |
| `summary_conflict` | the visit summary describes a different variant (e.g. laparoscopic vs open) |
| `unverified` | no confident match (below 85) → "could not verify", not counted in savings |

`potentialSavings` is an estimate: the largest excess per item (so overlapping rules aren't double counted).
Names are matched after normalising (abbreviations like CBC/USG, "X-ray", "500 mg"). Conflicting numbers
(650mg vs 500mg, 2 vs 3 views) never match.

## ⚠️ Replace the sample data before real use

`data/*.sample.csv` are **fictional** (so the demo works). While they're in use the API sets
`isDemo: true` and the frontend shows its "Demo results" badge. To use real data, add:

- `data/cghs_rates.csv`: columns `code, name, nabh_rate, non_nabh_rate` (+ optional `aliases`, separated by `|`).
  Headers are matched loosely ("NABH Rate", "Non-NABH Rate", "Procedure"…); a single `rate` column also works.
- `data/drug_mrp.csv`: columns `name, mrp` (+ optional `aliases`). `mrp` is **per unit** (tablet, vial, ml).

Lines starting with `#` are ignored. Note: unless **both** real files exist, the API stays in demo mode.

## Bill formats

- **CSV**: header row with a description and an amount column (many names accepted). Optional: quantity, rate, date, code, category (`drug` marks medicines). Rows named Total / Discount / GST are used for the total check, not reviewed as items. See `samples/`.
- **Text-based PDF**: best-effort table/text extraction; a warning asks the user to check the items.
- **Not supported yet**: photos/scanned PDFs (HEIC, PNG, JPG, WEBP). They need OCR, which isn't included; the API says so clearly.

## Known limits

- Insurance plans are only echoed back; no insurer-specific tariffs are modelled.
- Accreditation isn't in the UI yet, so it defaults to NABH (the higher rate, fewer flags). Change with `DEFAULT_ACCREDITATION`.
- Wording is deliberately "above the reference rate" / "could not verify". CGHS rates are not a legal price cap.
