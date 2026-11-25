import type { BillItem, InsurancePlan } from './types'

/**
 * DEMO DATA ONLY.
 * Every plan, code, item, and amount below is fictional.
 * No real patient, hospital, or insurer information is used.
 */

export const DEMO_INSURANCE_PLANS: InsurancePlan[] = [
  { id: 'demo-basic', name: 'Demo Shield Basic (fictional)' },
  { id: 'demo-family', name: 'Demo CareFirst Family Floater (fictional)' },
  { id: 'demo-senior', name: 'Demo Senior Secure Plus (fictional)' },
]

export const DEMO_BILL_ITEMS: BillItem[] = [
  {
    id: 'item-1',
    description: 'Specialist consultation (OPD)',
    appliedCode: 'D-0102',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 350,
    referenceAmount: 350,
    status: 'matched',
    uncertain: false,
    reason: null,
  },
  {
    id: 'item-2',
    description: 'Complete blood count (CBC)',
    appliedCode: 'D-1201',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 180,
    referenceAmount: 180,
    status: 'matched',
    uncertain: false,
    reason: null,
  },
  {
    id: 'item-3',
    description: 'Chest X-ray, PA view',
    appliedCode: 'D-2104',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 2400,
    referenceAmount: 290,
    status: 'needs_review',
    uncertain: false,
    reason:
      'The billed amount is much higher than the reference rate for this test. You may want to ask the hospital how this charge was calculated.',
  },
  {
    id: 'item-4',
    description: 'Laparoscopic appendectomy',
    appliedCode: 'D-3310',
    suggestedCode: 'D-3312',
    suggestedReferenceItem: 'Appendectomy, laparoscopic',
    billedAmount: 48000,
    referenceAmount: 31500,
    status: 'needs_review',
    uncertain: false,
    reason:
      'The visit summary describes a laparoscopic procedure, but the applied code refers to an open procedure. A different reference item may fit better.',
  },
  {
    id: 'item-5',
    description: 'General ward room charges (3 days)',
    appliedCode: 'D-0501',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 4500,
    referenceAmount: 4500,
    status: 'matched',
    uncertain: false,
    reason: null,
  },
  {
    id: 'item-6',
    description: 'Surgical consumables kit',
    appliedCode: null,
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 6200,
    referenceAmount: null,
    status: 'needs_review',
    uncertain: true,
    reason:
      'No matching reference item was found for this charge. Asking the hospital for an itemised list of consumables can help clarify it.',
  },
  {
    id: 'item-7',
    description: 'IV cannula (listed twice on the same date)',
    appliedCode: 'D-4410',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 760,
    referenceAmount: 380,
    status: 'needs_review',
    uncertain: true,
    reason:
      'This item appears twice on the same date. That can be correct if two were used, so it is worth confirming with the hospital.',
  },
  {
    id: 'item-8',
    description: 'Ultrasound, whole abdomen',
    appliedCode: 'D-2201',
    suggestedCode: null,
    suggestedReferenceItem: null,
    billedAmount: 1100,
    referenceAmount: 1100,
    status: 'matched',
    uncertain: false,
    reason: null,
  },
]
