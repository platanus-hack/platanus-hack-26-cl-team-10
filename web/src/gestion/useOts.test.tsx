import { act, renderHook } from '@testing-library/react'
import { api } from '../api/cliente'
import type { OtResumen } from '../api/tipos'
import { useOts } from './useOts'

afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

const ot = (id: string): OtResumen => ({
  ot: id, pauta: 'p', version: 1, equipo: 'CT-01', abierta_en: '', paso_actual: null, completa: false, operador: null, estado_general: 'sin_asignar',
})

it('reports a timeout when the API hangs, instead of loading forever', async () => {
  vi.useFakeTimers()
  vi.spyOn(api, 'listarOts').mockReturnValue(new Promise(() => {}))
  const { result } = renderHook(() => useOts(60_000, 100))
  await act(() => vi.advanceTimersByTimeAsync(150))
  expect(result.current.ots).toBeNull()
  expect(result.current.error).toBe('La API no respondió a tiempo')
})

it('keeps the newest answer when an older one arrives late', async () => {
  let soltarVieja: (v: OtResumen[]) => void = () => {}
  vi.spyOn(api, 'listarOts')
    .mockReturnValueOnce(new Promise((r) => (soltarVieja = r)))
    .mockResolvedValueOnce([ot('nueva')])
  vi.spyOn(api, 'leerOt').mockRejectedValue(new Error('sin avance'))
  vi.spyOn(api, 'listarPautas').mockRejectedValue(new Error('sin nombres'))
  const { result } = renderHook(() => useOts(60_000, 60_000))
  await act(async () => {
    await Promise.resolve()
    await result.current.recargar()
  })
  await act(async () => soltarVieja([ot('vieja')]))
  expect(result.current.ots?.map((o) => o.ot)).toEqual(['nueva'])
  expect(result.current.ots?.[0].avance).toBeNull()
})
