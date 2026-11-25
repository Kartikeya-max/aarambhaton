import type { BillItem } from '@/lib/types'
import { BillItemRow, ITEM_GRID } from './bill-item-row'

export function BillItemsList({ items }: { items: BillItem[] }) {
  return (
    <section aria-labelledby="bill-items-heading" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <h2 id="bill-items-heading" className="text-xl font-semibold tracking-tight">
          Bill items
        </h2>
        <p className="text-sm text-muted-foreground">
          Select an item marked “Needs review” to see why it was flagged. Codes and amounts are
          fictional demo values.
        </p>
      </div>

      <div
        className={`hidden px-4 pr-12 text-xs font-medium tracking-wide text-muted-foreground uppercase ${ITEM_GRID}`}
        aria-hidden="true"
      >
        <span>Bill description</span>
        <span>Applied CGHS code</span>
        <span className="text-right">Billed</span>
        <span className="text-right">Reference</span>
        <span>Status</span>
      </div>

      <ul className="flex flex-col gap-3">
        {items.map((item) => (
          <BillItemRow key={item.id} item={item} />
        ))}
      </ul>
    </section>
  )
}
