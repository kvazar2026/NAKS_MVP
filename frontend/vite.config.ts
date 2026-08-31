/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // `npm run dev` proxies same-origin `/api/...` calls to the local
    // backend (see src/survey/api.ts) so the widget needs no CORS
    // configuration in dev, matching how a same-origin reverse proxy will
    // serve both services later (ticket 07).
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
