import type { EstadoOt, OtResumen, PasoEstado } from '../api/tipos'
import { avanceDe, estadoDe, porPrioridad, puedeAsignarse } from './estados'

const resumen = (extra: Partial<OtResumen>): OtResumen => ({
  ot: 'ot-1',
  pauta: 'pauta',
  version: 1,
  equipo: 'CT-01',
  abierta_en: '2026-11-21T00:00:00Z',
  paso_actual: 'p1',
  completa: false,
  ...extra,
})

const paso = (id: string, orden: number, estado: PasoEstado['estado']): PasoEstado => ({
  id,
  orden,
  titulo: `Paso ${orden}`,
  estado,
  control_critico: false,
  capa: null,
  evidencia: null,
  detalle: null,
})

it('uses the estado_general the API sends', () => {
  expect(estadoDe(resumen({ estado_general: 'entregada', operador: null }))).toBe('entregada')
})

it('falls back when the real API sends no estado_general', () => {
  expect(estadoDe(resumen({}))).toBe('sin_asignar')
  expect(estadoDe(resumen({ operador: 'operario:1' }))).toBe('asignada')
  expect(estadoDe(resumen({ completa: true }))).toBe('completa')
})

it('counts every verified step as closed, by evidence or by a person', () => {
  const estado: EstadoOt = {
    pauta: 'Cambio de rodillo v1',
    equipo: 'CT-01',
    paso_actual: 'p3',
    completa: false,
    pasos: [paso('p1', 1, 'verificado'), paso('p2', 2, 'verificado'), paso('p3', 3, 'en_conflicto'), paso('p4', 4, 'no_verificado')],
    verificados: ['p1'],
    en_conflicto: ['p3'],
    pendientes: ['p4'],
  }
  expect(avanceDe(estado)).toEqual({ cerrados: 2, total: 4, nombre: 'Cambio de rodillo v1', pasoActual: '3. Paso 3' })
})

it('puts what needs the supervisor first', () => {
  const ots = [
    { ot: 'ot-3', estado: 'completa' as const },
    { ot: 'ot-1', estado: 'asignada' as const },
    { ot: 'ot-2', estado: 'entregada' as const },
    { ot: 'ot-4', estado: 'sin_asignar' as const },
  ]
  expect(porPrioridad(ots).map((o) => o.ot)).toEqual(['ot-2', 'ot-4', 'ot-1', 'ot-3'])
})

it('only unassigned and handed-over OTs can be assigned', () => {
  expect(puedeAsignarse('sin_asignar')).toBe(true)
  expect(puedeAsignarse('entregada')).toBe(true)
  expect(puedeAsignarse('asignada')).toBe(false)
  expect(puedeAsignarse('en_ejecucion')).toBe(false)
  expect(puedeAsignarse('completa')).toBe(false)
})
