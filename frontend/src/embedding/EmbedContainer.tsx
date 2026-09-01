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
  // Held in a ref, not state: an allowlisted host can identify itself at any
  // time (see below) and that must not re-run the effect and re-register the
  // observer and listener.
  const targetOriginRef = useRef<string | null>(parentOrigin)

  useEffect(() => {
    targetOriginRef.current = parentOrigin
  }, [parentOrigin])

  // Mirrored onto the document root as well as the wrapper below. The
  // wrapper's attribute drives the widget's own dark styles; the root's
  // paints the iframe canvas, which the wrapper cannot do without stretching
  // itself — and its height is exactly what auto-resize reports to the host.
  useEffect(() => {
    document.documentElement.dataset.theme = config.theme
  }, [config.theme])

  useEffect(() => {
    const element = rootRef.current
    if (element === null || window.parent === window) {
      return // Not embedded at all.
    }

    const postHeight = () => {
      const message = buildResizeMessage(element.offsetHeight)
      const resolved = targetOriginRef.current
      if (resolved !== null) {
        window.parent.postMessage(message, resolved)
        return
      }
      // Host not resolvable from the referrer (referrerpolicy="no-referrer",
      // or an HTTPS page framed over HTTP). Address every allowlisted origin
      // instead of giving up: postMessage only delivers when targetOrigin
      // equals the parent's real origin, so the browser itself picks the one
      // that matches and drops the rest. That is still never "*" — a host the
      // operator did not allowlist receives nothing.
      //
      // Waiting to be asked instead does not work: a message posted before
      // this component mounts is not queued anywhere, so a host that asks on
      // iframe `load` is simply never heard.
      for (const origin of allowedParentOrigins) {
        window.parent.postMessage(message, origin)
      }
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
      // An allowlisted host has identified itself. This is the only way to
      // learn the target origin when the referrer is missing — a host using
      // `referrerpolicy="no-referrer"`, or an HTTPS page framed over HTTP,
      // is allowlisted but unresolvable from the referrer alone. Without
      // this the listener used to be skipped entirely for such a host, so it
      // got no auto-resize and no way to ask for one, and the iframe stayed
      // at its initial height with the form clipped.
      targetOriginRef.current = event.origin
      postHeight()
    }

    window.addEventListener('message', handleMessage)

    return () => {
      observer.disconnect()
      window.removeEventListener('message', handleMessage)
    }
  }, [allowedParentOrigins])

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
