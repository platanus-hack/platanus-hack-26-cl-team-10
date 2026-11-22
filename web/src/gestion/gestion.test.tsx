// Las pantallas de gestión de punta a punta contra el mock (MSW en Node), con las mismas rutas que App.

import { MantineProvider } from '@mantine/core'
import { act, render, screen, waitFor, within } from '@testing-library/react'
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
import type { Mejora, Persona } from '../api/tipos'
import { leerSesion, tokenDeSesion } from '../sesion/sesion'
import { tema } from '../tema'
import { Inicio } from './Inicio'
import { PaginaLogin } from './PaginaLogin'
import { PaginaOperador } from './PaginaOperador'
import { campana } from './campana'
import { PaginaProtocolos } from './PaginaProtocolos'
import { PaginaSupervisor } from './PaginaSupervisor'

const sinEspera: Temporizador = () => {}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
// Los espías de un test (la campana) no se le deben pegar al siguiente.
afterEach(() => vi.restoreAllMocks())

let m: Mundo
beforeEach(() => {
  m = new Mundo(PAUTA_DEMO)
  ESCENARIOS.feliz!.preparar(m)
  server.resetHandlers(...crearHandlers(m, ESCENARIOS.feliz!, sinEspera))
})

function Ejecucion() {
  return <p>ejecución de {useParams().id}</p>
}

function VistaEnVivo() {
  return <p>vista en vivo de {useParams().id}</p>
}

function abrir(ruta: string) {
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter initialEntries={[ruta]}>
        <Routes>
          <Route path="/login" element={<PaginaLogin />} />
          <Route path="/supervisor" element={<RequiereRol rol="supervisor"><PaginaSupervisor /></RequiereRol>} />
          <Route path="/supervisor/ot/:id" element={<RequiereRol rol="supervisor"><VistaEnVivo /></RequiereRol>} />
          <Route path="/supervisor/protocolos" element={<RequiereRol rol="supervisor"><PaginaProtocolos /></RequiereRol>} />
          <Route path="/operador" element={<RequiereRol rol="operador"><PaginaOperador /></RequiereRol>} />
          <Route path="/ot/:id" element={<RequiereRol rol="operador"><Ejecucion /></RequiereRol>} />
          <Route path="*" element={<Inicio />} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

/** La fila de una OT en la tabla del supervisor, o su tarjeta en la lista del operario. */
const tarjeta = async (ot: string) => (await screen.findByText(ot.toUpperCase())).closest<HTMLElement>('tr, .mantine-Card-root')!

/** Asigna desde el selector de la fila, como lo haría el supervisor: abre, elige el nombre. */
async function asignar(ot: string, nombre: string, verbo = 'Asignar') {
  const selector = (await screen.findAllByLabelText(`${verbo} ${ot}`))[0]!
  await userEvent.click(selector)
  // jsdom no posiciona el desplegable: sus opciones existen, pero quedan «ocultas». Se buscan en la fila de esa OT.
  await userEvent.click(await within(selector.closest('tr')!).findByRole('option', { name: nombre, hidden: true }))
}

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
  it('the logo opens a menu that pushes the page, with the sections and «Salir»; Escape closes it', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const menu = await screen.findByRole('complementary', { name: 'Menú' })
    expect(menu).toHaveAttribute('inert')
    await userEvent.click(screen.getByRole('button', { name: 'Abrir el menú' }))
    expect(menu).not.toHaveAttribute('inert')
    expect(document.documentElement.dataset.menu).toBe('abierto')
    expect(within(menu).getByRole('link', { name: 'Mejoras' })).toHaveAttribute('href', '/supervisor/mejoras')
    expect(within(menu).getByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(within(menu).getByText('Carla Muñoz')).toBeInTheDocument()
    await userEvent.keyboard('{Escape}')
    expect(menu).toHaveAttribute('inert')
    expect(document.documentElement.dataset.menu).toBeUndefined()
  })

  it('lists the active OTs in one table, with how many there are in each filter', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByText('Por asignar (1)')).toBeInTheDocument()
    expect(screen.getByText('Activas (3)')).toBeInTheDocument()
    const ids = screen.getAllByText(/^OT-\d+$/).map((e) => e.textContent)
    expect(ids).toEqual(['OT-14', 'OT-12', 'OT-13'])
    expect(within(await tarjeta('ot-12')).getByText('Ana Rojas')).toBeInTheDocument()
  })

  it('assigns an unassigned OT to an operator', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await asignar('ot-14', 'Bruno Díaz')
    await waitFor(async () => expect(within(await tarjeta('ot-14')).getByText('Bruno Díaz')).toBeInTheDocument())
    expect(m.operador('ot-14')).toBe('operario:2')
    expect(await screen.findByText('Por asignar (0)')).toBeInTheDocument()
    // La bitácora dice qué supervisor la asignó, como en la API real.
    expect(m.eventos('ot-14').at(-1)).toMatchObject({ tipo: 'ot_asignada', actor: 'supervisor:oculta', evidencia: { operador: 'operario:2' } })
  })

  it('reads names and progress from the list, and asks only the running OTs for their current step', async () => {
    m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', paso_id: 'p1', estado: 'verificado', detalle: 'ok' })
    entrarComo(SUPERVISORA)
    const pedidas = await lecturasDeOt(async () => {
      abrir('/supervisor')
      const ot12 = await tarjeta('ot-12')
      expect(within(ot12).getByText(`${PAUTA_DEMO.nombre} v${PAUTA_DEMO.version}`)).toBeInTheDocument()
      expect(within(ot12).getByText('1/6 pasos')).toBeInTheDocument()
    })
    // ot-12 ya empezó: se lee su paso en curso. Las demás no se piden una por una.
    expect(pedidas).toEqual(['/ot/ot-12'])
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
    expect(within(ot12).getByText('Turno entregado por Ana Rojas')).toBeInTheDocument()
    await asignar('ot-12', 'Bruno Díaz', 'Reasignar')
    await waitFor(() => expect(m.operador('ot-12')).toBe('operario:2'))
    expect(await screen.findByText('Por asignar (1)')).toBeInTheDocument()
  })

  it('shows the rule when the API refuses the assignment', async () => {
    server.use(http.post(`${config.API_URL}/cliente/ots/:id/asignar`, () => HttpResponse.json({ regla: 'la OT ya tiene operador' }, { status: 409 })))
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await asignar('ot-14', 'Ana Rojas')
    expect(await screen.findByRole('alert')).toHaveTextContent('la OT ya tiene operador')
    expect(m.operador('ot-14')).toBeNull()
  })

  it('refreshes the list after a refused assignment, so a stale OT drops its selector', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await tarjeta('ot-14')
    m.asignar('ot-14', 'operario:2') // otro supervisor se adelantó
    await asignar('ot-14', 'Ana Rojas')
    await waitFor(() => expect(screen.queryAllByLabelText('Asignar ot-14')).toHaveLength(0))
    expect(within(await tarjeta('ot-14')).getByText('Bruno Díaz')).toBeInTheDocument()
  })

  it('puts the OTs running now on top, the one that warns first', async () => {
    m.abrirSesion('ot-12', 'edge-2', 'operario:1')
    m.abrirSesion('ot-13', config.EDGE_ID, 'operario:2')
    m.agregar('ot-13', { tipo: 'veredicto', actor: 'sistema', paso_id: m.pauta.pasos[0].id, estado: 'en_conflicto', capa: 2, detalle: 'La cámara no ve el candado puesto.', evidencia: { tipo: 'camara' } })
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await tarjeta('ot-13')
    await waitFor(() => expect(screen.getAllByText(/^OT-\d+$/).map((e) => e.textContent)).toEqual(['OT-13', 'OT-12', 'OT-14']))
    await userEvent.click(screen.getByText('Con alerta (1)'))
    expect(screen.getAllByText(/^OT-\d+$/).map((e) => e.textContent)).toEqual(['OT-13'])
  })

  it('finds an OT by operator, OT or pauta, and says so when nothing matches', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await tarjeta('ot-12')
    await userEvent.type(screen.getByLabelText('Buscar OT, operario o pauta'), 'ana')
    expect(screen.getAllByText(/^OT-\d+$/).map((e) => e.textContent)).toEqual(['OT-12'])
    await userEvent.clear(screen.getByLabelText('Buscar OT, operario o pauta'))
    await userEvent.type(screen.getByLabelText('Buscar OT, operario o pauta'), 'nadie-asi')
    expect(screen.getByText('Nada coincide con la búsqueda.')).toBeInTheDocument()
  })

  it('the completed OTs live in their own filter, out of the daily view', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByText('Completas (0)')).toBeInTheDocument()
    expect(screen.getByText('Activas (3)')).toBeInTheDocument()
  })

  it('a warning from the station lights up its card and says why on hover, without raising the red bar', async () => {
    m.abrirSesion('ot-13', config.EDGE_ID, 'operario:2')
    m.agregar('ot-13', { tipo: 'veredicto', actor: 'sistema', paso_id: m.pauta.pasos[0].id, estado: 'en_conflicto', capa: 2, detalle: 'La cámara no ve el candado puesto.', evidencia: { tipo: 'camara' } })
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const ot13 = await tarjeta('ot-13')
    expect(ot13).toHaveAttribute('data-nivel', 'warning')
    expect(within(ot13).getByText('Atención')).toBeInTheDocument()
    expect(within(ot13).getByLabelText('Atención: La cámara no ve el candado puesto.')).toBeInTheDocument()
    expect(within(ot13).getByText('Bruno Díaz')).toBeInTheDocument()
    expect(await tarjeta('ot-12')).not.toHaveAttribute('data-nivel')
    expect(screen.queryByRole('alert', { name: 'Incidentes en curso' })).toBeNull()
  })

  it('a «detente» lights its card in red, with the reason', async () => {
    m.abrirSesion('ot-13', config.EDGE_ID, 'operario:2')
    m.agregar('ot-13', { tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA.', evidencia: { tipo: 'sensor', clave: 'seguridad:g' } })
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const ot13 = await tarjeta('ot-13')
    expect(ot13).toHaveAttribute('data-nivel', 'error')
    expect(within(ot13).getByLabelText(/: GUARDA ABIERTA\.$/)).toBeInTheDocument()
  })

  it('a click anywhere on a card opens its live view', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await userEvent.click(within(await tarjeta('ot-12')).getByText('Ana Rojas'))
    expect(await screen.findByText('vista en vivo de ot-12')).toBeInTheDocument()
  })

  it('orders a new OT from a company pauta: it shows up unassigned', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByText('Por asignar (1)')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Pedir OT' }))
    const modal = await screen.findByRole('dialog', { name: 'Pedir una OT' })
    expect(within(modal).getByRole('button', { name: 'Pedir esta OT' })).toBeDisabled()
    await userEvent.click(await within(modal).findByRole('radio', { name: `${PAUTA_DEMO.nombre}` }))
    await userEvent.click(within(modal).getByRole('button', { name: 'Pedir esta OT' }))
    expect(await screen.findByText(`Pediste la OT-0004, ${PAUTA_DEMO.nombre}. Queda por asignar.`)).toBeInTheDocument()
    expect(await screen.findByText('Por asignar (2)')).toBeInTheDocument()
    expect((await screen.findAllByLabelText('Asignar ot-0004'))[0]).toBeInTheDocument()
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

  it('shows how each OT is going, except the unassigned ones', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(within(await tarjeta('ot-12')).getByText('Todo bien')).toBeInTheDocument()
    expect(within(await tarjeta('ot-14')).queryByText('Todo bien')).toBeNull()
  })

  it('every OT opens its live view, from its id or from its row', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(within(await tarjeta('ot-12')).getByRole('link', { name: 'OT-12' })).toHaveAttribute('href', '/supervisor/ot/ot-12')
    await userEvent.click(within(await tarjeta('ot-12')).getByText(PAUTA_DEMO.nombre, { exact: false }))
    expect(await screen.findByText('vista en vivo de ot-12')).toBeInTheDocument()
  })

  it('a new incident raises the red bar and chimes once; Ver en vivo opens it', async () => {
    const sonar = vi.spyOn(campana, 'sonar').mockImplementation(() => {})
    m.abrirSesion('ot-13', config.EDGE_ID, 'operario:2')
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await tarjeta('ot-13')
    expect(screen.queryByRole('alert', { name: 'Incidentes en curso' })).toBeNull()

    m.agregar('ot-13', {
      tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA.',
      evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: 'seguridad:guarda' },
    })
    act(() => void window.dispatchEvent(new Event('focus'))) // volver a la pestaña lee al tiro, sin esperar el reloj
    const barra = await screen.findByRole('alert', { name: 'Incidentes en curso' })
    expect(within(barra).getByText('OT-13 · Bruno Díaz')).toBeInTheDocument()
    // En una línea y sin mayúsculas gritadas: el detalle completo está en la vista en vivo.
    expect(within(barra).getByText(/Guarda abierta con energía viva$/)).toBeInTheDocument()
    expect(within(await tarjeta('ot-13')).getByText('Detente')).toBeInTheDocument()
    expect(sonar).toHaveBeenCalledOnce()

    // El mismo incidente no vuelve a sonar.
    act(() => void window.dispatchEvent(new Event('focus'))) // volver a la pestaña lee al tiro, sin esperar el reloj
    await waitFor(() => expect(within(screen.getByRole('alert', { name: 'Incidentes en curso' })).getByText('OT-13 · Bruno Díaz')).toBeInTheDocument())
    expect(sonar).toHaveBeenCalledOnce()

    await userEvent.click(within(screen.getByRole('alert', { name: 'Incidentes en curso' })).getByRole('link', { name: 'Ver ot-13 en vivo' }))
    expect(await screen.findByText('vista en vivo de ot-13')).toBeInTheDocument()
  })

  it('an incident already open on arrival shows, but does not chime', async () => {
    const sonar = vi.spyOn(campana, 'sonar').mockImplementation(() => {})
    m.abrirSesion('ot-13', config.EDGE_ID, 'operario:2')
    m.agregar('ot-13', { tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA.', evidencia: { tipo: 'sensor', clave: 'seguridad:g' } })
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByRole('alert', { name: 'Incidentes en curso' })).toBeInTheDocument()
    expect(sonar).not.toHaveBeenCalled()
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
  await asignar('ot-14', 'Ana Rojas')
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
  await asignar('ot-14', 'Bruno Díaz', 'Reasignar')
  await waitFor(() => expect(m.operador('ot-14')).toBe('operario:2'))
  await userEvent.click(screen.getByRole('button', { name: 'Salir' }))

  await entrarConFormulario(BRUNO)
  await userEvent.click(within(await tarjeta('ot-14')).getByRole('button', { name: /Comenzar|Continuar/ }))
  expect(await screen.findByText('ejecución de ot-14')).toBeInTheDocument()
})

describe('protocols', () => {
  it('lists each protocol with its pautas, and «Ver sus OT» opens the table filtered by that pauta', async () => {
    entrarComo(SUPERVISORA)
    abrir('/supervisor/protocolos')
    const protocolo = await screen.findByRole('region', { name: 'Aislamiento y bloqueo de energías' })
    expect(within(protocolo).getByText(PAUTA_DEMO.nombre)).toBeInTheDocument()
    expect(within(protocolo).getByText(/por empezar/)).toBeInTheDocument()
    await userEvent.click(within(protocolo).getByRole('link', { name: `Ver las OT de ${PAUTA_DEMO.nombre}` }))
    expect(await screen.findByText(/^Pauta: /)).toBeInTheDocument()
    expect(screen.getAllByText(/^OT-\d+$/)).toHaveLength(3)
    await userEvent.click(screen.getByRole('button', { name: 'Ver las OT de todas las pautas' }))
    await waitFor(() => expect(screen.queryByText(/^Pauta: /)).toBeNull())
  })
})

describe('Factum recommendations on the supervisor screen', () => {
  const recomendacion = (detectada: boolean): Mejora => ({
    id: 'pauta-polin-estacion:v7:e1', tipo: 'desviacion', conformidad: null, ots: ['ot-11', 'ot-12', 'ot-13'], aplicable: true, por_que_no: null, pauta: 'pauta-polin-estacion', nombre: 'Cambio de polín en la cinta', version: 7,
    paso: 'e1', titulo: 'Apagar el motor', control_critico: false, ejecuciones: 3, ots_con_senal: 3, operarios_distintos: 2,
    senales: { seguridad: 3, orden: 0, control: 0, conflicto: 0, persona: 0, observacion: 0 }, observaciones: [], revision: null, validacion: null, motivo: '«Apagar el motor» tuvo señales en 3 de 3 OT',
    sugerencia: 'Con este paso todavía abierto se dio una condición de peligro.',
    recurrencia: { ots_con_senal: 3, ots: 3, tasa: 1, tasa_del_resto: 0.05, p_valor: 0.0001, recurrente: true },
    detectada: detectada ? { ot: 'ot-13', evento: 40, ts: '2026-11-21T22:10:00+00:00' } : null,
    estado: 'abierta',
  })

  it('appears and chimes as soon as Factum detects the pattern, summarized per pauta and without naming the operator', async () => {
    const sonar = vi.spyOn(campana, 'sonar').mockImplementation(() => {})
    m.mejoras = [recomendacion(false)]
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    await tarjeta('ot-13')
    expect(screen.queryByRole('region', { name: 'Recomendaciones de Factum' })).toBeNull()

    m.mejoras = [recomendacion(true)]
    act(() => void window.dispatchEvent(new Event('focus'))) // volver a la pestaña lee al tiro, sin esperar el reloj
    const zona = await screen.findByRole('region', { name: 'Recomendaciones de Factum' })
    await userEvent.click(within(zona).getByRole('button', { name: /Cambio de polín en la cinta/ })) // la pauta parte cerrada
    expect(within(zona).getByText('Factum propone mejorar una pauta')).toBeInTheDocument()
    expect(within(zona).getByText('Cambio de polín en la cinta')).toBeInTheDocument()
    expect(within(zona).getByText('versión 8 · 1 cambio')).toBeInTheDocument()
    expect(within(zona).getByText(/^Reescribe «/)).toBeInTheDocument()
    expect(within(zona).getByRole('button', { name: /Se desvió en 3 de 3 OT/ })).toBeInTheDocument()
    expect(within(zona).queryByText(/Bruno|Ana/)).toBeNull()
    expect(sonar).toHaveBeenCalledOnce()
    expect(within(zona).getByRole('link', { name: 'Ver el detalle' })).toHaveAttribute('href', '/supervisor/mejoras')
  })

  it('one tap applies the whole summary: Factum builds the next version and the card leaves', async () => {
    const conformidad: Mejora = {
      ...recomendacion(true), id: 'conformidad:pauta-polin-estacion@7:prot-maqueta-01:M2:falta', tipo: 'conformidad', paso: '', ots: [],
      titulo: 'Ningún paso cumple M2 Bloquear el encendido', motivo: 'prot-maqueta-01: ningún paso cumple M2 Bloquear el encendido.',
      conformidad: { protocolo: 'prot-maqueta-01', control: 'M2', tipo: 'falta', detalle: 'ningún paso cumple M2 Bloquear el encendido', pasos: [], nombres: ['Bloquear el encendido'] },
      recurrencia: null, detectada: { ot: null, evento: null, ts: '2026-11-22T03:00:00+00:00' },
    }
    m.mejoras = [conformidad, recomendacion(true)]
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const zona = await screen.findByRole('region', { name: 'Recomendaciones de Factum' })
    await userEvent.click(within(zona).getByRole('button', { name: /Cambio de polín en la cinta/ })) // la pauta parte cerrada
    expect(within(zona).getAllByRole('button', { name: /Aplicar/ })).toHaveLength(1)
    expect(within(zona).getByText('Agrega «Bloquear el encendido»')).toBeInTheDocument()
    expect(within(zona).getByRole('button', { name: 'El protocolo lo exige y hoy ningún paso de la pauta lo hace.' })).toBeInTheDocument()
    expect(within(zona).queryByText(/prot-maqueta-01|M2/)).toBeNull()
    await userEvent.click(within(zona).getByRole('button', { name: 'Aplicar los 2 cambios' }))
    expect(await within(zona).findByText(/Factum armó la versión 8/)).toBeInTheDocument()
    expect(m.mejoras.map((x) => x.estado)).toEqual(['aceptada', 'aceptada'])
    expect(within(zona).queryByRole('button', { name: /Aplicar/ })).toBeNull()
  })

  it('what Factum will not change says why not, and is acknowledged instead of applied', async () => {
    m.mejoras = [{ ...recomendacion(true), aplicable: false, por_que_no: 'La evidencia no vio el paso y lo confirmó una persona: se revisa el sensor.' }]
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const zona = await screen.findByRole('region', { name: 'Recomendaciones de Factum' })
    await userEvent.click(within(zona).getByRole('button', { name: /Cambio de polín en la cinta/ })) // la pauta parte cerrada
    expect(within(zona).getByText(/^No cambia: «/)).toBeInTheDocument()
    expect(within(zona).getByRole('button', { name: /se revisa el sensor/ })).toBeInTheDocument()
    expect(within(zona).getByText('sin cambios a la pauta')).toBeInTheDocument()
    await userEvent.click(within(zona).getByRole('button', { name: 'Entendido' }))
    await waitFor(() => expect(m.mejoras[0]!.estado).toBe('aceptada'))
  })

  it('«Ahora no» hides it until the next visit', async () => {
    m.mejoras = [recomendacion(true)]
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    const zona = await screen.findByRole('region', { name: 'Recomendaciones de Factum' })
    await userEvent.click(within(zona).getByRole('button', { name: /Cambio de polín en la cinta/ })) // la pauta parte cerrada
    await userEvent.click(within(zona).getByRole('button', { name: 'Ahora no' }))
    expect(screen.queryByRole('region', { name: 'Recomendaciones de Factum' })).toBeNull()
    expect(m.mejoras[0]!.estado).toBe('abierta')
  })

  it('a recommendation already detected on arrival shows, but does not chime', async () => {
    const sonar = vi.spyOn(campana, 'sonar').mockImplementation(() => {})
    m.mejoras = [recomendacion(true)]
    entrarComo(SUPERVISORA)
    abrir('/supervisor')
    expect(await screen.findByRole('region', { name: 'Recomendaciones de Factum' })).toBeInTheDocument()
    expect(sonar).not.toHaveBeenCalled()
  })
})
