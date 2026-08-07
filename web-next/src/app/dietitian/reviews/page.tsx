'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function ReviewsPageRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/dietitian')
  }, [router])

  return (
    <div style={{ display: 'grid', placeItems: 'center', height: '50vh' }}>
      <span className="spinner" style={{ width: 28, height: 28, color: 'var(--c-green)' }} />
    </div>
  )
}
