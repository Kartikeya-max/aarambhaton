'use client'

import { ChevronDown, Info, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DEMO_INSURANCE_PLANS } from '@/lib/demo-data'
import { MAX_FILE_SIZE_MB } from '@/lib/review-service'
import { Disclaimer, ReferenceRateNote } from './disclaimer'
import { FileDropZone } from './file-drop-zone'

type UploadScreenProps = {
  planId: string
  onPlanChange: (planId: string) => void
  billFile: File | null
  onBillFileChange: (file: File | null) => void
  visitSummaryFile: File | null
  onVisitSummaryFileChange: (file: File | null) => void
  errorMessage: string | null
  onSubmit: () => void
}

export function UploadScreen({
  planId,
  onPlanChange,
  billFile,
  onBillFileChange,
  visitSummaryFile,
  onVisitSummaryFileChange,
  errorMessage,
  onSubmit,
}: UploadScreenProps) {
  const canSubmit = Boolean(planId && billFile && visitSummaryFile)
  const missing = [
    !planId && 'an insurance plan',
    !billFile && 'a hospital bill',
    !visitSummaryFile && 'a hospital visit summary',
  ].filter(Boolean)

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-10">
      <div className="flex flex-col gap-3">
        <span className="flex size-11 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <ShieldCheck className="size-6" aria-hidden="true" />
        </span>
        <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
          BillSatyapana
        </h1>
        <p className="max-w-xl text-pretty text-lg leading-relaxed text-muted-foreground">
          Review your hospital bill against your insurance plan and reference rates.
        </p>
      </div>

      <form
        className="flex flex-col gap-8"
        onSubmit={(event) => {
          event.preventDefault()
          if (canSubmit) onSubmit()
        }}
      >
        <div className="flex flex-col gap-2">
          <label htmlFor="insurance-plan" className="text-base font-medium">
            Insurance plan
          </label>
          <div className="relative">
            <select
              id="insurance-plan"
              value={planId}
              onChange={(event) => onPlanChange(event.target.value)}
              className="h-12 w-full appearance-none rounded-lg border border-input bg-card pr-10 pl-4 text-base text-foreground shadow-xs outline-none transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/30 invalid:text-muted-foreground"
              required
            >
              <option value="" disabled>
                Select your plan
              </option>
              {DEMO_INSURANCE_PLANS.map((plan) => (
                <option key={plan.id} value={plan.id}>
                  {plan.name}
                </option>
              ))}
            </select>
            <ChevronDown
              className="pointer-events-none absolute top-1/2 right-3 size-5 -translate-y-1/2 text-muted-foreground"
              aria-hidden="true"
            />
          </div>
          <p className="text-sm text-muted-foreground">These plans are fictional and for demo only.</p>
        </div>

        <fieldset className="flex flex-col gap-4">
          <legend className="mb-4 text-base font-medium">Your documents</legend>
          <div className="grid gap-4 md:grid-cols-2">
            <FileDropZone
              id="hospital-bill"
              label="Hospital bill"
              hint="The itemised bill from the hospital."
              file={billFile}
              onFileChange={onBillFileChange}
            />
            <FileDropZone
              id="visit-summary"
              label="Hospital visit summary"
              hint="Discharge or visit summary describing your treatment."
              file={visitSummaryFile}
              onFileChange={onVisitSummaryFileChange}
            />
          </div>
          <p className="text-sm text-muted-foreground">
            Accepted formats: PDF or CSV. Bills must be CSV or text-based PDFs. Up to {MAX_FILE_SIZE_MB} MB each.
          </p>
        </fieldset>

        <div className="flex items-start gap-3 rounded-lg border bg-secondary/60 p-4 text-sm leading-relaxed text-secondary-foreground">
          <Info className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
          <p>
            This is a demo. Please use fictional or de-identified files only, and do not upload real
            patient information.
          </p>
        </div>

        {errorMessage && (
          <p role="alert" className="rounded-lg border border-review-border bg-review-soft p-4 text-sm text-review">
            {errorMessage}
          </p>
        )}

        <div className="flex flex-col gap-3">
          <Button
            type="submit"
            disabled={!canSubmit}
            aria-describedby="submit-hint"
            className="h-13 w-full rounded-lg text-base font-semibold hover:bg-primary/90 sm:w-auto sm:self-start sm:px-8"
          >
            Review my bill
          </Button>
          <p id="submit-hint" className="text-sm text-muted-foreground" aria-live="polite">
            {canSubmit ? 'Ready to review.' : `To continue, add ${joinWithAnd(missing as string[])}.`}
          </p>
        </div>

        <div className="flex flex-col gap-3 border-t pt-6">
          <Disclaimer />
          <ReferenceRateNote />
        </div>
      </form>
    </div>
  )
}

function joinWithAnd(parts: string[]) {
  if (parts.length <= 1) return parts.join('')
  return `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}`
}
