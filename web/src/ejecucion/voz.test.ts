import type { Evento, Nivel } from '../api/tipos'
import {
  crearTono,
  crearVoz,
  debeSonar,
  duracionTonoMs,
  ESPERA_INICIO_AUDIO_MS,
  TONOS,
  type AudioLike,
  type ContextoAudio,
  type DepsVoz,
} from './voz'

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

function armar(urlVoz: DepsVoz['urlVoz'] = (t) => `/voz?texto=${t}`, pedir?: DepsVoz['pedir'], tono?: DepsVoz['tono']) {
  const audio = new FakeAudio()
  const dichos: string[] = []
  const finDe: Array<() => void> = []
  const registros: string[] = []
  const callado = { veces: 0 }
  const voz = crearVoz({
    crearAudio: () => audio,
    urlVoz,
    hablarNavegador: (texto, alTerminar) => {
      dichos.push(texto)
      finDe.push(alTerminar)
    },
    callarNavegador: () => void callado.veces++,
    registrar: (m) => void registros.push(m),
    pedir,
    tono,
  })
  return { voz, audio, dichos, finDe, registros, callado }
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

  it('falls back to the browser voice when the audio does not start within 1.5 s', async () => {
    const { voz, audio, dichos } = armar()
    audio.colgar = true
    voz.decir('Oye, el candado no aparece puesto')
    expect(ESPERA_INICIO_AUDIO_MS).toBe(1500)
    await vi.advanceTimersByTimeAsync(ESPERA_INICIO_AUDIO_MS - 1)
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

describe('Alto: a capa 1 safety alert goes first', () => {
  it('cuts the warning being played, then says the cut warning again and the rest', async () => {
    const { voz, audio } = armar()
    voz.decir('a')
    voz.decir('b')
    await esperar()
    voz.decir('ALTO', { alto: true })
    await esperar()
    expect(audio.pausado).toBe(true)
    expect(audio.fuentes).toEqual(['/voz?texto=a', '/voz?texto=ALTO'])
    audio.terminar()
    await esperar()
    expect(audio.fuentes.at(-1)).toBe('/voz?texto=a')
    audio.terminar()
    await esperar()
    expect(audio.fuentes.at(-1)).toBe('/voz?texto=b')
  })

  it('never cuts another Alto: Altos go in order, ahead of everything else', async () => {
    const { voz, audio } = armar()
    voz.decir('a')
    await esperar()
    voz.decir('ALTO 1', { alto: true })
    voz.decir('b')
    voz.decir('ALTO 2', { alto: true })
    await esperar()
    expect(audio.fuentes).toEqual(['/voz?texto=a', '/voz?texto=ALTO 1'])
    for (const esperado of ['ALTO 2', 'a', 'b']) {
      audio.terminar()
      await esperar()
      expect(audio.fuentes.at(-1)).toBe(`/voz?texto=${esperado}`)
    }
  })

  it('cuts the browser voice too, and the cut warning ending late changes nothing', () => {
    const { voz, dichos, finDe, callado } = armar(null)
    voz.decir('a')
    voz.decir('ALTO', { alto: true })
    expect(callado.veces).toBe(1)
    expect(dichos).toEqual(['a', 'ALTO'])
    finDe[0]()
    expect(dichos).toEqual(['a', 'ALTO'])
    finDe[1]()
    expect(dichos).toEqual(['a', 'ALTO', 'a'])
  })

  it('an Alto with nothing playing just plays, without cutting anything', async () => {
    const { voz, audio, callado } = armar()
    voz.decir('ALTO', { alto: true })
    await esperar()
    expect(audio.fuentes).toEqual(['/voz?texto=ALTO'])
    expect(audio.pausado).toBe(false)
    expect(callado.veces).toBe(0)
  })
})

describe('the fallback leaves a log with its reason', () => {
  it('without a voz url and when play is rejected', async () => {
    const sinUrl = armar(null)
    sinUrl.voz.decir('a')
    expect(sinUrl.registros).toEqual(['[voz] el aviso lo dice el navegador: sin-url'])

    const rechazado = armar()
    rechazado.audio.rechazar = true
    rechazado.voz.decir('a')
    await esperar()
    expect(rechazado.registros).toEqual(['[voz] el aviso lo dice el navegador: play-rechazado'])
  })

  it('when the audio does not start in time', async () => {
    vi.useFakeTimers()
    try {
      const { voz, audio, registros } = armar()
      audio.colgar = true
      voz.decir('a')
      await vi.advanceTimersByTimeAsync(ESPERA_INICIO_AUDIO_MS)
      expect(registros).toEqual(['[voz] el aviso lo dice el navegador: sin-inicio'])
    } finally {
      vi.useRealTimers()
    }
  })

  it('a warning that plays leaves no log', async () => {
    const { voz, audio, registros } = armar()
    voz.decir('a')
    await esperar()
    audio.terminar()
    expect(registros).toEqual([])
  })
})

describe('precalentar', () => {
  const respuesta = (status: number) => ({ ok: status < 400, status, arrayBuffer: async () => new ArrayBuffer(0) }) as Response

  it('asks for each phrase one at a time', async () => {
    const pedidos: string[] = []
    let abiertos = 0
    let maxAbiertos = 0
    const pedir = (async (url: string) => {
      pedidos.push(url)
      maxAbiertos = Math.max(maxAbiertos, ++abiertos)
      await esperar()
      abiertos--
      return respuesta(200)
    }) as unknown as typeof fetch
    const { voz, registros } = armar(undefined, pedir)
    await voz.precalentar(['a', 'b', 'c'])
    expect(pedidos).toEqual(['/voz?texto=a', '/voz?texto=b', '/voz?texto=c'])
    expect(maxAbiertos).toBe(1)
    expect(registros).toEqual([])
  })

  it('stops and logs at the first error response', async () => {
    const pedidos: string[] = []
    const pedir = (async (url: string) => (pedidos.push(url), respuesta(503))) as unknown as typeof fetch
    const { voz, registros } = armar(undefined, pedir)
    await voz.precalentar(['a', 'b'])
    expect(pedidos).toEqual(['/voz?texto=a'])
    expect(registros).toEqual(['[voz] precalentado detenido: /voz respondió 503'])
  })

  it('stops and logs when the request fails', async () => {
    const pedir = (async () => {
      throw new TypeError('Failed to fetch')
    }) as unknown as typeof fetch
    const { voz, registros } = armar(undefined, pedir)
    await voz.precalentar(['a', 'b'])
    expect(registros).toEqual(['[voz] precalentado detenido: TypeError'])
  })

  it('stops quietly when the screen leaves', async () => {
    const corte = new AbortController()
    const pedidos: string[] = []
    const pedir = (async (url: string) => {
      pedidos.push(url)
      corte.abort()
      throw new DOMException('cortado', 'AbortError')
    }) as unknown as typeof fetch
    const { voz, registros } = armar(undefined, pedir)
    await voz.precalentar(['a', 'b'], corte.signal)
    expect(pedidos).toEqual(['/voz?texto=a'])
    expect(registros).toEqual([])
  })

  it('does nothing without a voz url', async () => {
    const pedir = vi.fn() as unknown as typeof fetch
    const { voz } = armar(null, pedir)
    await voz.precalentar(['a'])
    expect(pedir).not.toHaveBeenCalled()
  })
})

class FakeOscilador {
  type = ''
  frequency = { value: 0 }
  inicio = -1
  fin = -1
  cortado = false
  connect<T>(destino: T): T {
    return destino
  }
  start(t: number) {
    this.inicio = t
  }
  stop(t?: number) {
    if (t === undefined) this.cortado = true
    else this.fin = t
  }
}

class FakeContexto {
  state: AudioContextState = 'running'
  currentTime = 10
  destination = {}
  reanudado = 0
  osciladores: FakeOscilador[] = []
  async resume() {
    this.reanudado++
    this.state = 'running'
  }
  createOscillator() {
    const o = new FakeOscilador()
    this.osciladores.push(o)
    return o
  }
  createGain() {
    return { gain: { setValueAtTime() {}, exponentialRampToValueAtTime() {} }, connect: <T>(d: T) => d }
  }
}

const tonoCon = (ctx: FakeContexto | null) => crearTono(() => ctx as unknown as ContextoAudio | null)

describe('the alert tone (Web Audio)', () => {
  it('a warning is a short ding-ding: two equal sine notes', () => {
    const ctx = new FakeContexto()
    const espera = tonoCon(ctx).tocar('aviso')
    expect(ctx.osciladores.map((o) => [o.type, o.frequency.value])).toEqual([
      ['sine', 1175],
      ['sine', 1175],
    ])
    expect(ctx.osciladores.map((o) => o.inicio)).toEqual([10, 10.16])
    expect(espera).toBe(duracionTonoMs('aviso'))
    expect(espera).toBeLessThan(500)
  })

  it('an Alto is three high beeps, higher than the ding-ding', () => {
    const ctx = new FakeContexto()
    tonoCon(ctx).tocar('alto')
    expect(ctx.osciladores).toHaveLength(3)
    expect(ctx.osciladores.every((o) => o.type === 'square' && o.frequency.value > TONOS.aviso[0].hz)).toBe(true)
    expect(duracionTonoMs('alto')).toBeLessThan(ESPERA_INICIO_AUDIO_MS)
  })

  it('plays nothing and asks no wait without Web Audio or while the context is still locked', () => {
    expect(tonoCon(null).tocar('aviso')).toBe(0)
    const bloqueado = new FakeContexto()
    bloqueado.state = 'suspended'
    expect(tonoCon(bloqueado).tocar('alto')).toBe(0)
    expect(bloqueado.osciladores).toEqual([])
  })

  it('preparar resumes a locked context (inside the tap)', () => {
    const ctx = new FakeContexto()
    ctx.state = 'suspended'
    tonoCon(ctx).preparar()
    expect(ctx.reanudado).toBe(1)
  })

  it('callar stops the tone that is playing', () => {
    const ctx = new FakeContexto()
    const tono = tonoCon(ctx)
    tono.tocar('aviso')
    tono.callar()
    expect(ctx.osciladores.every((o) => o.cortado)).toBe(true)
  })
})

describe('the tone goes before the voice', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  function tonoFalso(ms = 400) {
    const t = {
      tocados: [] as string[],
      callado: 0,
      preparado: 0,
      falla: false,
      tocar(tipo: string) {
        if (t.falla) throw new Error('NotSupportedError')
        t.tocados.push(tipo)
        return ms
      },
      callar() {
        t.callado++
      },
      preparar() {
        t.preparado++
      },
    }
    return t
  }

  it('a warning plays its ding-ding, then the voice', async () => {
    const tono = tonoFalso()
    const { voz, audio } = armar(undefined, undefined, tono)
    voz.decir('a')
    expect(tono.tocados).toEqual(['aviso'])
    expect(audio.src).toBe('/voz?texto=a') // ya carga mientras suena el tono
    await vi.advanceTimersByTimeAsync(399)
    expect(audio.fuentes).toEqual([])
    await vi.advanceTimersByTimeAsync(1)
    expect(audio.fuentes).toEqual(['/voz?texto=a'])
  })

  it('an Alto plays the three beeps; the browser voice also waits for the tone', async () => {
    const tono = tonoFalso()
    const { voz, dichos } = armar(null, undefined, tono)
    voz.decir('ALTO', { alto: true })
    expect(tono.tocados).toEqual(['alto'])
    expect(dichos).toEqual([])
    await vi.advanceTimersByTimeAsync(400)
    expect(dichos).toEqual(['ALTO'])
  })

  it('if the tone fails, the voice plays right away and the failure is logged', async () => {
    const tono = tonoFalso()
    tono.falla = true
    const { voz, audio, registros } = armar(undefined, undefined, tono)
    voz.decir('a')
    await vi.advanceTimersByTimeAsync(0)
    expect(audio.fuentes).toEqual(['/voz?texto=a'])
    expect(registros).toEqual(['[voz] sin tono, sigue la voz: Error'])
  })

  it('a tone that could not sound (0 ms) does not delay the voice', async () => {
    const { voz, audio } = armar(undefined, undefined, tonoFalso(0))
    voz.decir('a')
    await vi.advanceTimersByTimeAsync(0)
    expect(audio.fuentes).toEqual(['/voz?texto=a'])
  })

  it('the 1.5 s limit counts from the start, tone included', async () => {
    const tono = tonoFalso()
    const { voz, audio, dichos } = armar(undefined, undefined, tono)
    audio.colgar = true
    voz.decir('a')
    await vi.advanceTimersByTimeAsync(ESPERA_INICIO_AUDIO_MS)
    expect(dichos).toEqual(['a'])
  })

  it('an Alto during a ding-ding cuts the tone, and the cut warning never starts its voice early', async () => {
    const tono = tonoFalso()
    const { voz, audio } = armar(undefined, undefined, tono)
    voz.decir('a')
    await vi.advanceTimersByTimeAsync(100)
    voz.decir('ALTO', { alto: true })
    expect(tono.callado).toBe(1)
    expect(tono.tocados).toEqual(['aviso', 'alto'])
    await vi.advanceTimersByTimeAsync(400)
    expect(audio.fuentes).toEqual(['/voz?texto=ALTO'])
    audio.terminar()
    await vi.advanceTimersByTimeAsync(400)
    expect(audio.fuentes).toEqual(['/voz?texto=ALTO', '/voz?texto=a'])
    expect(tono.tocados).toEqual(['aviso', 'alto', 'aviso'])
  })

  it('when /voz fails during the tone (503 without a key), the browser voice waits for the tone to end', async () => {
    const tono = tonoFalso()
    const { voz, audio, dichos } = armar(undefined, undefined, tono)
    voz.decir('ALTO', { alto: true })
    await vi.advanceTimersByTimeAsync(40)
    audio.onerror?.()
    expect(dichos).toEqual([])
    await vi.advanceTimersByTimeAsync(359)
    expect(dichos).toEqual([])
    await vi.advanceTimersByTimeAsync(1)
    expect(dichos).toEqual(['ALTO'])
    expect(audio.fuentes).toEqual([]) // el MP3 que falló nunca se reproduce
  })

  it('desbloquear prepares the tone inside the tap', async () => {
    const tono = tonoFalso()
    const { voz } = armar(undefined, undefined, tono)
    await voz.desbloquear()
    expect(tono.preparado).toBe(1)
  })
})
