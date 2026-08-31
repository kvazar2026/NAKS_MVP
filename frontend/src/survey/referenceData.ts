// Static MVP reference data, mirrored from the backend
// (backend/app/domain/reference_data.py, backend/config/attestation_centers.yaml).
// There is no endpoint that serves these lists (spec: the backend exposes
// exactly two public endpoints) — the values here must stay byte-for-byte
// identical to the backend's, since the backend re-validates every one of
// them and compares by exact string match.
//
// opo_group has no free-text/LLM normalization pass (unlike equipment_type/
// welding_method/purpose — see SurveyForm.tsx), so it is rendered as a
// select restricted to these exact labels rather than a text input.

import type { AttestationDirection } from './types'

export interface AttestationCenterOption {
  code: string
  label: string
}

export const ATTESTATION_CENTERS: readonly AttestationCenterOption[] = [{ code: 'demo', label: 'Демо-АЦ' }]

export interface AttestationDirectionOption {
  value: AttestationDirection
  label: string
  disabled: boolean
}

export const ATTESTATION_DIRECTIONS: readonly AttestationDirectionOption[] = [
  { value: 'equipment', label: 'Оборудование', disabled: false },
  { value: 'materials', label: 'Материалы (скоро)', disabled: true },
  { value: 'welders', label: 'Сварщики (скоро)', disabled: true },
]

export interface OpoGroupOption {
  code: string
  label: string
}

export const OPO_GROUPS: readonly OpoGroupOption[] = [
  { code: '1', label: 'Группа 1 — сосуды и аппараты, работающие под давлением' },
  { code: '2', label: 'Группа 2 — технологические трубопроводы' },
  { code: '3', label: 'Группа 3 — объекты котлонадзора' },
  { code: '4', label: 'Группа 4 — подъёмные сооружения' },
  { code: '5', label: 'Группа 5 — объекты горнодобывающей и металлургической промышленности' },
]
