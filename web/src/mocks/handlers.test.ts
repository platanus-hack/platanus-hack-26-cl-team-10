// Los handlers del mock, de punta a punta con MSW en Node: lo mismo que corre en el navegador.

import { setupServer } from 'msw/node'
import { crearCliente, urlStream } from '../api/cliente'
import type { MensajeStream } from '../api/tipos'
import { PAUTA_DEMO } from './pauta'
import { ESCENARIOS, type Temporizador } from './escenarios'
import { crearHandlers } from './handlers'
import { Mundo } from './mundo'
import { ANA, BRUNO, CLAVE_MOCK, SUPERVISORA, tokenMock } from './personas'
import type { Persona } from '../api/tipos'

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

/** Un cliente con el token del mock de esa persona (la supervisora, si no se dice). */
const api = (p: Persona | null = SUPERVISORA, alVencer = () => {}) =>
  crearCliente(BASE, undefined, { token: () => (p ? tokenMock(p.id) : null), alVencer })

it('serves the OT list, the state and the pauta', async () => {
  expect((await api().listarOts()).map((o) => o.ot)).toEqual(['ot-12', 'ot-13', 'ot-14'])
  expect((await api().leerOt('ot-12')).paso_actual).toBe('p1')
  expect((await api().leerPauta('pauta-correa-ct-01', 1)).pasos).toHaveLength(6)
})

it('serves the pautas the company can order, like GET /cliente/pautas', async () => {
  expect(await api().listarPautas()).toEqual([
    {
      id: pauta.id, nombre: pauta.nombre, version: pauta.version, equipo: pauta.equipo, pasos: 6,
      protocolos: [{ id: 'prot-aislamiento-01', nombre: 'Aislamiento y bloqueo de energías' }],
    },
  ])
})

describe('login and the client service', () => {
  it('signs in the Oculta people with the mock clave', async () => {
    const r = await api(null).entrar('Ana.Rojas@oculta.example ', CLAVE_MOCK)
    expect(r).toMatchObject({ token: tokenMock('operario:1'), persona: { id: 'operario:1', nombre: 'Ana Rojas', rol: 'operador' } })
    expect(Date.parse(r.expira)).toBeGreaterThan(Date.now())
    await expect(api(null).entrar(ANA.usuario, 'otra')).rejects.toMatchObject({ status: 401, tipo: 'credenciales' })
    await expect(api(null).entrar('nadie@oculta.example', CLAVE_MOCK)).rejects.toMatchObject({ tipo: 'credenciales' })
  })

  it('without a token the client service answers 401 and closes the session', async () => {
    const alVencer = vi.fn()
    await expect(api(null, alVencer).listarOts()).rejects.toMatchObject({ status: 401, tipo: 'sesion' })
    expect(alVencer).toHaveBeenCalledOnce()
    // Las rutas de la ejecución siguen abiertas, como en el servidor.
    expect((await api(null).leerOt('ot-12')).paso_actual).toBe('p1')
  })

  it('an operator sees only their OTs, and only the supervisor lists operators', async () => {
    expect((await api(ANA).listarOts()).map((o) => o.ot)).toEqual(['ot-12'])
    expect((await api(BRUNO).listarOts()).map((o) => o.ot)).toEqual(['ot-13'])
    expect((await api().listarOperadores()).map((p) => p.nombre)).toEqual(['Ana Rojas', 'Bruno Díaz'])
    await expect(api(ANA).listarOperadores()).rejects.toMatchObject({ status: 403, tipo: 'permiso' })
  })

  it('one OT carries its grading, and another operator\'s OT does not exist', async () => {
    const r = await fetch(`${BASE}/cliente/ots/ot-12`, { headers: { authorization: `Bearer ${tokenMock(ANA.id)}` } })
    expect(await r.json()).toMatchObject({ ot: 'ot-12', calificacion: { nivel: expect.any(String), avisos: [] } })
    const ajena = await fetch(`${BASE}/cliente/ots/ot-13`, { headers: { authorization: `Bearer ${tokenMock(ANA.id)}` } })
    expect(ajena.status).toBe(404)
  })

  it('the list carries the grading of each OT, the same one its detail gives', async () => {
    for (const o of await api().listarOts()) {
      expect(o.calificacion).toEqual((await api().leerOtCliente(o.ot)).calificacion)
    }
  })

  it('anyone in the company reads its people\'s names, without the login user', async () => {
    const personas = await api(ANA).listarPersonas()
    expect(personas).toEqual([
      { id: 'supervisor:oculta', nombre: 'Carla Muñoz', rol: 'supervisor' },
      { id: 'operario:1', nombre: 'Ana Rojas', rol: 'operador' },
      { id: 'operario:2', nombre: 'Bruno Díaz', rol: 'operador' },
    ])
    await expect(api(null).listarPersonas()).rejects.toMatchObject({ status: 401 })
  })

  it('an operator joins their OT to a free station with their token; the session is theirs', async () => {
    expect(await api(ANA).sesionDeEstacion('edge-1')).toBeNull()
    expect(await api(ANA).abrirSesion('ot-12', 'edge-1', 'no importa')).toMatchObject({ ot_id: 'ot-12', edge_id: 'edge-1', operario: 'operario:1' })
    expect(await api(BRUNO).sesionDeEstacion('edge-1')).toMatchObject({ ot_id: 'ot-12', operario: 'operario:1' })
  })

  it('a station running another open OT is taken only when asked', async () => {
    await api(BRUNO).abrirSesion('ot-13', 'edge-1', 'operario:2')
    await expect(api(ANA).abrirSesion('ot-12', 'edge-1', 'operario:1')).rejects.toMatchObject({ status: 409, tipo: 'regla' })
    expect(m.sesionDeEdge('edge-1')?.ot_id).toBe('ot-13')
    expect(await api(ANA).abrirSesion('ot-12', 'edge-1', 'operario:1', true)).toMatchObject({ ot_id: 'ot-12' })
    expect(m.sesionDe('ot-13')).toBeNull()
  })

  it('a station whose OT is already complete is joined without asking', async () => {
    await api(BRUNO).abrirSesion('ot-13', 'edge-1', 'operario:2')
    for (const p of pauta.pasos) m.agregar('ot-13', { tipo: 'veredicto', actor: 'sistema', paso_id: p.id, estado: 'verificado', capa: 1, detalle: 'ok' })
    expect(await api(ANA).abrirSesion('ot-12', 'edge-1', 'operario:1')).toMatchObject({ ot_id: 'ot-12' })
  })

  it('only the operator of an open OT starts its session', async () => {
    await expect(api().abrirSesion('ot-12', 'edge-1', 'x', true)).rejects.toMatchObject({ status: 403, tipo: 'permiso' })
    await expect(api(ANA).abrirSesion('ot-13', 'edge-1', 'x', true)).rejects.toMatchObject({ status: 404, tipo: 'no_existe' })
    await expect(api(null).abrirSesion('ot-12', 'edge-1', 'x', true)).rejects.toMatchObject({ status: 401 })
    for (const p of pauta.pasos) m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', paso_id: p.id, estado: 'verificado', capa: 1, detalle: 'ok' })
    await expect(api(ANA).abrirSesion('ot-12', 'edge-1', 'x', true)).rejects.toMatchObject({ status: 409, regla: 'la OT ot-12 ya está completa' })
    expect(m.sesionDeEdge('edge-1')).toBeNull()
  })

  it('the supervisor orders an OT, which starts unassigned', async () => {
    const r = await api().pedirOt(pauta.id)
    expect(r).toMatchObject({ ot: 'ot-0004', pauta: pauta.id, nombre: pauta.nombre, cliente: 'oculta' })
    expect((await api().listarOts()).find((o) => o.ot === 'ot-0004')).toMatchObject({ estado_general: 'sin_asignar', operador: null })
    await expect(api().pedirOt('pauta-ajena')).rejects.toMatchObject({ status: 403, tipo: 'permiso' })
    await expect(api(ANA).pedirOt(pauta.id)).rejects.toMatchObject({ status: 403 })
  })

  it('signs out with 204', async () => {
    await expect(api().salir()).resolves.toBeNull()
  })
})

it('each OT in the list carries its progress, like GET /ots', async () => {
  await api().declarar('ot-12', 'operario:1', 'hecho')
  expect((await api().listarOts())[0]).toMatchObject({ cerrados: 1, total: 6, entregada_por: null })
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
  expect((await api().listarOts())[0]).toMatchObject({ operador: null, estado_general: 'entregada', entregada_por: 'operario:1' })
  await api().recibirTurno('ot-12', 'operario:2')
  expect((await api().listarOts())[0]).toMatchObject({ operador: 'operario:2', entregada_por: null })
})

it('opening a session starts the timers of the current step', async () => {
  vi.useFakeTimers()
  try {
    await api(ANA).abrirSesion('ot-12', 'edge-1', 'operario:1')
    await vi.advanceTimersByTimeAsync(4000)
    expect(m.estado('ot-12').pasos[0].estado).toBe('verificado')
  } finally {
    vi.useRealTimers()
  }
})

it('each step that becomes current starts its own timers, once a session is open', async () => {
  vi.useFakeTimers()
  try {
    await api(ANA).abrirSesion('ot-12', 'edge-1', 'operario:1')
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

it('asignar gives an unassigned OT to an operator and logs the supervisor of the token', async () => {
  const r = await api().asignar('ot-14', 'operario:1')
  expect(r).toMatchObject({ ot: 'ot-14', operador: 'operario:1', estado_general: 'asignada' })
  expect((await api().listarOts()).find((o) => o.ot === 'ot-14')?.operador).toBe('operario:1')
  expect(m.eventos('ot-14').at(-1)).toMatchObject({
    tipo: 'ot_asignada', actor: 'supervisor:oculta', evidencia: { operador: 'operario:1' }, detalle: 'OT asignada a operario:1',
  })
})

it('asignar reassigns a handed-over OT', async () => {
  await api().entregarTurno('ot-12', 'operario:1')
  const r = await api().asignar('ot-12', 'operario:2')
  expect(r).toMatchObject({ operador: 'operario:2' })
  expect(r.estado_general).not.toBe('entregada')
})

it('asignar refuses an OT with an operator, someone who is not an operator, an unknown OT and an operator', async () => {
  await expect(api().asignar('ot-12', 'operario:2')).rejects.toMatchObject({ status: 409, regla: 'la OT ot-12 ya tiene operador: operario:1' })
  await expect(api().asignar('ot-14', 'supervisor:oculta')).rejects.toMatchObject({ status: 403, message: 'supervisor:oculta no es operador de Oculta' })
  await expect(api().asignar('ot-99', 'operario:1')).rejects.toMatchObject({ status: 404 })
  await expect(api(ANA).asignar('ot-14', 'operario:1')).rejects.toMatchObject({ status: 403, tipo: 'permiso' })
})

it('asignar answers 403, not 500, to a body without operator, and names a complete OT', async () => {
  const r = await fetch(`${BASE}/cliente/ots/ot-14/asignar`, {
    method: 'POST', body: 'null', headers: { 'content-type': 'application/json', authorization: `Bearer ${tokenMock(SUPERVISORA.id)}` },
  })
  expect(r.status).toBe(403)
  for (const p of pauta.pasos) m.agregar('ot-14', { tipo: 'veredicto', actor: 'sistema', paso_id: p.id, estado: 'verificado', detalle: 'ok' })
  await expect(api().asignar('ot-14', 'operario:1')).rejects.toMatchObject({ status: 409, regla: 'la OT ot-14 ya está completa' })
})

it('serves a stand-in camera frame and streams station readings to the OTs a station runs', async () => {
  const r = await fetch(`${BASE}/edge/edge-1/video.mjpg`)
  expect(r.headers.get('content-type')).toBe('image/svg+xml')
  expect(await r.text()).toContain('Cámara de edge-1')

  m.abrirSesion('ot-12', 'edge-1', 'operario:1')
  m.leer('guarda', 'abierta')
  const { ws, mensajes } = abrir('ot-12')
  await hasta(() => mensajes.length === 1)
  expect(mensajes[0]).toMatchObject({ tipo: 'snapshot', sensores: { guarda: 'abierta' } })
  m.leer('energia', 'viva')
  await hasta(() => mensajes.length === 2)
  expect(mensajes[1]).toMatchObject({ tipo: 'lectura', edge_id: 'edge-1', sensor_id: 'energia', valor: 'viva' })
  ws.close()
})
