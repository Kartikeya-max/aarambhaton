import { Scale } from 'lucide-react'

export function Disclaimer() {
  return (
    <p className="flex items-start gap-2 text-sm leading-relaxed text-muted-foreground">
      <Scale className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      <span>Flags suspicious items against reference rates. Not a legal verdict.</span>
    </p>
  )
}

export function ReferenceRateNote() {
  return (
    <p className="text-sm leading-relaxed text-muted-foreground">
      CGHS (Central Government Health Scheme) rates are used here as reference rates. They are not a
      legal price cap for private hospitals, and your plan terms may differ.
    </p>
  )
}
