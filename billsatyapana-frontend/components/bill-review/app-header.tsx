import { ShieldCheck } from 'lucide-react'

export function AppHeader() {
  return (
    <header className="border-b bg-card/80">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
        <p className="flex items-center gap-2 text-base font-semibold text-foreground">
          <ShieldCheck className="size-5 text-primary" aria-hidden="true" />
          BillSatyapana
        </p>
        <p className="rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
          Demo prototype
        </p>
      </div>
    </header>
  )
}
