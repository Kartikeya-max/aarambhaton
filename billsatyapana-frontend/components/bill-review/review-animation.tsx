import type { CSSProperties } from 'react'
import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'

const DOCUMENT_LINES = ['w-4/5', 'w-3/5', 'w-full', 'w-2/3', 'w-4/5', 'w-1/2']

export function ReviewAnimation({ activeStep }: { activeStep: number }) {
  return (
    <div className="flex items-center gap-2 sm:gap-4" aria-hidden="true">
      <div className="flex flex-col gap-3">
        <ScannedDocument title="Bill" delay="0s" />
        <ScannedDocument title="Summary" delay="1.1s" />
      </div>

      <div className="relative h-4 w-10 overflow-hidden sm:w-14">
        {[0, 0.5, 1].map((delay) => (
          <span
            key={delay}
            className="animate-flow-dot absolute top-1/2 left-0 size-2 -translate-y-1/2 rounded-full bg-primary"
            style={{ animationDelay: `${delay}s` }}
          />
        ))}
      </div>

      <div className="flex w-36 flex-col gap-2 rounded-xl border bg-card p-3 shadow-sm sm:w-44">
        <p className="text-left text-[0.7rem] font-medium tracking-wide text-muted-foreground uppercase">
          Comparison
        </p>
        {[0, 1, 2].map((row) => {
          const isDone = row < activeStep
          const isActive = row === activeStep
          return (
            <div
              key={row}
              className={cn(
                'flex items-center gap-2 rounded-md px-2 py-1.5 transition-colors duration-500',
                isDone ? 'bg-success-soft' : 'bg-muted',
              )}
            >
              <span
                className={cn(
                  'h-1.5 flex-1 rounded-full',
                  isDone ? 'bg-success/40' : isActive ? 'animate-line-pulse bg-primary/40' : 'bg-border',
                )}
              />
              <span
                className={cn(
                  'flex size-4 items-center justify-center rounded-full transition-colors duration-500',
                  isDone ? 'bg-success text-primary-foreground' : 'bg-border',
                )}
              >
                {isDone && <Check className="size-3" />}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function ScannedDocument({ title, delay }: { title: string; delay: string }) {
  return (
    <div className="relative h-28 w-24 overflow-hidden rounded-lg border bg-card p-2.5 shadow-sm sm:w-28">
      <p className="mb-2 text-left text-[0.65rem] font-semibold text-foreground">{title}</p>
      <div className="flex flex-col gap-1.5">
        {DOCUMENT_LINES.map((width, index) => (
          <span key={index} className={cn('h-1 rounded-full bg-border', width)} />
        ))}
      </div>
      <span
        className="animate-scan-line absolute inset-x-0 top-0 h-5 border-b-2 border-primary/60 bg-gradient-to-b from-transparent to-primary/15"
        style={{ animationDelay: delay, '--scan-distance': '5.75rem' } as CSSProperties}
      />
    </div>
  )
}
