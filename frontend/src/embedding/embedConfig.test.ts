import { describe, expect, it } from 'vitest'

import { DEFAULT_THEME, parseAllowedParentOrigins, resolveEmbedConfig } from './embedConfig'
import { originOf, resolveParentOrigin } from './parentMessaging'

describe('resolveEmbedConfig', () => {
  it('accepts a theme from the allowed enum', () => {
    expect(resolveEmbedConfig('?theme=dark').theme).toBe('dark')
  })

  it('falls back to the default theme for a value outside the enum', () => {
    expect(resolveEmbedConfig('?theme=neon').theme).toBe(DEFAULT_THEME)
  })

  it('never lets a theme parameter through as raw CSS or markup', () => {
    const config = resolveEmbedConfig('?theme=' + encodeURIComponent('red; background: url(https://evil.example)'))

    expect(config.theme).toBe(DEFAULT_THEME)
  })

  it('falls back to the default theme when the parameter is absent', () => {
    expect(resolveEmbedConfig('').theme).toBe(DEFAULT_THEME)
  })

  it('resolves a known partner without flagging a fallback', () => {
    const config = resolveEmbedConfig('?partner=demo')

    expect(config.partner.id).toBe('demo')
    expect(config.didFallBackToDemoPartner).toBe(false)
  })

  it('falls back to the demo partner and flags it when the partner is unknown', () => {
    const config = resolveEmbedConfig('?partner=some-unregistered-ac')

    expect(config.partner.id).toBe('demo')
    expect(config.didFallBackToDemoPartner).toBe(true)
  })

  it('treats an omitted partner as the plain demo case, not a fallback', () => {
    const config = resolveEmbedConfig('?theme=light')

    expect(config.partner.id).toBe('demo')
    expect(config.didFallBackToDemoPartner).toBe(false)
  })

  it.each(['constructor', 'toString', 'valueOf', 'hasOwnProperty', '__proto__'])(
    'does not treat the inherited property %j as a known partner',
    (probe) => {
      // A bare PARTNERS[key] lookup reaches Object.prototype, so these would
      // pass as recognised partners and put a Function into config.partner.
      const config = resolveEmbedConfig(`?partner=${encodeURIComponent(probe)}`)

      expect(config.partner.id).toBe('demo')
      expect(config.partner.label).toBe('Демо-АЦ')
      expect(config.didFallBackToDemoPartner).toBe(true)
    },
  )
})

describe('parseAllowedParentOrigins', () => {
  it('splits and trims a configured list', () => {
    expect(parseAllowedParentOrigins('https://a.example, https://b.example', 'https://self.example')).toEqual([
      'https://a.example',
      'https://b.example',
    ])
  })

  it.each([undefined, '', '   ', ','])('defaults to same-origin only for %j', (raw) => {
    expect(parseAllowedParentOrigins(raw, 'https://self.example')).toEqual(['https://self.example'])
  })
})

describe('resolveParentOrigin', () => {
  it('accepts a referrer whose origin is on the allowlist', () => {
    expect(resolveParentOrigin(['https://host.example'], 'https://host.example/page?x=1')).toBe('https://host.example')
  })

  it('returns null for a referrer outside the allowlist, so nothing is posted', () => {
    expect(resolveParentOrigin(['https://host.example'], 'https://evil.example/page')).toBeNull()
  })

  it('returns null when there is no referrer at all', () => {
    expect(resolveParentOrigin(['https://host.example'], '')).toBeNull()
  })

  it('does not match on a prefix of an allowed origin', () => {
    expect(resolveParentOrigin(['https://host.example'], 'https://host.example.evil.com/page')).toBeNull()
  })
})

describe('originOf', () => {
  it('returns null for unparseable input instead of throwing', () => {
    expect(originOf('not a url')).toBeNull()
  })
})
