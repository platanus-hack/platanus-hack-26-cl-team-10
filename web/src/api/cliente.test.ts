import { crearCliente, urlStream } from './cliente'

const json = (cuerpo: unknown, status = 200) =>
  new Response(JSON.stringify(cuerpo), { status, headers: { 'content-type': 'application/json' } })

it('maps 409 to ApiError regla', async () => {
  const c = crearCliente('https://x', async () => json({ regla: 'la pauta ya está completa' }, 409))
  await expect(c.declarar('ot-1', 'operario:1', 'hecho')).rejects.toMatchObject({
    status: 409,
    tipo: 'regla',
    regla: 'la pauta ya está completa',
  })
})

it('maps 404 to ApiError no_existe', async () => {
  const c = crearCliente('https://x', async () => json({ no_existe: 'OT ot-9' }, 404))
  await expect(c.leerOt('ot-9')).rejects.toMatchObject({ status: 404, tipo: 'no_existe' })
})

it('maps a network failure to tipo red', async () => {
  const c = crearCliente('https://x', async () => {
    throw new TypeError('Failed to fetch')
  })
  await expect(c.leerOt('ot-1')).rejects.toMatchObject({ status: 0, tipo: 'red' })
})

it('times out declarar after 10 s', async () => {
  vi.useFakeTimers()
  try {
    const c = crearCliente('https://x', (_url, init) =>
      new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
      }),
    )
    const promesa = c.declarar('ot-1', 'operario:1', 'hecho')
    const resultado = expect(promesa).rejects.toMatchObject({ status: 0, tipo: 'timeout' })
    await vi.advanceTimersByTimeAsync(10_000)
    await resultado
  } finally {
    vi.useRealTimers()
  }
})

it('sends actor as query on relevo', async () => {
  const urls: string[] = []
  const c = crearCliente('https://x', async (url) => {
    urls.push(String(url))
    return json({ resumen: 'r' })
  })
  await c.entregarTurno('ot-1', 'operario:1')
  expect(urls[0]).toBe('https://x/ot/ot-1/relevo/entregar?actor=operario%3A1')
})

it('posts the declaration body as JSON', async () => {
  let cuerpo: unknown = null
  const c = crearCliente('https://x', async (_url, init) => {
    cuerpo = JSON.parse(String(init?.body))
    return json({ paso: 'p1', estado: 'verificado', capa: 1, detalle: 'ok', interrumpe: false })
  })
  const r = await c.declarar('ot-1', 'operario:1', 'hecho')
  expect(cuerpo).toEqual({ actor: 'operario:1', texto: 'hecho' })
  expect(r.estado).toBe('verificado')
})

it('builds the stream url', () => {
  expect(urlStream('https://34-176-44-192.sslip.io', 'ot-1', 7)).toBe(
    'wss://34-176-44-192.sslip.io/ot/ot-1/stream?desde=7',
  )
  expect(urlStream('http://localhost:8000', 'ot-1', 0)).toBe('ws://localhost:8000/ot/ot-1/stream?desde=0')
})

it('posts the operator and who assigns to asignar', async () => {
  const pedidos: { url: string; metodo?: string; cuerpo: unknown }[] = []
  const c = crearCliente('https://x', async (url, init) => {
    pedidos.push({ url: String(url), metodo: init?.method, cuerpo: JSON.parse(String(init?.body)) })
    return json({ ot: 'ot-1', operador: 'operario:2', estado_general: 'asignada' })
  })
  const r = await c.asignar('ot-1', 'operario:2', 'supervisor:1')
  expect(pedidos).toEqual([
    { url: 'https://x/ot/ot-1/asignar', metodo: 'POST', cuerpo: { operador: 'operario:2', actor: 'supervisor:1' } },
  ])
  expect(r.operador).toBe('operario:2')
})

it('confirms a step with actor and motivo', async () => {
  const pedidos: { url: string; cuerpo: unknown }[] = []
  const c = crearCliente('https://x', async (url, init) => {
    pedidos.push({ url: String(url), cuerpo: JSON.parse(String(init?.body)) })
    return json({ paso: 'p1', estado: 'verificado', capa: null, detalle: 'ok', interrumpe: false })
  })
  const r = await c.confirmarPaso('ot-1', 'p1', 'operario:1', 'el reed está dañado; el candado está puesto')
  expect(pedidos).toEqual([
    { url: 'https://x/ot/ot-1/pasos/p1/confirmar', cuerpo: { actor: 'operario:1', motivo: 'el reed está dañado; el candado está puesto' } },
  ])
  expect(r.estado).toBe('verificado')
})

it('declarar sends the step the screen was showing', async () => {
  let cuerpo: unknown = null
  const c = crearCliente('https://x', async (_url, init) => {
    cuerpo = JSON.parse(String(init?.body))
    return json({ paso: 'p6', estado: 'verificado', capa: null, detalle: 'ok', interrumpe: false })
  })
  await c.declarar('ot-1', 'operario:1', 'hecho', 'p6')
  expect(cuerpo).toEqual({ actor: 'operario:1', texto: 'hecho', paso_id: 'p6' })
})
