import type { FormEvent } from 'react'

import DemoBanner from './DemoBanner'
import type { FormState } from './formState'
import { ATTESTATION_CENTERS, ATTESTATION_DIRECTIONS, OPO_GROUPS } from './referenceData'
import type { AttestationDirection, ValidationIssue } from './types'

interface FieldErrorsProps {
  errors: ValidationIssue[]
  field: string
}

function FieldErrors({ errors, field }: FieldErrorsProps) {
  const messages = errors.filter((error) => error.field === field).map((error) => error.message)
  if (messages.length === 0) {
    return null
  }
  return (
    <>
      {messages.map((message) => (
        <span key={message} className="field-error" role="alert">
          {message}
        </span>
      ))}
    </>
  )
}

interface SurveyFormProps {
  form: FormState
  onFieldChange: <K extends keyof FormState>(key: K, value: FormState[K]) => void
  errors: ValidationIssue[]
  isSubmitting: boolean
  onSubmit: () => void
}

/** The full equipment-direction survey (spec, User Stories 3-13).
 *
 * Purely controlled: field values and their setter live in the parent
 * (``SurveyWidget``, via ``formState.ts``) so a submit that comes back with
 * blocking errors leaves everything the user already typed in place — this
 * component only owns rendering and per-field error display.
 */
function SurveyForm({ form, onFieldChange, errors, isSubmitting, onSubmit }: SurveyFormProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {errors.length > 0 && (
        <div role="alert" className="error-summary">
          <p>Не удалось отправить заявку — исправьте отмеченные поля:</p>
          <ul>
            {errors.map((error) => (
              <li key={`${error.field}-${error.code}`}>{error.message}</li>
            ))}
          </ul>
        </div>
      )}

      <fieldset>
        <legend>Организация</legend>

        <div className="field">
          <label htmlFor="inn">ИНН организации</label>
          <input id="inn" value={form.inn} onChange={(event) => onFieldChange('inn', event.target.value)} />
          <FieldErrors errors={errors} field="organization.inn" />
        </div>

        <div className="field">
          <label htmlFor="company_name">Название организации</label>
          <input
            id="company_name"
            value={form.companyName}
            onChange={(event) => onFieldChange('companyName', event.target.value)}
          />
          <FieldErrors errors={errors} field="organization.company_name" />
        </div>

        <div className="field">
          <label htmlFor="address">Адрес организации</label>
          <input
            id="address"
            value={form.address}
            onChange={(event) => onFieldChange('address', event.target.value)}
          />
          <FieldErrors errors={errors} field="organization.address" />
        </div>
      </fieldset>

      <fieldset>
        <legend>Контактное лицо</legend>

        <div className="field">
          <label htmlFor="full_name">ФИО контактного лица</label>
          <input
            id="full_name"
            value={form.contactFullName}
            onChange={(event) => onFieldChange('contactFullName', event.target.value)}
          />
          <FieldErrors errors={errors} field="contact.full_name" />
        </div>

        <div className="field">
          <label htmlFor="position">Должность</label>
          <input
            id="position"
            value={form.contactPosition}
            onChange={(event) => onFieldChange('contactPosition', event.target.value)}
          />
          <FieldErrors errors={errors} field="contact.position" />
        </div>

        <div className="field">
          <label htmlFor="phone">Телефон</label>
          <input
            id="phone"
            type="tel"
            value={form.contactPhone}
            onChange={(event) => onFieldChange('contactPhone', event.target.value)}
          />
          <FieldErrors errors={errors} field="contact.phone" />
        </div>

        <div className="field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={form.contactEmail}
            onChange={(event) => onFieldChange('contactEmail', event.target.value)}
          />
          <FieldErrors errors={errors} field="contact.email" />
        </div>
      </fieldset>

      <fieldset>
        <legend>Аттестация</legend>

        <div className="field">
          <label htmlFor="attestation_center_code">Аттестационный центр</label>
          <select
            id="attestation_center_code"
            value={form.attestationCenterCode}
            onChange={(event) => onFieldChange('attestationCenterCode', event.target.value)}
          >
            {ATTESTATION_CENTERS.map((center) => (
              <option key={center.code} value={center.code}>
                {center.label}
              </option>
            ))}
          </select>
          <FieldErrors errors={errors} field="attestation_center_code" />
        </div>

        <fieldset>
          <legend>Направление аттестации</legend>
          {ATTESTATION_DIRECTIONS.map((option) => (
            <label key={option.value} htmlFor={`direction_${option.value}`} className="radio-option">
              <input
                id={`direction_${option.value}`}
                type="radio"
                name="attestation_direction"
                value={option.value}
                checked={form.attestationDirection === option.value}
                disabled={option.disabled}
                onChange={(event) => onFieldChange('attestationDirection', event.target.value as AttestationDirection)}
              />
              {option.label}
            </label>
          ))}
          <FieldErrors errors={errors} field="attestation_direction" />
        </fieldset>

        <div className="field">
          <label htmlFor="opo_group">Группа ОПО</label>
          <select
            id="opo_group"
            value={form.opoGroup}
            onChange={(event) => onFieldChange('opoGroup', event.target.value)}
          >
            <option value="" disabled>
              Выберите группу ОПО
            </option>
            {OPO_GROUPS.map((group) => (
              <option key={group.code} value={group.label}>
                {group.label}
              </option>
            ))}
          </select>
          <FieldErrors errors={errors} field="opo_group" />
        </div>

        <div className="field">
          <label htmlFor="region">Регион проведения аттестации</label>
          <input id="region" value={form.region} onChange={(event) => onFieldChange('region', event.target.value)} />
          <FieldErrors errors={errors} field="region" />
        </div>
      </fieldset>

      <fieldset>
        <legend>Сведения об оборудовании</legend>

        <div className="field">
          <label htmlFor="equipment_type">Тип оборудования</label>
          <input
            id="equipment_type"
            value={form.equipmentType}
            onChange={(event) => onFieldChange('equipmentType', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.equipment_type" />
        </div>

        <div className="field">
          <label htmlFor="brand">Марка</label>
          <input id="brand" value={form.brand} onChange={(event) => onFieldChange('brand', event.target.value)} />
          <FieldErrors errors={errors} field="equipment.brand" />
        </div>

        <div className="field">
          <label htmlFor="model">Модель</label>
          <input id="model" value={form.model} onChange={(event) => onFieldChange('model', event.target.value)} />
          <FieldErrors errors={errors} field="equipment.model" />
        </div>

        <div className="field">
          <label htmlFor="manufacturer">Изготовитель</label>
          <input
            id="manufacturer"
            value={form.manufacturer}
            onChange={(event) => onFieldChange('manufacturer', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.manufacturer" />
        </div>

        <div className="field">
          <label htmlFor="welding_method">Способ сварки</label>
          <input
            id="welding_method"
            value={form.weldingMethod}
            onChange={(event) => onFieldChange('weldingMethod', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.welding_method" />
        </div>

        <div className="field">
          <label htmlFor="quantity">Количество, шт.</label>
          <input
            id="quantity"
            type="number"
            min={1}
            value={form.quantity}
            onChange={(event) => onFieldChange('quantity', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.quantity" />
        </div>

        <div className="field">
          <label htmlFor="serial_numbers">Заводские номера (по одному в строке)</label>
          <textarea
            id="serial_numbers"
            rows={3}
            value={form.serialNumbersText}
            onChange={(event) => onFieldChange('serialNumbersText', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.serial_numbers" />
        </div>

        <div className="field">
          <label htmlFor="purpose">Назначение</label>
          <input
            id="purpose"
            value={form.purpose}
            onChange={(event) => onFieldChange('purpose', event.target.value)}
          />
          <FieldErrors errors={errors} field="equipment.purpose" />
        </div>
      </fieldset>

      <fieldset>
        <legend>Согласие на обработку данных</legend>
        <DemoBanner>
          Демонстрационный текст, не является утверждённой политикой обработки персональных данных.
        </DemoBanner>
        <label htmlFor="consent" className="checkbox-option">
          <input
            id="consent"
            type="checkbox"
            checked={form.consent}
            onChange={(event) => onFieldChange('consent', event.target.checked)}
          />
          Я согласен(на) на обработку данных в демонстрационном режиме
        </label>
        <FieldErrors errors={errors} field="consent" />
      </fieldset>

      <button type="submit" disabled={!form.consent || isSubmitting}>
        Отправить заявку
      </button>
    </form>
  )
}

export default SurveyForm
