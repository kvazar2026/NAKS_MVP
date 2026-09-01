import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { generateDocument } from './api'
import ResultScreen from './ResultScreen'
import type { NormalizedSurveyData, ValidationWarning } from './types'

// Spec, Testing Decisions: mock api.ts's exported functions, never `fetch`.
vi.mock('./api', () => ({
  generateDocument: vi.fn(),
}))

const NORMALIZED_DATA: NormalizedSurveyData = {
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
    quantity: 5,
    serial_numbers: ['SN-001', 'SN-002'],
    purpose: 'Ремонт и восстановление оборудования',
  },
}

const WARNING: ValidationWarning = {
  field: 'equipment.serial_numbers',
  code: 'quantity_serial_numbers_mismatch',
  message: 'Количество единиц оборудования не совпадает с числом заводских номеров',
  explanation: 'Часть парка окажется вне области аттестации.',
  source: 'naks-checklist-monetization.md',
  verification_status: 'not_verified_by_expert',
}

describe('ResultScreen warnings', () => {
  beforeEach(() => {
    vi.mocked(generateDocument).mockReset()
  })

  it('renders each warning with its explanation, source and provisional-check disclaimer', () => {
    render(<ResultScreen normalizedData={NORMALIZED_DATA} warnings={[WARNING]} onRestart={() => {}} />)

    const warningsBlock = screen.getByRole('note', { name: 'Предупреждения' })
    expect(warningsBlock.textContent).toContain(WARNING.message)
    expect(warningsBlock.textContent).toContain(WARNING.explanation)
    expect(warningsBlock.textContent).toContain(WARNING.source)
    expect(warningsBlock.textContent).toContain('Предварительная автоматическая проверка')
    expect(warningsBlock.textContent).toContain('требует подтверждения специалистом или АЦ')
    expect(warningsBlock.textContent).toContain('не проверено экспертом НАКС')
  })

  it('does not render the warnings block when there are none', () => {
    render(<ResultScreen normalizedData={NORMALIZED_DATA} warnings={[]} onRestart={() => {}} />)

    expect(screen.queryByRole('note', { name: 'Предупреждения' })).toBeNull()
  })

  it('still allows downloading the document while a warning is shown', async () => {
    vi.mocked(generateDocument).mockResolvedValue(new Blob(['docx-bytes']))
    URL.createObjectURL = vi.fn(() => 'blob:mock')
    URL.revokeObjectURL = vi.fn()

    render(<ResultScreen normalizedData={NORMALIZED_DATA} warnings={[WARNING]} onRestart={() => {}} />)

    const downloadButton = screen.getByRole('button', { name: 'Скачать заявку (.docx)' })
    expect(downloadButton.hasAttribute('disabled')).toBe(false)

    fireEvent.click(downloadButton)

    await waitFor(() => expect(generateDocument).toHaveBeenCalledTimes(1))
  })
})
