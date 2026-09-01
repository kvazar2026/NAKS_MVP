import { render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import EmbedContainer from './EmbedContainer'
import type { EmbedConfig } from './embedConfig'
import { PARTNERS, DEMO_PARTNER_ID } from './embedConfig'
import { RESIZE_MESSAGE_TYPE, SIZE_REQUEST_MESSAGE_TYPE } from './parentMessaging'

const HOST_ORIGIN = 'https://host.example'

const BASE_CONFIG: EmbedConfig = {
  theme: 'light',
  partner: PARTNERS[DEMO_PARTNER_ID],
  didFallBackToDemoPartner: false,
}

const postMessageToParent = vi.fn()
let resizeCallbacks: Array<() => void> = []
let originalParent: PropertyDescriptor | undefined

class ResizeObserverStub {
  constructor(callback: () => void) {
    resizeCallbacks.push(callback)
  }
  observe() {}
  disconnect() {}
  unobserve() {}
}

beforeEach(() => {
  postMessageToParent.mockReset()
  resizeCallbacks = []
  originalParent = Object.getOwnPropertyDescriptor(window, 'parent')
  // jsdom's window.parent is the window itself; the component treats that as
  // "not embedded", so a distinct parent is needed to exercise messaging.
  Object.defineProperty(window, 'parent', {
    value: { postMessage: postMessageToParent },
    configurable: true,
  })
  vi.stubGlobal('ResizeObserver', ResizeObserverStub)
})

afterEach(() => {
  if (originalParent) {
    Object.defineProperty(window, 'parent', originalParent)
  }
  vi.unstubAllGlobals()
})

function renderContainer(overrides: Partial<Parameters<typeof EmbedContainer>[0]> = {}) {
  return render(
    <EmbedContainer
      config={BASE_CONFIG}
      allowedParentOrigins={[HOST_ORIGIN]}
      parentOrigin={HOST_ORIGIN}
      {...overrides}
    >
      <p>содержимое виджета</p>
    </EmbedContainer>,
  )
}

describe('EmbedContainer messaging', () => {
  it('posts its height to the allowed parent origin on mount, never to "*"', () => {
    renderContainer()

    expect(postMessageToParent).toHaveBeenCalledTimes(1)
    const [message, targetOrigin] = postMessageToParent.mock.calls[0]
    expect(message.type).toBe(RESIZE_MESSAGE_TYPE)
    expect(typeof message.height).toBe('number')
    expect(targetOrigin).toBe(HOST_ORIGIN)
  })

  it('posts again when the content size changes', () => {
    renderContainer()
    postMessageToParent.mockClear()

    resizeCallbacks.forEach((callback) => callback())

    expect(postMessageToParent).toHaveBeenCalledTimes(1)
    expect(postMessageToParent.mock.calls[0][1]).toBe(HOST_ORIGIN)
  })

  it('addresses every allowlisted origin — and only those — when the referrer is missing', () => {
    // A host using referrerpolicy="no-referrer" (or an HTTPS page framed over
    // HTTP) is allowlisted but unresolvable from the referrer, so it reaches
    // this component as parentOrigin: null. Addressing each allowlisted
    // origin is safe because postMessage only delivers when targetOrigin
    // matches the parent's real origin — the browser picks the right one and
    // drops the rest (verified in Chromium: an allowlisted host receives the
    // height, a non-allowlisted one receives nothing). jsdom does no such
    // filtering, so here we can only assert who was addressed.
    renderContainer({
      parentOrigin: null,
      allowedParentOrigins: [HOST_ORIGIN, 'https://second-host.example'],
    })

    const targets = postMessageToParent.mock.calls.map(([, target]) => target)
    expect(targets).toEqual([HOST_ORIGIN, 'https://second-host.example'])
    expect(targets).not.toContain('*')
  })

  it('waiting to be asked is not enough, so it announces on mount', () => {
    // A host that posts request-size on iframe `load` may well do so before
    // this component mounts, and that message is not queued anywhere — the
    // announce above is what makes the no-referrer case work at all.
    renderContainer({ parentOrigin: null })

    expect(postMessageToParent).toHaveBeenCalledTimes(1)
    expect(postMessageToParent.mock.calls[0][0].type).toBe(RESIZE_MESSAGE_TYPE)
  })

  it('pins to an allowlisted host once it identifies itself', () => {
    renderContainer({
      parentOrigin: null,
      allowedParentOrigins: [HOST_ORIGIN, 'https://second-host.example'],
    })
    postMessageToParent.mockClear()

    window.dispatchEvent(
      new MessageEvent('message', { origin: HOST_ORIGIN, data: { type: SIZE_REQUEST_MESSAGE_TYPE } }),
    )
    postMessageToParent.mockClear()
    resizeCallbacks.forEach((callback) => callback())

    // No longer fanned out across the allowlist.
    expect(postMessageToParent.mock.calls.map(([, target]) => target)).toEqual([HOST_ORIGIN])
  })

  it('does not let a non-allowlisted origin identify itself as the host', () => {
    renderContainer({ parentOrigin: null, allowedParentOrigins: [HOST_ORIGIN] })

    window.dispatchEvent(
      new MessageEvent('message', { origin: 'https://evil.example', data: { type: SIZE_REQUEST_MESSAGE_TYPE } }),
    )
    postMessageToParent.mockClear()
    resizeCallbacks.forEach((callback) => callback())

    // Still only the allowlist — evil.example never became the target.
    expect(postMessageToParent.mock.calls.map(([, target]) => target)).toEqual([HOST_ORIGIN])
  })

  it('answers a size request from an allowed origin', () => {
    renderContainer()
    postMessageToParent.mockClear()

    window.dispatchEvent(
      new MessageEvent('message', { origin: HOST_ORIGIN, data: { type: SIZE_REQUEST_MESSAGE_TYPE } }),
    )

    expect(postMessageToParent).toHaveBeenCalledTimes(1)
    expect(postMessageToParent.mock.calls[0][0].type).toBe(RESIZE_MESSAGE_TYPE)
  })

  it('ignores a size request from an origin outside the allowlist', () => {
    renderContainer()
    postMessageToParent.mockClear()

    window.dispatchEvent(
      new MessageEvent('message', { origin: 'https://evil.example', data: { type: SIZE_REQUEST_MESSAGE_TYPE } }),
    )

    expect(postMessageToParent).not.toHaveBeenCalled()
  })

  it('ignores an unrelated message from an allowed origin', () => {
    renderContainer()
    postMessageToParent.mockClear()

    window.dispatchEvent(new MessageEvent('message', { origin: HOST_ORIGIN, data: { type: 'something-else' } }))

    expect(postMessageToParent).not.toHaveBeenCalled()
  })
})

describe('EmbedContainer rendering', () => {
  it('applies the resolved theme to the widget wrapper and the document root', () => {
    // The wrapper attribute drives the widget's own dark styles; the document
    // root's paints the iframe canvas behind them.
    const { container } = renderContainer({ config: { ...BASE_CONFIG, theme: 'dark' } })

    expect(container.querySelector('.embed-root')?.getAttribute('data-theme')).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('shows a notice when an unknown partner fell back to the demo configuration', () => {
    renderContainer({ config: { ...BASE_CONFIG, didFallBackToDemoPartner: true } })

    expect(screen.getByRole('status').textContent).toContain('Идентификатор партнёра не распознан')
  })

  it('shows no notice for a recognised partner', () => {
    renderContainer()

    expect(screen.queryByRole('status')).toBeNull()
  })

  it('renders the widget content it wraps', () => {
    renderContainer()

    expect(screen.getByText('содержимое виджета')).toBeTruthy()
  })
})
