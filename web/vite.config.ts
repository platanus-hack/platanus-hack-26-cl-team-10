/// <reference types="vitest/config" />
import basicSsl from '@vitejs/plugin-basic-ssl'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'
import { defineConfig, loadEnv, type Connect, type Plugin } from 'vite'
import { cacheEnDisco, servicioVoz } from './servidor/voz.ts'

/**
 * GET /api/voz?texto=: la voz de ElevenLabs, servida por el mismo servidor del front. Lee
 * ELEVENLABS_API_KEY (y ELEVENLABS_VOICE_ID, si se quiere otra voz) de web/.env.local o del entorno.
 */
function voz(env: Record<string, string>): Plugin {
  const servir = servicioVoz({
    llave: env.ELEVENLABS_API_KEY || undefined,
    vozId: env.ELEVENLABS_VOICE_ID || undefined,
    cache: cacheEnDisco(fileURLToPath(new URL('./.cache/voz', import.meta.url))),
  })
  const atender: Connect.NextHandleFunction = (req, res, next) => {
    if (req.method !== 'GET' && req.method !== 'HEAD') return next()
    servir(new URL(req.originalUrl ?? req.url ?? '/', 'http://localhost'))
      .then(async (r) => {
        res.statusCode = r.status
        r.headers.forEach((valor, nombre) => res.setHeader(nombre, valor))
        res.end(Buffer.from(await r.arrayBuffer()))
      })
      .catch(next)
  }
  return {
    name: 'factum-voz',
    configureServer: (server) => void server.middlewares.use('/api/voz', atender),
    configurePreviewServer: (server) => void server.middlewares.use('/api/voz', atender),
  }
}

// `npm run dev:celular` sirve por HTTPS en la red local: Wake Lock y el audio del celular
// exigen un contexto seguro. El certificado es autofirmado: el celular pide aceptarlo una vez.
export default defineConfig(({ mode }) => {
  // Todas las variables, también las sin VITE_: la llave se usa acá, en el servidor, y no llega al navegador.
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), voz(env), ...(mode === 'celular' ? [basicSsl()] : [])],
    // El mock importa la pauta real desde ../datos/pauta-correa.json.
    server: { fs: { allow: ['..'] } },
    test: {
      environment: 'jsdom',
      setupFiles: ['src/test-setup.ts'],
      globals: true,
    },
  }
})
