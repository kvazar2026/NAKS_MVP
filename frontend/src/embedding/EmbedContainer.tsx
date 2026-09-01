import { useEffect, useRef, type ReactNode } from 'react'

import type { EmbedConfig } from './embedConfig'
import { buildResizeMessage, isAllowedOrigin, isSizeRequest } from './parentMessaging'

interface EmbedContainerProps {
  config: EmbedConfig
  /** Origins allowed to message this widget (incoming direction). */
  allowedParentOrigins: string[]
  /** Origin resize messages are sent to, or null when the host is unknown —
   * in which case nothing is sent (see parentMessaging.ts).
   */
  parentOrigin: string | null
  children: ReactNode
}

/** The embedding shell: theme attribute, partner notice, and the host-page
 * `postMessage` conversation (ticket 05, ADR 0003).
 *
 * Deliberately the *only* place that knows the widget might live in an
 * iframe. The survey flow underneath (`SurveyWidget`) has no idea, which is
 * what keeps a second embedding mechanism — a JS snippet, should it ever be
 * built — from requiring changes to the form logic.
 */
function EmbedContainer({ config, allowedParentOrigins, parentOrigin, children }: EmbedContainerProps) {
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = rootRef.current
    if (element === null || parentOrigin === null || window.parent === window) {
      // Not embedded, or embedded by a host we are not allowed to talk to.
      return
    }

    const postHeight = () => {
      window.parent.postMessage(buildResizeMessage(element.offsetHeight), parentOrigin)
    }

    postHeight()

    const observer = new ResizeObserver(postHeight)
    observer.observe(element)

    const handleMessage = (event: MessageEvent) => {
      // Origin check before anything else — an unrecognised sender's message
      // is dropped without being inspected further (User Story 22).
      if (!isAllowedOrigin(allowedParentOrigins, event.origin) || !isSizeRequest(event.data)) {
        return
      }
      postHeight()
    }

    window.addEventListener('message', handleMessage)

    return () => {
      observer.disconnect()
      window.removeEventListener('message', handleMessage)
    }
  }, [allowedParentOrigins, parentOrigin])

  return (
    <div ref={rootRef} className="embed-root" data-theme={config.theme}>
      {config.didFallBackToDemoPartner && (
        <p role="status" className="demo-banner">
          Идентификатор партнёра не распознан — виджет показан в демонстрационной конфигурации.
        </p>
      )}
      {children}
    </div>
  )
}

export default EmbedContainer
