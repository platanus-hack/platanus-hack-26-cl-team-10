import { act, renderHook, waitFor } from '@testing-library/react'
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

describe('grading for the supervisor', () => {
  const con = (id: string, estado: OtResumen['estado_general'], cerrados = 0): OtResumen => ({ ...ot(id), estado_general: estado, operador: 'operario:1', cerrados, total: 6 })
  const calificacion = { nivel: 'warning' as const, certeza: 0.5, capa: 2, motivos: ['temp alta'], avisos: [] }

  function preparar(lista: () => OtResumen[]) {
    vi.spyOn(api, 'listarOts').mockImplementation(async () => lista())
    vi.spyOn(api, 'listarPautas').mockResolvedValue([])
    return vi.spyOn(api, 'leerOtCliente').mockImplementation(async (id) => ({ ...lista().find((o) => o.ot === id)!, calificacion }))
  }

  it('the operator view asks for no grading', async () => {
    const leer = preparar(() => [con('ot-1', 'en_ejecucion')])
    const { result } = renderHook(() => useOts(60_000, 60_000, null, false))
    await waitFor(() => expect(result.current.ots).not.toBeNull())
    expect(leer).not.toHaveBeenCalled()
    expect(result.current.ots?.[0].calificacion).toBeNull()
  })

  it('grades every OT but the unassigned ones, and asks again only for running or changed ones', async () => {
    let cerradosAsignada = 0
    const leer = preparar(() => [con('ot-run', 'en_ejecucion'), con('ot-asig', 'asignada', cerradosAsignada), con('ot-fin', 'completa'), con('ot-libre', 'sin_asignar')])
    const { result } = renderHook(() => useOts(60_000, 60_000, null, true))
    // La primera carga la hace el hook al montarse.
    await waitFor(() => expect(result.current.ots).not.toBeNull())
    expect(leer.mock.calls.map(([id]) => id).sort()).toEqual(['ot-asig', 'ot-fin', 'ot-run'])
    expect(result.current.ots?.find((o) => o.ot === 'ot-run')?.calificacion?.nivel).toBe('warning')
    expect(result.current.ots?.find((o) => o.ot === 'ot-libre')?.calificacion).toBeNull()

    leer.mockClear()
    await act(async () => {
      await result.current.recargar()
    })
    expect(leer.mock.calls.map(([id]) => id)).toEqual(['ot-run'])

    leer.mockClear()
    cerradosAsignada = 1
    await act(async () => {
      await result.current.recargar()
    })
    expect(leer.mock.calls.map(([id]) => id).sort()).toEqual(['ot-asig', 'ot-run'])
  })

  it('keeps the last grading when asking again fails', async () => {
    const leer = preparar(() => [con('ot-run', 'en_ejecucion')])
    const { result } = renderHook(() => useOts(60_000, 60_000, null, true))
    await waitFor(() => expect(result.current.ots?.[0].calificacion).not.toBeNull())
    leer.mockRejectedValue(new Error('caída'))
    await act(async () => {
      await result.current.recargar()
    })
    expect(result.current.ots?.[0].calificacion?.nivel).toBe('warning')
  })
})
