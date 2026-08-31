import type { ReactNode } from 'react'

interface DemoBannerProps {
  children: ReactNode
}

/** Reusable demo-mode notice (spec, User Story 2 and the consent banner). */
function DemoBanner({ children }: DemoBannerProps) {
  return (
    <p role="note" className="demo-banner">
      {children}
    </p>
  )
}

export default DemoBanner
