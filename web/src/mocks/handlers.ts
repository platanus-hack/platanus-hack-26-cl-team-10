// La API del mock: las rutas de la API desplegada, la de confirmar un paso por persona
// (rama de servicios de Francisco) y la que falta (asignar).

import { http, HttpResponse, ws, type RequestHandler, type WebSocketHandler } from 'msw'
import { config } from '../config'
import { USUARIOS } from '../sesion/usuarios'
import { resumenDeRelevo, type Escenario, type Temporizador } from './escenarios'
import { ErrorMock, type Mundo } from './mundo'

const CIERRE_NO_EXISTE = 4404
const CIERRE_CAIDA = 4503

const regla = (texto: string) => HttpResponse.json({ regla: texto }, { status: 409 })
const noExiste = (que: string) => HttpResponse.json({ no_existe: que }, { status: 404 })

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

  // Cada paso que pasa a ser el actual en una OT con sesión arranca sus temporizadores
  // (el sensor o la cámara que lo cierran solos, el salto, el control que se pierde…).
  m.alCambiarPaso = (otId, paso) => {
    if (m.sesionDe(otId)) e.alAvanzar?.(m, otId, paso, t)
  }

  const clientes = new Set<{ close(code?: number, reason?: string): void }>()
  m.alCaer.add(() => {
    for (const c of clientes) c.close(CIERRE_CAIDA, 'la API no responde')
    clientes.clear()
  })

  const stream = ws.link(`${raiz.replace(/^http/, 'ws')}/ot/:id/stream`)

  return [
    http.get(`${raiz}/ots`, vivo(() => HttpResponse.json(m.resumenes()))),

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

    // Propuesta (docs/gestion-ot/PRD.md §6): asigna una OT sin operador o reasigna una entregada.
    http.post(`${raiz}/ot/:id/asignar`, vivo(async ({ params, request }) => {
      const id = otDe(params)
      if (!m.existe(id)) return noExiste(`OT ${id}`)
      const cuerpo = (await request.json().catch(() => null)) as { operador?: unknown } | null
      const operador = cuerpo?.operador
      if (!USUARIOS.some((u) => u.rol === 'operador' && u.id === operador)) return regla('el operador no existe')
      const actual = m.resumenes().find((o) => o.ot === id)!
      if (actual.estado_general === 'completa') return regla('la OT ya está completa')
      if (actual.estado_general !== 'sin_asignar' && actual.estado_general !== 'entregada') {
        return regla('la OT ya tiene operador')
      }
      m.asignar(id, operador as string)
      return HttpResponse.json(m.resumenes().find((o) => o.ot === id))
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
