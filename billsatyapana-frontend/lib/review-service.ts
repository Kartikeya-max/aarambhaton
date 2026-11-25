import type { ReviewRequest, ReviewResult } from './types'

export const ACCEPTED_FILE_TYPES = [
  'application/pdf',
  'text/csv',
]
export const ACCEPTED_FILE_EXTENSIONS = ['.pdf', '.csv']
export const MAX_FILE_SIZE_MB = 10

export function isAcceptedFile(file: File) {
  const name = file.name.toLowerCase()
  return (
    ACCEPTED_FILE_TYPES.includes(file.type) ||
    ACCEPTED_FILE_EXTENSIONS.some((extension) => name.endsWith(extension))
  )
}

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/+$/, '')

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
    const detail =
      body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : null
    throw new Error(detail ?? `The backend could not process the files (HTTP ${response.status}).`)
  }

  return (await response.json()) as ReviewResult
}
