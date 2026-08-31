import { useState } from 'react'

import { validateSurvey } from './api'
import DemoBanner from './DemoBanner'
import { buildSurveyPayload, initialFormState, type FormState } from './formState'
import ResultScreen from './ResultScreen'
import SurveyForm from './SurveyForm'
import type { NormalizedSurveyData, ValidationIssue, ValidationWarning } from './types'

const GENERIC_SUBMIT_ERROR = 'Сервис временно недоступен. Попробуйте повторить попытку позже.'

type Stage = 'form' | 'loading' | 'result'

function LoadingScreen() {
  return (
    <section aria-live="polite">
      <p>Идёт проверка данных, подождите…</p>
    </section>
  )
}

/** Orchestrates the survey flow: опросник → экран ожидания → блокирующие
 * ошибки (остаёмся на форме, с уже введёнными значениями) | экран
 * результата (spec, Frontend section). Not coupled to iframe embedding in
 * any way — that is ticket 05's module.
 */
function SurveyWidget() {
  const [stage, setStage] = useState<Stage>('form')
  const [form, setForm] = useState<FormState>(initialFormState)
  const [errors, setErrors] = useState<ValidationIssue[]>([])
  const [warnings, setWarnings] = useState<ValidationWarning[]>([])
  const [normalizedData, setNormalizedData] = useState<NormalizedSurveyData | null>(null)
  const [generalError, setGeneralError] = useState<string | null>(null)

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((previous) => ({ ...previous, [key]: value }))
  }

  async function handleSubmit() {
    setGeneralError(null)
    setErrors([])
    setStage('loading')

    try {
      const response = await validateSurvey(buildSurveyPayload(form))
      if (response.valid && response.normalized_data) {
        setNormalizedData(response.normalized_data)
        setWarnings(response.warnings)
        setStage('result')
      } else {
        setErrors(response.errors)
        setStage('form')
      }
    } catch {
      // Network failure or non-OK HTTP status (ApiError, see api.ts) — either
      // way the user only ever sees one safe, non-technical message
      // (User Story 18), never the underlying cause.
      setGeneralError(GENERIC_SUBMIT_ERROR)
      setStage('form')
    }
  }

  function handleRestart() {
    setStage('form')
    setForm(initialFormState)
    setErrors([])
    setWarnings([])
    setNormalizedData(null)
    setGeneralError(null)
  }

  return (
    <div className="survey-widget">
      <DemoBanner>
        Демонстрационный режим: введённые данные не сохраняются, это не финальная версия сервиса.
      </DemoBanner>

      {generalError && (
        <p role="alert" className="error-summary">
          {generalError}
        </p>
      )}

      {stage === 'loading' && <LoadingScreen />}
      {stage === 'form' && (
        <SurveyForm form={form} onFieldChange={updateField} errors={errors} isSubmitting={false} onSubmit={handleSubmit} />
      )}
      {stage === 'result' && normalizedData && (
        <ResultScreen normalizedData={normalizedData} warnings={warnings} onRestart={handleRestart} />
      )}
    </div>
  )
}

export default SurveyWidget
