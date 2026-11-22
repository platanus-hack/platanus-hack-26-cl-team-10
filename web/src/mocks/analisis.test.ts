// El reporte, las mejoras y las métricas del mock, con las reglas de app/reporte.py, app/mejora.py y app/metricas.py.

import { mejorasDe, metricasDe, reporteDe } from './analisis'
import { cerrarSolo, declararFeliz, ESCENARIOS, salto, type Temporizador } from './escenarios'
import { Mundo } from './mundo'
import { PAUTA_DEMO } from './pauta'

const nombreDe = (id: string) => ({ 'operario:1': 'Ana Rojas', 'operario:2': 'Bruno Díaz' })[id] ?? id

function mundo() {
  const m = new Mundo(PAUTA_DEMO)
  m.crearOt('ot-1', 'operario:1')
  m.crearOt('ot-2', 'operario:2')
  m.crearOt('ot-3', null)
  return m
}

/** El operario hace un paso posterior antes del control crítico y después lo corrige. */
function desviar(m: Mundo, otId: string) {
  const s = salto(m.pauta)!
  m.saltar(otId, s.pendiente, s.adelantado)
  cerrarSolo(m, otId, s.pendiente)
  return s
}

describe('mejoras', () => {
  it('one OT that deviates is not a proposal', () => {
    const m = mundo()
    desviar(m, 'ot-1')
    expect(mejorasDe(m)).toEqual([])
  })

  it('the same step deviating in two OTs is a proposal, by step and never by person', () => {
    const m = mundo()
    const { adelantado } = desviar(m, 'ot-1')
    desviar(m, 'ot-2')

    const [p, ...resto] = mejorasDe(m)
    expect(resto).toEqual([])
    expect(p).toMatchObject({
      id: `${m.pauta.id}:v${m.pauta.version}:${adelantado.id}`,
      paso: adelantado.id,
      titulo: adelantado.titulo,
      ejecuciones: 3,
      ots_con_senal: 2,
      operarios_distintos: 2,
      estado: 'abierta',
      revision: null,
    })
    expect(p.senales.orden).toBe(2)
    expect(p.motivo).toBe(`«${adelantado.titulo}» tuvo señales en 2 de 3 OT de la versión ${m.pauta.version}, con 2 operarios distintos`)
    expect(p.sugerencia).toMatch(/^El paso se hace antes de su turno/)
    expect(JSON.stringify(p)).not.toMatch(/operario:|Ana|Bruno/)
  })

  it('a review stays on the proposal, and the last one wins', () => {
    const m = mundo()
    desviar(m, 'ot-1')
    desviar(m, 'ot-2')
    const id = mejorasDe(m)[0].id

    m.revisar(id, 'descartar', 'ya se corrigió en terreno', 'supervisor:oculta')
    expect(mejorasDe(m)[0]).toMatchObject({ estado: 'descartada', revision: { decision: 'descartar', nota: 'ya se corrigió en terreno', por: 'supervisor:oculta' } })
    m.revisar(id, 'aceptar', '', 'supervisor:oculta')
    expect(mejorasDe(m)[0].estado).toBe('aceptada')
  })
})

describe('reporte', () => {
  it('says what closed each step, and how long a deviation stayed open', () => {
    const m = mundo()
    const { pendiente, adelantado } = desviar(m, 'ot-1')
    const r = reporteDe(m, 'ot-1', nombreDe)

    expect(r.personas).toMatchObject({ a_cargo: 'Ana Rojas' })
    const cerrado = r.pasos.find((p) => p.paso === pendiente.id)!
    expect(cerrado).toMatchObject({ estado: 'verificado', intentos: 1, cerrado_con: { con: 'sensor', sensor: pendiente.sensor!.id, leido: pendiente.sensor!.espera } })
    expect(r.pasos.find((p) => p.paso === adelantado.id)).toMatchObject({ estado: 'no_verificado', cerrado_con: null })

    expect(r.desviaciones).toHaveLength(1)
    expect(r.desviaciones[0]).toMatchObject({ clase: 'orden', que: 'Orden invertido', paso: adelantado.id })
    expect(r.desviaciones[0].resuelta).not.toBeNull()
    expect(r.resultado).toMatchObject({ sin_desviaciones: false, desviaciones: 1, pasos_verificados: 1, pasos: m.pauta.pasos.length })
    expect(r.pendientes).toContain(adelantado.id)
    expect(r.eventos.total).toBe(m.eventos('ot-1').length)
  })

  it('a complete OT with no deviations says so, with its duration', () => {
    const m = mundo()
    for (const paso of m.pauta.pasos) declararFeliz(m, 'ot-1', paso, 'operario:1')
    const r = reporteDe(m, 'ot-1', nombreDe)

    expect(r.completa).toBe(true)
    expect(r.resultado).toMatchObject({ sin_desviaciones: true, desviaciones: 0, pasos_verificados: m.pauta.pasos.length })
    expect(r.pendientes).toEqual([])
    expect(r.tiempos.fin).not.toBeNull()
    expect(r.tiempos.minutos_de_ejecucion).not.toBeNull()
    expect(r.personas.ejecutaron).toEqual(['Ana Rojas'])
  })
})

describe('métricas', () => {
  it('counts complete OTs with no deviations, what closed the steps and the open proposals', () => {
    const m = mundo()
    for (const paso of m.pauta.pasos) declararFeliz(m, 'ot-1', paso, 'operario:1')
    desviar(m, 'ot-2')
    desviar(m, 'ot-3')
    const k = metricasDe(m)

    expect(k.ots.total).toBe(3)
    expect(k.cumplimiento).toEqual({ completas: 1, sin_desviaciones: 1, porcentaje: 100 })
    expect(k.pasos.verificados).toBe(m.pauta.pasos.length + 2)
    expect(k.desviaciones.por_clase.orden).toBe(2)
    expect(k.mejoras.abierta).toBe(1)
  })
})

describe('el escenario «mejora»', () => {
  it('the proposal is born while the supervisor watches, when the second OT deviates; then the OT finishes', () => {
    const m = new Mundo(PAUTA_DEMO)
    const e = ESCENARIOS.mejora!
    e.preparar(m)
    const cola: Array<() => void> = []
    const t: Temporizador = (_ms, fn) => void cola.push(fn)
    m.alCambiarPaso = (otId, paso) => {
      if (m.sesionDe(otId)) e.alAvanzar?.(m, otId, paso, t)
    }
    e.alIniciar?.(m, t)
    expect(mejorasDe(m)).toEqual([])

    cola.shift()!()
    expect(mejorasDe(m)).toHaveLength(1)
    expect(m.alertasActivas('ot-13')).toHaveLength(1)

    while (cola.length) cola.shift()!()
    expect(m.alertasActivas('ot-13')).toEqual([])
    expect(m.estado('ot-13').completa).toBe(true)
  })
})
