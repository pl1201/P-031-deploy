'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { getSession, redirectByRole } from '@/lib/auth'

export default function HomePage() {
  const router = useRouter()
  useEffect(() => {
    const session = getSession()
    if (session) {
      router.replace(redirectByRole(session.role))
    } else {
      router.replace('/login')
    }
  }, [router])
  return (
    <div style={{ display: 'grid', placeItems: 'center', height: '100vh' }}>
      <span className="spinner" style={{ width: 32, height: 32, color: 'var(--c-green)' }} />
    </div>
  )
}
