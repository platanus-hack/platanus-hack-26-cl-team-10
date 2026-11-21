import type { Calificacion, EstadoOt, EstadoPasoApi, Evento, Nivel, PasoEstado, Snapshot } from '../api/tipos'
import { avance, cerradoPor, contarCierre, estadoUi, inicial, reducir, relevoPendiente, type Accion, type Ejecucion } from './estado'

const cal = (nivel: Nivel): Calificacion => ({ nivel, certeza: 1, capa: 1, motivos: ['m'] })

function ev(id: number, extra: Partial<Evento> = {}): Evento {
  return {
    id, ot_id: 'ot-12', tipo: 'veredicto', ts: '2026-11-21T10:00:00Z', actor: 'sistema', detalle: `ev ${id}`,
    paso_id: null, estado: null, capa: null, declarado: null, evidencia: null, calificacion: null, ...extra,
  }
}
const error = (id: number, extra: Partial<Evento> = {}) => ev(id, { tipo: 'alerta', capa: 1, estado: 'en_conflicto', calificacion: cal('error'), ...extra })

function paso(id: string, estado: EstadoPasoApi = 'no_verificado'): PasoEstado {
  return { id, orden: Number(id.slice(1)), titulo: id, estado, control_critico: false, capa: null, evidencia: null, detalle: null }
}
function ot(pasoActual: string | null, pasos: PasoEstado[] = [paso('p1'), paso('p2'), paso('p3')]): EstadoOt {
  return { pauta: 'Pauta v1', equipo: 'CT-01', paso_actual: pasoActual, completa: pasoActual === null, pasos, verificados: [], en_conflicto: [], pendientes: [] }
}
function snap(bitacora: Evento[], extra: Partial<Snapshot> = {}): Snapshot {
  return {
    tipo: 'snapshot', ot: 'ot-12', estado: ot('p1'), calificacion: { ...cal('ok'), avisos: [] },
    alertas_activas: [], sesion: null, video: null, sensores: {}, bitacora, ...extra,
  }
}
const correr = (s: Ejecucion, ...acciones: Accion[]) => acciones.reduce(reducir, s)

describe('the stream', () => {
  it('first snapshot does not speak, reconnect snapshot speaks missed errors', () => {
    const s1 = reducir(inicial, { tipo: 'snapshot', inicial: true, snapshot: snap([ev(1), error(2)]) })
    expect(s1.porSonar).toEqual([])
    expect(s1).toMatchObject({ ultimoId: 2, conexion: 'en_vivo' })
    const s2 = reducir(s1, { tipo: 'snapshot', inicial: false, snapshot: snap([error(3), ev(4, { calificacion: cal('warning') })]) })
    expect(s2.porSonar.map((e) => e.id)).toEqual([3])
    expect(s2.bitacora.map((e) => e.id)).toEqual([1, 2, 3, 4])
  })

  it('a repeated event id is ignored and never queued twice', () => {
    const s = correr(inicial, { tipo: 'evento', evento: error(5) }, { tipo: 'evento', evento: error(5) })
    expect(s.bitacora).toHaveLength(1)
    expect(s.porSonar).toHaveLength(1)
  })

  it('only error events are queued to speak', () => {
    const s = correr(inicial, { tipo: 'evento', evento: ev(1, { calificacion: cal('warning') }) }, { tipo: 'evento', evento: ev(2, { calificacion: cal('ok') }) })
    expect(s.porSonar).toEqual([])
  })

  it('sonado removes spoken events from the queue', () => {
    const s = correr(inicial, { tipo: 'evento', evento: error(1) }, { tipo: 'evento', evento: error(2) }, { tipo: 'sonado', ids: [1] })
    expect(s.porSonar.map((e) => e.id)).toEqual([2])
  })

  it('a verdict updates its step right away, without touching paso_actual', () => {
    const s = correr(inicial, { tipo: 'estado', estado: ot('p1') }, { tipo: 'evento', evento: ev(1, { paso_id: 'p1', estado: 'verificado', capa: 1, detalle: 'ok' }) })
    expect(s.ot?.pasos[0]).toMatchObject({ estado: 'verificado', capa: 1, detalle: 'ok' })
    expect(s.ot?.paso_actual).toBe('p1')
  })
})

describe('alerts', () => {
  it('alerta_resuelta and alert overwrite remove the alert', () => {
    const s1 = correr(inicial, { tipo: 'evento', evento: error(1) }, { tipo: 'evento', evento: error(2) })
    expect(s1.alertas.map((a) => a.id)).toEqual([1, 2])
    const s2 = correr(
      s1,
      { tipo: 'evento', evento: ev(3, { tipo: 'alerta_resuelta', evidencia: { resuelve: 1 } }) },
      { tipo: 'evento', evento: ev(4, { tipo: 'sobrescritura', evidencia: { alerta_id: 2 } }) },
    )
    expect(s2.alertas).toEqual([])
  })

  it('the snapshot replaces the active alerts', () => {
    const s = correr(inicial, { tipo: 'evento', evento: error(1) }, { tipo: 'snapshot', inicial: false, snapshot: snap([], { alertas_activas: [error(7)] }) })
    expect(s.alertas.map((a) => a.id)).toEqual([7])
  })
})

describe('Hecho', () => {
  const base = reducir(inicial, { tipo: 'estado', estado: ot('p1') })

  it('hecho_enviado is ignored while pendiente', () => {
    const s = correr(base, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_enviado', pasoId: 'p2' })
    expect(s.pendiente).toEqual({ pasoId: 'p1' })
  })

  it('shows comprobando while the declaration is in flight', () => {
    const s = reducir(base, { tipo: 'hecho_enviado', pasoId: 'p1' })
    expect(estadoUi(s.ot!.pasos[0], s)).toBe('comprobando')
  })

  it('error clears pendiente and keeps the message', () => {
    const s = correr(base, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'error', mensaje: 'la pauta ya está completa' })
    expect(s).toMatchObject({ pendiente: null, mensaje: 'la pauta ya está completa' })
    expect(reducir(s, { tipo: 'mensaje_visto' }).mensaje).toBeNull()
  })

  it('a new Hecho clears the previous message', () => {
    const s = correr(base, { tipo: 'error', mensaje: 'x' }, { tipo: 'hecho_enviado', pasoId: 'p1' })
    expect(s.mensaje).toBeNull()
  })

  it('no_verificado answer goes to sin_senal, a later verdict leaves it', () => {
    const s1 = correr(base, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_respondido', pasoId: 'p1', estado: 'no_verificado' })
    expect(estadoUi(s1.ot!.pasos[0], s1)).toBe('sin_senal')
    const s2 = reducir(s1, { tipo: 'evento', evento: ev(9, { paso_id: 'p1', estado: 'verificado', capa: 1 }) })
    expect(estadoUi(s2.ot!.pasos[0], s2)).toBe('verificado')
    expect(s2.sinSenal).toEqual([])
  })

  it('no answer within the timeout also goes to sin_senal', () => {
    const s = correr(base, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_sin_respuesta', pasoId: 'p1' })
    expect(s.pendiente).toBeNull()
    expect(estadoUi(s.ot!.pasos[0], s)).toBe('sin_senal')
  })

  it('a verdict for the pending step over the stream clears pendiente', () => {
    const s = correr(base, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'evento', evento: ev(3, { paso_id: 'p1', estado: 'en_conflicto', capa: 1 }) })
    expect(s.pendiente).toBeNull()
  })
})

it('maps every API state to its UI state', () => {
  const s = reducir(inicial, { tipo: 'estado', estado: ot('p2') })
  expect(estadoUi(paso('p1', 'verificado'), s)).toBe('verificado')
  expect(estadoUi(paso('p1', 'sobrescrito'), s)).toBe('sobrescrito')
  expect(estadoUi(paso('p1', 'en_conflicto'), s)).toBe('warn')
  expect(estadoUi(paso('p2'), s)).toBe('en_curso')
  expect(estadoUi(paso('p3'), s)).toBe('pendiente')
})

it('relevoPendiente is the last handover not yet received', () => {
  const entregado = ev(1, { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen', ts: 'T1' })
  expect(relevoPendiente([ev(0), entregado])).toEqual({ resumen: 'resumen', entregado_por: 'operario:1', ts: 'T1' })
  expect(relevoPendiente([entregado, ev(2, { tipo: 'relevo_recibido', actor: 'operario:2' })])).toBeNull()
  expect(relevoPendiente([])).toBeNull()
})

it('avance counts verified and overwritten steps', () => {
  expect(avance(ot('p3', [paso('p1', 'verificado'), paso('p2', 'sobrescrito'), paso('p3', 'en_conflicto')]))).toEqual({ hechos: 2, total: 3 })
})

it('contarCierre counts overwrites and warnings', () => {
  const bitacora = [
    ev(1, { tipo: 'sobrescritura' }),
    error(2),
    ev(3, { estado: 'en_conflicto' }),
    ev(4, { estado: 'verificado' }),
    ev(5, { tipo: 'alerta_resuelta' }),
  ]
  expect(contarCierre(bitacora)).toEqual({ sobrescritos: 1, avisos: 2 })
})

it('cerradoPor names who overwrote a step, latest first', () => {
  const bitacora = [
    ev(1, { tipo: 'sobrescritura', paso_id: 'p2', actor: 'operario:1' }),
    ev(2, { tipo: 'sobrescritura', paso_id: 'p2', actor: 'operario:2' }),
  ]
  expect(cerradoPor(bitacora, 'p2')).toBe('operario:2')
  expect(cerradoPor(bitacora, 'p1')).toBeNull()
})
