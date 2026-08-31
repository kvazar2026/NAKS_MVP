import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the demo placeholder for the prequalification widget', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: 'НАКС — виджет преквалификации (демо)',
      }),
    ).toBeTruthy()
    expect(
      screen.getByText('Опросник появится в следующем тикете.'),
    ).toBeTruthy()
  })
})
