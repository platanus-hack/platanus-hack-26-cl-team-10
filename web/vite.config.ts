/// <reference types="vitest/config" />
import basicSsl from '@vitejs/plugin-basic-ssl'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// `npm run dev:celular` sirve por HTTPS en la red local: Wake Lock y el audio del celular
// exigen un contexto seguro. El certificado es autofirmado: el celular pide aceptarlo una vez.
export default defineConfig(({ mode }) => ({
  plugins: [react(), ...(mode === 'celular' ? [basicSsl()] : [])],
  // El mock importa la pauta real desde ../datos/pauta-correa.json.
  server: { fs: { allow: ['..'] } },
  test: {
    environment: 'jsdom',
    setupFiles: ['src/test-setup.ts'],
    globals: true,
  },
}))
