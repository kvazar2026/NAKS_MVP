import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('renders the widget heading and the equipment survey form', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: 'НАКС — виджет преквалификации (демо)',
      }),
    ).toBeTruthy()
    expect(screen.getByLabelText('ИНН организации')).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Отправить заявку' })).toBeTruthy()
  })
})
