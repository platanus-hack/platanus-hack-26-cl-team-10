import type { EstadoPasoApi, MensajeStream } from '../api/tipos'
import { PAUTA_DEMO } from './pauta'
import { Mundo } from './mundo'

const pauta = PAUTA_DEMO

function nuevo() {
  const m = new Mundo(pauta)
  m.crearOt('ot-1', 'operario:1')
  return m
}

const veredicto = (m: Mundo, paso_id: string, estado: EstadoPasoApi, capa: number | null = 1) =>
  m.agregar('ot-1', { tipo: 'veredicto', actor: 'sistema', detalle: `${paso_id} ${estado}`, paso_id, estado, capa, declarado: null, evidencia: null })

const alerta = (m: Mundo) =>
  m.agregar('ot-1', { tipo: 'alerta', actor: 'sistema', detalle: 'GUARDA ABIERTA', paso_id: null, estado: 'en_conflicto', capa: 1, declarado: null, evidencia: null })

it('starts at the first step with an ot_abierta event', () => {
  const m = nuevo()
  expect(m.estado('ot-1').paso_actual).toBe('p1')
  expect(m.snapshot('ot-1', 0).bitacora.map((e) => e.tipo)).toEqual(['ot_abierta'])
})

it('sobrescrito counts as closed for paso_actual', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'verificado')
  m.agregar('ot-1', { tipo: 'sobrescritura', actor: 'operario:1', detalle: 'dice que lo hizo', paso_id: 'p2', estado: 'sobrescrito', capa: null, declarado: null, evidencia: null })
  const e = m.estado('ot-1')
  expect(e.paso_actual).toBe('p3')
  expect(e.pasos[1].estado).toBe('sobrescrito')
})

it('the last verdict of a step wins', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'en_conflicto')
  veredicto(m, 'p1', 'verificado')
  expect(m.estado('ot-1').pasos[0]).toMatchObject({ estado: 'verificado', detalle: 'p1 verificado', capa: 1 })
})

it('is complete when every step is closed', () => {
  const m = nuevo()
  for (const p of pauta.pasos) veredicto(m, p.id, 'verificado')
  expect(m.estado('ot-1')).toMatchObject({ completa: true, paso_actual: null })
})

it('alerta_resuelta removes the alert', () => {
  const m = nuevo()
  const a = alerta(m)
  expect(m.alertasActivas('ot-1').map((e) => e.id)).toEqual([a.id])
  m.agregar('ot-1', { tipo: 'alerta_resuelta', actor: 'sistema', detalle: 'normalizada', paso_id: null, estado: null, capa: 1, declarado: null, evidencia: { resuelve: a.id } })
  expect(m.alertasActivas('ot-1')).toEqual([])
})

it('an alert overwrite removes the alert', () => {
  const m = nuevo()
  const a = alerta(m)
  m.agregar('ot-1', { tipo: 'sobrescritura', actor: 'operario:1', detalle: 'ya lo corrigió', paso_id: null, estado: null, capa: null, declarado: null, evidencia: { alerta_id: a.id } })
  expect(m.alertasActivas('ot-1')).toEqual([])
})

it('publishes evento then calificacion_ot', () => {
  const m = nuevo()
  const recibidos: MensajeStream[] = []
  m.suscribir('ot-1', (msg) => recibidos.push(msg))
  alerta(m)
  expect(recibidos.map((r) => r.tipo)).toEqual(['evento', 'calificacion_ot'])
  const c = recibidos[1]
  expect(c.tipo === 'calificacion_ot' && c.calificacion.nivel).toBe('error')
})

it('grades the OT by its worst live part, errors first', () => {
  const m = nuevo()
  expect(m.calificacion('ot-1')).toEqual({ nivel: 'ok', certeza: 1, capa: null, motivos: ['sin nada que calificar'], avisos: [] })
  veredicto(m, 'p1', 'verificado')
  veredicto(m, 'p3', 'en_conflicto', 3)
  alerta(m)
  const c = m.calificacion('ot-1')
  expect(c.nivel).toBe('error')
  expect(c.avisos.map((a) => a.nivel)).toEqual(['error', 'warning'])
})

it('snapshot honours desde', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'verificado')
  const ultimo = veredicto(m, 'p2', 'verificado')
  expect(m.snapshot('ot-1', ultimo.id - 1).bitacora.map((e) => e.id)).toEqual([ultimo.id])
})

it('calls alCambiarPaso when the current step moves', () => {
  const m = nuevo()
  const vistos: string[] = []
  m.alCambiarPaso = (_ot, paso) => vistos.push(paso.id)
  veredicto(m, 'p1', 'en_conflicto')
  veredicto(m, 'p1', 'verificado')
  expect(vistos).toEqual(['p2'])
})

it('derives the general state of each OT', () => {
  const m = nuevo()
  m.crearOt('ot-2', null)
  const general = (id: string) => m.resumenes().find((r) => r.ot === id)?.estado_general
  expect(general('ot-1')).toBe('asignada')
  expect(general('ot-2')).toBe('sin_asignar')
  veredicto(m, 'p1', 'verificado')
  expect(general('ot-1')).toBe('en_ejecucion')
  m.agregar('ot-1', { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen', paso_id: null, estado: null, capa: null, declarado: null, evidencia: null })
  m.asignar('ot-1', null)
  expect(general('ot-1')).toBe('entregada')
  m.asignar('ot-1', 'operario:2')
  expect(general('ot-1')).toBe('en_ejecucion')
})

it('lists OTs with the fields of GET /ots', () => {
  const m = nuevo()
  expect(m.resumenes()[0]).toMatchObject({
    ot: 'ot-1',
    pauta: 'pauta-correa-ct-01',
    version: 1,
    equipo: 'correa CT-01',
    paso_actual: 'p1',
    completa: false,
    operador: 'operario:1',
  })
})
