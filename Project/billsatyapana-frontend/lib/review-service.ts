import { DEMO_BILL_ITEMS, DEMO_INSURANCE_PLANS } from './demo-data'
import type { BillItem, ReviewRequest, ReviewResult, ReviewSummary } from './types'

/** How long the simulated analysis takes, in milliseconds. */
export const SIMULATED_REVIEW_DURATION_MS = 4800

export const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'text/csv',
  'image/png',
  'image/jpeg',
  'image/webp',
  'image/heic',
]
export const ACCEPTED_FILE_EXTENSIONS = ['.pdf', '.csv', '.png', '.jpg', '.jpeg', '.webp', '.heic']
export const ACCEPTED_BILL_FILE_EXTENSIONS = ['.pdf', '.csv']
export const MAX_FILE_SIZE_MB = 10

export function isAcceptedFile(file: File, allowedExtensions?: string[]) {
  const name = file.name.toLowerCase()
  return (
    (allowedExtensions ?? ACCEPTED_FILE_EXTENSIONS).some((extension) => name.endsWith(extension)) ||
    (!allowedExtensions && ACCEPTED_FILE_TYPES.includes(file.type))
  )
}

export function summarizeItems(items: BillItem[]): ReviewSummary {
  return items.reduce<ReviewSummary>(
    (summary, item) => {
      summary.totalBilled += item.billedAmount
      if (item.status === 'needs_review') {
        summary.issuesFound += 1
        if (item.referenceAmount !== null && item.billedAmount > item.referenceAmount) {
          summary.potentialSavings += item.billedAmount - item.referenceAmount
        }
      }
      return summary
    },
    { totalBilled: 0, potentialSavings: 0, issuesFound: 0 },
  )
}

/**
 * SIMULATED DEMO BEHAVIOUR.
 *
 * This function does not read the uploaded files. It waits for a short delay
 * and returns fictional sample results so the interface can be demonstrated.
 *
 * To connect a real Python backend later, replace the body with something like:
 *
 *   const formData = new FormData()
 *   formData.append('plan_id', request.planId)
 *   formData.append('bill', request.billFile)
 *   formData.append('visit_summary', request.visitSummaryFile)
 *   const response = await fetch('/api/review', { method: 'POST', body: formData })
 *   if (!response.ok) throw new Error('Review failed')
 *   return (await response.json()) as ReviewResult
 */


  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function reviewBill(request: ReviewRequest): Promise<ReviewResult> {
  const formData = new FormData()
  formData.append('plan_id', request.planId)
  formData.append('bill', request.billFile)
  formData.append('visit_summary', request.visitSummaryFile)

  let response: Response
  try {
    response = await fetch(`${API_URL}/api/review`, { method: 'POST', body: formData })
  } catch {
    throw new Error(`Cannot connect to the backend at ${API_URL}. Start the backend and try again.`)
  }
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    const detail = body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
      ? body.detail
      : null
    throw new Error(detail ?? `The backend could not process the files (HTTP ${response.status}).`)
  }
  return (await response.json()) as ReviewResult
}

