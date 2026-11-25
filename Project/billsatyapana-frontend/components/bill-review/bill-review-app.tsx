'use client'

import { useRef, useState } from 'react'
import { reviewBill } from '@/lib/review-service'
import type { ReviewResult } from '@/lib/types'
import { AppHeader } from './app-header'
import { LoadingScreen } from './loading-screen'
import { ResultsScreen } from './results-screen'
import { UploadScreen } from './upload-screen'

type Screen = 'upload' | 'loading' | 'results'

export function BillReviewApp() {
  const [screen, setScreen] = useState<Screen>('upload')
  const [planId, setPlanId] = useState('')
  const [billFile, setBillFile] = useState<File | null>(null)
  const [visitSummaryFile, setVisitSummaryFile] = useState<File | null>(null)
  const [result, setResult] = useState<ReviewResult | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const activeRequestId = useRef(0)

  async function handleSubmit() {
    if (!planId || !billFile || !visitSummaryFile) return

    const requestId = ++activeRequestId.current
    setErrorMessage(null)
    setScreen('loading')

    try {
      const reviewResult = await reviewBill({ planId, billFile, visitSummaryFile })
      if (requestId !== activeRequestId.current) return
      setResult(reviewResult)
      setScreen('results')
    } catch (error) {
      if (requestId !== activeRequestId.current) return
      setErrorMessage(error instanceof Error ? error.message : 'We could not review your bill. Please try again.')
      setScreen('upload')
    }
  }

  function handleStartOver() {
    activeRequestId.current += 1
    setPlanId('')
    setBillFile(null)
    setVisitSummaryFile(null)
    setResult(null)
    setErrorMessage(null)
    setScreen('upload')
  }

  return (
    <div className="flex min-h-dvh flex-col">
      {screen !== 'upload' && <AppHeader />}
      <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 py-10 sm:px-6 md:py-14">
        {screen === 'upload' && (
          <UploadScreen
            planId={planId}
            onPlanChange={setPlanId}
            billFile={billFile}
            onBillFileChange={setBillFile}
            visitSummaryFile={visitSummaryFile}
            onVisitSummaryFileChange={setVisitSummaryFile}
            errorMessage={errorMessage}
            onSubmit={handleSubmit}
          />
        )}
        {screen === 'loading' && <LoadingScreen />}
        {screen === 'results' && result && (
          <ResultsScreen result={result} onStartOver={handleStartOver} />
        )}
      </main>
    </div>
  )
}
