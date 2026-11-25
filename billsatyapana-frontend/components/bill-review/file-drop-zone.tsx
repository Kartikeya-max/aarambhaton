'use client'

import { useRef, useState, type DragEvent } from 'react'
import { CheckCircle2, FileText, UploadCloud } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { formatFileSize } from '@/lib/format'
import {
  ACCEPTED_FILE_EXTENSIONS,
  ACCEPTED_FILE_TYPES,
  MAX_FILE_SIZE_MB,
  isAcceptedFile,
} from '@/lib/review-service'

type FileDropZoneProps = {
  id: string
  label: string
  hint: string
  file: File | null
  onFileChange: (file: File | null) => void
}

export function FileDropZone({ id, label, hint, file, onFileChange }: FileDropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function selectFile(candidate: File | undefined) {
    if (!candidate) return
    if (!isAcceptedFile(candidate)) {
      setError('This file type is not supported. Please choose a PDF or CSV file.')
      return
    }
    if (candidate.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setError(`This file is larger than ${MAX_FILE_SIZE_MB} MB.`)
      return
    }
    setError(null)
    onFileChange(candidate)
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  const errorId = `${id}-error`
  const hintId = `${id}-hint`

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        'flex min-h-60 flex-col rounded-xl border-2 border-dashed bg-card p-5 transition-colors',
        isDragging && 'border-primary bg-accent',
        file && !isDragging && 'border-solid border-success-border',
        !file && !isDragging && 'border-input',
      )}
    >
      <input
        ref={inputRef}
        id={id}
        type="file"
        className="sr-only"
        accept={[...ACCEPTED_FILE_TYPES, ...ACCEPTED_FILE_EXTENSIONS].join(',')}
        aria-describedby={error ? `${hintId} ${errorId}` : hintId}
        onChange={(event) => {
          selectFile(event.target.files?.[0])
          event.target.value = ''
        }}
        tabIndex={-1}
      />

      <div className="flex flex-col gap-1">
        <p className="text-base font-semibold">{label}</p>
        <p id={hintId} className="text-sm text-muted-foreground">
          {hint}
        </p>
      </div>

      {file ? (
        <div className="mt-auto flex flex-col gap-4 pt-5">
          <div className="flex items-start gap-3 rounded-lg bg-success-soft p-3">
            <FileText className="mt-0.5 size-5 shrink-0 text-success" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={file.name}>
                {file.name}
              </p>
              <p className="flex items-center gap-1 text-xs text-success">
                <CheckCircle2 className="size-3.5" aria-hidden="true" />
                Selected · {formatFileSize(file.size)}
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            className="h-11 rounded-lg text-sm"
            onClick={() => inputRef.current?.click()}
          >
            Replace file
            <span className="sr-only"> for {label}</span>
          </Button>
        </div>
      ) : (
        <div className="mt-auto flex flex-col items-center gap-3 pt-5 text-center">
          <span className="flex size-12 items-center justify-center rounded-full bg-secondary text-primary">
            <UploadCloud className="size-6" aria-hidden="true" />
          </span>
          <p className="text-sm text-muted-foreground">
            Drag and drop your file here, or
          </p>
          <Button
            type="button"
            variant="outline"
            className="h-11 rounded-lg px-5 text-sm"
            onClick={() => inputRef.current?.click()}
          >
            Browse files
            <span className="sr-only"> for {label}</span>
          </Button>
        </div>
      )}

      {error && (
        <p id={errorId} role="alert" className="mt-3 text-sm text-review">
          {error}
        </p>
      )}
    </div>
  )
}
