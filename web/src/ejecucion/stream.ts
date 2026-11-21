// El WebSocket de la OT: solo escucha. Si se corta, vuelve con ?desde=<último evento.id>
// para no perder bitácora. Una OT que no existe (cierre 4404) no se reintenta.

import type { MensajeStream } from '../api/tipos'
import type { Conexion } from './estado'

const CIERRE_NO_EXISTE = 4404
const ESPERAS_MS = [1000, 2000, 4000, 8000]

export type OyenteStream = {
  mensaje(m: MensajeStream, inicial: boolean): void
  conexion(c: Conexion): void
}

export function conectarStream(
  urlDe: (desde: number) => string,
  desde: () => number,
  on: OyenteStream,
  opciones: { WebSocketImpl?: typeof WebSocket; esperasMs?: number[] } = {},
): () => void {
  const Impl = opciones.WebSocketImpl ?? WebSocket
  const esperas = opciones.esperasMs ?? ESPERAS_MS
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

  abrir()

  return () => {
    cerrado = true
    if (reloj) clearTimeout(reloj)
    socket?.close()
    socket = null
  }
}
