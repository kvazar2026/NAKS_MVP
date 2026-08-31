// Thin HTTP client — the boundary tests mock (spec, Testing Decisions:
// "Сетевой слой мокается на границе HTTP-клиента, а не глубже").
//
// Requests use relative paths so the widget works unmodified behind a
// same-origin reverse proxy (the eventual Docker Compose setup, ticket 07)
// and, for local `npm run dev`, behind Vite's dev-server proxy
// (vite.config.ts forwards `/api` to the backend) — no CORS configuration
// needed on the backend for either case.

import type { DocumentGenerateRequest, SurveyValidateRequest, SurveyValidateResponse } from './types'

export class ApiError extends Error {}

export async function validateSurvey(payload: SurveyValidateRequest): Promise<SurveyValidateResponse> {
  const response = await fetch('/api/v1/survey/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new ApiError(`survey validate request failed with status ${response.status}`)
  }

  return (await response.json()) as SurveyValidateResponse
}

export async function generateDocument(payload: DocumentGenerateRequest): Promise<Blob> {
  const response = await fetch('/api/v1/documents/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new ApiError(`document generate request failed with status ${response.status}`)
  }

  return await response.blob()
}
