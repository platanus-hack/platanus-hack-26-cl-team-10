import type { CalificacionOt, EstadoGeneral, EstadoOt, Nivel, OtResumen } from '../api/tipos'
import { enPalabras } from './sensores'
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

/** Cómo se agrupan las OT del supervisor. Arriba, las que se ejecutan ahora. Un grupo vacío no se muestra. */
const GRUPOS: { titulo: string; estados: EstadoGeneral[] }[] = [
  { titulo: 'En ejecución', estados: ['en_ejecucion'] },
  { titulo: 'Por asignar', estados: ['entregada', 'sin_asignar'] },
  { titulo: 'Asignadas, sin empezar', estados: ['asignada'] },
  { titulo: 'Completas', estados: ['completa'] },
]

const GRAVEDAD: Record<Nivel, number> = { error: 0, warning: 1, ok: 2 }

export type Grupo<T> = { titulo: string; ots: T[] }

/** Las OT en sus grupos. Dentro de cada uno van primero las que avisan: «detente», después «atención». */
export function enGrupos<T extends { ot: string; estado: EstadoGeneral; calificacion: CalificacionOt | null }>(ots: T[]): Grupo<T>[] {
  if (ots.length === 0) return []
  const gravedad = (o: T) => GRAVEDAD[avisoDe(o)?.nivel ?? 'ok']
  return GRUPOS.map(({ titulo, estados }) => ({
    titulo,
    ots: ots
      .filter((o) => estados.includes(o.estado))
      .sort(
        (a, b) =>
          gravedad(a) - gravedad(b) ||
          estados.indexOf(a.estado) - estados.indexOf(b.estado) ||
          a.ot.localeCompare(b.ot, undefined, { numeric: true }),
      ),
  })).filter((g) => g.ots.length > 0)
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

/** Lo que avisa una OT abierta que no va bien: «atención» o «detente», con su motivo más grave. */
export type Aviso = { nivel: 'warning' | 'error'; que: string }

export function avisoDe(o: { estado: EstadoGeneral; calificacion: CalificacionOt | null }): Aviso | null {
  const c = o.calificacion
  if (o.estado === 'completa' || !c || c.nivel === 'ok') return null
  const grave = c.avisos.find((a) => a.nivel === c.nivel) ?? c
  return { nivel: c.nivel, que: (grave.motivos[0] && enPalabras(grave.motivos[0])) ?? (c.nivel === 'error' ? 'Hay un control que no se cumple' : 'Hay algo que revisar') }
}

/** Un incidente: una OT abierta cuya calificación es «detente». `que` es el motivo más grave. */
export type Incidente = { ot: string; operador: string | null; que: string }

export function incidentesDe(ots: { ot: string; operador?: string | null; estado: EstadoGeneral; calificacion: CalificacionOt | null }[]): Incidente[] {
  return ots.flatMap((o) => {
    const aviso = avisoDe(o)
    return aviso?.nivel === 'error' ? [{ ot: o.ot, operador: o.operador ?? null, que: aviso.que }] : []
  })
}

export function inicioDe(rol: Rol): string {
  return rol === 'supervisor' ? '/supervisor/hoy' : '/operador'
}
