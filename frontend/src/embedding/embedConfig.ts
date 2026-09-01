// Embedding configuration read from the widget page's query string
// (ticket 05, ADR 0003).
//
// Security note, because this is the one place host-page input reaches the
// widget: neither parameter is ever rendered or evaluated as-is. `theme`
// selects a value from a closed enum and is only used as a `data-theme`
// attribute matched by our own CSS — arbitrary CSS, URLs or HTML passed here
// never reach the DOM. `partner` is only ever used as a lookup key into the
// registry below; what gets displayed is our own label, never the raw
// parameter. Adding a parameter that is rendered directly would break that
// property, so don't.

export const THEMES = ['light', 'dark'] as const

export type Theme = (typeof THEMES)[number]

export const DEFAULT_THEME: Theme = 'light'

export interface PartnerConfig {
  id: string
  label: string
}

export const DEMO_PARTNER_ID = 'demo'

/** Known partners. MVP ships exactly one — the demo attestation centre
 * (CONTEXT.md): no real centre names or branding appear anywhere in the
 * widget. Real partners get added here, not passed in from the URL.
 */
export const PARTNERS: Record<string, PartnerConfig> = {
  [DEMO_PARTNER_ID]: { id: DEMO_PARTNER_ID, label: 'Демо-АЦ' },
}

export interface EmbedConfig {
  theme: Theme
  partner: PartnerConfig
  /** True only when a partner was explicitly requested and not recognised.
   * An omitted `partner` is the normal demo case, not a fallback, and must
   * not raise the notice.
   */
  didFallBackToDemoPartner: boolean
}

function isTheme(value: string | null): value is Theme {
  return value !== null && (THEMES as readonly string[]).includes(value)
}

/** Resolve `theme` and `partner` from a query string.
 *
 * Both degrade instead of failing (User Story 21): an unknown theme falls
 * back to the default silently, an unknown partner falls back to the demo
 * configuration and flags it so the UI can say so.
 */
export function resolveEmbedConfig(search: string): EmbedConfig {
  const params = new URLSearchParams(search)

  const requestedTheme = params.get('theme')
  const requestedPartner = params.get('partner')

  // Object.hasOwn, not a plain `PARTNERS[key]` lookup: a bare index also
  // reaches Object.prototype, so `?partner=constructor` (or toString,
  // valueOf, __proto__) would count as a known partner — suppressing the
  // unknown-partner notice and putting a Function where a PartnerConfig
  // belongs.
  const knownPartner =
    requestedPartner !== null && Object.hasOwn(PARTNERS, requestedPartner)
      ? PARTNERS[requestedPartner]
      : undefined

  return {
    theme: isTheme(requestedTheme) ? requestedTheme : DEFAULT_THEME,
    partner: knownPartner ?? PARTNERS[DEMO_PARTNER_ID],
    didFallBackToDemoPartner: requestedPartner !== null && knownPartner === undefined,
  }
}

/** Parent origins this widget is allowed to talk to, from the build-time
 * `VITE_ALLOWED_PARENT_ORIGINS` (comma-separated).
 *
 * Defaults to the widget's own origin, which is what makes the bundled demo
 * page work out of the box while keeping real cross-origin embedding an
 * explicit, deliberate configuration step rather than something that works by
 * accident.
 */
export function parseAllowedParentOrigins(raw: string | undefined, selfOrigin: string): string[] {
  const configured = (raw ?? '')
    .split(',')
    .map((origin) => origin.trim())
    .filter((origin) => origin.length > 0)

  return configured.length > 0 ? configured : [selfOrigin]
}
