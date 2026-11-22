// GET /api/voz?texto= — el aviso en voz, con ElevenLabs. Es nuestro: lo sirve el servidor del
// front (Vite en desarrollo; una función de Vercel al desplegar), no la API de Francisco.
//
// La llamada es la de ~/code/Godoy97/elevenlabs-tts/tts.py, con el modelo de menor latencia.
// La llave (ELEVENLABS_API_KEY) vive solo en el servidor: en desarrollo, en web/.env.local, que
// git ignora. Nunca lleva el prefijo VITE_, así Vite no la manda al navegador.
// Cada frase se pide una sola vez y queda guardada: un aviso que se repite suena sin esperar.

import { createHash } from 'node:crypto'
import { mkdir, readFile, rename, writeFile } from 'node:fs/promises'
import { join } from 'node:path'

export const MODELO = 'eleven_flash_v2_5'
/**
 * «Catalina - Chilean Spanish», de la biblioteca de ElevenLabs: acento chileno, conversacional y
 * clara, para que el aviso suene como alguien de la faena. Se cambia con ELEVENLABS_VOICE_ID.
 */
export const VOZ_POR_DEFECTO = '6Gr4AVmTax1pMJO0lHRK'
export const MAX_TEXTO = 300
/** La URL no tiene autenticación: sin tope, cualquiera gasta los créditos pidiendo textos al azar. */
export const MAX_GENERACIONES = 200
const ESPERA_ELEVENLABS_MS = 15_000

export type CacheVoz = {
  leer(clave: string): Promise<Uint8Array | null>
  guardar(clave: string, audio: Uint8Array): Promise<void>
}

export type OpcionesVoz = {
  llave: string | undefined
  vozId?: string
  cache: CacheVoz
  fetch?: typeof fetch
  maxGeneraciones?: number
}

const json = (status: number, voz: string) =>
  new Response(JSON.stringify({ voz }), { status, headers: { 'content-type': 'application/json' } })

const mp3 = (audio: Uint8Array) =>
  new Response(audio, {
    status: 200,
    // La misma frase es siempre el mismo audio: el navegador lo guarda (max-age) y la CDN también
    // (s-maxage), así una frase se genera una vez aunque la función arranque en otra instancia.
    headers: { 'content-type': 'audio/mpeg', 'cache-control': 'public, max-age=31536000, s-maxage=31536000, immutable' },
  })

/** La llave del audio guardado: la misma que usaba app/voz.py, así sirve lo que ya se generó. */
const claveDe = (vozId: string, texto: string) => createHash('sha256').update(`${vozId}:${MODELO}:${texto}`).digest('hex')

/** El servicio: recibe la URL pedida y devuelve el MP3, o un error en JSON `{voz: motivo}`. */
export function servicioVoz({ llave, vozId = VOZ_POR_DEFECTO, cache, fetch: pedir = fetch, maxGeneraciones = MAX_GENERACIONES }: OpcionesVoz) {
  let generadas = 0

  return async (url: URL): Promise<Response> => {
    const texto = (url.searchParams.get('texto') ?? '').trim()
    if (!texto || texto.length > MAX_TEXTO) return json(422, `el texto tiene que tener entre 1 y ${MAX_TEXTO} caracteres`)

    const clave = claveDe(vozId, texto)
    const guardado = await cache.leer(clave)
    if (guardado) return mp3(guardado)

    if (!llave) return json(503, 'falta ELEVENLABS_API_KEY en web/.env.local')
    if (generadas >= maxGeneraciones) return json(503, 'se alcanzó el máximo de avisos nuevos; reinicia el servidor para generar más')
    generadas++

    let r: Response
    try {
      r = await pedir(`https://api.elevenlabs.io/v1/text-to-speech/${vozId}?output_format=mp3_44100_128`, {
        method: 'POST',
        headers: { 'xi-api-key': llave, 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: texto, model_id: MODELO }),
        signal: AbortSignal.timeout(ESPERA_ELEVENLABS_MS),
      })
    } catch {
      return json(502, 'no se pudo llegar a ElevenLabs')
    }
    if (!r.ok) return json(502, `ElevenLabs respondió ${r.status}`)

    const audio = new Uint8Array(await r.arrayBuffer())
    await cache.guardar(clave, audio)
    return mp3(audio)
  }
}

export function cacheEnMemoria(): CacheVoz {
  const audios = new Map<string, Uint8Array>()
  return {
    leer: async (clave) => audios.get(clave) ?? null,
    guardar: async (clave, audio) => void audios.set(clave, audio),
  }
}

/** Un MP3 por frase en `carpeta`: sobrevive a reiniciar el servidor de desarrollo. */
export function cacheEnDisco(carpeta: string): CacheVoz {
  const ruta = (clave: string) => join(carpeta, `${clave}.mp3`)
  return {
    async leer(clave) {
      try {
        return new Uint8Array(await readFile(ruta(clave)))
      } catch {
        return null
      }
    },
    async guardar(clave, audio) {
      await mkdir(carpeta, { recursive: true })
      const temporal = `${ruta(clave)}.tmp`
      await writeFile(temporal, audio)
      await rename(temporal, ruta(clave))
    },
  }
}
