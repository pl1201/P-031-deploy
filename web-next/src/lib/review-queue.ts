export const REVIEW_QUEUE_CHANGED_EVENT = 'vnutricare:review-queue-changed'

export type ReviewQueueChangedDetail = { count?: number }

export function notifyReviewQueueChanged(count?: number) {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent<ReviewQueueChangedDetail>(REVIEW_QUEUE_CHANGED_EVENT, {
    detail: typeof count === 'number' ? { count } : {},
  }))
}
