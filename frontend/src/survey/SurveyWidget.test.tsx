import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { generateDocument, validateSurvey } from './api'
import SurveyWidget from './SurveyWidget'
import type { NormalizedSurveyData, SurveyValidateResponse } from './types'

// Spec, Testing Decisions: "Сетевой слой мокается на границе HTTP-клиента,
// а не глубже" — mock api.ts's exported functions, never `fetch` itself.
vi.mock('./api', () => ({
  validateSurvey: vi.fn(),
  generateDocument: vi.fn(),
}))

const VALID_NORMALIZED_DATA: NormalizedSurveyData = {
  organization: { inn: '7701234567', company_name: 'ООО "Завод"', address: 'г. Москва' },
  contact: { full_name: 'Иванов Иван Иванович', position: 'Главный сварщик', phone: '+79001234567', email: 'a@example.com' },
  attestation_center_code: 'demo',
  attestation_direction: 'equipment',
  opo_group: 'Группа 1 — сосуды и аппараты, работающие под давлением',
  region: 'Московская область',
  equipment: {
    equipment_type: 'Источник сварочного тока',
    brand: 'ESAB',
    model: 'Origo Mig 4002i',
    manufacturer: 'ESAB AB',
    welding_method: 'РД — ручная дуговая сварка покрытым электродом',
    quantity: 2,
    serial_numbers: ['SN-001'],
    purpose: 'Ремонт и восстановление оборудования',
  },
}

function checkConsentAndSubmit() {
  fireEvent.click(screen.getByLabelText(/согласен\(на\) на обработку данных/))
  fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }))
}

describe('SurveyWidget', () => {
  beforeEach(() => {
    vi.mocked(validateSurvey).mockReset()
    vi.mocked(generateDocument).mockReset()
  })

  it('shows a loading screen while /survey/validate is in flight, then the result screen on success', async () => {
    let resolveValidate: (value: SurveyValidateResponse) => void = () => {}
    vi.mocked(validateSurvey).mockReturnValue(
      new Promise((resolve) => {
        resolveValidate = resolve
      }),
    )

    render(<SurveyWidget />)
    checkConsentAndSubmit()

    expect(await screen.findByText('Идёт проверка данных, подождите…')).toBeTruthy()

    resolveValidate({ valid: true, normalized_data: VALID_NORMALIZED_DATA, errors: [], warnings: [] })

    expect(await screen.findByRole('heading', { name: 'Заявка успешно проверена' })).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Скачать заявку (.docx)' })).toBeTruthy()
  })

  it('stays on the form and shows the blocking errors when validation fails', async () => {
    vi.mocked(validateSurvey).mockResolvedValue({
      valid: false,
      normalized_data: null,
      errors: [{ field: 'organization.inn', code: 'required', message: 'ИНН обязателен' }],
      warnings: [],
    })

    render(<SurveyWidget />)
    checkConsentAndSubmit()

    // Rendered twice by design (SurveyForm.tsx): once in the error summary,
    // once inline next to the field it belongs to.
    expect((await screen.findAllByText('ИНН обязателен')).length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: 'Отправить заявку' })).toBeTruthy()
  })

  it('shows a generic, non-technical message when the request fails outright', async () => {
    vi.mocked(validateSurvey).mockRejectedValue(new Error('network down'))

    render(<SurveyWidget />)
    checkConsentAndSubmit()

    expect(await screen.findByText('Сервис временно недоступен. Попробуйте повторить попытку позже.')).toBeTruthy()
  })

  it('calls generateDocument with the normalized data when the download button is clicked', async () => {
    vi.mocked(validateSurvey).mockResolvedValue({
      valid: true,
      normalized_data: VALID_NORMALIZED_DATA,
      errors: [],
      warnings: [],
    })
    vi.mocked(generateDocument).mockResolvedValue(new Blob(['docx-bytes']))
    URL.createObjectURL = vi.fn(() => 'blob:mock')
    URL.revokeObjectURL = vi.fn()

    render(<SurveyWidget />)
    checkConsentAndSubmit()

    const downloadButton = await screen.findByRole('button', { name: 'Скачать заявку (.docx)' })
    fireEvent.click(downloadButton)

    await waitFor(() => expect(generateDocument).toHaveBeenCalledTimes(1))
    expect(vi.mocked(generateDocument).mock.calls[0][0]).toMatchObject({
      attestation_direction: 'equipment',
      attestation_center_code: 'demo',
    })
  })
})
