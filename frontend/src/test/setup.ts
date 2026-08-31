import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Unmount rendered components after each test so DOM state doesn't leak
// between test cases.
afterEach(() => {
  cleanup()
})
