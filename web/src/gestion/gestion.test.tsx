// Las pantallas de gestión de punta a punta contra el mock (MSW en Node), con las mismas rutas que App.

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes, useParams } from 'react-router'
import { config } from '../config'
import { voz } from '../ejecucion/voz'
import { ESCENARIOS, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { RequiereRol } from '../sesion/RequiereRol'
import { ANA, BRUNO, CLAVE_MOCK, SUPERVISORA, entrarComo } from '../mocks/personas'
import type { Persona } from '../api/tipos'
import { leerSesion, tokenDeSesion } from '../sesion/sesion'
import { tema } from '../tema'
import { Inicio } from './Inicio'
import { PaginaLogin } from './PaginaLogin'
import { PaginaOperador } from './PaginaOperador'
import { PaginaSupervisor } from './PaginaSupervisor'

const sinEspera: Temporizador = () => {}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

let m: Mundo
beforeEach(() => {
  m = new Mundo(PAUTA_DEMO)
  ESCENARIOS.feliz!.preparar(m)
  server.resetHandlers(...crearHandlers(m, ESCENARIOS.feliz!, sinEspera))
})

function Ejecucion() {
  return <p>ejecución de {useParams().id}</p>
}

function abrir(ruta: string) {
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path="/login" element={<PaginaLogin />} />
          <Route path="/supervisor" element={<RequiereRol rol="supervisor"><PaginaSupervisor /></RequiereRol>} />
          <Route path="/operador" element={<RequiereRol rol="operador"><PaginaOperador /></RequiereRol>} />
          <Route path="/ot/:id" element={<RequiereRol rol="operador"><Ejecucion /></RequiereRol>} />
          <Route path="*" element={<Inicio />} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

/** La tarjeta de una OT, por su id en mayúsculas. */
const tarjeta = async (ot: string) => (await screen.findByText(ot.toUpperCase())).closest<HTMLElement>('.mantine-Card-root')!

/** Entra por el formulario, como en el servidor: correo y clave (la del mock). */
async function entrarConFormulario(p: Persona) {
  await userEvent.type(await screen.findByLabelText(/Correo/), p.usuario)
  await userEvent.type(screen.getByLabelText(/Clave/), CLAVE_MOCK)
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
}

/** Las lecturas de una OT por separado (`GET /ot/{id}`) mientras corre `fn`. */
async function lecturasDeOt(fn: () => Promise<void>): Promise<string[]> {
  const pedidas: string[] = []
  const oir = ({ request }: { request: Request }) => {
    const ruta = new URL(request.url).pathname
    if (request.method === 'GET' && ruta.startsWith('/ot/')) pedidas.push(ruta)
  }
  server.events.on('request:start', oir)
  try {
    await fn()
  } finally {
    server.events.removeListener('request:start', oir)
  }
  return pedidas
}

describe('login and routes', () => {
  it('sends a visitor without session from / to the login', async () => {
    abrir('/')
    expect(await screen.findByRole('heading', { name: 'Entrar', level: 1 })).toBeInTheDocument()
  })

  it('signs in with correo and clave and lands on their dashboard', async () => {
    abrir('/login')
    await entrarConFormulario(ANA)
    expect(await screen.findByRole('heading', { name: 'Mis órdenes de trabajo' })).toBeInTheDocument()
    expect(leerSesion()).toMatchObject({ id: 'operario:1', nombre: 'Ana Rojas', cliente: { nombre: 'Oculta' } })
    expect(tokenDeSesion()).toBe('mock.operario:1')
    expect(screen.getByText('Oculta')).toBeInTheDocument()
  })

  it('says so when the correo or the clave are wrong, and stays on the login', async () => {
    abrir('/login')
    await userEvent.type(screen.getByLabelText(/Correo/), ANA.usuario)
    await userEvent.type(screen.getByLabelText(/Clave/), 'otra')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Correo o clave incorrectos.')
    expect(leerSesion()).toBeNull()
  })

  it('says so when the server is unreachable', async () => {
    m.caido = true
    abrir('/login')
    await entrarConFormulario(ANA)
    expect(await screen.findByRole('alert')).toHaveTextContent('No pudimos conectar con el servidor')
  })

  it('sends a supervisor whose token expired back to the login, and says why', async () => {
    entrarComo(SUPERVISORA)
    server.use(http.get(`${config.API_URL}/cliente/ots`, () => HttpResponse.json({ login: 'venció' }, { status: 401 })))
    abrir('/supervisor')
    expect(await screen.findByText('Tu sesión venció. Vuelve a entrar.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Entrar', level: 1 })).toBeInTheDocument()
    expect(leerSesion()).toBeNull()
  })

  it('with the mock, offers one tap per test person', async () => {
    const antes = config.MOCK
    config.MOCK = true
    try {
      abrir('/login')
      await userEvent.click(screen.getByRole('button', { name: 'Entrar como Carla Muñoz' }))
      expect(await screen.findByRole('heading', { name: 'Órdenes de trabajo' })).toBeInTheDocument()
    } finally {
      config.MOCK = antes
    }
  })

  it('sends a signed-in supervisor from the login to supervision', async () => {
    entrarComo(SUPERVISORA)
    abrir('/login')
    expect(await screen.findByRole('heading', { name: 'Órdenes de trabajo' })).toBeInTheDocument()
  })

  it('keeps an operator out of supervision', async () => {
    entrarComo(ANA)
    abrir('/supervisor')
    expect(await screen.findByRole('heading', { name: 'Mis órdenes de trabajo' })).toBeInTheDocument()
  })

  it('signs out back to the login', async () => {
    entrarComo(ANA)
    abrir('/operador')
    await userEvent.click(await screen.findByRole('button', { name: 'Salir' }))
    expect(await screen.findByRole('heading', { name: 'Entrar', level: 1 })).toBeInTheDocument()
    expect(leerSesion()).toBeNull()
    // Salir no es una sesión vencida.
    expect(screen.queryByText(/Tu sesión venció/)).not.toBeInTheDocument()
  })
})

describe('operator dashboard', () => {
  it('shows only their OTs, with progress and the next step', async () => {
    entrarComo(ANA)
    abrir('/operador')
    const ot12 = await tarjeta('ot-12')
    expect(within(ot12).getByText('0/6')).toBeInTheDocument()
    expect(within(ot12).getByText(/^Sigue en: 1\. /)).toBeInTheDocument()
    expect(screen.queryByText('OT-13')).not.toBeInTheDocument()
    expect(screen.queryByText('OT-14')).not.toBeInTheDocument()
  })

  it('asks for the detail only of their own open OTs', async () => {
    entrarComo(ANA)
    const pedidas = await lecturasDeOt(async () => {
      abrir('/operador')
      expect(within(await tarjeta('ot-12')).getByText(/^Sigue en: 1\. /)).toBeInTheDocument()
    })
    expect(new Set(pedidas)).toEqual(new Set(['/ot/ot-12']))
  })

  it('unlocks the audio on Comenzar and opens the execution', async () => {
    const desbloquear = vi.spyOn(voz, 'desbloquear')
    entrarComo(ANA)
    abrir('/operador')
    await userEvent.click(within(await tarjeta('ot-12')).getByRole('button', { name: 'Comenzar' }))
    expect(await screen.findByText('ejecución de ot-12')).toBeInTheDocument()
    expect(desbloquear).toHaveBeenCalledOnce()
  })

  it('offers Continuar once the OT is under way and Ver resumen once complete', async () => {
    m.abrirSesion('ot-12', config.EDGE_ID, 'operario:1')
    m.asignar('ot-14', 'operario:1')
    for (const p of PAUTA_DEMO.pasos) m.agregar('ot-14', { tipo: 'veredicto', actor: 'sistema', paso_id: p.id, estado: 'verificado', detalle: 'ok' })
    entrarComo(ANA)
    abrir('/operador')
    expect(within(await tarjeta('ot-12')).getByRole('button', { name: 'Continuar' })).toBeInTheDocument()
    expect(within(await tarjeta('ot-14')).getByRole('link', { name: 'Ver resumen' })).toHaveAttribute('href', '/ot/ot-14')
  })

  it('says so when there is nothing assigned', async () => {
    m.asignar('ot-13', null)
    entrarComo(BRUNO)
    abrir('/operador')
    expect(await screen.findByText(/No tienes OT asignadas/)).toBeInTheDocument()
  })

  it('shows the error and retries when the API is down', async () => {
    m.caido = true
    entrarComo(ANA)
    abrir('/operador')
    expect(await screen.findByText('No se pudieron cargar las OT')).toBeInTheDocument()
    m.caido = false
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('OT-12')).toBeInTheDocument()
  })
})

describe('supervisor dashboard', () => {
  it('lists every OT, what needs action first, with counters', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByLabelText('Por asignar: 1')).toBeInTheDocument()
    expect(screen.getByLabelText('En curso: 2')).toBeInTheDocument()
    const ids = screen.getAllByText(/^OT-\d+$/).map((e) => e.textContent)
    expect(ids).toEqual(['OT-14', 'OT-12', 'OT-13'])
    expect(within(await tarjeta('ot-12')).getByText('Ana Rojas')).toBeInTheDocument()
  })

  it('assigns an unassigned OT to an operator', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await userEvent.click(await screen.findByRole('button', { name: 'Asignar ot-14 a Bruno Díaz' }))
    await waitFor(() => expect(within(screen.getByText('OT-14').closest<HTMLElement>('.mantine-Card-root')!).getByText('Bruno Díaz')).toBeInTheDocument())
    expect(m.operador('ot-14')).toBe('operario:2')
    expect(screen.getByLabelText('Por asignar: 0')).toBeInTheDocument()
    // La bitácora dice qué supervisor la asignó, como en la API real.
    expect(m.eventos('ot-14').at(-1)).toMatchObject({ tipo: 'ot_asignada', actor: 'supervisor:oculta', evidencia: { operador: 'operario:2' } })
  })

  it('reads names and progress from the list, without asking for each OT', async () => {
    m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', paso_id: 'p1', estado: 'verificado', detalle: 'ok' })
    entrarComo(SUPERVISORA)
    const pedidas = await lecturasDeOt(async () => {
      abrir('/supervisor')
      const ot12 = await tarjeta('ot-12')
      expect(within(ot12).getByText(`${PAUTA_DEMO.nombre} v${PAUTA_DEMO.version}`)).toBeInTheDocument()
      expect(within(ot12).getByText('1/6 pasos')).toBeInTheDocument()
    })
    expect(pedidas).toEqual([])
  })

  it('shows the pauta id when the names do not load', async () => {
    server.use(http.get(`${config.API_URL}/cliente/pautas`, () => new HttpResponse(null, { status: 500 })))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const ot14 = await tarjeta('ot-14')
    expect(within(ot14).getByText(PAUTA_DEMO.id)).toBeInTheDocument()
    expect(within(ot14).getByText('0/6 pasos')).toBeInTheDocument()
  })

  it('reassigns a handed-over OT', async () => {
    m.agregar('ot-12', { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen' })
    m.asignar('ot-12', null)
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const ot12 = await tarjeta('ot-12')
    expect(within(ot12).getByText('Entregada')).toBeInTheDocument()
    expect(within(ot12).getByText('Turno entregado por Ana Rojas')).toBeInTheDocument()
    await userEvent.click(within(ot12).getByRole('button', { name: 'Reasignar ot-12 a Bruno Díaz' }))
    await waitFor(() => expect(m.operador('ot-12')).toBe('operario:2'))
    expect(await screen.findByLabelText('Entregadas: 0')).toBeInTheDocument()
  })

  it('shows the rule when the API refuses the assignment', async () => {
    server.use(http.post(`${config.API_URL}/cliente/ots/:id/asignar`, () => HttpResponse.json({ regla: 'la OT ya tiene operador' }, { status: 409 })))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await userEvent.click(await screen.findByRole('button', { name: 'Asignar ot-14 a Ana Rojas' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('la OT ya tiene operador')
    expect(m.operador('ot-14')).toBeNull()
  })

  it('refreshes the list after a refused assignment, so a stale OT drops its buttons', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const boton = await screen.findByRole('button', { name: 'Asignar ot-14 a Ana Rojas' })
    m.asignar('ot-14', 'operario:2') // otro supervisor se adelantó
    await userEvent.click(boton)
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Asignar ot-14 a Ana Rojas' })).not.toBeInTheDocument())
    expect(within(await tarjeta('ot-14')).getByText('Bruno Díaz')).toBeInTheDocument()
  })

  it('shows a table on wide screens', async () => {
    vi.spyOn(window, 'matchMedia').mockImplementation(
      (query) => ({ matches: true, media: query, onchange: null, addEventListener: () => {}, removeEventListener: () => {}, addListener: () => {}, removeListener: () => {}, dispatchEvent: () => false }) as MediaQueryList,
    )
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const fila = (await screen.findByText('OT-14')).closest('tr')!
    expect(screen.getByRole('columnheader', { name: 'Avance' })).toBeInTheDocument()
    expect(within(fila).getByRole('button', { name: 'Asignar ot-14 a Ana Rojas' })).toBeInTheDocument()
    expect(within(screen.getByText('OT-12').closest('tr')!).getByText('Ana Rojas')).toBeInTheDocument()
  })

  it('orders a new OT from a company pauta: it shows up unassigned', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByLabelText('Por asignar: 1')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Pedir OT' }))
    const modal = await screen.findByRole('dialog', { name: 'Pedir una OT' })
    expect(within(modal).getByRole('button', { name: 'Pedir esta OT' })).toBeDisabled()
    await userEvent.click(await within(modal).findByRole('radio', { name: `${PAUTA_DEMO.nombre}` }))
    await userEvent.click(within(modal).getByRole('button', { name: 'Pedir esta OT' }))
    expect(await screen.findByText(`Pediste la OT-0004, ${PAUTA_DEMO.nombre}. Queda por asignar.`)).toBeInTheDocument()
    expect(await screen.findByLabelText('Por asignar: 2')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Asignar ot-0004 a Ana Rojas' })).toBeInTheDocument()
    expect(m.eventos('ot-0004')[0]).toMatchObject({ tipo: 'ot_abierta' })
  })

  it('shows why the API refused the order, inside the dialog', async () => {
    server.use(http.post(`${config.API_URL}/cliente/ots`, () => HttpResponse.json({ permiso: 'la pauta no está habilitada para Oculta' }, { status: 403 })))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await userEvent.click(await screen.findByRole('button', { name: 'Pedir OT' }))
    const modal = await screen.findByRole('dialog', { name: 'Pedir una OT' })
    await userEvent.click(await within(modal).findByRole('radio', { name: `${PAUTA_DEMO.nombre}` }))
    await userEvent.click(within(modal).getByRole('button', { name: 'Pedir esta OT' }))
    expect(await within(modal).findByRole('alert')).toHaveTextContent('la pauta no está habilitada para Oculta')
  })

  it('says so when the operators do not load, instead of offering no one', async () => {
    server.use(http.get(`${config.API_URL}/cliente/operadores`, () => new HttpResponse(null, { status: 500 })))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByText('No se pudo cargar a los operadores')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Asignar ot-14/ })).not.toBeInTheDocument()
  })

  it('says so when there are no OTs', async () => {
    server.use(http.get(`${config.API_URL}/cliente/ots`, () => HttpResponse.json([])))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByText('No hay órdenes de trabajo abiertas.')).toBeInTheDocument()
  })
})

it('the demo handover: Carla assigns, Ana sees it, hands over, Bruno takes it', async () => {
  entrarComo(SUPERVISORA)
  abrir('/supervisor')
  await userEvent.click(await screen.findByRole('button', { name: 'Asignar ot-14 a Ana Rojas' }))
  await waitFor(() => expect(m.operador('ot-14')).toBe('operario:1'))
  await userEvent.click(screen.getByRole('button', { name: 'Salir' }))

  await entrarConFormulario(ANA)
  expect(await tarjeta('ot-14')).toBeInTheDocument()
  // Ana entrega el turno desde la ejecución; acá se imita su llamada.
  m.agregar('ot-14', { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen' })
  m.asignar('ot-14', null)
  await userEvent.click(screen.getByRole('button', { name: 'Salir' }))
  await entrarConFormulario(ANA)
  expect(await tarjeta('ot-12')).toBeInTheDocument()
  expect(screen.queryByText('OT-14')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Salir' }))

  await entrarConFormulario(SUPERVISORA)
  await userEvent.click(await screen.findByRole('button', { name: 'Reasignar ot-14 a Bruno Díaz' }))
  await waitFor(() => expect(m.operador('ot-14')).toBe('operario:2'))
  await userEvent.click(screen.getByRole('button', { name: 'Salir' }))

  await entrarConFormulario(BRUNO)
  await userEvent.click(within(await tarjeta('ot-14')).getByRole('button', { name: /Comenzar|Continuar/ }))
  expect(await screen.findByText('ejecución de ot-14')).toBeInTheDocument()
})
