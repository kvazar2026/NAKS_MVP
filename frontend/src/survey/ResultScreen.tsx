import { useState } from 'react'

import { generateDocument } from './api'
import type { NormalizedSurveyData, ValidationWarning } from './types'

const DOWNLOAD_FILENAME = 'naks-zayavka-demo.docx'
const GENERIC_DOWNLOAD_ERROR = 'Не удалось сформировать документ. Попробуйте повторить попытку позже.'

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

interface ResultScreenProps {
  normalizedData: NormalizedSurveyData
  warnings: ValidationWarning[]
  onRestart: () => void
}

/** Result screen: warnings (if any) plus the download button that calls
 * `/documents/generate` (spec: opens only from here, no email delivery).
 */
function ResultScreen({ normalizedData, warnings, onRestart }: ResultScreenProps) {
  const [isDownloading, setIsDownloading] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)

  async function handleDownload() {
    setIsDownloading(true)
    setDownloadError(null)
    try {
      const blob = await generateDocument({
        normalized_data: normalizedData,
        attestation_direction: normalizedData.attestation_direction,
        attestation_center_code: normalizedData.attestation_center_code,
      })
      triggerBrowserDownload(blob, DOWNLOAD_FILENAME)
    } catch {
      setDownloadError(GENERIC_DOWNLOAD_ERROR)
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <section aria-label="Результат проверки">
      <h2>Заявка успешно проверена</h2>

      {warnings.length > 0 && (
        <div role="note" aria-label="Предупреждения">
          <h3>Обратите внимание</h3>
          <ul>
            {warnings.map((warning) => (
              <li key={`${warning.field}-${warning.code}`}>
                {warning.message} — {warning.explanation} (источник: {warning.source}, требует подтверждения
                специалистом или АЦ)
              </li>
            ))}
          </ul>
        </div>
      )}

      {downloadError && (
        <p role="alert" className="error-summary">
          {downloadError}
        </p>
      )}

      <button type="button" onClick={handleDownload} disabled={isDownloading}>
        {isDownloading ? 'Формирование документа…' : 'Скачать заявку (.docx)'}
      </button>
      <button type="button" onClick={onRestart}>
        Заполнить новую заявку
      </button>
    </section>
  )
}

export default ResultScreen
