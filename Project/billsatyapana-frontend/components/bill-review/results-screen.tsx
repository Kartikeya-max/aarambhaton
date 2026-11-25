'use client'

import { useEffect, useRef } from 'react'
import { RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { ReviewResult } from '@/lib/types'
import { BillItemsList } from './bill-items-list'
import { Disclaimer, ReferenceRateNote } from './disclaimer'
import { SummaryCards } from './summary-cards'

type ResultsScreenProps = {
  result: ReviewResult
  onStartOver: () => void
}

export function ResultsScreen({ result, onStartOver }: ResultsScreenProps) {
  const headingRef = useRef<HTMLHeadingElement>(null)

  useEffect(() => {
    headingRef.current?.focus()
  }, [])

  return (
    <div className="flex flex-col gap-10">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-2">
          {result.isDemo && (
            <p className="w-fit rounded-full border border-primary/30 bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground">
              Demo results
            </p>
          )}
          <h1
            ref={headingRef}
            tabIndex={-1}
            className="text-3xl font-semibold tracking-tight outline-none sm:text-4xl"
          >
            Results
          </h1>
          <p className="text-muted-foreground">
            Plan: <span className="font-medium text-foreground">{result.planName}</span>
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={onStartOver}
          className="h-11 w-full rounded-lg px-5 text-sm sm:w-auto"
        >
          <RotateCcw aria-hidden="true" />
          Start over
        </Button>
      </div>

      <SummaryCards summary={result.summary} />

      {result.warnings && result.warnings.length > 0 && (
        <div role="status" className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-950">
          {result.warnings.map((warning, index) => <p key={`${index}-${warning}`}>{warning}</p>)}
        </div>
      )}

      <BillItemsList items={result.items} />

      <div className="flex flex-col gap-3 border-t pt-6">
        <Disclaimer />
        <ReferenceRateNote />
      </div>
    </div>
  )
}
