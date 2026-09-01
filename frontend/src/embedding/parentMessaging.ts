// `postMessage` contract between the embedded widget and the host page
// (ticket 05, User Stories 20 and 22).
//
// The rule this module exists to enforce: the widget never posts to `*` and
// never acts on a message whose `event.origin` is not on the allowlist. Both
// directions fail closed — an unrecognised parent means no messages are sent
// at all, rather than a broadcast to whoever happens to be framing us.

/** Widget → host: the content height changed. */
export const RESIZE_MESSAGE_TYPE = 'naks-widget:resize'

/** Host → widget: re-send the current height (for when the host's own layout
 * changed and it wants to re-sync without waiting for widget content to move).
 */
export const SIZE_REQUEST_MESSAGE_TYPE = 'naks-widget:request-size'

export interface ResizeMessage {
  type: typeof RESIZE_MESSAGE_TYPE
  height: number
}

/** Origin of `url`, or null if it is empty or unparseable. */
export function originOf(url: string): string | null {
  if (!url) {
    return null
  }
  try {
    return new URL(url).origin
  } catch {
    return null
  }
}

export function isAllowedOrigin(allowedOrigins: string[], origin: string): boolean {
  return allowedOrigins.includes(origin)
}

/** The origin resize messages may be sent to, or null when there is none.
 *
 * Resolved from the referrer — the host page that framed us — and accepted
 * only if it is on the allowlist. Returning null (so the caller sends
 * nothing) is the deliberate behaviour for an unknown host: posting to `*`
 * would leak the widget's size to any page that embeds it.
 */
export function resolveParentOrigin(allowedOrigins: string[], referrer: string): string | null {
  const referrerOrigin = originOf(referrer)
  if (referrerOrigin === null) {
    return null
  }
  return isAllowedOrigin(allowedOrigins, referrerOrigin) ? referrerOrigin : null
}

export function isSizeRequest(data: unknown): boolean {
  return typeof data === 'object' && data !== null && (data as { type?: unknown }).type === SIZE_REQUEST_MESSAGE_TYPE
}

export function buildResizeMessage(height: number): ResizeMessage {
  return { type: RESIZE_MESSAGE_TYPE, height }
}
