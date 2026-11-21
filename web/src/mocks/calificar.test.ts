import { calificarEvento } from './calificar'

const ev = (tipo: string, capa: number | null, estado: string | null, evidencia: Record<string, unknown> | null = null) =>
  calificarEvento({ tipo, capa, estado, detalle: 'X', evidencia } as Parameters<typeof calificarEvento>[0])

it('capa 1 alert is an error', () => {
  expect(ev('alerta', 1, 'en_conflicto')).toEqual({ nivel: 'error', certeza: 1, capa: 1, motivos: ['X'] })
})

it('capa 2 alert is a warning', () => {
  expect(ev('alerta', 2, 'en_conflicto')?.nivel).toBe('warning')
})

it('alerta_resuelta is ok', () => {
  expect(ev('alerta_resuelta', 1, null)?.nivel).toBe('ok')
})

it('capa 1 verdict: conflict is error, anything else ok', () => {
  expect(ev('veredicto', 1, 'en_conflicto')?.nivel).toBe('error')
  expect(ev('veredicto', 1, 'verificado')?.nivel).toBe('ok')
  expect(ev('veredicto', 1, 'no_verificado')?.nivel).toBe('ok')
})

it('camera conflict is a warning with the judge confidence', () => {
  expect(ev('veredicto', 3, 'en_conflicto', { confianza: 0.62 })).toMatchObject({ nivel: 'warning', certeza: 0.62, capa: 3 })
  expect(ev('veredicto', 3, 'verificado', { confianza: 0.91 })).toMatchObject({ nivel: 'ok', certeza: 0.91 })
})

it('a step closed by a person is ok and says so', () => {
  expect(ev('veredicto', null, 'verificado')).toEqual({
    nivel: 'ok',
    certeza: 1,
    capa: null,
    motivos: ['X', 'lo cerró una persona, no un sensor'],
  })
})

it('an overwrite is a warning', () => {
  expect(ev('sobrescritura', null, 'sobrescrito')?.nivel).toBe('warning')
})

it('other events are not graded', () => {
  expect(ev('declaracion', null, null)).toBeNull()
  expect(ev('relevo_entregado', null, null)).toBeNull()
})
