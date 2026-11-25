'use client'

import { useEffect, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SIMULATED_REVIEW_DURATION_MS } from '@/lib/review-service'
import { ReviewAnimation } from './review-animation'

export const REVIEW_STEPS = [
  'Reading bill items',
  'Checking plan details',
  'Comparing items with reference rates',
]

/**
 * SIMULATED DEMO BEHAVIOUR.
 * The steps advance on a timer. With a real backend, you could keep this timer
 * for visual feedback, or drive `activeStep` from progress events it sends.
 */
const STEP_DURATION_MS = SIMULATED_REVIEW_DURATION_MS / REVIEW_STEPS.length

export function LoadingScreen() {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    const timers = REVIEW_STEPS.slice(1).map((_, index) =>
      setTimeout(() => setActiveStep(index + 1), STEP_DURATION_MS * (index + 1)),
    )
    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center gap-10 text-center">
      <ReviewAnimation activeStep={activeStep} />

      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Reviewing your bill</h1>
        <p className="text-muted-foreground">This usually takes a few moments.</p>
      </div>

      <ol className="flex w-full max-w-sm flex-col gap-3 text-left">
        {REVIEW_STEPS.map((step, index) => {
          const isDone = index < activeStep
          const isActive = index === activeStep
          return (
            <li
              key={step}
              className={cn(
                'flex items-center gap-3 rounded-lg border bg-card px-4 py-3 text-sm transition-colors',
                isActive && 'border-primary/40 text-foreground',
                isDone && 'text-foreground',
                !isDone && !isActive && 'text-muted-foreground',
              )}
            >
              <span
                className={cn(
                  'flex size-6 shrink-0 items-center justify-center rounded-full',
                  isDone && 'bg-success-soft text-success',
                  isActive && 'bg-accent text-primary',
                  !isDone && !isActive && 'bg-muted',
                )}
                aria-hidden="true"
              >
                {isDone && <Check className="size-4" />}
                {isActive && <Loader2 className="size-4 animate-spin motion-reduce:animate-none" />}
              </span>
              <span className="flex-1">{step}</span>
              <span className="sr-only">
                {isDone ? '(done)' : isActive ? '(in progress)' : '(waiting)'}
              </span>
            </li>
          )
        })}
      </ol>

      <p className="sr-only" role="status" aria-live="polite">
        {REVIEW_STEPS[activeStep]}
      </p>
    </div>
  )
}
