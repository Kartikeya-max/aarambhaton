/**
 * Shared data shapes for BillSatyapana.
 *
 * When you connect a Python backend, make its JSON response match
 * `ReviewResult` so the results screen keeps working without changes.
 */

export type InsurancePlan = {
  id: string
  name: string
}

export type ItemStatus = 'matched' | 'needs_review'

export type BillItem = {
  id: string
  description: string
  /** CGHS code the hospital applied on the bill. `null` if no code was shown. */
  appliedCode: string | null
  /** Better-fitting CGHS code or reference item, if one was found. */
  suggestedCode: string | null
  suggestedReferenceItem: string | null
  /** Amounts are in Indian rupees. */
  billedAmount: number
  /** `null` when no reference rate is available for this item. */
  referenceAmount: number | null
  status: ItemStatus
  /** True when the match is uncertain and could not be verified. */
  uncertain: boolean
  /** Plain-language explanation shown for items that need review. */
  reason: string | null
}

export type ReviewSummary = {
  totalBilled: number
  /** Estimate based on reference rates. Not guaranteed savings. */
  potentialSavings: number
  issuesFound: number
}

export type ReviewResult = {
  isDemo: boolean
  planName: string
  summary: ReviewSummary
  items: BillItem[]
  /** Explanations when an optional service such as NVIDIA AI falls back. */
  warnings?: string[]
}

export type ReviewRequest = {
  planId: string
  billFile: File
  visitSummaryFile: File
}
