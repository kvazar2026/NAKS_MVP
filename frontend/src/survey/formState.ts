// Form field state lives here (not inside SurveyForm) and is owned by
// SurveyWidget, so it survives the form -> loading -> form round trip after
// a blocking-error response: the spec requires the form to "stay editable"
// (User Story 11) with what the user already typed, not reset to blank.

import { ATTESTATION_CENTERS } from './referenceData'
import type { AttestationDirection, SurveyValidateRequest } from './types'

export interface FormState {
  inn: string
  companyName: string
  address: string
  contactFullName: string
  contactPosition: string
  contactPhone: string
  contactEmail: string
  attestationCenterCode: string
  attestationDirection: AttestationDirection
  opoGroup: string
  region: string
  equipmentType: string
  brand: string
  model: string
  manufacturer: string
  weldingMethod: string
  quantity: string
  serialNumbersText: string
  purpose: string
  consent: boolean
}

export const initialFormState: FormState = {
  inn: '',
  companyName: '',
  address: '',
  contactFullName: '',
  contactPosition: '',
  contactPhone: '',
  contactEmail: '',
  attestationCenterCode: ATTESTATION_CENTERS[0].code,
  attestationDirection: 'equipment',
  opoGroup: '',
  region: '',
  equipmentType: '',
  brand: '',
  model: '',
  manufacturer: '',
  weldingMethod: '',
  quantity: '1',
  serialNumbersText: '',
  purpose: '',
  consent: false,
}

export function buildSurveyPayload(form: FormState): SurveyValidateRequest {
  return {
    organization: {
      inn: form.inn,
      company_name: form.companyName,
      address: form.address,
    },
    contact: {
      full_name: form.contactFullName,
      position: form.contactPosition,
      phone: form.contactPhone,
      email: form.contactEmail,
    },
    attestation_center_code: form.attestationCenterCode,
    attestation_direction: form.attestationDirection,
    opo_group: form.opoGroup,
    region: form.region,
    equipment: {
      equipment_type: form.equipmentType,
      brand: form.brand,
      model: form.model,
      manufacturer: form.manufacturer,
      welding_method: form.weldingMethod,
      quantity: Number.parseInt(form.quantity, 10) || 0,
      serial_numbers: form.serialNumbersText
        .split('\n')
        .map((value) => value.trim())
        .filter((value) => value.length > 0),
      purpose: form.purpose,
    },
    consent: form.consent,
  }
}
