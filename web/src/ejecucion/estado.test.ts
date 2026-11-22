import type { Calificacion, EstadoOt, EstadoPasoApi, Evento, Nivel, PasoEstado, Snapshot } from '../api/tipos'
import {
  avance,
  avisoDelPaso,
  cerradoPor,
  contarCierre,
  esAlto,
  estadoUi,
  frasesDeLaOt,
  inicial,
  reducir,
  relevoPendiente,
  textoParaVoz,
  tipoDeAlerta,
  type Accion,
  type Ejecucion,
} from './estado'

const cal = (nivel: Nivel): Calificacion => ({ nivel, certeza: 1, capa: 1, motivos: ['m'] })

function ev(id: number, extra: Partial<Evento> = {}): Evento {
  return {
    id, ot_id: 'ot-12', tipo: 'veredicto', ts: '2026-11-21T10:00:00Z', actor: 'sistema', detalle: `ev ${id}`,
    paso_id: null, estado: null, capa: null, declarado: null, evidencia: null, calificacion: null, ...extra,
  }
}
const error = (id: number, extra: Partial<Evento> = {}) => ev(id, { tipo: 'alerta', capa: 1, estado: 'en_conflicto', calificacion: cal('error'), ...extra })
const saltoDeP1 = (id: number) =>
  error(id, {
    detalle: 'ORDEN INVERTIDO: «p2» (guarda = abierta) antes de «p1».',
    evidencia: { tipo: 'orden', pendiente: 'p1', adelantado: 'p2', sensor: 'guarda', valor: 'abierta', clave: 'orden:p2' },
  })

function paso(id: string, estado: EstadoPasoApi = 'no_verificado', extra: Partial<PasoEstado> = {}): PasoEstado {
  const n = Number(id.slice(1))
  return { id, orden: n, titulo: `Paso ${n}`, estado, control_critico: false, capa: null, evidencia: null, detalle: null, ...extra }
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
const enP1 = reducir(inicial, { tipo: 'estado', estado: ot('p1') })

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
    const s = reducir(enP1, { tipo: 'evento', evento: ev(1, { paso_id: 'p1', estado: 'verificado', capa: 1, detalle: 'ok' }) })
    expect(s.ot?.pasos[0]).toMatchObject({ estado: 'verificado', capa: 1, detalle: 'ok' })
    expect(s.ot?.paso_actual).toBe('p1')
  })
})

describe('a skipped or undone step always speaks and pops up on screen', () => {
  const comoWarning = { calificacion: cal('warning') }

  it('a skip or a lost control speaks even if the API grades it warning; a camera doubt does not', () => {
    const s = correr(
      inicial,
      { tipo: 'evento', evento: { ...saltoDeP1(1), ...comoWarning } },
      { tipo: 'evento', evento: error(2, { ...comoWarning, evidencia: { tipo: 'control', paso: 'p1', clave: 'control:p1' } }) },
      { tipo: 'evento', evento: ev(3, { paso_id: 'p3', estado: 'en_conflicto', capa: 2, ...comoWarning }) },
    )
    expect(s.porSonar.map((e) => e.id)).toEqual([1, 2])
    expect(s.enPantalla.map((e) => e.id)).toEqual([1, 2])
  })

  it('what speaks stays on screen until the operator closes it', () => {
    const s1 = correr(inicial, { tipo: 'evento', evento: saltoDeP1(1) }, { tipo: 'sonado', ids: [1] })
    expect(s1.enPantalla.map((e) => e.id)).toEqual([1])
    expect(reducir(s1, { tipo: 'aviso_cerrado', id: 1 }).enPantalla).toEqual([])
  })

  it('the first snapshot pops nothing up; a reconnect pops up what was missed and still active', () => {
    const s1 = reducir(inicial, { tipo: 'snapshot', inicial: true, snapshot: snap([error(2)], { alertas_activas: [error(2)] }) })
    expect(s1.enPantalla).toEqual([])
    const s2 = reducir(s1, { tipo: 'snapshot', inicial: false, snapshot: snap([error(3), error(4)], { alertas_activas: [error(2), error(4)] }) })
    expect(s2.enPantalla.map((e) => e.id)).toEqual([4])
  })

  it('leaves the screen by itself when its alert is resolved', () => {
    const s = correr(inicial, { tipo: 'evento', evento: error(1) }, { tipo: 'evento', evento: ev(2, { tipo: 'alerta_resuelta', evidencia: { resuelve: 1 } }) })
    expect(s.enPantalla).toEqual([])
  })

  it('a step conflict leaves the screen once its step is verified', () => {
    const conflicto = ev(1, { paso_id: 'p1', estado: 'en_conflicto', capa: 1, calificacion: cal('error') })
    const s1 = correr(enP1, { tipo: 'evento', evento: conflicto })
    expect(s1.enPantalla.map((e) => e.id)).toEqual([1])
    const s2 = reducir(s1, { tipo: 'estado', estado: ot('p2', [paso('p1', 'verificado'), paso('p2'), paso('p3')]) })
    expect(s2.enPantalla).toEqual([])
  })
})

describe('alerts', () => {
  it('alerta_resuelta removes the alert, the snapshot replaces them', () => {
    const s1 = correr(inicial, { tipo: 'evento', evento: error(1) }, { tipo: 'evento', evento: error(2) })
    expect(s1.alertas.map((a) => a.id)).toEqual([1, 2])
    const s2 = reducir(s1, { tipo: 'evento', evento: ev(3, { tipo: 'alerta_resuelta', evidencia: { resuelve: 1 } }) })
    expect(s2.alertas.map((a) => a.id)).toEqual([2])
    const s3 = reducir(s2, { tipo: 'snapshot', inicial: false, snapshot: snap([], { alertas_activas: [error(7)] }) })
    expect(s3.alertas.map((a) => a.id)).toEqual([7])
  })

  it('classifies each alert by its key, or by its evidence', () => {
    expect(tipoDeAlerta(error(1, { evidencia: { clave: 'seguridad:GUARDA ABIERTA' } }))).toBe('seguridad')
    expect(tipoDeAlerta(saltoDeP1(2))).toBe('orden')
    expect(tipoDeAlerta(error(3, { evidencia: { tipo: 'control', paso: 'p1' } }))).toBe('control')
    expect(tipoDeAlerta(ev(4, { tipo: 'alerta', capa: 2, evidencia: { clave: 'senal:vibracion' } }))).toBe('senal')
    expect(tipoDeAlerta(error(5, { evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva' } }))).toBe('seguridad')
  })
})

describe('steps', () => {
  it('maps every API state to its UI state', () => {
    const s = reducir(inicial, { tipo: 'estado', estado: ot('p2') })
    expect(estadoUi(paso('p1', 'verificado'), s)).toBe('verificado')
    expect(estadoUi(paso('p1', 'verificado', { evidencia: { tipo: 'persona', motivo: 'lo vi' } }), s)).toBe('confirmado')
    expect(estadoUi(paso('p1', 'en_conflicto'), s)).toBe('warn')
    expect(estadoUi(paso('p2'), s)).toBe('en_curso')
    expect(estadoUi(paso('p3'), s)).toBe('pendiente')
  })

  it('an active skip warning puts the skipped step in warn and names what was done early', () => {
    const s = reducir(enP1, { tipo: 'evento', evento: saltoDeP1(1) })
    expect(estadoUi(s.ot!.pasos[0], s)).toBe('warn')
    expect(avisoDelPaso(s.ot!.pasos[0], s)).toBe('Te saltaste este paso: hiciste «Paso 2» antes.')
    const resuelto = reducir(s, { tipo: 'evento', evento: ev(2, { tipo: 'alerta_resuelta', evidencia: { resuelve: 1, tipo: 'orden' } }) })
    expect(estadoUi(resuelto.ot!.pasos[0], resuelto)).toBe('en_curso')
  })

  it('a verdict conflict tells its detail', () => {
    const s = reducir(enP1, { tipo: 'estado', estado: ot('p1', [paso('p1', 'en_conflicto', { detalle: 'la cámara responde que no (62%)' })]) })
    expect(avisoDelPaso(s.ot!.pasos[0], s)).toBe('la cámara responde que no (62%)')
  })

  it('a conflict with evidence is said in plain words', () => {
    const conPaso = (extra: Partial<PasoEstado>) => {
      const s = reducir(enP1, { tipo: 'estado', estado: ot('p1', [paso('p1', 'en_conflicto', extra)]) })
      return avisoDelPaso(s.ot!.pasos[0], s)
    }
    expect(conPaso({ capa: 3, detalle: 'el operario declaró «hecho» y la cámara responde que no (62%)', evidencia: { tipo: 'camara', respuesta: false, confianza: 0.62 } })).toBe(
      'La cámara no lo ve (62 % de certeza). Revisa y toca «Hecho» de nuevo, o confírmalo si ya lo hiciste.',
    )
    expect(conPaso({ capa: 1, detalle: 'x', evidencia: { tipo: 'sensor', id: 'reed_bloqueo', valor: 'abierto', espera: 'cerrado' } })).toBe(
      'El sensor reed_bloqueo marca «abierto»; el paso espera «cerrado».',
    )
  })

  it('the evidence wait running out puts only the current open step in sin_senal', () => {
    const s = correr(enP1, { tipo: 'espera_vencida', pasoId: 'p1' }, { tipo: 'espera_vencida', pasoId: 'p2' })
    expect(estadoUi(s.ot!.pasos[0], s)).toBe('sin_senal')
    expect(estadoUi(s.ot!.pasos[1], s)).toBe('pendiente')
    const cerrado = reducir(s, { tipo: 'evento', evento: ev(1, { paso_id: 'p1', estado: 'verificado', capa: 1 }) })
    expect(estadoUi(cerrado.ot!.pasos[0], cerrado)).toBe('verificado')
    expect(cerrado.sinSenal).toEqual([])
  })
})

describe('Hecho', () => {
  it('hecho_enviado is ignored while pendiente', () => {
    const s = correr(enP1, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_enviado', pasoId: 'p2' })
    expect(s.pendiente).toEqual({ pasoId: 'p1' })
  })

  it('shows comprobando while the declaration is in flight, even over a conflict', () => {
    const conflicto = reducir(inicial, { tipo: 'estado', estado: ot('p1', [paso('p1', 'en_conflicto')]) })
    const s = reducir(conflicto, { tipo: 'hecho_enviado', pasoId: 'p1' })
    expect(estadoUi(s.ot!.pasos[0], s)).toBe('comprobando')
  })

  it('error clears pendiente and keeps the message; a new Hecho clears it', () => {
    const s = correr(enP1, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'error', mensaje: 'la pauta ya está completa' })
    expect(s).toMatchObject({ pendiente: null, mensaje: 'la pauta ya está completa' })
    expect(reducir(s, { tipo: 'mensaje_visto' }).mensaje).toBeNull()
    expect(reducir(s, { tipo: 'hecho_enviado', pasoId: 'p1' }).mensaje).toBeNull()
  })

  it('no_verificado answer or no answer at all goes to sin_senal', () => {
    const s1 = correr(enP1, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_respondido', pasoId: 'p1', estado: 'no_verificado' })
    expect(estadoUi(s1.ot!.pasos[0], s1)).toBe('sin_senal')
    const s2 = correr(enP1, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'hecho_sin_respuesta', pasoId: 'p1' })
    expect(s2.pendiente).toBeNull()
    expect(estadoUi(s2.ot!.pasos[0], s2)).toBe('sin_senal')
  })

  it('a verdict for the pending step over the stream clears pendiente', () => {
    const s = correr(enP1, { tipo: 'hecho_enviado', pasoId: 'p1' }, { tipo: 'evento', evento: ev(3, { paso_id: 'p1', estado: 'en_conflicto', capa: 3 }) })
    expect(s.pendiente).toBeNull()
  })
})

describe('what the voice says', () => {
  const o = ot('p1', [paso('p1'), paso('p2')])

  it('a skip is said as a plain sentence naming the skipped step', () => {
    expect(textoParaVoz(saltoDeP1(1), o)).toBe('Oye, te saltaste el paso 1: Paso 1. Hazlo antes de seguir.')
  })

  it('a lost control names the step that came undone', () => {
    expect(textoParaVoz(error(1, { detalle: 'CONTROL PERDIDO: «Paso 1» se deshizo.', evidencia: { tipo: 'control', paso: 'p1', clave: 'control:p1' } }), o)).toBe(
      'Oye, se deshizo el paso 1: Paso 1. Vuelve a dejarlo como estaba.',
    )
  })

  it('a shouted detail is said in sentence case', () => {
    expect(textoParaVoz(error(1, { detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.' }), o)).toBe(
      'Guarda abierta con energía viva. Detener y aislar la energía antes de continuar.',
    )
    expect(textoParaVoz(error(2, { detalle: 'el operario declaró «hecho» y reed_bloqueo = abierto' }), o)).toBe(
      'el operario declaró «hecho» y reed_bloqueo = abierto',
    )
  })

  it('the phrases known ahead are the ones textoParaVoz says: a skip on every step, a lost control only on critical controls', () => {
    const conControl = ot('p1', [paso('p2', 'no_verificado', { control_critico: true }), paso('p1')])
    const frases = frasesDeLaOt(conControl)
    expect(frases).toEqual([
      textoParaVoz(saltoDeP1(1), conControl),
      'Oye, te saltaste el paso 2: Paso 2. Hazlo antes de seguir.',
      textoParaVoz(error(2, { evidencia: { tipo: 'control', paso: 'p2', clave: 'control:p2' } }), conControl),
    ])
    expect(frasesDeLaOt(ot('p1', []))).toEqual([])
  })
})

describe('Alto: the capa 1 safety alert', () => {
  const guarda = { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: 'seguridad:GUARDA ABIERTA' }

  it('is a capa 1 safety alert', () => {
    expect(esAlto(error(1, { evidencia: guarda }))).toBe(true)
  })

  it('is not a skip, a lost control, a capa 1 step verdict or a signal alert', () => {
    expect(esAlto(saltoDeP1(1))).toBe(false)
    expect(esAlto(error(2, { evidencia: { tipo: 'control', paso: 'p1', clave: 'control:p1' } }))).toBe(false)
    expect(esAlto(error(3, { tipo: 'veredicto', paso_id: 'p1', evidencia: { tipo: 'sensor' } }))).toBe(false)
    expect(esAlto(error(4, { capa: 2, evidencia: { clave: 'seguridad:x' } }))).toBe(false)
  })
})

it('relevoPendiente is the last handover not yet received', () => {
  const entregado = ev(1, { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen', ts: 'T1' })
  expect(relevoPendiente([ev(0), entregado])).toEqual({ resumen: 'resumen', entregado_por: 'operario:1', ts: 'T1' })
  expect(relevoPendiente([entregado, ev(2, { tipo: 'relevo_recibido', actor: 'operario:2' })])).toBeNull()
  expect(relevoPendiente([])).toBeNull()
})

it('avance counts every verified step, by evidence or by a person', () => {
  expect(avance(ot('p3', [paso('p1', 'verificado'), paso('p2', 'verificado', { evidencia: { tipo: 'persona' } }), paso('p3', 'en_conflicto')]))).toEqual({ hechos: 2, total: 3 })
})

it('cerradoPor names who confirmed a step against the evidence, latest first', () => {
  const persona = (id: number, actor: string) => ev(id, { paso_id: 'p2', estado: 'verificado', actor, evidencia: { tipo: 'persona', motivo: 'lo vi' } })
  const bitacora = [persona(1, 'operario:1'), persona(2, 'supervisor:1'), ev(3, { paso_id: 'p1', estado: 'verificado' })]
  expect(cerradoPor(bitacora, 'p2')).toBe('supervisor:1')
  expect(cerradoPor(bitacora, 'p1')).toBeNull()
})

it('contarCierre counts confirmations by a person and warnings', () => {
  const bitacora = [
    ev(1, { paso_id: 'p2', estado: 'verificado', evidencia: { tipo: 'persona' } }),
    error(2),
    ev(3, { estado: 'en_conflicto' }),
    ev(4, { estado: 'verificado' }),
    ev(5, { tipo: 'alerta_resuelta' }),
  ]
  expect(contarCierre(bitacora)).toEqual({ confirmados: 1, avisos: 2 })
})
