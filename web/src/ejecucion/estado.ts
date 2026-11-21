// La máquina de estados de la ejecución. Funciones puras: sin React, sin red.
//
// La API manda: el estado de cada paso y el paso actual vienen de ella. Lo único que
// agrega el front es lo que pasa mientras el operario espera («comprobando») y cuando
// la evidencia no llega («sin_senal»). Ver knowledge/architecture/FRONTEND.md §6.

import type { CalificacionOt, EstadoOt, EstadoPasoApi, Evento, PasoEstado, Snapshot } from '../api/tipos'

export type EstadoUi = 'pendiente' | 'en_curso' | 'comprobando' | 'sin_senal' | 'verificado' | 'warn' | 'sobrescrito'
export type Conexion = 'conectando' | 'en_vivo' | 'reconectando' | 'no_existe'

export type Ejecucion = {
  ot: EstadoOt | null
  calificacion: CalificacionOt | null
  alertas: Evento[]
  bitacora: Evento[]
  ultimoId: number
  pendiente: { pasoId: string } | null
  sinSenal: string[]
  conexion: Conexion
  mensaje: string | null
  /** Eventos de nivel error que todavía no suenan. */
  porSonar: Evento[]
}

export type Accion =
  | { tipo: 'snapshot'; snapshot: Snapshot; inicial: boolean }
  | { tipo: 'evento'; evento: Evento }
  | { tipo: 'calificacion'; calificacion: CalificacionOt }
  | { tipo: 'estado'; estado: EstadoOt }
  | { tipo: 'hecho_enviado'; pasoId: string }
  | { tipo: 'hecho_respondido'; pasoId: string; estado: EstadoPasoApi }
  | { tipo: 'hecho_sin_respuesta'; pasoId: string }
  | { tipo: 'error'; mensaje: string }
  | { tipo: 'mensaje_visto' }
  | { tipo: 'conexion'; conexion: Conexion }
  | { tipo: 'sonado'; ids: number[] }

export const inicial: Ejecucion = {
  ot: null,
  calificacion: null,
  alertas: [],
  bitacora: [],
  ultimoId: 0,
  pendiente: null,
  sinSenal: [],
  conexion: 'conectando',
  mensaje: null,
  porSonar: [],
}

const suena = (e: Evento) => e.calificacion?.nivel === 'error'
const sinRepetir = (lista: string[], id: string) => (lista.includes(id) ? lista : [...lista, id])

function aplicarEvento(s: Ejecucion, ev: Evento): Ejecucion {
  if (ev.id <= s.ultimoId) return s
  let { alertas, pendiente, sinSenal, ot } = s

  if (ev.tipo === 'alerta') alertas = [...alertas, ev]
  if (ev.tipo === 'alerta_resuelta') alertas = alertas.filter((a) => a.id !== ev.evidencia?.resuelve)
  if (ev.tipo === 'sobrescritura' && ev.evidencia?.alerta_id != null) alertas = alertas.filter((a) => a.id !== ev.evidencia?.alerta_id)

  if (ev.paso_id && ev.estado) {
    if (ev.tipo === 'veredicto' && pendiente?.pasoId === ev.paso_id) pendiente = null
    sinSenal =
      ev.estado === 'no_verificado'
        ? ev.tipo === 'veredicto' && s.pendiente?.pasoId === ev.paso_id
          ? sinRepetir(sinSenal, ev.paso_id)
          : sinSenal
        : sinSenal.filter((id) => id !== ev.paso_id)
    // El paso se pinta al instante; el paso actual lo trae el GET /ot/{id} que sigue.
    if (ot) {
      const { estado, capa, detalle, evidencia } = ev
      ot = { ...ot, pasos: ot.pasos.map((p) => (p.id === ev.paso_id ? { ...p, estado, capa, detalle, evidencia } : p)) }
    }
  }

  return {
    ...s,
    ot,
    alertas,
    pendiente,
    sinSenal,
    bitacora: [...s.bitacora, ev],
    ultimoId: ev.id,
    porSonar: suena(ev) ? [...s.porSonar, ev] : s.porSonar,
  }
}

export function reducir(s: Ejecucion, a: Accion): Ejecucion {
  switch (a.tipo) {
    case 'snapshot': {
      const { snapshot, inicial: primero } = a
      const nuevos = snapshot.bitacora.filter((e) => e.id > s.ultimoId).sort((x, y) => x.id - y.id)
      const ultimoId = Math.max(s.ultimoId, ...nuevos.map((e) => e.id))
      return {
        ...s,
        ot: snapshot.estado,
        calificacion: snapshot.calificacion,
        alertas: snapshot.alertas_activas,
        bitacora: [...s.bitacora, ...nuevos],
        ultimoId,
        conexion: 'en_vivo',
        porSonar: primero ? s.porSonar : [...s.porSonar, ...nuevos.filter(suena)],
      }
    }
    case 'evento':
      return aplicarEvento(s, a.evento)
    case 'calificacion':
      return { ...s, calificacion: a.calificacion }
    case 'estado':
      return { ...s, ot: a.estado }
    case 'hecho_enviado':
      return s.pendiente ? s : { ...s, pendiente: { pasoId: a.pasoId }, mensaje: null }
    case 'hecho_respondido':
      return {
        ...s,
        pendiente: null,
        sinSenal: a.estado === 'no_verificado' ? sinRepetir(s.sinSenal, a.pasoId) : s.sinSenal,
      }
    case 'hecho_sin_respuesta':
      return { ...s, pendiente: null, sinSenal: sinRepetir(s.sinSenal, a.pasoId) }
    case 'error':
      return { ...s, pendiente: null, mensaje: a.mensaje }
    case 'mensaje_visto':
      return { ...s, mensaje: null }
    case 'conexion':
      return { ...s, conexion: a.conexion }
    case 'sonado':
      return { ...s, porSonar: s.porSonar.filter((e) => !a.ids.includes(e.id)) }
  }
}

export function estadoUi(paso: PasoEstado, s: Ejecucion): EstadoUi {
  switch (paso.estado) {
    case 'verificado':
      return 'verificado'
    case 'sobrescrito':
      return 'sobrescrito'
    case 'en_conflicto':
      return 'warn'
    case 'no_verificado':
      if (s.pendiente?.pasoId === paso.id) return 'comprobando'
      if (s.sinSenal.includes(paso.id)) return 'sin_senal'
      return s.ot?.paso_actual === paso.id ? 'en_curso' : 'pendiente'
  }
}

export function relevoPendiente(bitacora: Evento[]): { resumen: string; entregado_por: string; ts: string } | null {
  const i = bitacora.findLastIndex((e) => e.tipo === 'relevo_entregado')
  if (i < 0 || bitacora.slice(i + 1).some((e) => e.tipo === 'relevo_recibido')) return null
  const e = bitacora[i]
  return { resumen: e.detalle, entregado_por: e.actor, ts: e.ts }
}

export function avance(ot: EstadoOt): { hechos: number; total: number } {
  return {
    hechos: ot.pasos.filter((p) => p.estado === 'verificado' || p.estado === 'sobrescrito').length,
    total: ot.pasos.length,
  }
}

export function contarCierre(bitacora: Evento[]): { sobrescritos: number; avisos: number } {
  return {
    sobrescritos: bitacora.filter((e) => e.tipo === 'sobrescritura').length,
    avisos: bitacora.filter((e) => e.tipo === 'alerta' || (e.tipo === 'veredicto' && e.estado === 'en_conflicto')).length,
  }
}
