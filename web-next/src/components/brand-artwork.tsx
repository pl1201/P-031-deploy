import type { SVGProps } from 'react'

export function Icon({name, ...props}: SVGProps<SVGSVGElement> & {name:string}) {
  const common={fill:'none',stroke:'currentColor',strokeWidth:1.8,strokeLinecap:'round' as const,strokeLinejoin:'round' as const}
  const paths:Record<string,React.ReactNode>={
    user:<><circle cx="12" cy="7" r="3.5"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/></>,
    expert:<><circle cx="12" cy="6" r="3"/><path d="M6 21v-3a6 6 0 0 1 12 0v3M9 11l3 4 3-4M12 15v6"/></>,
    mail:<><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></>,
    lock:<><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 15v2"/></>,
    eye:<><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="2.5"/></>,
    monitor:<><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4"/></>,
    headset:<><path d="M4 14v-2a8 8 0 0 1 16 0v2M4 14h3v6H5a2 2 0 0 1-2-2v-2a2 2 0 0 1 1-2ZM20 14h-3v6h2a2 2 0 0 0 2-2v-2a2 2 0 0 0-1-2ZM17 20c0 1-1 2-3 2"/></>,
    clipboard:<><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 12l2 2 4-5"/></>,
    document:<><path d="M6 2h8l4 4v16H6zM14 2v5h5M9 12h6M9 16h4"/></>,
    group:<><circle cx="12" cy="8" r="3"/><circle cx="4.5" cy="10" r="2"/><circle cx="19.5" cy="10" r="2"/><path d="M7 21v-2a5 5 0 0 1 10 0v2M1 20v-2a4 4 0 0 1 4-4M23 20v-2a4 4 0 0 0-4-4"/></>,
    shield:<><path d="M12 2 4 5v6c0 5 3.3 9 8 11 4.7-2 8-6 8-11V5zM9 12l2 2 4-5"/></>,
    database:<><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/></>,
    check:<path d="m5 12 4 4L19 6"/>,
    profile:<><circle cx="12" cy="7" r="3"/><path d="M7 19v-2a5 5 0 0 1 10 0v2M18 14h3v7h-5"/></>,
    chart:<><circle cx="12" cy="12" r="9"/><path d="M12 3v9h9M12 12l6.4 6.4"/></>,
    usercheck:<><circle cx="9" cy="7" r="3"/><path d="M3 20v-2a6 6 0 0 1 10-4.5M15 17l2 2 4-5"/></>,
    followup:<><path d="M6 3h12v19H6zM9 3V1h6v2M9 11h6M9 15h4"/><path d="m15 18 1.5 1.5L20 16"/></>,
  }
  return <svg viewBox="0 0 24 24" aria-hidden="true" {...props} {...common}>{paths[name]}</svg>
}

export function LeafMark({className}:{className?:string}){
  return <svg className={className} viewBox="0 0 42 52" aria-hidden="true"><g fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 49C19 31 23 16 36 3M21 37C12 33 7 26 6 18c8 1 14 5 17 11M25 26c7-2 12-8 13-15-7 1-12 4-15 9M18 24C11 20 8 14 9 7c7 2 11 6 13 11M27 15c4-2 7-6 8-11"/></g></svg>
}

export function RiceBotanical({className}:{className?:string}){
  return <svg className={className} viewBox="0 0 480 720" aria-hidden="true"><image href="/images/vnutricare-rice-botanical.png" width="480" height="720" preserveAspectRatio="xMinYMax meet"/></svg>
}
