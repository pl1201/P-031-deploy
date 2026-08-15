'use client'

import { useCallback, useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'
import styles from './guided-tour.module.css'

export type TourStep = {
  selector: string
  eyebrow: string
  title: string
  description: string
}

export function GuidedTour({ id, steps }: { id: string; steps: TourStep[] }) {
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)
  const [rect, setRect] = useState<DOMRect | null>(null)

  const close = useCallback((remember = true) => {
    setOpen(false)
    setIndex(0)
    if (remember) localStorage.setItem(`vn_tour_${id}`, 'seen')
  }, [id])

  useEffect(() => {
    const launch = () => { setIndex(0); setOpen(true) }
    window.addEventListener('vn:open-tour', launch)
    const timer = window.setTimeout(() => {
      if (!localStorage.getItem(`vn_tour_${id}`)) setOpen(true)
    }, 800)
    return () => { window.clearTimeout(timer); window.removeEventListener('vn:open-tour', launch) }
  }, [id])

  useEffect(() => {
    if (!open) return
    const update = () => {
      const node = document.querySelector(steps[index]?.selector)
      setRect(node?.getBoundingClientRect() ?? null)
      node?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    const timer = window.setTimeout(update, 120)
    window.addEventListener('resize', update)
    return () => { window.clearTimeout(timer); window.removeEventListener('resize', update) }
  }, [index, open, steps])

  if (!open || steps.length === 0) return null
  const step = steps[index]
  const last = index === steps.length - 1

  return (
    <div className={styles.layer} role="dialog" aria-modal="true" aria-label="Hướng dẫn sử dụng">
      <button className={styles.scrim} type="button" onClick={() => close()} aria-label="Bỏ qua hướng dẫn" />
      {rect && (
        <div className={styles.focus} style={{ left: rect.left - 7, top: rect.top - 7, width: rect.width + 14, height: rect.height + 14 }} />
      )}
      <section className={styles.card}>
        <div className={styles.top}>
          <span>{step.eyebrow}</span>
          <button type="button" onClick={() => close()} aria-label="Đóng hướng dẫn"><Icon name="close" /></button>
        </div>
        <div className={styles.progress}>{steps.map((_, i) => <i className={i <= index ? styles.done : undefined} key={i} />)}</div>
        <h2>{step.title}</h2>
        <p>{step.description}</p>
        <div className={styles.actions}>
          <button type="button" className={styles.skip} onClick={() => close()}>Bỏ qua</button>
          {index > 0 && <button type="button" className={styles.back} onClick={() => setIndex(value => value - 1)}>Quay lại</button>}
          <button type="button" className={styles.next} onClick={() => last ? close() : setIndex(value => value + 1)}>
            {last ? 'Bắt đầu sử dụng' : 'Tiếp theo'} <Icon name="arrowRight" />
          </button>
        </div>
      </section>
    </div>
  )
}
