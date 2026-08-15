import type { SVGProps } from 'react'

export function Icon({name, ...props}: SVGProps<SVGSVGElement> & {name:string}) {
  const common={fill:'none',stroke:'currentColor',strokeWidth:2,strokeLinecap:'round' as const,strokeLinejoin:'round' as const}
  const paths:Record<string,React.ReactNode>={
    user:<><circle cx="12" cy="7" r="3.5"/><path d="M5 21v-2a7 7 0 0 1 14 0v2"/></>,
    robot:<><rect x="4" y="9" width="16" height="11" rx="3"/><path d="M12 9V5M9 3.5h6"/><circle cx="12" cy="5" r="1.4" fill="currentColor" stroke="none"/><circle cx="9" cy="14.5" r="1.3" fill="currentColor" stroke="none"/><circle cx="15" cy="14.5" r="1.3" fill="currentColor" stroke="none"/><path d="M8 18h8M1 12v3M23 12v3"/></>,
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
    home:<><path d="m3 11 9-8 9 8"/><path d="M5 10v11h14V10M9 21v-7h6v7"/></>,
    diary:<><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 3v18M11 8h5M11 12h5M11 16h3"/></>,
    trend:<><path d="M4 19V5M4 19h16M7 15l4-4 3 2 5-6"/></>,
    heart:<><path d="M20.8 4.6a5.4 5.4 0 0 0-7.6 0L12 5.8l-1.2-1.2a5.4 5.4 0 0 0-7.6 7.6L12 21l8.8-8.8a5.4 5.4 0 0 0 0-7.6Z"/></>,
    plus:<><path d="M12 5v14M5 12h14"/></>,
    clock:<><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
    warning:<><path d="M12 3 2.8 20h18.4zM12 9v4M12 17h.01"/></>,
    sparkles:<><path d="m12 3 1.2 3.8L17 8l-3.8 1.2L12 13l-1.2-3.8L7 8l3.8-1.2zM18 14l.7 2.3L21 17l-2.3.7L18 20l-.7-2.3L15 17l2.3-.7z"/></>,
    calendar:<><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18M8 14h3M8 17h7"/></>,
    menu:<><path d="M4 7h16M4 12h16M4 17h16"/></>,
    close:<><path d="m6 6 12 12M18 6 6 18"/></>,
    logout:<><path d="M10 5H4v14h6M14 8l4 4-4 4M8 12h10"/></>,
    search:<><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
    chevronRight:<path d="m9 18 6-6-6-6"/>,
    chevronDown:<path d="m6 9 6 6 6-6"/>,
    info:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></>,
    bowl:<><path d="M4 11h16c0 5-3.5 9-8 9s-8-4-8-9ZM7 7c0-1 1-2 2-2M12 7c0-1 1-2 2-2M17 7c0-1 1-2 2-2"/></>,
    edit:<><path d="m4 20 4.5-1 10-10a2.1 2.1 0 0 0-3-3l-10 10zM14 7l3 3"/></>,
    refresh:<><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 8A7 7 0 0 1 18 6l2 6M17.9 16A7 7 0 0 1 6 18l-2-6"/></>,
    arrowLeft:<path d="m15 18-6-6 6-6"/>,
    arrowRight:<path d="m9 18 6-6-6-6"/>,
    message:<><path d="M21 15a4 4 0 0 1-4 4H8l-5 3 1.7-5A7 7 0 0 1 3 12V8a5 5 0 0 1 5-5h8a5 5 0 0 1 5 5z"/></>,
    bell:<><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></>,
    scale:<><path d="M12 3v18M6 6h12M4 6l-3 6h6zM20 6l-3 6h6zM8 21h8"/></>,
    sparkle:<><path d="m12 2 1.4 5.6L19 9l-5.6 1.4L12 16l-1.4-5.6L5 9l5.6-1.4zM19 16l.7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7z"/></>,
    sun:<><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/><circle cx="12" cy="12" r="4"/></>,
    moon:<path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5Z"/>,
    warn:<><path d="M12 3 2 21h20zM12 9v5M12 18h.01"/></>,
    save:<><path d="M5 3h12l2 2v16H5zM8 3v6h8V3M8 21v-7h8v7"/></>,
  }
  return <svg viewBox="0 0 24 24" aria-hidden="true" {...props} {...common}>{paths[name]}</svg>
}

export function LeafMark({className}:{className?:string}){
  return <svg className={className} viewBox="0 0 42 52" aria-hidden="true"><g fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 49C19 31 23 16 36 3M21 37C12 33 7 26 6 18c8 1 14 5 17 11M25 26c7-2 12-8 13-15-7 1-12 4-15 9M18 24C11 20 8 14 9 7c7 2 11 6 13 11M27 15c4-2 7-6 8-11"/></g></svg>
}

export function RiceBotanical({className}:{className?:string}){
  return <svg className={className} viewBox="0 0 480 720" aria-hidden="true"><image href="/images/vnutricare-rice-botanical.png" width="480" height="720" preserveAspectRatio="xMinYMax meet"/></svg>
}
