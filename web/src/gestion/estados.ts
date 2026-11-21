import type { CalificacionOt, EstadoGeneral, EstadoOt, Nivel, OtResumen } from '../api/tipos'
import type { Rol } from '../sesion/usuarios'

/**
 * El estado general lo trae la API. Mientras el back real no entregue `estado_general`
 * (docs/gestion-ot/PRD.md §6), se deduce de lo poco que sí trae.
 */
export function estadoDe(ot: OtResumen): EstadoGeneral {
  if (ot.estado_general) return ot.estado_general
  if (ot.completa) return 'completa'
  return ot.operador ? 'asignada' : 'sin_asignar'
}

export type Avance = { cerrados: number; total: number; nombre: string; pasoActual: string | null }

/**
 * El avance que ya trae `GET /ots`. El nombre legible sale de `GET /pautas` (`nombres`, por id);
 * sin él queda el id. Sin `cerrados`/`total` no hay avance.
 */
export function avanceDelResumen(ot: OtResumen, nombres: ReadonlyMap<string, string>): Avance | null {
  if (ot.cerrados == null || ot.total == null) return null
  const nombre = nombres.get(ot.pauta)
  return { cerrados: ot.cerrados, total: ot.total, nombre: nombre ? `${nombre} v${ot.version}` : ot.pauta, pasoActual: null }
}

/** Un paso cuenta como cerrado si está verificado: por su evidencia o porque una persona lo confirmó. */
export function avanceDe(estado: EstadoOt): Avance {
  const actual = estado.pasos.find((p) => p.id === estado.paso_actual)
  return {
    cerrados: estado.pasos.filter((p) => p.estado === 'verificado').length,
    total: estado.pasos.length,
    nombre: estado.pauta,
    pasoActual: actual ? `${actual.orden}. ${actual.titulo}` : null,
  }
}

export const ESTADOS: Record<EstadoGeneral, { etiqueta: string; color: string }> = {
  sin_asignar: { etiqueta: 'Sin asignar', color: 'roca' },
  asignada: { etiqueta: 'Asignada', color: 'accion' },
  en_ejecucion: { etiqueta: 'En ejecución', color: 'accion' },
  entregada: { etiqueta: 'Entregada', color: 'precaucion' },
  completa: { etiqueta: 'Completa', color: 'verificado' },
}

/** Lo que pide acción del supervisor va primero. */
const ORDEN: EstadoGeneral[] = ['entregada', 'sin_asignar', 'en_ejecucion', 'asignada', 'completa']

export function porPrioridad<T extends { estado: EstadoGeneral; ot: string }>(ots: T[]): T[] {
  return [...ots].sort((a, b) => ORDEN.indexOf(a.estado) - ORDEN.indexOf(b.estado) || a.ot.localeCompare(b.ot))
}

export function puedeAsignarse(estado: EstadoGeneral): boolean {
  return estado === 'sin_asignar' || estado === 'entregada'
}

/** La calificación de una OT en palabras del supervisor: cómo va lo que verifica Factum. */
export const VERIFICACION: Record<Nivel, { etiqueta: string; color: string }> = {
  ok: { etiqueta: 'Todo bien', color: 'verificado' },
  warning: { etiqueta: 'Atención', color: 'precaucion' },
  error: { etiqueta: 'Detente', color: 'peligro' },
}

/** Un incidente: una OT abierta cuya calificación es «detente». `que` es el motivo más grave. */
export type Incidente = { ot: string; operador: string | null; que: string }

export function incidentesDe(ots: { ot: string; operador?: string | null; estado: EstadoGeneral; calificacion: CalificacionOt | null }[]): Incidente[] {
  return ots.flatMap((o) => {
    const c = o.calificacion
    if (o.estado === 'completa' || c?.nivel !== 'error') return []
    const grave = c.avisos.find((a) => a.nivel === 'error') ?? c
    return [{ ot: o.ot, operador: o.operador ?? null, que: grave.motivos[0] ?? 'Hay un control que no se cumple' }]
  })
}

export function inicioDe(rol: Rol): string {
  return rol === 'supervisor' ? '/supervisor' : '/operador'
}
