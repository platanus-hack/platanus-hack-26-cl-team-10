// El WebSocket de la OT: solo escucha. Si se corta, vuelve con ?desde=<último evento.id>
// para no perder bitácora. Una OT que no existe (cierre 4404) no se reintenta.
// En el celular: si vuelve la red, o la pantalla vuelve después de un rato apagada, se
// reconecta al tiro, sin esperar el backoff ni confiar en una conexión que quedó muda.

import type { MensajeStream } from '../api/tipos'
import type { Conexion } from './estado'

const CIERRE_NO_EXISTE = 4404
const ESPERAS_MS = [1000, 2000, 4000, 8000]
const OCULTO_MAX_MS = 10_000

export type OyenteStream = {
  mensaje(m: MensajeStream, inicial: boolean): void
  conexion(c: Conexion): void
}

export function conectarStream(
  urlDe: (desde: number) => string,
  desde: () => number,
  on: OyenteStream,
  opciones: {
    WebSocketImpl?: typeof WebSocket
    esperasMs?: number[]
    /** Dónde llegan `online` y `visibilitychange` (por defecto, window). */
    entorno?: EventTarget
    visible?: () => boolean
    /** Tras este tiempo con la pantalla oculta, al volver se reconecta aunque la conexión parezca viva. */
    ocultoMaxMs?: number
  } = {},
): () => void {
  const Impl = opciones.WebSocketImpl ?? WebSocket
  const esperas = opciones.esperasMs ?? ESPERAS_MS
  const entorno = opciones.entorno ?? (typeof window !== 'undefined' ? window : undefined)
  const visible = opciones.visible ?? (() => typeof document === 'undefined' || document.visibilityState === 'visible')
  const ocultoMaxMs = opciones.ocultoMaxMs ?? OCULTO_MAX_MS
  let ocultoDesde: number | null = null
  let socket: WebSocket | null = null
  let reloj: ReturnType<typeof setTimeout> | null = null
  let intento = 0
  let huboSnapshot = false
  let cerrado = false

  function abrir() {
    if (cerrado) return
    on.conexion(intento === 0 && !huboSnapshot ? 'conectando' : 'reconectando')
    const ws = new Impl(urlDe(desde()))
    socket = ws
    ws.onopen = () => {
      intento = 0
    }
    ws.onmessage = (e) => {
      let m: MensajeStream
      try {
        m = JSON.parse(String(e.data)) as MensajeStream
      } catch {
        return
      }
      const inicial = m.tipo === 'snapshot' && !huboSnapshot
      if (m.tipo === 'snapshot') huboSnapshot = true
      on.mensaje(m, inicial)
    }
    ws.onclose = (e) => {
      if (cerrado || socket !== ws) return
      socket = null
      if (e.code === CIERRE_NO_EXISTE) {
        cerrado = true
        on.conexion('no_existe')
        return
      }
      on.conexion('reconectando')
      const espera = esperas[Math.min(intento, esperas.length - 1)]
      intento++
      reloj = setTimeout(abrir, espera)
    }
  }

  /** Deja la conexión actual (o la espera del backoff) y abre una nueva desde el último evento. */
  function reconectarYa() {
    if (cerrado) return
    if (reloj) clearTimeout(reloj)
    reloj = null
    const viejo = socket
    socket = null
    viejo?.close()
    intento = 0
    abrir()
  }
  const alVolverLaRed = () => reconectarYa()
  const alCambiarVisibilidad = () => {
    if (!visible()) {
      ocultoDesde = Date.now()
      return
    }
    const oculto = ocultoDesde === null ? 0 : Date.now() - ocultoDesde
    ocultoDesde = null
    if (oculto >= ocultoMaxMs || socket === null) reconectarYa()
  }
  entorno?.addEventListener('online', alVolverLaRed)
  entorno?.addEventListener('visibilitychange', alCambiarVisibilidad)

  abrir()

  return () => {
    cerrado = true
    entorno?.removeEventListener('online', alVolverLaRed)
    entorno?.removeEventListener('visibilitychange', alCambiarVisibilidad)
    if (reloj) clearTimeout(reloj)
    socket?.close()
    socket = null
  }
}
