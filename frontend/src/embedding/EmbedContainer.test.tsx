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

  it('posts nothing when the host origin is not on the allowlist', () => {
    renderContainer({ parentOrigin: null })

    expect(postMessageToParent).not.toHaveBeenCalled()
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
  it('applies the resolved theme as a data attribute', () => {
    const { container } = renderContainer({ config: { ...BASE_CONFIG, theme: 'dark' } })

    expect(container.querySelector('.embed-root')?.getAttribute('data-theme')).toBe('dark')
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
