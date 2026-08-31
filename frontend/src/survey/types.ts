// Wire types mirroring the backend Pydantic schemas
// (backend/app/schemas/survey.py, documents.py). Field names are snake_case
// on purpose — this is the JSON contract, not idiomatic TS naming.

export interface OrganizationInfo {
  inn: string
  company_name: string
  address: string
}

export interface ContactInfo {
  full_name: string
  position: string
  phone: string
  email: string
}

export interface EquipmentInfo {
  equipment_type: string
  brand: string
  model: string
  manufacturer: string
  welding_method: string
  quantity: number
  serial_numbers: string[]
  purpose: string
}

export type AttestationDirection = 'equipment' | 'materials' | 'welders'

export interface SurveyData {
  organization: OrganizationInfo
  contact: ContactInfo
  attestation_center_code: string
  attestation_direction: AttestationDirection
  opo_group: string
  region: string
  equipment: EquipmentInfo
}

export interface SurveyValidateRequest extends SurveyData {
  consent: boolean
}

export type NormalizedSurveyData = SurveyData

export interface ValidationIssue {
  field: string
  code: string
  message: string
}

export type WarningVerificationStatus = 'not_verified_by_expert' | 'verified'

export interface ValidationWarning extends ValidationIssue {
  explanation: string
  source: string
  verification_status: WarningVerificationStatus
}

export interface SurveyValidateResponse {
  valid: boolean
  normalized_data: NormalizedSurveyData | null
  errors: ValidationIssue[]
  warnings: ValidationWarning[]
}

export interface DocumentGenerateRequest {
  normalized_data: NormalizedSurveyData
  attestation_direction: AttestationDirection
  attestation_center_code: string
}

export interface DocumentGenerateErrorResponse {
  detail: string
  errors: ValidationIssue[]
}
