'use client'

import { useId, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, HelpCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatRupees } from '@/lib/format'
import type { BillItem } from '@/lib/types'

export const ITEM_GRID =
  'md:grid md:grid-cols-[minmax(0,2.2fr)_minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_12rem] md:items-center md:gap-4'

export function BillItemRow({ item }: { item: BillItem }) {
  const [isOpen, setIsOpen] = useState(false)
  const detailsId = useId()
  const needsReview = item.status === 'needs_review'

  const rowContent = (
    <span className={cn('flex flex-col gap-3', ITEM_GRID)}>
      <span className="font-medium text-foreground">{item.description}</span>
      <Cell label="Applied CGHS code">
        <span className="font-mono text-sm">{item.appliedCode ?? 'Not shown'}</span>
      </Cell>
      <Cell label="Billed" alignRight>
        <span className="tabular-nums">{formatRupees(item.billedAmount)}</span>
      </Cell>
      <Cell label="Reference" alignRight>
        <span className="tabular-nums">
          {item.referenceAmount !== null ? formatRupees(item.referenceAmount) : 'Not available'}
        </span>
      </Cell>
      <StatusBox item={item} />
    </span>
  )

  if (!needsReview) {
    return (
      <li className="rounded-xl border border-success-border bg-success-soft/60 p-4">{rowContent}</li>
    )
  }

  return (
    <li className="rounded-xl border border-review-border bg-review-soft/60">
      <button
        type="button"
        aria-expanded={isOpen}
        aria-controls={detailsId}
        onClick={() => setIsOpen((open) => !open)}
        className="flex w-full items-start gap-3 rounded-xl p-4 text-left outline-none transition-colors hover:bg-review-soft focus-visible:ring-3 focus-visible:ring-ring/40 md:items-center"
      >
        <span className="block min-w-0 flex-1">{rowContent}</span>
        <ChevronDown
          className={cn(
            'mt-0.5 size-5 shrink-0 text-muted-foreground transition-transform md:mt-0',
            isOpen && 'rotate-180',
          )}
          aria-hidden="true"
        />
        <span className="sr-only">{isOpen ? 'Hide details' : 'Show details'}</span>
      </button>

      {isOpen && (
        <div id={detailsId} className="border-t border-review-border px-4 pt-4 pb-5">
          <ReviewDetails item={item} />
        </div>
      )}
    </li>
  )
}

function Cell({
  label,
  alignRight,
  children,
}: {
  label: string
  alignRight?: boolean
  children: React.ReactNode
}) {
  return (
    <span className={cn('flex items-baseline justify-between gap-4 text-sm', alignRight && 'md:justify-end')}>
      <span className="text-muted-foreground md:sr-only">{label}</span>
      {children}
    </span>
  )
}

function StatusBox({ item }: { item: BillItem }) {
  if (item.status === 'matched') {
    return (
      <span className="inline-flex w-fit items-center gap-1.5 rounded-md border border-success-border bg-success-soft px-2.5 py-1 text-sm font-medium text-success">
        <CheckCircle2 className="size-4" aria-hidden="true" />
        Matched to reference
      </span>
    )
  }

  return (
    <span className="flex flex-col gap-1">
      <span className="inline-flex w-fit items-center gap-1.5 rounded-md border border-review-border bg-review-soft px-2.5 py-1 text-sm font-medium text-review">
        <AlertTriangle className="size-4" aria-hidden="true" />
        Needs review
      </span>
      {item.uncertain && (
        <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
          <HelpCircle className="size-3.5" aria-hidden="true" />
          Could not verify
        </span>
      )}
    </span>
  )
}

function ReviewDetails({ item }: { item: BillItem }) {
  const suggestion = [item.suggestedCode, item.suggestedReferenceItem].filter(Boolean).join(' · ')

  return (
    <div className="flex flex-col gap-4">
      {item.uncertain && (
        <p className="inline-flex w-fit items-center gap-1.5 rounded-md bg-card px-2.5 py-1 text-sm font-medium text-foreground">
          <HelpCircle className="size-4 text-muted-foreground" aria-hidden="true" />
          Could not verify
        </p>
      )}

      <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
        <Detail term="Bill item description" value={item.description} />
        <Detail term="Applied CGHS code" value={item.appliedCode ?? 'Not shown on bill'} mono />
        <Detail
          term="Suggested CGHS code or reference item"
          value={suggestion || 'None found'}
          mono={Boolean(item.suggestedCode)}
        />
        <Detail
          term="Billed amount vs reference amount"
          value={`${formatRupees(item.billedAmount)} billed · ${
            item.referenceAmount !== null
              ? `${formatRupees(item.referenceAmount)} reference`
              : 'no reference available'
          }`}
        />
      </dl>

      {item.reason && (
        <div className="rounded-lg bg-card p-4">
          <p className="text-sm font-medium">Why this was flagged</p>
          <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{item.reason}</p>
        </div>
      )}
    </div>
  )
}

function Detail({ term, value, mono }: { term: string; value: string; mono?: boolean }) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-muted-foreground">{term}</dt>
      <dd className={cn('text-foreground', mono && 'font-mono')}>{value}</dd>
    </div>
  )
}
