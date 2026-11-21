import { mkdtemp, readdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { cacheEnDisco, cacheEnMemoria, MAX_TEXTO, servicioVoz, type CacheVoz } from './voz.ts'

const MP3 = new Uint8Array([0x49, 0x44, 0x33, 1, 2, 3])
const url = (texto: string) => new URL(`http://localhost/api/voz?texto=${encodeURIComponent(texto)}`)

function elevenLabs(respuesta: () => Response = () => new Response(MP3, { status: 200 })) {
  const pedidos: { url: string; init: RequestInit }[] = []
  const fetch = (async (u: string | URL | Request, init?: RequestInit) => {
    pedidos.push({ url: String(u), init: init ?? {} })
    return respuesta()
  }) as typeof globalThis.fetch
  return { pedidos, fetch }
}

const bytes = async (r: Response) => new Uint8Array(await r.arrayBuffer())

it('asks ElevenLabs once per phrase, like tts.py, and serves the MP3', async () => {
  const el = elevenLabs()
  const voz = servicioVoz({ llave: 'k', cache: cacheEnMemoria(), fetch: el.fetch })
  const r1 = await voz(url('Oye, te saltaste el paso 1.'))
  const r2 = await voz(url('Oye, te saltaste el paso 1.'))
  for (const r of [r1, r2]) {
    expect(r.status).toBe(200)
    expect(r.headers.get('content-type')).toBe('audio/mpeg')
    expect(await bytes(r)).toEqual(MP3)
  }
  expect(el.pedidos).toHaveLength(1)
  const [p] = el.pedidos
  expect(p.url).toBe('https://api.elevenlabs.io/v1/text-to-speech/JBFqnCBsd6RMkjVDRZzb?output_format=mp3_44100_128')
  expect(p.init.method).toBe('POST')
  expect(p.init.headers).toMatchObject({ 'xi-api-key': 'k', 'Content-Type': 'application/json' })
  expect(JSON.parse(String(p.init.body))).toEqual({ text: 'Oye, te saltaste el paso 1.', model_id: 'eleven_flash_v2_5' })
})

it('uses another voice when one is configured', async () => {
  const el = elevenLabs()
  await servicioVoz({ llave: 'k', vozId: 'otra', cache: cacheEnMemoria(), fetch: el.fetch })(url('Hola'))
  expect(el.pedidos[0].url).toContain('/text-to-speech/otra?')
})

it('refuses an empty or too long text without calling ElevenLabs', async () => {
  const el = elevenLabs()
  const voz = servicioVoz({ llave: 'k', cache: cacheEnMemoria(), fetch: el.fetch })
  expect((await voz(url('   '))).status).toBe(422)
  expect((await voz(url('a'.repeat(MAX_TEXTO + 1)))).status).toBe(422)
  expect((await voz(new URL('http://localhost/api/voz'))).status).toBe(422)
  expect(el.pedidos).toEqual([])
})

it('without a key, a new phrase is 503 (the front falls back to the browser voice) but a saved one still plays', async () => {
  const cache = cacheEnMemoria()
  await servicioVoz({ llave: 'k', cache, fetch: elevenLabs().fetch })(url('Guardada'))
  const sinLlave = servicioVoz({ llave: undefined, cache, fetch: elevenLabs().fetch })
  expect((await sinLlave(url('Guardada'))).status).toBe(200)
  const r = await sinLlave(url('Nueva'))
  expect(r.status).toBe(503)
  expect(await r.json()).toEqual({ voz: 'falta ELEVENLABS_API_KEY en web/.env.local' })
})

it('an ElevenLabs error is a 502 and nothing is saved', async () => {
  const cache = cacheEnMemoria()
  const voz = servicioVoz({ llave: 'k', cache, fetch: elevenLabs(() => new Response('no', { status: 401 })).fetch })
  const r = await voz(url('Hola'))
  expect(r.status).toBe(502)
  expect(await r.json()).toEqual({ voz: 'ElevenLabs respondió 401' })
  expect(await cache.leer('cualquiera')).toBeNull()
})

it('stops creating new phrases after the cap, so a public URL cannot burn the credits', async () => {
  const el = elevenLabs()
  const voz = servicioVoz({ llave: 'k', cache: cacheEnMemoria(), fetch: el.fetch, maxGeneraciones: 2 })
  expect((await voz(url('uno'))).status).toBe(200)
  expect((await voz(url('dos'))).status).toBe(200)
  expect((await voz(url('tres'))).status).toBe(503)
  expect((await voz(url('uno'))).status).toBe(200)
  expect(el.pedidos).toHaveLength(2)
})

it('the disk cache keeps each phrase as an MP3 between restarts', async () => {
  const carpeta = await mkdtemp(join(tmpdir(), 'voz-'))
  const el = elevenLabs()
  await servicioVoz({ llave: 'k', cache: cacheEnDisco(carpeta), fetch: el.fetch })(url('Hola'))
  expect((await readdir(carpeta)).filter((f) => f.endsWith('.mp3'))).toHaveLength(1)
  const otraVez: CacheVoz = cacheEnDisco(carpeta)
  const r = await servicioVoz({ llave: undefined, cache: otraVez, fetch: el.fetch })(url('Hola'))
  expect(r.status).toBe(200)
  expect(await bytes(r)).toEqual(MP3)
  expect(el.pedidos).toHaveLength(1)
})
