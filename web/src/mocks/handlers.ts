// La API del mock: las rutas de la API desplegada que usa el front, con sus mismas reglas.

import { http, HttpResponse, ws, type RequestHandler, type WebSocketHandler } from 'msw'
import type { Persona } from '../api/tipos'
import { config } from '../config'
import { resumenDeRelevo, type Escenario, type Temporizador } from './escenarios'
import { ErrorMock, type Mundo } from './mundo'
import { CLAVE_MOCK, expiraMock, PERSONAS, personaDeCabecera, tokenMock } from './personas'

const CIERRE_NO_EXISTE = 4404
const CIERRE_CAIDA = 4503

const regla = (texto: string) => HttpResponse.json({ regla: texto }, { status: 409 })
const noExiste = (que: string) => HttpResponse.json({ no_existe: que }, { status: 404 })
const sinPermiso = (texto: string) => HttpResponse.json({ permiso: texto }, { status: 403 })
const sinLogin = (texto: string) =>
  HttpResponse.json({ login: texto }, { status: 401, headers: { 'WWW-Authenticate': 'Bearer' } })

const cuadroDeMentira = (edge: string) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">` +
  `<rect width="640" height="480" fill="#1f2a33"/>` +
  `<rect x="120" y="230" width="400" height="40" rx="20" fill="#3b4a56"/>` +
  `<circle cx="160" cy="250" r="34" fill="#55687a"/><circle cx="480" cy="250" r="34" fill="#55687a"/>` +
  `<text x="320" y="120" fill="#c9d3dc" font-family="sans-serif" font-size="26" text-anchor="middle">Cámara de ${edge}</text>` +
  `<text x="320" y="380" fill="#8c9aa6" font-family="sans-serif" font-size="18" text-anchor="middle">Mock: en el servidor aquí va el video en vivo</text>` +
  `</svg>`

/** Los protocolos de los que sale la pauta del mock, como los trae `GET /cliente/pautas`. */
const PROTOCOLOS = [{ id: 'prot-aislamiento-01', nombre: 'Aislamiento y bloqueo de energías' }]

export function crearHandlers(
  m: Mundo,
  e: Escenario,
  t: Temporizador,
  base: string = config.API_URL,
): Array<RequestHandler | WebSocketHandler> {
  const raiz = base.replace(/\/$/, '')

  // Mientras la API está «caída», toda petición falla como falla la red.
  type Resolver = Parameters<typeof http.get>[1]
  const vivo =
    (fn: Resolver): Resolver =>
    (info) =>
      m.caido ? HttpResponse.error() : fn(info)

  const otDe = (params: Record<string, unknown>) => String(params.id)

  // El servicio para clientes (app/acceso.py): sin token, 401; el supervisor ve todas las OT de
  // su empresa y el operador las suyas. En el mock todas son de Oculta.
  type ResolverConPersona = (info: Parameters<Resolver>[0], p: Persona) => ReturnType<Resolver>
  const conLogin =
    (fn: ResolverConPersona): Resolver =>
    (info) => {
      const p = personaDeCabecera(info.request.headers.get('authorization'))
      if (!p) return sinLogin('el token no existe o venció: vuelve a entrar')
      return fn(info, p)
    }
  const soloSupervisor =
    (fn: ResolverConPersona): ResolverConPersona =>
    (info, p) =>
      p.rol === 'supervisor' ? fn(info, p) : sinPermiso(`eso lo hace un supervisor; ${p.id} es ${p.rol}`)
  const otsDe = (p: Persona) => m.resumenes().filter((o) => p.rol === 'supervisor' || o.operador === p.id)
  const operadores = () => PERSONAS.filter((p) => p.rol === 'operador')

  // Cada paso que pasa a ser el actual en una OT con sesión arranca sus temporizadores
  // (el sensor o la cámara que lo cierran solos, el salto, el control que se pierde…).
  m.alCambiarPaso = (otId, paso) => {
    if (m.sesionDe(otId)) e.alAvanzar?.(m, otId, paso, t)
  }
  e.alIniciar?.(m, t)

  const clientes = new Set<{ close(code?: number, reason?: string): void }>()
  m.alCaer.add(() => {
    for (const c of clientes) c.close(CIERRE_CAIDA, 'la API no responde')
    clientes.clear()
  })

  const stream = ws.link(`${raiz.replace(/^http/, 'ws')}/ot/:id/stream`)

  return [
    http.post(`${raiz}/auth/entrar`, vivo(async ({ request }) => {
      const { usuario = '', clave = '' } = ((await request.json().catch(() => null)) ?? {}) as { usuario?: string; clave?: string }
      const p = PERSONAS.find((x) => x.usuario === usuario.trim().toLowerCase())
      if (!p || clave !== CLAVE_MOCK) return sinLogin('usuario o clave incorrectos')
      return HttpResponse.json({ token: tokenMock(p.id), expira: expiraMock(), persona: p })
    })),

    http.post(`${raiz}/auth/salir`, vivo(conLogin(() => new HttpResponse(null, { status: 204 })))),

    http.get(`${raiz}/yo`, vivo(conLogin((_, p) => HttpResponse.json(p)))),

    http.get(`${raiz}/cliente/ots`, vivo(conLogin((_, p) => HttpResponse.json(otsDe(p))))),

    http.get(`${raiz}/cliente/ots/:id`, vivo(conLogin(({ params }, p) => {
      const id = otDe(params)
      const o = otsDe(p).find((x) => x.ot === id)
      return o ? HttpResponse.json({ ...o, calificacion: m.calificacion(id) }) : noExiste(`OT ${id}`)
    }))),

    http.get(`${raiz}/cliente/pautas`, vivo(conLogin(() => {
      const { id, nombre, version, equipo, pasos } = m.pauta
      return HttpResponse.json([{ id, nombre, version, equipo, pasos: pasos.length, protocolos: PROTOCOLOS }])
    }))),

    http.get(`${raiz}/cliente/operadores`, vivo(conLogin(soloSupervisor(() => HttpResponse.json(operadores()))))),

    // Un supervisor pide una OT de una pauta habilitada; nace sin operador (catalogo.generar_ot).
    http.post(`${raiz}/cliente/ots`, vivo(conLogin(soloSupervisor(async ({ request }, p) => {
      const { pauta_id } = ((await request.json().catch(() => null)) ?? {}) as { pauta_id?: string }
      if (pauta_id !== m.pauta.id) return sinPermiso(`la pauta ${String(pauta_id)} no está habilitada para ${p.cliente.nombre}`)
      const id = m.idNuevo()
      m.crearOt(id, null)
      const { nombre, version } = m.pauta
      return HttpResponse.json({ ot: id, pauta: m.pauta.id, version, nombre, protocolos: PROTOCOLOS, cliente: p.cliente.id }, { status: 201 })
    })))),

    // Asigna una OT sin operador o reasigna una entregada (app/catalogo.py, asignacion).
    http.post(`${raiz}/cliente/ots/:id/asignar`, vivo(conLogin(soloSupervisor(async ({ params, request }, p) => {
      const id = otDe(params)
      const actual = otsDe(p).find((o) => o.ot === id)
      if (!actual) return noExiste(`OT ${id}`)
      const { operador } = ((await request.json().catch(() => null)) ?? {}) as { operador?: unknown }
      if (!operadores().some((o) => o.id === operador)) return sinPermiso(`${String(operador)} no es operador de ${p.cliente.nombre}`)
      if (actual.completa) return regla(`la OT ${id} ya está completa`)
      if (actual.operador) return regla(`la OT ${id} ya tiene operador: ${actual.operador}`)
      m.agregar(id, { tipo: 'ot_asignada', actor: p.id, evidencia: { operador }, detalle: `OT asignada a ${String(operador)}` })
      m.asignar(id, operador as string)
      return HttpResponse.json(m.resumenes().find((o) => o.ot === id))
    })))),

    // La cámara de la estación: en el mock, un cuadro fijo que dice que es de mentira.
    http.get(`${raiz}/edge/:edge/video.mjpg`, vivo(({ params }) =>
      new HttpResponse(cuadroDeMentira(String(params.edge)), { headers: { 'content-type': 'image/svg+xml' } }),
    )),

    http.get(`${raiz}/ot/:id`, vivo(({ params }) => {
      const id = otDe(params)
      return m.existe(id) ? HttpResponse.json(m.estado(id)) : noExiste(`OT ${id}`)
    })),

    http.get(`${raiz}/pautas/:id`, vivo(({ params }) =>
      params.id === m.pauta.id ? HttpResponse.json(m.pauta) : noExiste(`pauta ${String(params.id)}`),
    )),

    http.post(`${raiz}/ot/:id/sesion`, vivo(async ({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const { edge_id = config.EDGE_ID, operario } = (await request.json()) as { edge_id?: string; operario: string }
      const sesion = m.abrirSesion(id, edge_id, operario)
      e.alAbrirSesion?.(m, id, t)
      const actual = m.estado(id).paso_actual
      const paso = actual ? m.paso(actual) : undefined
      if (paso) e.alAvanzar?.(m, id, paso, t)
      return HttpResponse.json(sesion)
    })),

    http.post(`${raiz}/ot/:id/declarar`, vivo(async ({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const { actor, paso_id } = (await request.json()) as { actor: string; texto: string; paso_id?: string }
      // Si la evidencia ya cerró el paso que la pantalla mostraba, la palabra llegó tarde: se registra y listo.
      const nombrado = paso_id ? m.paso(paso_id) : undefined
      if (nombrado && m.estado(id).pasos.find((p) => p.id === nombrado.id)?.estado === 'verificado') {
        m.agregar(id, {
          tipo: 'declaracion', actor, paso_id: nombrado.id, declarado: 'hecho',
          detalle: `confirma «${nombrado.titulo}», que su evidencia ya había cerrado`,
        })
        return HttpResponse.json({
          paso: nombrado.id, estado: 'verificado', capa: null, interrumpe: false,
          detalle: 'la evidencia ya había cerrado este paso; la declaración queda registrada',
        })
      }
      const actual = m.estado(id).paso_actual
      if (!actual) return regla('la pauta ya está completa')
      return HttpResponse.json(e.alDeclarar(m, id, m.paso(actual)!, actor, t))
    })),

    http.post(`${raiz}/ot/:id/pasos/:paso/confirmar`, vivo(async ({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const { actor = '', motivo = '' } = ((await request.json().catch(() => null)) ?? {}) as { actor?: string; motivo?: string }
      try {
        return HttpResponse.json(m.confirmar(id, String(params.paso), actor, motivo))
      } catch (err) {
        if (!(err instanceof ErrorMock)) throw err
        return err.status === 404 ? noExiste(err.message) : regla(err.message)
      }
    })),

    http.post(`${raiz}/ot/:id/relevo/entregar`, vivo(({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const actor = new URL(request.url).searchParams.get('actor') ?? 'desconocido'
      const resumen = resumenDeRelevo(m, id)
      m.agregar(id, { tipo: 'relevo_entregado', actor, detalle: resumen })
      m.asignar(id, null)
      return HttpResponse.json({ resumen, estado: m.estado(id) })
    })),

    http.post(`${raiz}/ot/:id/relevo/recibir`, vivo(({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const actor = new URL(request.url).searchParams.get('actor') ?? 'desconocido'
      m.agregar(id, { tipo: 'relevo_recibido', actor, detalle: `${actor} confirma que recibió el turno` })
      m.asignar(id, actor)
      return HttpResponse.json({ firmado_por: actor })
    })),

    stream.addEventListener('connection', ({ client, params }) => {
      if (m.caido) return client.close(CIERRE_CAIDA, 'la API no responde')
      const id = otDe(params)
      if (!m.existe(id)) return client.close(CIERRE_NO_EXISTE, `OT ${id} no existe`)
      const desde = Number(client.url.searchParams.get('desde') ?? 0)
      client.send(JSON.stringify(m.snapshot(id, desde)))
      const dejar = m.suscribir(id, (msg) => client.send(JSON.stringify(msg)))
      clientes.add(client)
      client.addEventListener('close', () => {
        dejar()
        clientes.delete(client)
      })
    }),
  ]
}
