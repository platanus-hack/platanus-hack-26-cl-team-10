// La voz de los avisos. El audio viene de /voz (ElevenLabs en el servidor); si no hay URL,
// si el navegador no deja reproducir, si /voz falla o tarda, el mismo texto lo dice el navegador.
// Un aviso nunca queda mudo, dos avisos nunca se pisan y uno trabado nunca traba a los siguientes.

import { config } from '../config'

/** Lo que se usa de un HTMLAudioElement (los tipos calzan con los del DOM). */
export type AudioLike = {
  src: string
  play(): Promise<void>
  pause(): void
  onended: ((ev: Event) => unknown) | null
  onerror: ((ev: Event | string) => unknown) | null
}

export type DepsVoz = {
  crearAudio(): AudioLike
  urlVoz: ((texto: string) => string) | null
  hablarNavegador(texto: string, alTerminar: () => void): void
}

export type EstadoAudio = 'bloqueado' | 'activo'

export const FRASE_DE_PRUEBA = 'Audio activo. Así vas a escuchar los avisos.'

/** Si el audio de /voz no empezó en este tiempo, el aviso lo dice el navegador. */
export const ESPERA_INICIO_AUDIO_MS = 2500
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

export function crearVoz(deps: DepsVoz) {
  const audio = deps.crearAudio()
  const cola: string[] = []
  const oyentes = new Set<(e: EstadoAudio) => void>()
  let estado: EstadoAudio = 'bloqueado'
  let sonando = false
  /** Un aviso está usando el elemento de audio (entre que se le pone src y que termina o cae al navegador). */
  let usandoAudio = false

  function cambiar(e: EstadoAudio) {
    if (e === estado) return
    estado = e
    for (const fn of oyentes) fn(e)
  }

  function siguiente() {
    const texto = cola.shift()
    if (texto === undefined) {
      sonando = false
      return
    }
    sonando = true
    let terminado = false
    let respaldoUsado = false
    let reloj: ReturnType<typeof setTimeout> | null = null
    const vigilar = (ms: number, fn: () => void) => {
      if (reloj) clearTimeout(reloj)
      reloj = setTimeout(fn, ms)
    }

    const soltarAudio = () => {
      usandoAudio = false
      audio.onended = null
      audio.onerror = null
    }
    const fin = () => {
      if (terminado) return
      terminado = true
      if (reloj) clearTimeout(reloj)
      soltarAudio()
      siguiente()
    }
    const respaldo = () => {
      if (respaldoUsado || terminado) return
      respaldoUsado = true
      soltarAudio()
      try {
        audio.pause() // si el audio llega tarde, que no suene encima de la voz del navegador
      } catch {
        // nada que pausar
      }
      vigilar(topeHablaMs(texto), fin)
      deps.hablarNavegador(texto, fin)
    }

    if (!deps.urlVoz) return respaldo()
    usandoAudio = true
    audio.onended = fin
    audio.onerror = respaldo
    audio.src = deps.urlVoz(texto)
    vigilar(ESPERA_INICIO_AUDIO_MS, respaldo)
    // play() puede tirar al tiro o devolver undefined (Safari viejo): se trata igual que un rechazo o un éxito.
    let reproduccion: Promise<void> | undefined
    try {
      reproduccion = audio.play()
    } catch {
      return respaldo()
    }
    Promise.resolve(reproduccion).then(() => {
      cambiar('activo')
      if (!respaldoUsado && !terminado) vigilar(topeAudioMs(texto), fin)
    }, respaldo)
  }

  return {
    /** Llamar dentro de un toque del usuario: es lo que deja sonar al celular. */
    async desbloquear(): Promise<void> {
      // Primero la voz del navegador, sin esperar nada: iOS solo la deja hablar dentro del toque.
      deps.hablarNavegador('', () => {})
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
    decir(texto: string): void {
      cola.push(texto)
      if (!sonando) siguiente()
    },
    probar(): void {
      this.decir(FRASE_DE_PRUEBA)
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

export const voz: Voz = crearVoz({
  crearAudio: () => new Audio(),
  urlVoz: config.VOZ_URL ? (t) => `${config.VOZ_URL}?texto=${encodeURIComponent(t)}` : null,
  hablarNavegador: hablarConElNavegador,
})

/** Para el botón «Comenzar»/«Continuar» de Diego: desbloquea el audio dentro del toque. */
export const desbloquearAudio = (): Promise<void> => voz.desbloquear()

export { debeSonar } from './estado'
