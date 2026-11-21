// La pantalla de ejecución entera contra el mock (MSW en Node, HTTP y WebSocket).
// Los tiempos de los escenarios corren 100 veces más rápido.

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import type { Pauta } from '../api/tipos'
import { config } from '../config'
import { ESCENARIOS, type NombreEscenario, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO, PAUTA_LOTO } from '../mocks/pauta'
import type { Persona } from '../api/tipos'
import { ANA, BRUNO, entrarComo } from '../mocks/personas'
import { tokenDeSesion } from '../sesion/sesion'
import { tema } from '../tema'
import { PaginaOt } from './PaginaOt'
import { tiempos } from './useEjecucion'
import { voz } from './voz'

const rapido: Temporizador = (ms, fn) => {
  setTimeout(fn, ms / 100)
}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

const tiemposOriginales = { ...tiempos }
afterEach(() => {
  Object.assign(tiempos, tiemposOriginales)
  vi.restoreAllMocks()
})

let m: Mundo
let dicho: string[]

function abrir(escenario: NombreEscenario, { ot = 'ot-12', usuario = ANA, pauta = PAUTA_DEMO }: { ot?: string; usuario?: Persona; pauta?: Pauta } = {}) {
  m = new Mundo(pauta)
  const e = ESCENARIOS[escenario]!
  e.preparar(m)
  server.resetHandlers(...crearHandlers(m, e, rapido))
  entrarComo(usuario)
  dicho = []
  vi.spyOn(voz, 'decir').mockImplementation((t) => void dicho.push(t))
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter initialEntries={[`/ot/${ot}`]}>
        <Routes>
          <Route path="/ot/:id" element={<PaginaOt />} />
          <Route path="/operador" element={<p>mis OT</p>} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

/** El primer toque de la sesión: aparece solo si el audio no estaba desbloqueado. */
async function entrar() {
  const boton = await screen.findByRole('button', { name: /^(Comenzar|Continuar|Entregar turno)$/ })
  if (boton.textContent !== 'Entregar turno') await userEvent.click(boton)
  await screen.findByRole('button', { name: 'Entregar turno' })
}

/** La tarjeta de un paso, por su título. */
const fila = (titulo: string) => screen.getByText(new RegExp(`^\\d\\. ${titulo}$`)).closest('.mantine-Paper-root') as HTMLElement
const enFila = (titulo: string, texto: string | RegExp) => within(fila(titulo)).queryByText(texto)
const boton = (nombre: string) => screen.queryByRole('button', { name: nombre })

describe('steps close on their own; Hecho only where the API needs it', () => {
  it('feliz (correa): sensor steps close alone, Hecho appears only on the camera and confirmation steps, and the OT completes', async () => {
    abrir('feliz')
    await entrar()
    await waitFor(() => expect(m.resumenes()[0].estado_general).toBe('en_ejecucion'))
    // p1 y p2 se cierran solos; p3 es de cámara sin detección: ahí aparece «Hecho».
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    await waitFor(() => expect(enFila('Cambiar el rodillo', 'por la cámara')).not.toBeNull())
    // p4 y p5 se cierran solos; p6 es de confirmación.
    await waitFor(() => expect(enFila('Prueba de detención', 'Cuando lo termines, toca «Hecho».')).not.toBeNull(), { timeout: 2000 })
    await userEvent.click(screen.getByRole('button', { name: 'Hecho' }))
    expect(await screen.findByText('OT completa')).toBeInTheDocument()
    // Solo se declaró donde la API lo necesita: la cámara sin detección y la confirmación.
    expect(m.eventos('ot-12').filter((e) => e.tipo === 'declaracion').map((e) => e.paso_id)).toEqual(['p3', 'p6'])
    expect(dicho).toEqual([])
  }, 10_000)

  it('feliz (LOTO): the whole OT closes with no button pressed', async () => {
    abrir('feliz', { pauta: PAUTA_LOTO })
    await entrar()
    expect(enFila('Poner el dispositivo de bloqueo', /./)).not.toBeNull()
    expect(await screen.findByText('OT completa', {}, { timeout: 4000 })).toBeInTheDocument()
    expect(m.eventos('ot-12').some((e) => e.tipo === 'declaracion')).toBe(false)
  }, 10_000)
})

describe('when the API warns that a step was skipped', () => {
  it('warn-sobrescrito: the skip pops up and is spoken once; «Ya lo hice» with a reason confirms the step', async () => {
    abrir('warn-sobrescrito')
    await entrar()
    // Lo mismo que se oye, en grande sobre la pantalla.
    const aviso = await screen.findByRole('dialog', { name: 'Paso saltado' }, { timeout: 2000 })
    expect(within(aviso).getByText('Oye, te saltaste el paso 1: Cortar la energía y bloquear con candado. Hazlo antes de seguir.')).toBeInTheDocument()
    await waitFor(() => expect(dicho).toEqual(['Oye, te saltaste el paso 1: Cortar la energía y bloquear con candado. Hazlo antes de seguir.']))
    await userEvent.click(within(aviso).getByRole('button', { name: 'Entendido' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    // Cerrado el aviso, el banner y el paso siguen diciendo qué hacer.
    const banner = screen.getByRole('alert')
    expect(within(banner).getByText('Paso saltado')).toBeInTheDocument()
    expect(enFila('Cortar la energía y bloquear con candado', 'Te saltaste este paso: hiciste «Retirar la guarda» antes.')).not.toBeNull()
    await userEvent.click(within(fila('Cortar la energía y bloquear con candado')).getByRole('button', { name: 'Ya lo hice' }))
    await userEvent.click(screen.getByRole('button', { name: 'El sensor no lo marca' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'Confirmado por Ana Rojas: «El sensor no lo marca»')).not.toBeNull())
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
    expect(m.eventos('ot-12').some((e) => e.evidencia?.tipo === 'persona' && e.actor === 'operario:1')).toBe(true)
    expect(dicho).toHaveLength(1)
  })

  it('the warning can be heard again from the pop-up, if the operator missed it', async () => {
    abrir('warn-sobrescrito')
    await entrar()
    const aviso = await screen.findByRole('dialog', { name: 'Paso saltado' }, { timeout: 2000 })
    await waitFor(() => expect(dicho).toHaveLength(1))
    await userEvent.click(within(aviso).getByRole('button', { name: 'Escuchar de nuevo' }))
    expect(dicho).toEqual([dicho[0], dicho[0]])
  })

  it('warn-corregido: doing the skipped step clears the warning and the pop-up by themselves', async () => {
    abrir('warn-corregido')
    await entrar()
    await screen.findByRole('dialog', { name: 'Paso saltado' }, { timeout: 2000 })
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull(), { timeout: 2000 })
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'por sensor')).not.toBeNull())
  })
})

describe('other alerts', () => {
  it('alerta-seguridad: the lockout tag appears, is spoken in plain words, has nothing to override, and clears with the sensor', async () => {
    abrir('alerta-seguridad')
    await entrar()
    const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
    expect(within(banner).getByText('Peligro')).toBeInTheDocument()
    expect(within(banner).queryAllByRole('button')).toEqual([])
    expect(await screen.findByRole('dialog', { name: 'Peligro' })).toBeInTheDocument()
    await waitFor(() => expect(dicho).toContain('Guarda abierta con energía viva. Detener y aislar la energía antes de continuar.'))
    // Corregido con el sensor, se van el banner y el aviso, sin tocar nada.
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
  })

  it('control-perdido: the undone control is named and spoken, then clears', async () => {
    abrir('control-perdido')
    await entrar()
    const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
    expect(within(banner).getByText('Control perdido')).toBeInTheDocument()
    expect(await screen.findByRole('dialog', { name: 'Control perdido' })).toBeInTheDocument()
    await waitFor(() => expect(dicho).toEqual(['Oye, se deshizo el paso 1: Cortar la energía y bloquear con candado. Vuelve a dejarlo como estaba.']))
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
  })

  it('camara-no: a camera conflict is shown but not spoken, and offers to try again or to confirm', async () => {
    abrir('camara-no')
    await entrar()
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    await waitFor(() => expect(enFila('Cambiar el rodillo', 'La cámara no lo ve (62 % de certeza). Revisa y toca «Hecho» de nuevo, o confírmalo si ya lo hiciste.')).not.toBeNull())
    expect(within(fila('Cambiar el rodillo')).getByRole('button', { name: 'Hecho' })).toBeInTheDocument()
    expect(within(fila('Cambiar el rodillo')).getByRole('button', { name: 'Ya lo hice' })).toBeInTheDocument()
    expect(dicho).toEqual([])
    expect(screen.queryByRole('dialog')).toBeNull()
  })

  it('sin-senal: after the wait, a step whose evidence never comes offers «Ya lo hice»', async () => {
    tiempos.esperaEvidenciaMs = 100
    abrir('sin-senal')
    await entrar()
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'Todavía no se marca.')).not.toBeNull())
    await userEvent.click(within(fila('Cortar la energía y bloquear con candado')).getByRole('button', { name: 'Ya lo hice' }))
    await userEvent.type(screen.getByLabelText('Motivo'), 'el reed está dañado; el candado está puesto')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', /^Confirmado por Ana Rojas/)).not.toBeNull())
    expect(dicho).toEqual([])
  })

  it('a 409 shows the rule, clears Comprobando and does not retry', async () => {
    abrir('feliz')
    let intentos = 0
    server.use(
      http.post(`${config.API_URL}/ot/:id/declarar`, () => {
        intentos++
        return HttpResponse.json({ regla: 'la pauta ya está completa' }, { status: 409 })
      }),
    )
    await entrar()
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    expect(await screen.findByText('la pauta ya está completa')).toBeInTheDocument()
    expect(screen.queryByText('Comprobando…')).toBeNull()
    await new Promise((r) => setTimeout(r, 100))
    expect(intentos).toBe(1)
    await userEvent.click(screen.getByRole('button', { name: 'Entendido' }))
    expect(screen.queryByText('la pauta ya está completa')).toBeNull()
  })

  it('api-caida: the strip shows while down, writes are disabled, and nothing is spoken twice', async () => {
    abrir('api-caida')
    await entrar()
    expect(await screen.findByText('Sin conexión, reintentando', {}, { timeout: 2000 })).toBeInTheDocument()
    expect(boton('Entregar turno')).toBeDisabled()
    await waitFor(() => expect(screen.queryByText('Sin conexión, reintentando')).toBeNull(), { timeout: 5000 })
    await waitFor(() => expect(boton('Entregar turno')).toBeEnabled())
    expect(dicho).toEqual([])
  }, 10_000)
})

describe('handover and navigation', () => {
  it('relevo: Bruno reads the briefing, signs it and continues at step 4', async () => {
    abrir('relevo', { usuario: BRUNO })
    expect(await screen.findByText('Relevo de turno')).toBeInTheDocument()
    expect(screen.getByText(/confirmado por Ana Rojas/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Recibido' }))
    await screen.findByRole('button', { name: 'Entregar turno' })
    expect(enFila('Reinstalar la guarda', 'Vuelve a montar la guarda y asegúrala.')).not.toBeNull()
    expect(enFila('Retirar la guarda', /^Confirmado por Ana Rojas/)).not.toBeNull()
    expect(m.eventos('ot-12').map((e) => [e.tipo, e.actor])).toContainEqual(['relevo_recibido', 'operario:2'])
    expect(m.resumenes()[0].operador).toBe('operario:2')
  })

  it('the operator who handed over can no longer open the OT, and gets no briefing', async () => {
    abrir('relevo', { usuario: ANA })
    expect(await screen.findByText('Esta OT no está en tu lista')).toBeInTheDocument()
    expect(screen.queryByText('Relevo de turno')).toBeNull()
  })

  it("another operator's OT does not open by URL, and no session starts on it", async () => {
    abrir('feliz', { ot: 'ot-13', usuario: ANA })
    expect(await screen.findByText('Esta OT no está en tu lista')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver a mis OT' })).toBeInTheDocument()
    expect(m.sesionDe('ot-13')).toBeNull()
  })

  it('Entregar turno asks first, hands over and goes back to the list', async () => {
    abrir('feliz')
    await entrar()
    await userEvent.click(screen.getByRole('button', { name: 'Entregar turno' }))
    expect(screen.getByText('¿Entregar el turno?')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(m.eventos('ot-12').some((e) => e.tipo === 'relevo_entregado')).toBe(false)
    await userEvent.click(screen.getByRole('button', { name: 'Entregar turno' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
    expect(m.resumenes()[0]).toMatchObject({ operador: null, estado_general: 'entregada' })
  })

  it('«Mis OT» goes back to the list without handing over', async () => {
    abrir('feliz')
    await entrar()
    await userEvent.click(screen.getByRole('link', { name: 'Mis OT' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
    expect(m.eventos('ot-12').some((e) => e.tipo === 'relevo_entregado')).toBe(false)
  })

  it('completa: shows the closing counts and the way back', async () => {
    abrir('completa')
    expect(await screen.findByText('OT completa')).toBeInTheDocument()
    expect(screen.getByText('6 de 6 pasos verificados')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Volver a mis OT' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
  })

  it('Recibido shows why the handover could not be signed', async () => {
    abrir('relevo', { usuario: BRUNO })
    server.use(http.post(`${config.API_URL}/ot/:id/relevo/recibir`, () => HttpResponse.json({ regla: 'el turno ya fue recibido' }, { status: 409 })))
    await userEvent.click(await screen.findByRole('button', { name: 'Recibido' }))
    expect(await screen.findByText('el turno ya fue recibido')).toBeInTheDocument()
    expect(screen.getByText('Relevo de turno')).toBeInTheDocument()
  })

  it('a failed session opening is retried until it works', async () => {
    tiempos.reintentoSesionMs = 100
    abrir('feliz')
    server.use(http.post(`${config.API_URL}/cliente/ots/:id/sesion`, () => HttpResponse.error(), { once: true }))
    await entrar()
    expect(await screen.findByText('Sin conexión, reintentando')).toBeInTheDocument()
    await waitFor(() => expect(m.snapshot('ot-12', 0).sesion).not.toBeNull())
  })

  it('an unknown OT says so and offers the way back', async () => {
    abrir('feliz', { ot: 'ot-99' })
    expect(await screen.findByText('Esta OT no está en tu lista')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver a mis OT' })).toBeInTheDocument()
  })
})

describe('a station busy with another OT', () => {
  afterEach(() => server.events.removeAllListeners())
  const panel = () => screen.queryByRole('region', { name: 'La estación está ocupada' })

  it('names the OT and who runs it, instead of the API rule, and takes the station only on a tap', async () => {
    abrir('estacion-ocupada')
    await entrar()
    const p = await screen.findByRole('region', { name: 'La estación está ocupada' })
    expect(within(p).getByText(/La estación edge-1 está con la OT-13 de Bruno Díaz desde las \d\d:\d\d\./)).toBeInTheDocument()
    expect(within(p).getByText(/Si la tomas, esa OT deja de recibir sus sensores/)).toBeInTheDocument()
    expect(screen.queryByText(/tomar. en true/)).toBeNull()
    expect(screen.queryByText('No se pudo')).toBeNull()
    expect(tokenDeSesion()).not.toBeNull()
    expect(m.sesionDe('ot-12')).toBeNull()

    await userEvent.click(within(p).getByRole('button', { name: 'Tomar la estación' }))
    await waitFor(() => expect(m.sesionDe('ot-12')).toMatchObject({ edge_id: 'edge-1', operario: 'operario:1' }))
    expect(m.sesionDe('ot-13')).toBeNull()
    await waitFor(() => expect(panel()).toBeNull())
  })

  it('the automatic retry never takes it: the OT starts by itself once the station is free', async () => {
    tiempos.reintentoSesionMs = 30
    abrir('estacion-ocupada')
    const pedidos: unknown[] = []
    server.events.on('request:start', ({ request }) => {
      if (request.method === 'POST' && new URL(request.url).pathname.endsWith('/sesion')) void request.clone().json().then((b) => pedidos.push(b))
    })
    await entrar()
    await screen.findByRole('region', { name: 'La estación está ocupada' })
    await waitFor(() => expect(pedidos.length).toBeGreaterThanOrEqual(3))
    expect(m.sesionDe('ot-13')).not.toBeNull()

    m.terminarSesion('edge-1')
    await waitFor(() => expect(m.sesionDe('ot-12')).not.toBeNull())
    await waitFor(() => expect(panel()).toBeNull())
    expect(pedidos.every((b) => (b as { tomar: boolean }).tomar === false)).toBe(true)
  })

  it("a station running another company's OT cannot be taken: no button, it says so and keeps waiting", async () => {
    tiempos.reintentoSesionMs = 30
    let ajena = true
    abrir('feliz')
    server.use(
      http.post(`${config.API_URL}/cliente/ots/:id/sesion`, () =>
        ajena ? HttpResponse.json({ permiso: 'la estación edge-1 ejecuta la OT de otra empresa' }, { status: 403 }) : undefined,
      ),
    )
    await entrar()
    expect(await screen.findByText('La estación está ocupada con una OT de otra empresa. Pide que la liberen; esta OT parte sola apenas quede libre.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Tomar la estación' })).toBeNull()
    expect(tokenDeSesion()).not.toBeNull()
    ajena = false
    await waitFor(() => expect(m.sesionDe('ot-12')).not.toBeNull())
  })

  it('a rule that is not a busy station is shown as is and not retried', async () => {
    tiempos.reintentoSesionMs = 30
    let intentos = 0
    abrir('feliz')
    server.use(
      http.post(`${config.API_URL}/cliente/ots/:id/sesion`, () => {
        intentos++
        return HttpResponse.json({ regla: 'la OT ot-12 ya está completa' }, { status: 409 })
      }),
    )
    await entrar()
    expect(await screen.findByText('la OT ot-12 ya está completa')).toBeInTheDocument()
    expect(panel()).toBeNull()
    await new Promise((r) => setTimeout(r, 150))
    expect(intentos).toBe(1)
  })
})
