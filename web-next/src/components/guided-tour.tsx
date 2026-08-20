'use client'

import { useCallback, useEffect, useState } from 'react'
import { Icon } from '@/components/brand-artwork'

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
    <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true" aria-label="Hướng dẫn sử dụng">
      <button className="absolute inset-0 h-full w-full bg-[rgba(15,45,46,.56)] backdrop-blur-[2px]" type="button" onClick={() => close()} aria-label="Bỏ qua hướng dẫn" />
      {rect && (
        <div className="pointer-events-none fixed z-[1] max-[620px]:hidden rounded-2xl border-2 border-white shadow-[0_0_0_5px_rgba(0,114,188,.55),0_18px_50px_rgba(0,0,0,.25)] transition-all duration-[280ms] ease-out" style={{ left: rect.left - 7, top: rect.top - 7, width: rect.width + 14, height: rect.height + 14 }} />
      )}
      <section className="fixed right-[16px] bottom-[16px] z-[2] w-[min(420px,calc(100vw-32px))] rounded-[20px] border border-white/80 bg-white/[.97] p-[22px] text-[var(--c-ink)] shadow-[0_28px_80px_rgba(8,54,55,.3)] sm:right-[26px] sm:bottom-[26px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-[.08em] text-[var(--c-green2)]">{step.eyebrow}</span>
          <button type="button" className="grid h-[30px] w-[30px] place-items-center rounded-[9px] bg-[#edf4f6]" onClick={() => close()} aria-label="Đóng hướng dẫn"><Icon name="close" className="w-4"/></button>
        </div>
        <div className="my-3.5 mb-[18px] flex gap-[5px]">{steps.map((_, i) => <i key={i} className={`h-[3px] flex-1 rounded-full ${i <= index ? 'bg-[var(--c-green)]' : 'bg-[#dbe4e7]'}`} />)}</div>
        <h2 className="font-[family-name:var(--f-serif)] text-[25px] font-semibold">{step.title}</h2>
        <p className="mt-[9px] text-sm leading-[1.6] text-[#4d5960]">{step.description}</p>
        <div className="mt-[22px] flex items-center justify-end gap-2">
          <button type="button" className="mr-auto min-h-[44px] rounded-[10px] px-[13px] text-sm font-semibold text-[#565f65]" onClick={() => close()}>Bỏ qua</button>
          {index > 0 && <button type="button" className="min-h-[44px] rounded-[10px] border border-[#d4dddf] px-[13px] text-sm font-semibold" onClick={() => setIndex(value => value - 1)}>Quay lại</button>}
          <button type="button" className="flex min-h-[44px] items-center gap-[7px] rounded-[10px] bg-[linear-gradient(100deg,var(--c-green),#78a1bb)] px-[15px] text-sm font-semibold text-white" onClick={() => last ? close() : setIndex(value => value + 1)}>
            {last ? 'Bắt đầu sử dụng' : 'Tiếp theo'} <Icon name="arrowRight" className="w-[15px]"/>
          </button>
        </div>
      </section>
    </div>
  )
}
