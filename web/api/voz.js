// GET /api/voz en Vercel: el mismo servicio que vite.config.ts monta en desarrollo.
// La llave (ELEVENLABS_API_KEY) es una variable de entorno del proyecto en Vercel, nunca del repo.
// Sin ella responde 503 y el aviso lo dice la voz del navegador.
//
// Es JS a propósito: el builder de Vercel no compila con TypeScript 7. `npm run build:funcion`
// deja servidor/voz.ts compilado en api/_servicio/ (la carpeta con «_» no se publica como ruta).

import { cacheEnDisco, servicioVoz } from './_servicio/voz.js'

const servir = servicioVoz({
  llave: process.env.ELEVENLABS_API_KEY || undefined,
  vozId: process.env.ELEVENLABS_VOICE_ID || undefined,
  // En Vercel solo se escribe en /tmp y dura lo que la instancia: lo que perdura lo guarda la CDN.
  cache: cacheEnDisco('/tmp/voz'),
})

/** @param {Request} request */
export const GET = (request) => servir(new URL(request.url))
