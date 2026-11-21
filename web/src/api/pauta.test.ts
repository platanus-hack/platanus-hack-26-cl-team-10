import { PAUTA_DEMO, PAUTA_LOTO } from '../mocks/pauta'
import { cierraSolo, pideHecho, sePuedeConfirmar } from './pauta'

const paso = (pauta: typeof PAUTA_DEMO, id: string) => pauta.pasos.find((p) => p.id === id)!

it('sensor steps and camera steps with a detection close on their own', () => {
  expect(cierraSolo(paso(PAUTA_DEMO, 'p1'))).toBe(true)
  expect(cierraSolo(paso(PAUTA_LOTO, 'l2'))).toBe(true)
  expect(PAUTA_LOTO.pasos.every(cierraSolo)).toBe(true)
})

it('confirmation steps and camera steps without a detection need «Hecho»', () => {
  expect(pideHecho(paso(PAUTA_DEMO, 'p3'))).toBe(true)
  expect(pideHecho(paso(PAUTA_DEMO, 'p6'))).toBe(true)
  expect(pideHecho(paso(PAUTA_DEMO, 'p1'))).toBe(false)
})

it('a confirmation step cannot be confirmed against the evidence', () => {
  expect(sePuedeConfirmar(paso(PAUTA_DEMO, 'p6'))).toBe(false)
  expect(sePuedeConfirmar(paso(PAUTA_DEMO, 'p3'))).toBe(true)
})
