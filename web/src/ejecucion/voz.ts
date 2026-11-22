// La voz de los avisos. El audio viene de /voz (ElevenLabs en el servidor); si no hay URL,
// si el navegador no deja reproducir, si /voz falla o tarda, el mismo texto lo dice el navegador.
// Un aviso nunca queda mudo, dos avisos nunca se pisan y uno trabado nunca traba a los siguientes.
// La excepción es un «Alto» (alerta de seguridad de capa 1): corta lo que esté sonando, suena
// primero y lo cortado vuelve a sonar entero después. Un «Alto» no corta a otro «Alto».
// Antes de cada aviso suena un tono hecho con Web Audio (sin archivos): «ding-ding» para uno
// normal, tres pitidos agudos para un «Alto». Si el tono falla, la voz suena igual.

import { config } from '../config'

/** Lo que se usa de un HTMLAudioElement (los tipos calzan con los del DOM). */
export type AudioLike = {
  src: string
  play(): Promise<void>
  pause(): void
  onended: ((ev: Event) => unknown) | null
  onerror: ((ev: Event | string) => unknown) | null
}

/** Por qué un aviso cayó a la voz del navegador. */
export type MotivoRespaldo = 'sin-url' | 'error-audio' | 'sin-inicio' | 'play-rechazado'

export type DepsVoz = {
  crearAudio(): AudioLike
  urlVoz: ((texto: string) => string) | null
  hablarNavegador(texto: string, alTerminar: () => void): void
  /** Corta la voz del navegador, para que un «Alto» no espere a que termine. */
  callarNavegador?(): void
  /** Cada vez que un aviso cae a la voz del navegador. Por defecto, console.warn. */
  registrar?(mensaje: string): void
  /** Con qué se piden las frases al precalentar. Por defecto, fetch. */
  pedir?: typeof fetch
  /** El tono antes de cada aviso. Sin él, la voz parte al tiro. */
  tono?: Tono
}

export type TipoTono = 'aviso' | 'alto'
type Nota = { hz: number; desde: number; dura: number; forma: OscillatorType; volumen: number }

/** «Ding-ding» para un aviso; tres pitidos agudos para un «Alto». Tiempos en segundos. */
export const TONOS: Record<TipoTono, Nota[]> = {
  aviso: [0, 0.16].map((desde) => ({ hz: 1175, desde, dura: 0.22, forma: 'sine' as const, volumen: 0.35 })),
  alto: [0, 0.18, 0.36].map((desde) => ({ hz: 2000, desde, dura: 0.12, forma: 'square' as const, volumen: 0.2 })),
}
/** Silencio entre el tono y la voz, para que no se pisen. */
const PAUSA_TONO_MS = 80
export const duracionTonoMs = (tipo: TipoTono): number =>
  Math.round(Math.max(...TONOS[tipo].map((n) => n.desde + n.dura)) * 1000) + PAUSA_TONO_MS

/** Lo que se usa de un AudioContext (los tipos calzan con los del DOM). */
export type ContextoAudio = Pick<AudioContext, 'state' | 'currentTime' | 'destination' | 'resume' | 'createOscillator' | 'createGain'>

export type Tono = ReturnType<typeof crearTono>

export function crearTono(crearContexto: () => ContextoAudio | null) {
  let ctx: ContextoAudio | null = null
  let sonando: Pick<OscillatorNode, 'stop'>[] = []
  const contexto = () => (ctx ??= crearContexto())
  const reanudar = (c: ContextoAudio) => void c.resume().catch(() => {})

  return {
    /** Dentro de un toque: el navegador solo deja arrancar el AudioContext ahí. */
    preparar(): void {
      const c = contexto()
      if (c?.state === 'suspended') reanudar(c)
    },
    /** Toca el tono y devuelve cuánto esperar antes de la voz; 0 si no pudo sonar. */
    tocar(tipo: TipoTono): number {
      const c = contexto()
      if (!c) return 0
      if (c.state !== 'running') {
        reanudar(c)
        return 0
      }
      const t0 = c.currentTime
      sonando = TONOS[tipo].map((n) => {
        const o = c.createOscillator()
        const g = c.createGain()
        const t = t0 + n.desde
        o.type = n.forma
        o.frequency.value = n.hz
        g.gain.setValueAtTime(0.0001, t)
        g.gain.exponentialRampToValueAtTime(n.volumen, t + 0.01)
        g.gain.exponentialRampToValueAtTime(0.0001, t + n.dura)
        o.connect(g).connect(c.destination)
        o.start(t)
        o.stop(t + n.dura + 0.02)
        return o
      })
      return duracionTonoMs(tipo)
    },
    /** Corta el tono que esté sonando: un «Alto» no espera a que termine el ding-ding. */
    callar(): void {
      for (const o of sonando) {
        try {
          o.stop()
        } catch {
          // ya había terminado
        }
      }
      sonando = []
    },
  }
}

export type EstadoAudio = 'bloqueado' | 'activo'

export const FRASE_DE_PRUEBA = 'Audio activo. Así vas a escuchar los avisos.'

/**
 * Si el audio de /voz no empezó en este tiempo, el aviso lo dice el navegador. La meta es que un
 * aviso suene en menos de 2 s desde que llega: una frase precalentada empieza al tiro, y una que
 * ElevenLabs tarda en generar la dice el navegador antes de esa marca.
 */
export const ESPERA_INICIO_AUDIO_MS = 1500
/** Tope para generar una frase al precalentar (el servidor espera a ElevenLabs hasta 15 s). */
export const ESPERA_PRECALENTAR_MS = 16_000
/** Tope para un audio que empezó y nunca avisó que terminó. */
const topeAudioMs = (texto: string) => Math.max(10_000, 150 * texto.length)
/** Tope para la voz del navegador, que a veces no avisa que terminó (Chrome en Android, iOS). */
const topeHablaMs = (texto: string) => Math.max(4000, 90 * texto.length)

/** Una décima de segundo de silencio en WAV: lo que se reproduce para desbloquear el audio. */
function silencioWav(): string {
  const muestras = 800
  const bytes = new Uint8Array(44 + muestras)
  const v = new DataView(bytes.buffer)
  const texto = (en: number, s: string) => [...s].forEach((c, i) => v.setUint8(en + i, c.charCodeAt(0)))
  texto(0, 'RIFF')
  v.setUint32(4, 36 + muestras, true)
  texto(8, 'WAVEfmt ')
  v.setUint32(16, 16, true)
  v.setUint16(20, 1, true) // PCM
  v.setUint16(22, 1, true) // mono
  v.setUint32(24, 8000, true)
  v.setUint32(28, 8000, true)
  v.setUint16(32, 1, true)
  v.setUint16(34, 8, true)
  texto(36, 'data')
  v.setUint32(40, muestras, true)
  bytes.fill(128, 44) // silencio en PCM de 8 bits
  return `data:audio/wav;base64,${btoa(String.fromCharCode(...bytes))}`
}

type Aviso = { texto: string; alto: boolean }
type EnCurso = Aviso & { cortar(): void }

export function crearVoz(deps: DepsVoz) {
  const audio = deps.crearAudio()
  const registrar = deps.registrar ?? ((mensaje: string) => console.warn(mensaje))
  const cola: Aviso[] = []
  const oyentes = new Set<(e: EstadoAudio) => void>()
  let estado: EstadoAudio = 'bloqueado'
  let enCurso: EnCurso | null = null
  /** Un aviso está usando el elemento de audio (entre que se le pone src y que termina o cae al navegador). */
  let usandoAudio = false

  function cambiar(e: EstadoAudio) {
    if (e === estado) return
    estado = e
    for (const fn of oyentes) fn(e)
  }

  const pausar = () => {
    try {
      audio.pause()
    } catch {
      // nada que pausar
    }
  }

  const nombreDe = (e: unknown) => (e instanceof Error ? e.name : 'error')

  /** Cuánto esperar antes de la voz. Si el tono falla, 0: la voz no depende de él. */
  const tocarTono = (tipo: TipoTono): number => {
    if (!deps.tono) return 0
    try {
      return deps.tono.tocar(tipo)
    } catch (e) {
      registrar(`[voz] sin tono, sigue la voz: ${nombreDe(e)}`)
      return 0
    }
  }
  const callarTono = () => {
    try {
      deps.tono?.callar()
    } catch (e) {
      registrar(`[voz] no se pudo cortar el tono: ${nombreDe(e)}`)
    }
  }

  function siguiente() {
    const aviso = cola.shift()
    if (aviso === undefined) {
      enCurso = null
      return
    }
    const { texto } = aviso
    let terminado = false
    let respaldoUsado = false
    let reloj: ReturnType<typeof setTimeout> | null = null
    let relojTono: ReturnType<typeof setTimeout> | null = null
    /** Cuándo termina el tono de este aviso (Date.now()); antes de eso no parte ninguna voz. */
    let finDelTono = 0
    const vigilar = (ms: number, fn: () => void) => {
      if (reloj) clearTimeout(reloj)
      reloj = setTimeout(fn, ms)
    }

    const soltarAudio = () => {
      usandoAudio = false
      audio.onended = null
      audio.onerror = null
    }
    const cerrar = () => {
      terminado = true
      if (reloj) clearTimeout(reloj)
      if (relojTono) clearTimeout(relojTono)
      soltarAudio()
    }
    /** La voz parte cuando termina el tono, salvo que el aviso ya se haya cortado o caído al navegador. */
    const trasElTono = (ms: number, fn: () => void) => {
      if (ms <= 0) return fn()
      relojTono = setTimeout(() => {
        if (!terminado && !respaldoUsado) fn()
      }, ms)
    }
    const fin = () => {
      if (terminado) return
      cerrar()
      siguiente()
    }
    const respaldo = (motivo: MotivoRespaldo) => {
      if (respaldoUsado || terminado) return
      respaldoUsado = true
      registrar(`[voz] el aviso lo dice el navegador: ${motivo}`)
      soltarAudio()
      pausar() // si el audio llega tarde, que no suene encima de la voz del navegador
      // /voz puede fallar al tiro (503 sin llave) mientras el tono sigue sonando: la voz lo espera.
      const resta = Math.max(0, finDelTono - Date.now())
      vigilar(resta + topeHablaMs(texto), fin)
      const hablar = () => {
        if (!terminado) deps.hablarNavegador(texto, fin)
      }
      if (relojTono) clearTimeout(relojTono)
      if (resta > 0) relojTono = setTimeout(hablar, resta)
      else hablar()
    }

    // Antes de reproducir: la voz del navegador puede terminar en el acto y pasar al siguiente.
    enCurso = {
      ...aviso,
      cortar() {
        if (terminado) return
        cerrar()
        callarTono()
        pausar()
        if (respaldoUsado) deps.callarNavegador?.()
        enCurso = null
      },
    }

    const espera = tocarTono(aviso.alto ? 'alto' : 'aviso')
    finDelTono = Date.now() + espera
    if (!deps.urlVoz) return respaldo('sin-url')
    usandoAudio = true
    audio.onended = fin
    audio.onerror = () => respaldo('error-audio')
    // El audio carga mientras suena el tono, y el plazo para que empiece cuenta desde ya, con el
    // tono adentro: así la meta de 2 s no se corre por el tono.
    audio.src = deps.urlVoz(texto)
    vigilar(ESPERA_INICIO_AUDIO_MS, () => respaldo('sin-inicio'))
    trasElTono(espera, reproducir)

    function reproducir() {
      // play() puede tirar al tiro o devolver undefined (Safari viejo): se trata igual que un rechazo o un éxito.
      let reproduccion: Promise<void> | undefined
      try {
        reproduccion = audio.play()
      } catch {
        return respaldo('play-rechazado')
      }
      Promise.resolve(reproduccion).then(
        () => {
          cambiar('activo')
          if (!respaldoUsado && !terminado) vigilar(topeAudioMs(texto), fin)
        },
        () => respaldo('play-rechazado'),
      )
    }
  }

  return {
    /** Llamar dentro de un toque del usuario: es lo que deja sonar al celular. */
    async desbloquear(): Promise<void> {
      // Primero la voz del navegador y el tono, sin esperar nada: iOS solo los deja sonar dentro del toque.
      deps.hablarNavegador('', () => {})
      try {
        deps.tono?.preparar()
      } catch (e) {
        registrar(`[voz] sin tono, sigue la voz: ${nombreDe(e)}`)
      }
      if (!usandoAudio) {
        audio.onended = null
        audio.onerror = null
        audio.src = silencioWav()
      }
      // Si un aviso está usando el audio, play() sobre el mismo elemento también lo desbloquea.
      try {
        await audio.play()
        cambiar('activo')
      } catch {
        // El navegador no dejó: la pantalla sigue mostrando «Audio bloqueado».
      }
    },
    decir(texto: string, { alto = false }: { alto?: boolean } = {}): void {
      if (alto && enCurso && !enCurso.alto) {
        const cortado = enCurso
        cortado.cortar()
        cola.unshift({ texto: cortado.texto, alto: false })
      }
      // Un «Alto» pasa delante de todo lo que no es «Alto»; entre ellos, en orden de llegada.
      const donde = alto ? cola.findIndex((a) => !a.alto) : -1
      cola.splice(donde < 0 ? cola.length : donde, 0, { texto, alto })
      if (!enCurso) siguiente()
    },
    probar(): void {
      this.decir(FRASE_DE_PRUEBA)
    },
    /**
     * Pide las frases de antemano, de a una, para que el servidor las genere y las guarde antes de
     * que haga falta decirlas: así un aviso conocido suena sin esperar a ElevenLabs. Una a la vez
     * para no chocar con el límite de pedidos simultáneos de ElevenLabs; al primer fallo se detiene,
     * porque sin llave o con el tope de frases alcanzado las demás tampoco salen.
     */
    async precalentar(textos: string[], signal?: AbortSignal): Promise<void> {
      if (!deps.urlVoz) return
      const pedir = deps.pedir ?? fetch
      for (const texto of textos) {
        if (signal?.aborted) return
        const tope = AbortSignal.timeout(ESPERA_PRECALENTAR_MS)
        try {
          const r = await pedir(deps.urlVoz(texto), { signal: signal ? AbortSignal.any([signal, tope]) : tope })
          if (!r.ok) {
            registrar(`[voz] precalentado detenido: /voz respondió ${r.status}`)
            return
          }
          await r.arrayBuffer()
        } catch (e) {
          if (signal?.aborted) return
          registrar(`[voz] precalentado detenido: ${nombreDe(e)}`)
          return
        }
      }
    },
    estado: (): EstadoAudio => estado,
    alCambiar(fn: (e: EstadoAudio) => void): () => void {
      oyentes.add(fn)
      return () => oyentes.delete(fn)
    },
  }
}

export type Voz = ReturnType<typeof crearVoz>

// Chrome suelta un utterance sin referencia y nunca avisa que terminó: se guarda el último.
let hablando: SpeechSynthesisUtterance | null = null

function hablarConElNavegador(texto: string, alTerminar: () => void): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return alTerminar()
  const u = new SpeechSynthesisUtterance(texto)
  u.lang = 'es-CL'
  const listo = () => {
    if (hablando === u) hablando = null
    alTerminar()
  }
  u.onend = listo
  u.onerror = listo
  hablando = u
  window.speechSynthesis.speak(u)
}

function callarAlNavegador(): void {
  if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel()
}

type ConAudioViejo = typeof window & { webkitAudioContext?: typeof AudioContext }

function contextoDelNavegador(): ContextoAudio | null {
  if (typeof window === 'undefined') return null
  const AC = window.AudioContext ?? (window as ConAudioViejo).webkitAudioContext
  return AC ? new AC() : null
}

export const voz: Voz = crearVoz({
  crearAudio: () => new Audio(),
  urlVoz: config.VOZ_URL ? (t) => `${config.VOZ_URL}?texto=${encodeURIComponent(t)}` : null,
  hablarNavegador: hablarConElNavegador,
  callarNavegador: callarAlNavegador,
  tono: crearTono(contextoDelNavegador),
})

/** Para el botón «Comenzar»/«Continuar» de Diego: desbloquea el audio dentro del toque. */
export const desbloquearAudio = (): Promise<void> => voz.desbloquear()

export { debeSonar } from './estado'
