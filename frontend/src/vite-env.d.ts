/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Comma-separated host origins allowed to embed the widget and exchange
   * `postMessage` with it (ticket 05). Build-time, since the widget is a
   * static bundle — see .env.example and the frontend Dockerfile build arg.
   * Empty/unset means "same origin only".
   */
  readonly VITE_ALLOWED_PARENT_ORIGINS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
