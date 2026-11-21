// El único lugar del front que sabe de la API. Un cambio del back se absorbe acá.

import { config } from '../config'
import type {
  EstadoOt,
  OtResumen,
  Pauta,
  PautaResumen,
  RespuestaConfirmar,
  RespuestaDeclarar,
  Sesion,
} from './tipos'

export type TipoError = 'regla' | 'no_existe' | 'timeout' | 'red' | 'http'

/** `regla` trae, en un 409, la regla de negocio que se violó: se muestra tal cual y no se reintenta. */
export class ApiError extends Error {
  status: number
  tipo: TipoError
  regla: string | null

  constructor(status: number, tipo: TipoError, mensaje: string, regla: string | null = null) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.tipo = tipo
    this.regla = regla
  }
}

export type Cliente = {
  listarOts(): Promise<OtResumen[]>
  leerOt(otId: string): Promise<EstadoOt>
  leerPauta(pautaId: string, version: number): Promise<Pauta>
  /** Las pautas con su nombre legible: la lista de OT solo trae el id. */
  listarPautas(): Promise<PautaResumen[]>
  abrirSesion(otId: string, edgeId: string, operario: string): Promise<Sesion>
  /** `pasoId` es el paso que la pantalla mostraba: si su evidencia ya lo cerró, no se evalúa el siguiente. */
  declarar(otId: string, actor: string, texto: string, pasoId?: string): Promise<RespuestaDeclarar>
  /** Una persona cierra el paso en curso contra la evidencia, con un motivo (obligatorio). */
  confirmarPaso(otId: string, pasoId: string, actor: string, motivo: string): Promise<RespuestaConfirmar>
  entregarTurno(otId: string, actor: string): Promise<{ resumen: string }>
  recibirTurno(otId: string, actor: string): Promise<{ firmado_por: string }>
  /** Asigna o reasigna el operador de la OT. `actor` es quién asigna: queda en la bitácora. */
  asignar(otId: string, operador: string, actor: string): Promise<OtResumen>
}

const TIMEOUT_DECLARAR_MS = 10_000

export function crearCliente(base: string, fetchImpl: typeof fetch = (...a) => fetch(...a)): Cliente {
  const raiz = base.replace(/\/$/, '')
  const ot = (id: string) => `/ot/${encodeURIComponent(id)}`

  async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown, timeoutMs?: number): Promise<T> {
    const control = timeoutMs ? new AbortController() : null
    const reloj = control ? setTimeout(() => control.abort(), timeoutMs) : null
    let r: Response
    try {
      r = await fetchImpl(`${raiz}${ruta}`, {
        method: metodo,
        headers: cuerpo === undefined ? undefined : { 'content-type': 'application/json' },
        body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
        signal: control?.signal,
      })
    } catch {
      if (control?.signal.aborted) throw new ApiError(0, 'timeout', 'La API no respondió a tiempo')
      throw new ApiError(0, 'red', 'Sin conexión, reintentando')
    } finally {
      if (reloj) clearTimeout(reloj)
    }
    const datos = await r.json().catch(() => null)
    if (r.ok) return datos as T
    if (r.status === 409 && datos?.regla) throw new ApiError(409, 'regla', datos.regla, datos.regla)
    if (r.status === 404) throw new ApiError(404, 'no_existe', datos?.no_existe ?? 'No existe')
    throw new ApiError(r.status, 'http', `La API respondió ${r.status}`)
  }

  return {
    listarOts: () => pedir('GET', '/ots'),
    leerOt: (id) => pedir('GET', ot(id)),
    leerPauta: (id, version) => pedir('GET', `/pautas/${encodeURIComponent(id)}?version=${version}`),
    listarPautas: () => pedir('GET', '/pautas'),
    abrirSesion: (id, edgeId, operario) => pedir('POST', `${ot(id)}/sesion`, { edge_id: edgeId, operario }),
    declarar: (id, actor, texto, pasoId) =>
      pedir('POST', `${ot(id)}/declarar`, pasoId ? { actor, texto, paso_id: pasoId } : { actor, texto }, TIMEOUT_DECLARAR_MS),
    confirmarPaso: (id, pasoId, actor, motivo) =>
      pedir('POST', `${ot(id)}/pasos/${encodeURIComponent(pasoId)}/confirmar`, { actor, motivo }),
    entregarTurno: (id, actor) => pedir('POST', `${ot(id)}/relevo/entregar?actor=${encodeURIComponent(actor)}`),
    recibirTurno: (id, actor) => pedir('POST', `${ot(id)}/relevo/recibir?actor=${encodeURIComponent(actor)}`),
    asignar: (id, operador, actor) => pedir('POST', `${ot(id)}/asignar`, { operador, actor }),
  }
}

export const api: Cliente = crearCliente(config.API_URL)

/** La URL del WebSocket de la OT: https → wss, http → ws. */
export function urlStream(base: string, otId: string, desde: number): string {
  const ws = base.replace(/\/$/, '').replace(/^http/, 'ws')
  return `${ws}/ot/${encodeURIComponent(otId)}/stream?desde=${desde}`
}
