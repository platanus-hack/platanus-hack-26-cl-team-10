// La voz de los avisos. El audio viene de /voz (ElevenLabs en el servidor); si no hay URL,
// si el navegador no deja reproducir o si /voz falla, el mismo texto lo dice el navegador.
// Un aviso nunca queda mudo y dos avisos nunca se pisan.

import type { Evento } from '../api/tipos'
import { config } from '../config'

/** Lo que se usa de un HTMLAudioElement (los tipos calzan con los del DOM). */
export type AudioLike = {
  src: string
  play(): Promise<void>
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

    const fin = () => {
      if (terminado) return
      terminado = true
      audio.onended = null
      audio.onerror = null
      siguiente()
    }
    const respaldo = () => {
      if (respaldoUsado || terminado) return
      respaldoUsado = true
      audio.onended = null
      audio.onerror = null
      deps.hablarNavegador(texto, fin)
    }

    if (!deps.urlVoz) return respaldo()
    audio.onended = fin
    audio.onerror = respaldo
    audio.src = deps.urlVoz(texto)
    audio.play().then(() => cambiar('activo'), respaldo)
  }

  return {
    /** Llamar dentro de un toque del usuario: es lo que deja sonar al celular. */
    async desbloquear(): Promise<void> {
      if (!sonando) {
        audio.onended = null
        audio.onerror = null
        audio.src = silencioWav()
        try {
          await audio.play()
          cambiar('activo')
        } catch {
          // El navegador no dejó: la pantalla sigue mostrando «Audio bloqueado».
        }
      }
      deps.hablarNavegador('', () => {})
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

function hablarConElNavegador(texto: string, alTerminar: () => void): void {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) return alTerminar()
  const u = new SpeechSynthesisUtterance(texto)
  u.lang = 'es-CL'
  u.onend = alTerminar
  u.onerror = alTerminar
  window.speechSynthesis.speak(u)
}

export const voz: Voz = crearVoz({
  crearAudio: () => new Audio(),
  urlVoz: config.VOZ_URL ? (t) => `${config.VOZ_URL}?texto=${encodeURIComponent(t)}` : null,
  hablarNavegador: hablarConElNavegador,
})

/** Para el botón «Comenzar»/«Continuar» de Diego: desbloquea el audio dentro del toque. */
export const desbloquearAudio = (): Promise<void> => voz.desbloquear()

export const debeSonar = (ev: Evento): boolean => ev.calificacion?.nivel === 'error'
