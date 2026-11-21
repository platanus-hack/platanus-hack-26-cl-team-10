import type { Evento, Nivel } from '../api/tipos'
import { crearVoz, debeSonar, type AudioLike, type DepsVoz } from './voz'

class FakeAudio implements AudioLike {
  src = ''
  onended: (() => void) | null = null
  onerror: (() => void) | null = null
  fuentes: string[] = []
  rechazar = false
  colgar = false
  pausado = false
  pause() {
    this.pausado = true
  }
  async play() {
    if (this.colgar) return new Promise<void>(() => {})
    this.fuentes.push(this.src)
    if (this.rechazar) throw new Error('NotAllowedError')
  }
  terminar() {
    this.onended?.()
  }
}

function armar(urlVoz: DepsVoz['urlVoz'] = (t) => `/voz?texto=${t}`) {
  const audio = new FakeAudio()
  const dichos: string[] = []
  const finDe: Array<() => void> = []
  const voz = crearVoz({
    crearAudio: () => audio,
    urlVoz,
    hablarNavegador: (texto, alTerminar) => {
      dichos.push(texto)
      finDe.push(alTerminar)
    },
  })
  return { voz, audio, dichos, finDe }
}

const esperar = () => new Promise((r) => setTimeout(r, 0))

it('plays in order without overlapping', async () => {
  const { voz, audio } = armar()
  voz.decir('a')
  voz.decir('b')
  await esperar()
  expect(audio.fuentes).toEqual(['/voz?texto=a'])
  audio.terminar()
  await esperar()
  expect(audio.fuentes).toEqual(['/voz?texto=a', '/voz?texto=b'])
})

it('falls back once when play rejects and audio errors', async () => {
  const { voz, audio, dichos, finDe } = armar()
  audio.rechazar = true
  const onerror = () => audio.onerror
  voz.decir('Oye, el candado no aparece puesto')
  const manejador = onerror()
  await esperar()
  manejador?.()
  expect(dichos).toEqual(['Oye, el candado no aparece puesto'])
  audio.rechazar = false
  voz.decir('siguiente')
  await esperar()
  expect(audio.fuentes.at(-1)).not.toBe('/voz?texto=siguiente')
  finDe[0]()
  await esperar()
  expect(audio.fuentes.at(-1)).toBe('/voz?texto=siguiente')
})

it('falls back when the audio errors after it started', async () => {
  const { voz, audio, dichos } = armar()
  voz.decir('a')
  await esperar()
  audio.onerror?.()
  expect(dichos).toEqual(['a'])
})

it('uses the browser voice when there is no voz url', () => {
  const { voz, audio, dichos } = armar(null)
  voz.decir('hola')
  expect(dichos).toEqual(['hola'])
  expect(audio.fuentes).toEqual([])
})

it('desbloquear marks activo when play resolves, stays bloqueado when it rejects', async () => {
  const bien = armar()
  const cambios: string[] = []
  bien.voz.alCambiar((e) => cambios.push(e))
  expect(bien.voz.estado()).toBe('bloqueado')
  await bien.voz.desbloquear()
  expect(bien.voz.estado()).toBe('activo')
  expect(cambios).toEqual(['activo'])
  expect(bien.audio.fuentes[0]).toMatch(/^data:audio\/wav;base64,/)

  const mal = armar()
  mal.audio.rechazar = true
  await mal.voz.desbloquear()
  expect(mal.voz.estado()).toBe('bloqueado')
})

it('probar says the test sentence', async () => {
  const { voz, audio } = armar()
  voz.probar()
  await esperar()
  expect(audio.fuentes).toEqual(['/voz?texto=Audio activo. Así vas a escuchar los avisos.'])
})

it('debeSonar only for error', () => {
  const ev = (nivel: Nivel | null) => ({ calificacion: nivel ? { nivel, certeza: 1, capa: 1, motivos: [] } : null }) as Evento
  expect(debeSonar(ev('error'))).toBe(true)
  expect(debeSonar(ev('warning'))).toBe(false)
  expect(debeSonar(ev('ok'))).toBe(false)
  expect(debeSonar(ev(null))).toBe(false)
})

it('falls back when play throws synchronously', () => {
  const { voz, audio, dichos } = armar()
  audio.play = () => {
    throw new Error('NotSupportedError')
  }
  voz.decir('a')
  expect(dichos).toEqual(['a'])
})

describe('watchdogs: one stuck warning never mutes the next', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('falls back to the browser voice when the audio does not start within 2.5 s', async () => {
    const { voz, audio, dichos } = armar()
    audio.colgar = true
    voz.decir('Oye, el candado no aparece puesto')
    await vi.advanceTimersByTimeAsync(2499)
    expect(dichos).toEqual([])
    await vi.advanceTimersByTimeAsync(1)
    expect(dichos).toEqual(['Oye, el candado no aparece puesto'])
    expect(audio.pausado).toBe(true)
  })

  it('moves on when the browser voice never says it ended', async () => {
    const { voz, dichos } = armar(null)
    voz.decir('a')
    voz.decir('b')
    expect(dichos).toEqual(['a'])
    await vi.advanceTimersByTimeAsync(4000)
    expect(dichos).toEqual(['a', 'b'])
  })

  it('moves on when the audio stalls after it started', async () => {
    const { voz, audio } = armar()
    voz.decir('a')
    voz.decir('b')
    await vi.advanceTimersByTimeAsync(0)
    expect(audio.fuentes).toEqual(['/voz?texto=a'])
    await vi.advanceTimersByTimeAsync(10_000)
    expect(audio.fuentes).toEqual(['/voz?texto=a', '/voz?texto=b'])
  })
})

it('desbloquear speaks the empty utterance before waiting for the audio', () => {
  const { voz, audio, dichos } = armar()
  audio.colgar = true
  void voz.desbloquear()
  expect(dichos).toEqual([''])
})

it('desbloquear still unlocks while a warning is being spoken by the browser voice', async () => {
  const { voz, audio } = armar()
  audio.rechazar = true
  voz.decir('a')
  await esperar()
  audio.rechazar = false
  await voz.desbloquear()
  expect(voz.estado()).toBe('activo')
})
