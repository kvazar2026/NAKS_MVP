import { useMemo } from 'react'

import EmbedContainer from './embedding/EmbedContainer'
import { parseAllowedParentOrigins, resolveEmbedConfig } from './embedding/embedConfig'
import { resolveParentOrigin } from './embedding/parentMessaging'
import SurveyWidget from './survey/SurveyWidget'

function App() {
  // Memoized because these depend only on the URL and referrer, which do not
  // change for the life of the page — and because a fresh array identity on
  // every render would restart EmbedContainer's observer and listener each
  // time the survey form updates its state.
  const config = useMemo(() => resolveEmbedConfig(window.location.search), [])
  const allowedParentOrigins = useMemo(
    () => parseAllowedParentOrigins(import.meta.env.VITE_ALLOWED_PARENT_ORIGINS, window.location.origin),
    [],
  )
  const parentOrigin = useMemo(
    () => resolveParentOrigin(allowedParentOrigins, document.referrer),
    [allowedParentOrigins],
  )

  return (
    <EmbedContainer config={config} allowedParentOrigins={allowedParentOrigins} parentOrigin={parentOrigin}>
      <main>
        <h1>НАКС — виджет преквалификации (демо)</h1>
        <SurveyWidget />
      </main>
    </EmbedContainer>
  )
}

export default App
