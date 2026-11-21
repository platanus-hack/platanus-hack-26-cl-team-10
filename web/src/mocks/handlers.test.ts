// Los handlers del mock, de punta a punta con MSW en Node: lo mismo que corre en el navegador.

import { setupServer } from 'msw/node'
import { crearCliente, urlStream } from '../api/cliente'
import type { MensajeStream } from '../api/tipos'
import { PAUTA_DEMO } from './pauta'
import { ESCENARIOS, type Temporizador } from './escenarios'
import { crearHandlers } from './handlers'
import { Mundo } from './mundo'

const BASE = 'https://api.mock'
const pauta = PAUTA_DEMO
const t: Temporizador = (ms, fn) => {
  setTimeout(fn, ms)
}

let m: Mundo
const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
beforeEach(() => {
  m = new Mundo(pauta)
  ESCENARIOS.feliz!.preparar(m)
  server.resetHandlers(...crearHandlers(m, ESCENARIOS.feliz!, t, BASE))
})

const api = () => crearCliente(BASE)

it('serves the OT list, the state and the pauta', async () => {
  expect((await api().listarOts()).map((o) => o.ot)).toEqual(['ot-12', 'ot-13', 'ot-14'])
  expect((await api().leerOt('ot-12')).paso_actual).toBe('p1')
  expect((await api().leerPauta('pauta-correa-ct-01', 1)).pasos).toHaveLength(6)
})

it('answers 404 for an unknown OT', async () => {
  await expect(api().leerOt('ot-99')).rejects.toMatchObject({ status: 404, tipo: 'no_existe' })
})

it('declarar verifies the current step and refuses a complete OT', async () => {
  for (let i = 0; i < 6; i++) await api().declarar('ot-12', 'operario:1', 'hecho')
  expect((await api().leerOt('ot-12')).completa).toBe(true)
  await expect(api().declarar('ot-12', 'operario:1', 'hecho')).rejects.toMatchObject({ status: 409, regla: 'la pauta ya está completa' })
})

it('confirmar closes the current step on a person word and keeps who and why', async () => {
  const r = await api().confirmarPaso('ot-12', 'p1', 'operario:1', 'el reed está dañado; el candado está puesto')
  expect(r).toMatchObject({ paso: 'p1', estado: 'verificado', capa: null, interrumpe: false })
  const p1 = (await api().leerOt('ot-12')).pasos[0]
  expect(p1).toMatchObject({ estado: 'verificado', evidencia: { tipo: 'persona', motivo: 'el reed está dañado; el candado está puesto' } })
  expect((await api().leerOt('ot-12')).paso_actual).toBe('p2')
})

it('confirmar follows the API rules', async () => {
  const confirmar = (paso: string, actor = 'operario:1', motivo = 'lo vi') => api().confirmarPaso('ot-12', paso, actor, motivo)
  await expect(confirmar('p3')).rejects.toMatchObject({ status: 409, regla: 'solo se confirma el paso en curso (p1): el orden lo impone la app' })
  await expect(confirmar('p1', 'sistema')).rejects.toMatchObject({ status: 409, regla: 'un paso lo confirma una persona, no el sistema' })
  await expect(confirmar('p1', 'operario:1', '   ')).rejects.toMatchObject({ status: 409, regla: 'confirmar contra la evidencia necesita un motivo' })
  await expect(confirmar('p9')).rejects.toMatchObject({ status: 404 })
  for (const p of ['p1', 'p2', 'p3', 'p4', 'p5']) await confirmar(p)
  await expect(confirmar('p6')).rejects.toMatchObject({ status: 409, regla: '«Prueba de detención» es de confirmación: se cierra declarando' })
})

it('declarar with the step the screen showed does not judge the next one', async () => {
  m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', paso_id: 'p1', estado: 'verificado', capa: 1, detalle: 'ok' })
  const r = await api().declarar('ot-12', 'operario:1', 'hecho', 'p1')
  expect(r).toMatchObject({ paso: 'p1', estado: 'verificado' })
  expect((await api().leerOt('ot-12')).pasos[1].estado).toBe('no_verificado')
})

it('handover clears the operator and receiving assigns the new one', async () => {
  await api().declarar('ot-12', 'operario:1', 'hecho')
  const { resumen } = await api().entregarTurno('ot-12', 'operario:1')
  expect(resumen).toContain('Retomar desde p2')
  expect((await api().listarOts())[0]).toMatchObject({ operador: null, estado_general: 'entregada' })
  await api().recibirTurno('ot-12', 'operario:2')
  expect((await api().listarOts())[0].operador).toBe('operario:2')
})

it('opening a session starts the timers of the current step', async () => {
  vi.useFakeTimers()
  try {
    await api().abrirSesion('ot-12', 'edge-1', 'operario:1')
    await vi.advanceTimersByTimeAsync(4000)
    expect(m.estado('ot-12').pasos[0].estado).toBe('verificado')
  } finally {
    vi.useRealTimers()
  }
})

it('each step that becomes current starts its own timers, once a session is open', async () => {
  vi.useFakeTimers()
  try {
    await api().abrirSesion('ot-12', 'edge-1', 'operario:1')
    await vi.advanceTimersByTimeAsync(4000)
    await vi.advanceTimersByTimeAsync(4000)
    expect(m.estado('ot-12').pasos.slice(0, 2).map((p) => p.estado)).toEqual(['verificado', 'verificado'])
    // ot-13 no tiene sesión: sus pasos no avanzan solos.
    m.agregar('ot-13', { tipo: 'veredicto', actor: 'sistema', paso_id: 'p1', estado: 'verificado', capa: 1, detalle: 'ok' })
    await vi.advanceTimersByTimeAsync(10_000)
    expect(m.estado('ot-13').pasos[1].estado).toBe('no_verificado')
  } finally {
    vi.useRealTimers()
  }
})

it('fails every request while the API is down', async () => {
  m.caido = true
  await expect(api().listarOts()).rejects.toMatchObject({ status: 0, tipo: 'red' })
})

function abrir(otId: string, desde = 0) {
  const ws = new WebSocket(urlStream(BASE, otId, desde))
  const mensajes: MensajeStream[] = []
  const cerrado = new Promise<number>((resolve) => ws.addEventListener('close', (e) => resolve(e.code)))
  ws.addEventListener('message', (e) => mensajes.push(JSON.parse(String(e.data))))
  return { ws, mensajes, cerrado }
}

const hasta = async (cond: () => boolean) => {
  for (let i = 0; i < 50 && !cond(); i++) await new Promise((r) => setTimeout(r, 10))
  expect(cond()).toBe(true)
}

it('the stream sends the snapshot from desde, then every new event', async () => {
  m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', detalle: 'ok', paso_id: 'p1', estado: 'verificado', capa: 1 })
  const { ws, mensajes } = abrir('ot-12', 1)
  await hasta(() => mensajes.length === 1)
  const snap = mensajes[0]
  expect(snap.tipo === 'snapshot' && snap.bitacora.map((e) => e.tipo)).toEqual(['veredicto'])
  m.agregar('ot-12', { tipo: 'alerta', actor: 'sistema', detalle: 'GUARDA', estado: 'en_conflicto', capa: 1 })
  await hasta(() => mensajes.length === 3)
  expect(mensajes.slice(1).map((x) => x.tipo)).toEqual(['evento', 'calificacion_ot'])
  ws.close()
})

it('the stream closes with 4404 for an unknown OT', async () => {
  const { cerrado } = abrir('ot-99')
  expect(await cerrado).toBe(4404)
})

it('going down closes the open streams', async () => {
  const { mensajes, cerrado } = abrir('ot-12')
  await hasta(() => mensajes.length === 1)
  m.caido = true
  expect(await cerrado).not.toBe(4404)
})

it('asignar gives an unassigned OT to an operator', async () => {
  const r = await api().asignar('ot-14', 'operario:1')
  expect(r).toMatchObject({ ot: 'ot-14', operador: 'operario:1', estado_general: 'asignada' })
  expect((await api().listarOts()).find((o) => o.ot === 'ot-14')?.operador).toBe('operario:1')
})

it('asignar reassigns a handed-over OT', async () => {
  await api().entregarTurno('ot-12', 'operario:1')
  const r = await api().asignar('ot-12', 'operario:2')
  expect(r).toMatchObject({ operador: 'operario:2' })
  expect(r.estado_general).not.toBe('entregada')
})

it('asignar refuses an OT that already has an operator, an unknown operator and an unknown OT', async () => {
  await expect(api().asignar('ot-12', 'operario:2')).rejects.toMatchObject({ status: 409, regla: 'la OT ya tiene operador' })
  await expect(api().asignar('ot-14', 'supervisor:1')).rejects.toMatchObject({ status: 409, regla: 'el operador no existe' })
  await expect(api().asignar('ot-99', 'operario:1')).rejects.toMatchObject({ status: 404 })
})

it('asignar answers 409, not 500, to a body without operator, and names a complete OT', async () => {
  const r = await fetch(`${BASE}/ot/ot-14/asignar`, { method: 'POST', body: 'null', headers: { 'content-type': 'application/json' } })
  expect(r.status).toBe(409)
  for (const p of pauta.pasos) m.agregar('ot-14', { tipo: 'veredicto', actor: 'sistema', paso_id: p.id, estado: 'verificado', detalle: 'ok' })
  await expect(api().asignar('ot-14', 'operario:1')).rejects.toMatchObject({ status: 409, regla: 'la OT ya está completa' })
})
