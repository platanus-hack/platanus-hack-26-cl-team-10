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

it('assigns through the client service: who assigns travels in the token, not the body', async () => {
  const pedidos: { url: string; metodo?: string; cuerpo: unknown }[] = []
  const c = crearCliente('https://x', async (url, init) => {
    pedidos.push({ url: String(url), metodo: init?.method, cuerpo: JSON.parse(String(init?.body)) })
    return json({ ot: 'ot-1', operador: 'operario:2', estado_general: 'asignada' })
  })
  const r = await c.asignar('ot-1', 'operario:2')
  expect(pedidos).toEqual([{ url: 'https://x/cliente/ots/ot-1/asignar', metodo: 'POST', cuerpo: { operador: 'operario:2' } }])
  expect(r.operador).toBe('operario:2')
})

it('reads the lists from the client service', async () => {
  const urls: string[] = []
  const c = crearCliente('https://x', async (url) => {
    urls.push(String(url))
    return json([])
  })
  await c.listarOts()
  await c.listarPautas()
  await c.listarOperadores()
  expect(urls).toEqual(['https://x/cliente/ots', 'https://x/cliente/pautas', 'https://x/cliente/operadores'])
})

it('orders an OT with the pauta id', async () => {
  let pedido: { url: string; cuerpo: unknown } | null = null
  const c = crearCliente('https://x', async (url, init) => {
    pedido = { url: String(url), cuerpo: JSON.parse(String(init?.body)) }
    return json({ ot: 'ot-0016', pauta: 'pauta-polin-demo', version: 1, nombre: 'Cambio de polín', cliente: 'oculta' }, 201)
  })
  expect((await c.pedirOt('pauta-polin-demo')).ot).toBe('ot-0016')
  expect(pedido).toEqual({ url: 'https://x/cliente/ots', cuerpo: { pauta_id: 'pauta-polin-demo' } })
})

describe('login and token', () => {
  const persona = { id: 'operario:1', nombre: 'Ana Rojas', usuario: 'ana@x', rol: 'operador', cliente: { id: 'o', nombre: 'O', industria: '' } }

  it('signs in with usuario and clave', async () => {
    let cuerpo: unknown = null
    const c = crearCliente('https://x', async (_url, init) => {
      cuerpo = JSON.parse(String(init?.body))
      return json({ token: 't', expira: '2026-11-22T06:00:00+00:00', persona })
    })
    const r = await c.entrar('ana@x', 'clave')
    expect(cuerpo).toEqual({ usuario: 'ana@x', clave: 'clave' })
    expect(r.persona.nombre).toBe('Ana Rojas')
  })

  it('sends the token as Authorization: Bearer on every call', async () => {
    const cabeceras: (string | null)[] = []
    const c = crearCliente(
      'https://x',
      async (_url, init) => {
        cabeceras.push(new Headers(init?.headers).get('authorization'))
        return json([])
      },
      { token: () => 't-ana', alVencer: () => {} },
    )
    await c.listarOts()
    await c.leerOt('ot-1')
    expect(cabeceras).toEqual(['Bearer t-ana', 'Bearer t-ana'])
  })

  it('a wrong clave is a credentials error, not an expired session', async () => {
    const alVencer = vi.fn()
    const c = crearCliente('https://x', async () => json({ login: 'usuario o clave incorrectos' }, 401), { token: () => null, alVencer })
    await expect(c.entrar('ana@x', 'mal')).rejects.toMatchObject({ status: 401, tipo: 'credenciales', message: 'Correo o clave incorrectos.' })
    expect(alVencer).not.toHaveBeenCalled()
  })

  it('a rejected token closes the session', async () => {
    const alVencer = vi.fn()
    const c = crearCliente('https://x', async () => json({ login: 'el token no existe o venció' }, 401), { token: () => 'viejo', alVencer })
    await expect(c.listarOts()).rejects.toMatchObject({ status: 401, tipo: 'sesion' })
    expect(alVencer).toHaveBeenCalledOnce()
  })

  it('a busy station asking for the team key is not an expired session', async () => {
    const alVencer = vi.fn()
    const c = crearCliente(
      'https://x',
      async () => json({ clave: 'el edge edge-1 ejecuta la OT ot-prueba: quitárselo pide la clave del equipo' }, 401),
      { token: () => 't-ana', alVencer },
    )
    await expect(c.abrirSesion('ot-1007', 'edge-1', 'operario:1')).rejects.toMatchObject({
      status: 401,
      tipo: 'clave',
      message: 'el edge edge-1 ejecuta la OT ot-prueba: quitárselo pide la clave del equipo',
    })
    expect(alVencer).not.toHaveBeenCalled()
  })

  it('signing out with a dead token is not an expired session', async () => {
    const alVencer = vi.fn()
    const c = crearCliente('https://x', async () => json({ login: 'venció' }, 401), { token: () => 'viejo', alVencer })
    await expect(c.salir()).rejects.toMatchObject({ tipo: 'sesion' })
    expect(alVencer).not.toHaveBeenCalled()
  })

  it('maps 403 to ApiError permiso with the reason', async () => {
    const c = crearCliente('https://x', async () => json({ permiso: 'eso lo hace un supervisor; operario:1 es operador' }, 403))
    await expect(c.listarOperadores()).rejects.toMatchObject({ status: 403, tipo: 'permiso', message: 'eso lo hace un supervisor; operario:1 es operador' })
  })
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

describe('the station session by login', () => {
  const sesion = { edge_id: 'edge-1', ot_id: 'ot-1007', operario: 'operario:1', desde: '2026-11-21T20:00:00+00:00' }
  type Pedido = { metodo: string; url: string; cuerpo: unknown }
  const anotar = (pedidos: Pedido[], responder: (p: Pedido) => Response) => async (url: RequestInfo | URL, init?: RequestInit) => {
    const p = { metodo: String(init?.method), url: String(url), cuerpo: init?.body ? JSON.parse(String(init.body)) : null }
    pedidos.push(p)
    return responder(p)
  }

  it('opens the session on the client route, without the operario and without taking by default', async () => {
    const pedidos: Pedido[] = []
    const c = crearCliente('https://x', anotar(pedidos, () => json(sesion)))
    expect(await c.abrirSesion('ot-1007', 'edge-1', 'operario:1')).toEqual(sesion)
    await c.abrirSesion('ot-1007', 'edge-1', 'operario:1', true)
    expect(pedidos).toEqual([
      { metodo: 'POST', url: 'https://x/cliente/ots/ot-1007/sesion', cuerpo: { edge_id: 'edge-1', tomar: false } },
      { metodo: 'POST', url: 'https://x/cliente/ots/ot-1007/sesion', cuerpo: { edge_id: 'edge-1', tomar: true } },
    ])
  })

  it('falls back to the old route only when the server does not have the new one', async () => {
    const pedidos: Pedido[] = []
    const c = crearCliente('https://x', anotar(pedidos, (p) => (p.url.includes('/cliente/') ? json({ detail: 'Not Found' }, 404) : json(sesion))))
    expect(await c.abrirSesion('ot-1007', 'edge-1', 'operario:1')).toEqual(sesion)
    expect(pedidos[1]).toEqual({ metodo: 'POST', url: 'https://x/ot/ot-1007/sesion', cuerpo: { edge_id: 'edge-1', operario: 'operario:1' } })

    const ajena: Pedido[] = []
    const d = crearCliente('https://x', anotar(ajena, () => json({ no_existe: 'OT ot-1002' }, 404)))
    await expect(d.abrirSesion('ot-1002', 'edge-1', 'operario:1')).rejects.toMatchObject({ status: 404, tipo: 'no_existe' })
    expect(ajena).toHaveLength(1)
  })

  it('a busy station is a rule, and one of another company a permission', async () => {
    const ocupada = crearCliente('https://x', async () => json({ regla: 'la estación edge-1 ejecuta la OT ot-1002' }, 409))
    await expect(ocupada.abrirSesion('ot-1007', 'edge-1', 'operario:1')).rejects.toMatchObject({ status: 409, tipo: 'regla' })
    const ajena = crearCliente('https://x', async () => json({ permiso: 'la estación edge-1 ejecuta la OT de otra empresa' }, 403))
    await expect(ajena.abrirSesion('ot-1007', 'edge-1', 'operario:1', true)).rejects.toMatchObject({ status: 403, tipo: 'permiso' })
  })

  it('tells what the station runs, or null when it is free', async () => {
    const pedidos: Pedido[] = []
    const c = crearCliente('https://x', anotar(pedidos, () => json(sesion)))
    expect(await c.sesionDeEstacion('edge-1')).toEqual(sesion)
    expect(pedidos[0]).toMatchObject({ metodo: 'GET', url: 'https://x/edge/edge-1/sesion' })
    const libre = crearCliente('https://x', async () => json({ no_existe: 'sesión del edge edge-1' }, 404))
    expect(await libre.sesionDeEstacion('edge-1')).toBeNull()
  })

  it('reads the names of the company', async () => {
    const pedidos: Pedido[] = []
    const c = crearCliente('https://x', anotar(pedidos, () => json([{ id: 'operario:1', nombre: 'Ana Rojas', rol: 'operador' }])))
    expect(await c.listarPersonas()).toEqual([{ id: 'operario:1', nombre: 'Ana Rojas', rol: 'operador' }])
    expect(pedidos[0]).toMatchObject({ metodo: 'GET', url: 'https://x/cliente/personas' })
  })
})
