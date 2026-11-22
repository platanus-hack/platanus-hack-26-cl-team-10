// Lo que el servidor calcula leyendo la bitácora, hecho con las OT del mock: el reporte de una OT
// (app/reporte.py), las propuestas de mejora (app/mejora.py) y la foto de la empresa (app/metricas.py).

import { ALIMENTAN_MEJORAS, senalesDe } from '../api/mejoras'
import type { CierreReporte, DesviacionReporte, EstadoGeneral, EstadoMejora, Evento, Mejora, Metricas, ReporteOt, SenalMejora } from '../api/tipos'
import type { Mundo } from './mundo'

/** Como mejora.MINIMO: una desviación suelta no es una propuesta. */
export const MINIMO_OTS = 2

const SENALES: SenalMejora[] = ['orden', 'control', 'conflicto', 'persona', 'observacion']

const SUGERENCIAS: Record<SenalMejora, string> = {
  orden: 'El paso se hace antes de su turno: revisar si el orden de la pauta calza con cómo se trabaja en el equipo, o si el paso anterior se puede cumplir antes.',
  control: 'Un control se deshizo antes de tiempo: revisar si la pauta deja claro hasta cuándo se mantiene.',
  persona: 'La evidencia no vio el paso y una persona lo confirmó: revisar el sensor o la pregunta de la cámara de este paso antes que a quien lo ejecuta.',
  conflicto: 'La palabra del operario y la evidencia no coinciden: revisar cómo está escrito el paso.',
  observacion: 'Los operarios dejaron observaciones sobre este paso: leerlas antes de escribir la versión siguiente.',
}
const CONTROL_CRITICO = 'Es un control crítico: que se desvíe seguido no lo vuelve prescindible.'

const CLASES: Record<string, string> = {
  seguridad: 'Seguridad',
  orden: 'Orden invertido',
  control: 'Control perdido',
  senal: 'Señal fuera de lo normal',
  pegado: 'Sensor pegado',
}
/** Las alertas que hablan de cómo se ejecutó; `senal` y `pegado` hablan del sensor. */
const DE_EJECUCION = ['seguridad', 'orden', 'control']

const ESTADO_DE: Record<string, EstadoMejora> = { aceptar: 'aceptada', descartar: 'descartada' }

const minutosEntre = (desde: string, hasta: string) => Math.round((Date.parse(hasta) - Date.parse(desde)) / 6000) / 10
const esObservacion = (ev: Evento) => ev.tipo === 'observacion' && ALIMENTAN_MEJORAS.includes(String(ev.evidencia?.categoria))

export function mejorasDe(m: Mundo): Mejora[] {
  const ots = m.resumenes()
  type Grupo = { ots: number; senales: Record<SenalMejora, number>; operarios: Set<string>; observaciones: Mejora['observaciones'] }
  const grupos = new Map<string, Grupo>()
  for (const o of ots) {
    const eventos = m.eventos(o.ot)
    for (const [paso, senales] of senalesDe(eventos)) {
      const g = grupos.get(paso) ?? { ots: 0, senales: { orden: 0, control: 0, conflicto: 0, persona: 0, observacion: 0 }, operarios: new Set(), observaciones: [] }
      g.ots++
      for (const s of SENALES) g.senales[s] += senales[s] ?? 0
      if (o.operador) g.operarios.add(o.operador)
      for (const ev of eventos) {
        if (esObservacion(ev) && ev.paso_id === paso) g.observaciones.push({ categoria: String(ev.evidencia?.categoria), texto: ev.declarado ?? ev.detalle })
      }
      grupos.set(paso, g)
    }
  }

  const { id, nombre, version } = m.pauta
  const salida: Mejora[] = []
  for (const [pasoId, g] of grupos) {
    const paso = m.paso(pasoId)
    if (g.ots < MINIMO_OTS || !paso) continue
    const dominantes = SENALES.filter((s) => g.senales[s] > 0).sort((a, b) => g.senales[b] - g.senales[a])
    const pid = `${id}:v${version}:${pasoId}`
    const revision = m.revisionDe(pid)
    salida.push({
      id: pid, pauta: id, nombre, version,
      paso: pasoId, titulo: paso.titulo, control_critico: paso.control_critico,
      ejecuciones: ots.length, ots_con_senal: g.ots, operarios_distintos: g.operarios.size,
      senales: g.senales,
      observaciones: g.observaciones,
      motivo: `«${paso.titulo}» tuvo señales en ${g.ots} de ${ots.length} OT de la versión ${version}, con ${g.operarios.size} operarios distintos`,
      sugerencia: [...dominantes.map((s) => SUGERENCIAS[s]), ...(paso.control_critico ? [CONTROL_CRITICO] : [])].join(' '),
      estado: revision ? ESTADO_DE[revision.decision] : 'abierta',
      revision,
      validacion: null,
    })
  }
  return salida.sort((a, b) => b.ots_con_senal - a.ots_con_senal || Number(b.control_critico) - Number(a.control_critico) || a.id.localeCompare(b.id))
}

function cierreDe(ev: Evento): CierreReporte {
  const e = ev.evidencia ?? {}
  const texto = (v: unknown) => (v === null || v === undefined ? null : String(v))
  const numero = (v: unknown) => (typeof v === 'number' ? v : null)
  const sino = (v: unknown) => (typeof v === 'boolean' ? v : null)
  switch (e.tipo) {
    case 'sensor':
      return { con: 'sensor', sensor: texto(e.id), leido: texto(e.valor), esperado: texto(e.espera) }
    case 'deteccion':
      return { con: 'detector', clase: texto(e.clase), presente: sino(e.presente), confianza: numero(e.confianza ?? e.conf) }
    case 'camara':
      return { con: 'camara', pregunta: texto(e.pregunta), respuesta: sino(e.respuesta), confianza: numero(e.confianza) }
    case 'persona':
      return { con: 'persona', motivo: texto(e.motivo), contra: e.contra ?? null }
    default:
      return { con: 'palabra', declarado: ev.declarado }
  }
}

/** Las alertas de la OT y los conflictos entre la palabra y la evidencia, con cuánto tardaron en resolverse. */
function desviacionesDe(eventos: Evento[]): DesviacionReporte[] {
  const salida: DesviacionReporte[] = []
  const abiertas = new Map<number, DesviacionReporte>()
  for (const ev of eventos) {
    if (ev.tipo === 'alerta') {
      const [clase, ...resto] = String(ev.evidencia?.clave ?? '').split(':')
      const d: DesviacionReporte = {
        clase, que: CLASES[clase] ?? clase, paso: clase === 'orden' || clase === 'control' ? resto.join(':') : null,
        detalle: ev.detalle, abierta: ev.ts, resuelta: null, minutos: null, evento: ev.id,
      }
      salida.push(d)
      abiertas.set(ev.id, d)
    } else if (ev.tipo === 'alerta_resuelta') {
      const d = abiertas.get(Number(ev.evidencia?.resuelve))
      if (d) Object.assign(d, { resuelta: ev.ts, minutos: minutosEntre(d.abierta, ev.ts) })
    } else if (ev.tipo === 'veredicto' && ev.estado === 'en_conflicto') {
      salida.push({ clase: 'conflicto', que: 'La palabra y la evidencia no coinciden', paso: ev.paso_id, detalle: ev.detalle, abierta: ev.ts, resuelta: null, minutos: null, evento: ev.id })
    }
  }
  return salida
}

const porPersona = (ev: Evento) => ev.tipo === 'veredicto' && ev.evidencia?.tipo === 'persona'
const deEjecucion = (d: DesviacionReporte) => DE_EJECUCION.includes(d.clase) || d.clase === 'conflicto'

export function reporteDe(m: Mundo, otId: string, nombreDe: (id: string) => string): ReporteOt {
  const eventos = m.eventos(otId)
  const resumen = m.resumenes().find((o) => o.ot === otId)!
  const veredictos = eventos.filter((e) => e.tipo === 'veredicto')

  let anterior: string | null = null
  const pasos = m.pauta.pasos.map((p) => {
    const suyos = veredictos.filter((v) => v.paso_id === p.id)
    const cierre = suyos.findLast((v) => v.estado === 'verificado') ?? null
    const ultimo = suyos.at(-1) ?? null
    const segundos = cierre && anterior ? Math.round((Date.parse(cierre.ts) - Date.parse(anterior)) / 100) / 10 : null
    if (cierre) anterior = cierre.ts
    return {
      paso: p.id, orden: p.orden, titulo: p.titulo, control_critico: p.control_critico,
      estado: ultimo?.estado ?? ('no_verificado' as const),
      cerrado_con: cierre ? cierreDe(cierre) : null,
      capa: cierre ? (cierre.capa ?? (porPersona(cierre) ? 'persona' : 'palabra')) : null,
      hora: cierre?.ts ?? null, segundos, intentos: suyos.length,
      detalle: (cierre ?? ultimo)?.detalle ?? null, evento: (cierre ?? ultimo)?.id ?? null,
    }
  })

  const desviaciones = desviacionesDe(eventos)
  const confirmadas = eventos.filter(porPersona)
  const ejecucion = eventos.filter((e) => e.tipo === 'declaracion' || e.tipo === 'veredicto')
  const inicio = ejecucion[0]?.ts ?? null
  const fin = resumen.completa ? (pasos.map((p) => p.hora).filter((h) => h !== null).sort().at(-1) ?? null) : null
  const cuantas = desviaciones.filter(deEjecucion).length + confirmadas.length

  return {
    ot: otId,
    estado: resumen.estado_general as EstadoGeneral,
    completa: resumen.completa,
    pauta: { id: m.pauta.id, nombre: m.pauta.nombre, version: m.pauta.version },
    equipo: m.pauta.equipo,
    personas: {
      // En el mock todas las OT son de Oculta y las pidió su supervisora.
      pidio: nombreDe('supervisor:oculta'),
      a_cargo: resumen.operador ? nombreDe(resumen.operador) : null,
      ejecutaron: [...new Set(eventos.filter((e) => e.actor !== 'sistema' && (e.tipo === 'declaracion' || e.tipo === 'observacion' || e.tipo === 'relevo_recibido' || e.tipo === 'veredicto')).map((e) => nombreDe(e.actor)))].sort(),
    },
    tiempos: { abierta: resumen.abierta_en, inicio, fin, minutos_de_ejecucion: inicio && fin ? minutosEntre(inicio, fin) : null },
    resultado: {
      pasos_verificados: resumen.cerrados ?? 0, pasos: resumen.total ?? pasos.length,
      sin_desviaciones: cuantas === 0, desviaciones: cuantas,
      confirmados_por_persona: confirmadas.length, calificacion: m.calificacion(otId),
    },
    pasos,
    pendientes: pasos.filter((p) => p.estado !== 'verificado').map((p) => p.paso),
    desviaciones,
    confirmados_por_persona: confirmadas.map((e) => ({ paso: e.paso_id, quien: nombreDe(e.actor), motivo: e.evidencia?.motivo ? String(e.evidencia.motivo) : null, hora: e.ts, evento: e.id })),
    observaciones: eventos.filter((e) => e.tipo === 'observacion').map((e) => ({ paso: e.paso_id, categoria: String(e.evidencia?.categoria ?? 'otra'), texto: e.declarado ?? e.detalle, quien: nombreDe(e.actor), hora: e.ts, evento: e.id })),
    relevos: eventos
      .filter((e) => e.tipo === 'relevo_entregado' || e.tipo === 'relevo_recibido')
      .map((e) => ({ que: e.tipo === 'relevo_entregado' ? ('entregado' as const) : ('recibido' as const), quien: nombreDe(e.actor), resumen: e.detalle, hora: e.ts, evento: e.id })),
    eventos: { total: eventos.length, primero: eventos[0]?.id ?? null, ultimo: eventos.at(-1)?.id ?? null },
  }
}

const pct = (parte: number, total: number) => (total ? Math.round((1000 * parte) / total) / 10 : null)
const media = (valores: number[]) => (valores.length ? Math.round((10 * valores.reduce((a, b) => a + b, 0)) / valores.length) / 10 : null)

export function metricasDe(m: Mundo): Metricas {
  const reportes = m.resumenes().map((o) => reporteDe(m, o.ot, (id) => id))
  const porEstado: Record<EstadoGeneral, number> = { sin_asignar: 0, asignada: 0, en_ejecucion: 0, entregada: 0, completa: 0 }
  const porEvidencia = { sensor: 0, camara: 0, persona: 0, palabra: 0 }
  const porClase: Record<string, number> = { seguridad: 0, orden: 0, control: 0, conflicto: 0, persona: 0 }
  const paraResolver: number[] = []
  let abiertas = 0
  for (const r of reportes) {
    porEstado[r.estado]++
    for (const p of r.pasos) {
      const con = p.estado === 'verificado' ? p.cerrado_con?.con : undefined
      if (con) porEvidencia[con === 'detector' ? 'camara' : con]++
    }
    for (const d of r.desviaciones.filter(deEjecucion)) {
      porClase[d.clase]++
      if (d.clase === 'conflicto') continue
      if (d.minutos === null) abiertas++
      else paraResolver.push(d.minutos)
    }
    porClase.persona += r.confirmados_por_persona.length
  }
  const completas = reportes.filter((r) => r.completa)
  const limpias = completas.filter((r) => r.resultado.sin_desviaciones).length
  const verificados = Object.values(porEvidencia).reduce((a, b) => a + b, 0)
  const mejoras: Record<EstadoMejora, number> = { abierta: 0, aceptada: 0, descartada: 0, aplicada: 0, superada: 0 }
  for (const p of mejorasDe(m)) mejoras[p.estado]++

  return {
    ots: { total: reportes.length, por_estado: porEstado },
    cumplimiento: { completas: completas.length, sin_desviaciones: limpias, porcentaje: pct(limpias, completas.length) },
    pasos: { verificados, por_evidencia: porEvidencia, con_evidencia_objetiva_pct: pct(porEvidencia.sensor + porEvidencia.camara, verificados) },
    desviaciones: { total: Object.values(porClase).reduce((a, b) => a + b, 0), por_clase: porClase, alertas_abiertas: abiertas, minutos_medios_para_resolver: media(paraResolver) },
    minutos_medios_de_ejecucion: media(completas.map((r) => r.tiempos.minutos_de_ejecucion).filter((x): x is number => x !== null)),
    mejoras,
  }
}
