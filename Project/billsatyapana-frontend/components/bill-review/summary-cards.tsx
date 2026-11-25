import { AlertTriangle, PiggyBank, ReceiptIndianRupee } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { formatRupees } from '@/lib/format'
import type { ReviewSummary } from '@/lib/types'

export function SummaryCards({ summary }: { summary: ReviewSummary }) {
  return (
    <section aria-label="Summary" className="grid gap-4 sm:grid-cols-3">
      <SummaryCard
        icon={ReceiptIndianRupee}
        label="Total billed"
        value={formatRupees(summary.totalBilled)}
        note="Sum of all bill items."
      />
      <SummaryCard
        icon={PiggyBank}
        label="Potential savings"
        value={formatRupees(summary.potentialSavings)}
        note="Estimate based on reference rates. Not guaranteed."
      />
      <SummaryCard
        icon={AlertTriangle}
        label="Issues found"
        value={String(summary.issuesFound)}
        note="Items that may be worth asking about."
      />
    </section>
  )
}

type SummaryCardProps = {
  icon: LucideIcon
  label: string
  value: string
  note: string
}

function SummaryCard({ icon: Icon, label, value, note }: SummaryCardProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-5 shadow-xs">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Icon className="size-4 text-primary" aria-hidden="true" />
        <h2>{label}</h2>
      </div>
      <p className="text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
      <p className="text-sm leading-relaxed text-muted-foreground">{note}</p>
    </div>
  )
}
