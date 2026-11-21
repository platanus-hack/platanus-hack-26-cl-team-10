// La máquina de estados de la ejecución. Funciones puras: sin React, sin red.
//
// La API manda: el estado de cada paso y el paso actual vienen de ella, y los pasos se cierran
// solos con su evidencia (sensor o cámara). El operario solo actúa cuando la API avisa: un paso
// saltado, un conflicto, o una evidencia que no llega. Lo único que agrega el front es lo que pasa
// mientras se espera una respuesta («comprobando») y cuando la evidencia no llega («sin_senal»).
// Ver knowledge/architecture/FRONTEND.md §6.

import type { CalificacionOt, EstadoOt, EstadoPasoApi, Evento, PasoEstado, Snapshot } from '../api/tipos'

export type EstadoUi = 'pendiente' | 'en_curso' | 'comprobando' | 'sin_senal' | 'verificado' | 'warn' | 'confirmado'
export type Conexion = 'conectando' | 'en_vivo' | 'reconectando' | 'no_existe'
export type TipoAlerta = 'seguridad' | 'orden' | 'control' | 'senal' | 'otra'

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
  /** El paso actual lleva rato esperando su evidencia: se ofrece confirmarlo a mano. */
  | { tipo: 'espera_vencida'; pasoId: string }
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

/** Suena lo de nivel error, y solo la capa 1 llega a error. */
export const debeSonar = (e: Evento): boolean => e.calificacion?.nivel === 'error'
const sinRepetir = (lista: string[], id: string) => (lista.includes(id) ? lista : [...lista, id])

/** Qué clase de alerta es: por su clave en la API (`seguridad:…`, `orden:…`), o por su evidencia. */
export function tipoDeAlerta(ev: Evento): TipoAlerta {
  const prefijo = String(ev.evidencia?.clave ?? '').split(':')[0]
  if (prefijo === 'seguridad' || prefijo === 'orden' || prefijo === 'control' || prefijo === 'senal') return prefijo
  const tipo = ev.evidencia?.tipo
  if (tipo === 'orden' || tipo === 'control') return tipo
  if (ev.capa === 2) return 'senal'
  if (ev.capa === 1) return 'seguridad'
  return 'otra'
}

/** La alerta activa que dice que este paso se saltó, si la hay. */
export function saltoDe(s: Pick<Ejecucion, 'alertas'>, pasoId: string): Evento | null {
  return s.alertas.find((a) => tipoDeAlerta(a) === 'orden' && a.evidencia?.pendiente === pasoId) ?? null
}

function aplicarEvento(s: Ejecucion, ev: Evento): Ejecucion {
  if (ev.id <= s.ultimoId) return s
  let { alertas, pendiente, sinSenal, ot } = s

  if (ev.tipo === 'alerta') alertas = [...alertas, ev]
  if (ev.tipo === 'alerta_resuelta') alertas = alertas.filter((a) => a.id !== ev.evidencia?.resuelve)

  if (ev.paso_id && ev.estado) {
    const esperado = ev.tipo === 'veredicto' && pendiente?.pasoId === ev.paso_id
    if (esperado) pendiente = null
    sinSenal =
      ev.estado === 'no_verificado'
        ? esperado
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
    porSonar: debeSonar(ev) ? [...s.porSonar, ev] : s.porSonar,
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
        porSonar: primero ? s.porSonar : [...s.porSonar, ...nuevos.filter(debeSonar)],
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
    case 'espera_vencida': {
      const paso = s.ot?.pasos.find((p) => p.id === a.pasoId)
      const abierto = s.ot?.paso_actual === a.pasoId && paso?.estado === 'no_verificado'
      return abierto ? { ...s, sinSenal: sinRepetir(s.sinSenal, a.pasoId) } : s
    }
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
  // Mientras se espera la respuesta de «Hecho», eso es lo que se muestra, aunque hubiera un conflicto.
  if (s.pendiente?.pasoId === paso.id) return 'comprobando'
  switch (paso.estado) {
    case 'verificado':
      return paso.evidencia?.tipo === 'persona' ? 'confirmado' : 'verificado'
    case 'en_conflicto':
      return 'warn'
    case 'no_verificado':
      if (saltoDe(s, paso.id)) return 'warn'
      if (s.sinSenal.includes(paso.id)) return 'sin_senal'
      return s.ot?.paso_actual === paso.id ? 'en_curso' : 'pendiente'
  }
}

/** El texto del aviso de un paso en warn: el salto que lo provocó, o el detalle del veredicto. */
export function avisoDelPaso(paso: PasoEstado, s: Ejecucion): string | null {
  const salto = saltoDe(s, paso.id)
  if (salto) {
    const adelantado = s.ot?.pasos.find((p) => p.id === salto.evidencia?.adelantado)
    return adelantado ? `Te saltaste este paso: hiciste «${adelantado.titulo}» antes.` : salto.detalle
  }
  return paso.estado === 'en_conflicto' ? conflictoEnPalabras(paso) : null
}

/** El conflicto de un veredicto en palabras del operario; si la evidencia no alcanza, el detalle tal cual. */
function conflictoEnPalabras(paso: PasoEstado): string | null {
  const ev = paso.evidencia ?? {}
  if (ev.tipo === 'camara') {
    const certeza = typeof ev.confianza === 'number' ? ` (${Math.round(ev.confianza * 100)} % de certeza)` : ''
    return `La cámara no lo ve${certeza}. Revisa y toca «Hecho» de nuevo, o confírmalo si ya lo hiciste.`
  }
  if (ev.tipo === 'sensor' && ev.id && ev.valor != null)
    return `El sensor ${String(ev.id)} marca «${String(ev.valor)}»; el paso espera «${String(ev.espera)}».`
  return paso.detalle
}

/** Lo que dice la voz: una frase corta y en orden de lectura, no el detalle técnico tal cual. */
export function textoParaVoz(ev: Evento, ot: EstadoOt | null): string {
  const paso = (id: unknown) => ot?.pasos.find((p) => p.id === id)
  const tipo = ev.tipo === 'alerta' ? tipoDeAlerta(ev) : 'otra'
  if (tipo === 'orden') {
    const p = paso(ev.evidencia?.pendiente)
    if (p) return `Oye, te saltaste el paso ${p.orden}: ${p.titulo}. Hazlo antes de seguir.`
  }
  if (tipo === 'control') {
    const p = paso(ev.evidencia?.paso)
    if (p) return `Oye, se deshizo el paso ${p.orden}: ${p.titulo}. Vuelve a dejarlo como estaba.`
  }
  return comoOracion(ev.detalle)
}

/** «GUARDA ABIERTA CON ENERGÍA VIVA. Detener…» → «Guarda abierta con energía viva. Detener…». */
function comoOracion(texto: string): string {
  const m = /^([^.:]+)([.:])/.exec(texto)
  if (!m || m[1].length < 4 || m[1] !== m[1].toUpperCase() || !/[A-ZÁÉÍÓÚÑ]/.test(m[1])) return texto
  const minusculas = m[1].toLowerCase()
  return minusculas[0].toUpperCase() + minusculas.slice(1) + texto.slice(m[1].length)
}

export function relevoPendiente(bitacora: Evento[]): { resumen: string; entregado_por: string; ts: string } | null {
  const i = bitacora.findLastIndex((e) => e.tipo === 'relevo_entregado')
  if (i < 0 || bitacora.slice(i + 1).some((e) => e.tipo === 'relevo_recibido')) return null
  const e = bitacora[i]
  return { resumen: e.detalle, entregado_por: e.actor, ts: e.ts }
}

/** Cuántos pasos están cerrados: por su evidencia o por una persona. */
export function avance(ot: EstadoOt): { hechos: number; total: number } {
  return { hechos: ot.pasos.filter((p) => p.estado === 'verificado').length, total: ot.pasos.length }
}

const porPersona = (e: Evento) => e.tipo === 'veredicto' && e.estado === 'verificado' && e.evidencia?.tipo === 'persona'

export function contarCierre(bitacora: Evento[]): { confirmados: number; avisos: number } {
  return {
    confirmados: bitacora.filter(porPersona).length,
    avisos: bitacora.filter((e) => e.tipo === 'alerta' || (e.tipo === 'veredicto' && e.estado === 'en_conflicto')).length,
  }
}

/** Quién confirmó un paso contra la evidencia (el actor del último veredicto por persona), o null. */
export function cerradoPor(bitacora: Evento[], pasoId: string): string | null {
  return bitacora.findLast((e) => porPersona(e) && e.paso_id === pasoId)?.actor ?? null
}
