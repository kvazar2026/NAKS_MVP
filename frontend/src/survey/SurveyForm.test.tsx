import { useState } from 'react'

import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { initialFormState, type FormState } from './formState'
import SurveyForm from './SurveyForm'
import type { ValidationIssue } from './types'

/** SurveyForm is a controlled component (form state lives in SurveyWidget,
 * see formState.ts, so it survives the form -> loading -> form round trip
 * after a blocking-error response). This harness reproduces just enough of
 * that ownership for the checked/value props to actually update in tests.
 */
function TestHarness({
  errors = [],
  onSubmit = vi.fn(),
}: {
  errors?: ValidationIssue[]
  onSubmit?: () => void
}) {
  const [form, setForm] = useState<FormState>(initialFormState)

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((previous) => ({ ...previous, [key]: value }))
  }

  return <SurveyForm form={form} onFieldChange={updateField} errors={errors} isSubmitting={false} onSubmit={onSubmit} />
}

describe('SurveyForm', () => {
  it('renders every field from the equipment survey (organization, contact, attestation, equipment, consent)', () => {
    render(<TestHarness />)

    // Organization
    expect(screen.getByLabelText('ИНН организации')).toBeTruthy()
    expect(screen.getByLabelText('Название организации')).toBeTruthy()
    expect(screen.getByLabelText('Адрес организации')).toBeTruthy()

    // Contact
    expect(screen.getByLabelText('ФИО контактного лица')).toBeTruthy()
    expect(screen.getByLabelText('Должность')).toBeTruthy()
    expect(screen.getByLabelText('Телефон')).toBeTruthy()
    expect(screen.getByLabelText('Email')).toBeTruthy()

    // Attestation
    expect(screen.getByLabelText('Аттестационный центр')).toBeTruthy()
    expect(screen.getByRole('option', { name: 'Демо-АЦ' })).toBeTruthy()
    expect(screen.getByLabelText('Оборудование')).toBeTruthy()
    expect(screen.getByLabelText('Группа ОПО')).toBeTruthy()
    expect(screen.getByLabelText('Регион проведения аттестации')).toBeTruthy()

    // Equipment
    expect(screen.getByLabelText('Тип оборудования')).toBeTruthy()
    expect(screen.getByLabelText('Марка')).toBeTruthy()
    expect(screen.getByLabelText('Модель')).toBeTruthy()
    expect(screen.getByLabelText('Изготовитель')).toBeTruthy()
    expect(screen.getByLabelText('Способ сварки')).toBeTruthy()
    expect(screen.getByLabelText('Количество, шт.')).toBeTruthy()
    expect(screen.getByLabelText('Заводские номера (по одному в строке)')).toBeTruthy()
    expect(screen.getByLabelText('Назначение')).toBeTruthy()

    // Consent
    expect(screen.getByLabelText(/согласен\(на\) на обработку данных/)).toBeTruthy()
    expect(screen.getByRole('button', { name: 'Отправить заявку' })).toBeTruthy()
  })

  it('displays blocking errors returned from the last submit attempt', () => {
    const errors: ValidationIssue[] = [
      { field: 'organization.inn', code: 'invalid_format', message: 'ИНН должен состоять из 10 или 12 цифр' },
      { field: 'consent', code: 'consent_required', message: 'Необходимо согласие на обработку данных' },
    ]

    render(<TestHarness errors={errors} />)

    expect(screen.getAllByText('ИНН должен состоять из 10 или 12 цифр').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Необходимо согласие на обработку данных').length).toBeGreaterThan(0)
  })

  it('keeps the submit button disabled until consent is checked', () => {
    render(<TestHarness />)

    const submitButton = screen.getByRole('button', { name: 'Отправить заявку' })
    const consentCheckbox = screen.getByLabelText(/согласен\(на\) на обработку данных/)

    expect(submitButton.hasAttribute('disabled')).toBe(true)

    fireEvent.click(consentCheckbox)
    expect(submitButton.hasAttribute('disabled')).toBe(false)

    fireEvent.click(consentCheckbox)
    expect(submitButton.hasAttribute('disabled')).toBe(true)
  })

  it('renders "materials" and "welders" as disabled options, unlike "equipment"', () => {
    render(<TestHarness />)

    expect(screen.getByLabelText('Оборудование').hasAttribute('disabled')).toBe(false)
    expect(screen.getByLabelText('Материалы (скоро)').hasAttribute('disabled')).toBe(true)
    expect(screen.getByLabelText('Сварщики (скоро)').hasAttribute('disabled')).toBe(true)
  })

  it('calls onSubmit once consent is given and the form is submitted', () => {
    const handleSubmit = vi.fn()
    render(<TestHarness onSubmit={handleSubmit} />)

    fireEvent.click(screen.getByLabelText(/согласен\(на\) на обработку данных/))
    fireEvent.click(screen.getByRole('button', { name: 'Отправить заявку' }))

    expect(handleSubmit).toHaveBeenCalledTimes(1)
  })
})
