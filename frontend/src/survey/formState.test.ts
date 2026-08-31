import { describe, expect, it } from 'vitest'

import { buildSurveyPayload, initialFormState } from './formState'

describe('buildSurveyPayload', () => {
  it('maps every field into the wire request shape', () => {
    const payload = buildSurveyPayload({
      ...initialFormState,
      inn: '7701234567',
      companyName: 'ООО "Завод"',
      address: 'г. Москва',
      contactFullName: 'Иванов Иван Иванович',
      contactPosition: 'Главный сварщик',
      contactPhone: '+7 900 123-45-67',
      contactEmail: 'welder@example.com',
      opoGroup: 'Группа 1 — сосуды и аппараты, работающие под давлением',
      region: 'Московская область',
      equipmentType: 'Источник питания',
      brand: 'ESAB',
      model: 'Origo Mig 4002i',
      manufacturer: 'ESAB AB',
      weldingMethod: 'РД',
      quantity: '3',
      purpose: 'Ремонт',
      consent: true,
    })

    expect(payload).toEqual({
      organization: { inn: '7701234567', company_name: 'ООО "Завод"', address: 'г. Москва' },
      contact: {
        full_name: 'Иванов Иван Иванович',
        position: 'Главный сварщик',
        phone: '+7 900 123-45-67',
        email: 'welder@example.com',
      },
      attestation_center_code: 'demo',
      attestation_direction: 'equipment',
      opo_group: 'Группа 1 — сосуды и аппараты, работающие под давлением',
      region: 'Московская область',
      equipment: {
        equipment_type: 'Источник питания',
        brand: 'ESAB',
        model: 'Origo Mig 4002i',
        manufacturer: 'ESAB AB',
        welding_method: 'РД',
        quantity: 3,
        serial_numbers: [],
        purpose: 'Ремонт',
      },
      consent: true,
    })
  })

  it('splits the serial-numbers textarea into a trimmed, blank-free list', () => {
    const payload = buildSurveyPayload({
      ...initialFormState,
      serialNumbersText: 'SN-001\nSN-002\n\n  SN-003  \n',
    })

    expect(payload.equipment.serial_numbers).toEqual(['SN-001', 'SN-002', 'SN-003'])
  })

  it('falls back to 0 for a non-numeric quantity instead of throwing', () => {
    const payload = buildSurveyPayload({ ...initialFormState, quantity: '' })

    expect(payload.equipment.quantity).toBe(0)
  })
})
