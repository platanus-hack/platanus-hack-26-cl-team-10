// El único lugar del front que sabe de la API. Un cambio del back se absorbe acá.

import { config } from '../config'
import { cerrarSesion, tokenDeSesion } from '../sesion/sesion'
import type {
  Companero,
  Entrada,
  EstadoOt,
  OtDetalle,
  OtPedida,
  OtResumen,
  Pauta,
  PautaResumen,
  Persona,
  RespuestaConfirmar,
  RespuestaDeclarar,
  Sesion,
} from './tipos'

/**
 * `sesion`: la API no reconoce el token (venció o se cerró). `credenciales`: el login no calzó.
 * `permiso`: la persona entró, pero su rol o su empresa no la dejan.
 */
export type TipoError = 'regla' | 'no_existe' | 'timeout' | 'red' | 'http' | 'sesion' | 'credenciales' | 'permiso'

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
  /** Usuario y clave por un token de 12 horas. 401 → `credenciales`. */
  entrar(usuario: string, clave: string): Promise<Entrada>
  /** Invalida el token en el servidor. */
  salir(): Promise<void>
  /** Las OT de la empresa (supervisor) o las asignadas a quien pregunta (operador). */
  listarOts(): Promise<OtResumen[]>
  leerOt(otId: string): Promise<EstadoOt>
  /**
   * La OT por el servicio para clientes, con su calificación. 404 si no es de la empresa o, para
   * un operador, si no está asignada a él: sirve también para saber si la puede abrir.
   */
  leerOtCliente(otId: string): Promise<OtDetalle>
  leerPauta(pautaId: string, version: number): Promise<Pauta>
  /** Las pautas que la empresa puede pedir, con su nombre legible: la lista de OT solo trae el id. */
  listarPautas(): Promise<PautaResumen[]>
  /** Los operadores de la empresa, para asignarles OT. Solo supervisor. */
  listarOperadores(): Promise<Persona[]>
  /** Nombre y rol de todas las personas de la empresa; lo lee cualquiera de ellas. */
  listarPersonas(): Promise<Companero[]>
  /** Un supervisor pide una OT nueva de una pauta habilitada; queda sin asignar. */
  pedirOt(pautaId: string): Promise<OtPedida>
  /**
   * El operador une su OT a la estación con su token: el operario de la sesión es quien entró.
   * Si la estación ejecuta otra OT abierta responde 409; `tomar` se la quita, y solo se manda
   * cuando la persona lo pide con un toque. 403 si esa OT es de otra empresa.
   */
  abrirSesion(otId: string, edgeId: string, tomar?: boolean): Promise<Sesion>
  /** Qué OT ejecuta la estación ahora, o null si está libre. Es público. */
  leerSesionEdge(edgeId: string): Promise<Sesion | null>
  /** `pasoId` es el paso que la pantalla mostraba: si su evidencia ya lo cerró, no se evalúa el siguiente. */
  declarar(otId: string, actor: string, texto: string, pasoId?: string): Promise<RespuestaDeclarar>
  /** Una persona cierra el paso en curso contra la evidencia, con un motivo (obligatorio). */
  confirmarPaso(otId: string, pasoId: string, actor: string, motivo: string): Promise<RespuestaConfirmar>
  entregarTurno(otId: string, actor: string): Promise<{ resumen: string }>
  recibirTurno(otId: string, actor: string): Promise<{ firmado_por: string }>
  /** Asigna o reasigna el operador de la OT. Quién asigna lo sabe la API por el token. */
  asignar(otId: string, operador: string): Promise<OtResumen>
}

/** De dónde sale el token y qué hacer cuando la API deja de reconocerlo. */
export type Acceso = { token(): string | null; alVencer(): void }

const SIN_ACCESO: Acceso = { token: () => null, alVencer: () => {} }

const TIMEOUT_DECLARAR_MS = 10_000

export function crearCliente(
  base: string,
  fetchImpl: typeof fetch = (...a) => fetch(...a),
  acceso: Acceso = SIN_ACCESO,
): Cliente {
  const raiz = base.replace(/\/$/, '')
  const ot = (id: string) => `/ot/${encodeURIComponent(id)}`
  const otCliente = (id: string) => `/cliente/ots/${encodeURIComponent(id)}`

  async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown, timeoutMs?: number): Promise<T> {
    const control = timeoutMs ? new AbortController() : null
    const reloj = control ? setTimeout(() => control.abort(), timeoutMs) : null
    const headers: Record<string, string> = {}
    if (cuerpo !== undefined) headers['content-type'] = 'application/json'
    const token = acceso.token()
    if (token) headers.authorization = `Bearer ${token}`
    let r: Response
    try {
      r = await fetchImpl(`${raiz}${ruta}`, {
        method: metodo,
        headers: Object.keys(headers).length ? headers : undefined,
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
    if (r.status === 401) {
      if (ruta === '/auth/entrar') throw new ApiError(401, 'credenciales', 'Correo o clave incorrectos.')
      // Al salir, un token que ya no sirve no es una sesión vencida: la persona ya se fue.
      if (ruta !== '/auth/salir') acceso.alVencer()
      throw new ApiError(401, 'sesion', 'Tu sesión venció. Vuelve a entrar.')
    }
    if (r.status === 403) throw new ApiError(403, 'permiso', datos?.permiso ?? 'No tienes permiso para eso')
    if (r.status === 409 && datos?.regla) throw new ApiError(409, 'regla', datos.regla, datos.regla)
    if (r.status === 404) throw new ApiError(404, 'no_existe', datos?.no_existe ?? 'No existe')
    throw new ApiError(r.status, 'http', `La API respondió ${r.status}`)
  }

  return {
    entrar: (usuario, clave) => pedir('POST', '/auth/entrar', { usuario, clave }),
    salir: () => pedir('POST', '/auth/salir'),
    listarOts: () => pedir('GET', '/cliente/ots'),
    leerOt: (id) => pedir('GET', ot(id)),
    leerOtCliente: (id) => pedir('GET', otCliente(id)),
    leerPauta: (id, version) => pedir('GET', `/pautas/${encodeURIComponent(id)}?version=${version}`),
    listarPautas: () => pedir('GET', '/cliente/pautas'),
    listarOperadores: () => pedir('GET', '/cliente/operadores'),
    listarPersonas: () => pedir('GET', '/cliente/personas'),
    pedirOt: (pautaId) => pedir('POST', '/cliente/ots', { pauta_id: pautaId }),
    abrirSesion: (id, edgeId, tomar = false) => pedir('POST', `${otCliente(id)}/sesion`, { edge_id: edgeId, tomar }),
    leerSesionEdge: (edgeId) =>
      pedir<Sesion>('GET', `/edge/${encodeURIComponent(edgeId)}/sesion`).catch((e: unknown) => {
        if (e instanceof ApiError && e.tipo === 'no_existe') return null
        throw e
      }),
    declarar: (id, actor, texto, pasoId) =>
      pedir('POST', `${ot(id)}/declarar`, pasoId ? { actor, texto, paso_id: pasoId } : { actor, texto }, TIMEOUT_DECLARAR_MS),
    confirmarPaso: (id, pasoId, actor, motivo) =>
      pedir('POST', `${ot(id)}/pasos/${encodeURIComponent(pasoId)}/confirmar`, { actor, motivo }),
    entregarTurno: (id, actor) => pedir('POST', `${ot(id)}/relevo/entregar?actor=${encodeURIComponent(actor)}`),
    recibirTurno: (id, actor) => pedir('POST', `${ot(id)}/relevo/recibir?actor=${encodeURIComponent(actor)}`),
    asignar: (id, operador) => pedir('POST', `${otCliente(id)}/asignar`, { operador }),
  }
}

export const api: Cliente = crearCliente(config.API_URL, undefined, {
  token: tokenDeSesion,
  alVencer: () => cerrarSesion('vencida'),
})

/** La URL del WebSocket de la OT: https → wss, http → ws. */
export function urlStream(base: string, otId: string, desde: number): string {
  const ws = base.replace(/\/$/, '').replace(/^http/, 'ws')
  return `${ws}/ot/${encodeURIComponent(otId)}/stream?desde=${desde}`
}
