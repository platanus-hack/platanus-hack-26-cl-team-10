// La pantalla de ejecución entera contra el mock (MSW en Node, HTTP y WebSocket).
// Los tiempos de los escenarios corren 100 veces más rápido.

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import { config } from '../config'
import { ESCENARIOS, type NombreEscenario, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { guardarSesion } from '../sesion/sesion'
import { USUARIOS } from '../sesion/usuarios'
import { tema } from '../tema'
import { PaginaOt } from './PaginaOt'
import { voz } from './voz'

const rapido: Temporizador = (ms, fn) => {
  setTimeout(fn, ms / 100)
}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

let m: Mundo
let dicho: string[]

function abrir(escenario: NombreEscenario, ot = 'ot-12', usuario = USUARIOS[1]) {
  m = new Mundo(PAUTA_DEMO)
  const e = ESCENARIOS[escenario]!
  e.preparar(m)
  server.resetHandlers(...crearHandlers(m, e, rapido))
  guardarSesion(usuario)
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
  const boton = await screen.findByRole('button', { name: /^(Comenzar|Continuar|Hecho)$/ })
  if (boton.textContent !== 'Hecho') await userEvent.click(boton)
}

const fila = (titulo: string) => screen.getByText(new RegExp(`\\d\\. ${titulo}`)).closest('.mantine-Paper-root') as HTMLElement

afterEach(() => vi.restoreAllMocks())

it('feliz: the session opens and the first sensor step closes alone', async () => {
  abrir('feliz')
  await entrar()
  await waitFor(() => expect(m.resumenes()[0].estado_general).toBe('en_ejecucion'))
  await waitFor(() => expect(within(fila('Retirar la guarda')).getByText('Saca la guarda que cubre el rodillo.')).toBeInTheDocument())
  expect(screen.getByText('1/6')).toBeInTheDocument()
  expect(dicho).toEqual([])
})

it('warn-sobrescrito: the conflict is spoken once and «Ya lo hice» closes it on the operator word', async () => {
  abrir('warn-sobrescrito')
  await entrar()
  const hecho = await screen.findByRole('button', { name: 'Hecho' })
  await waitFor(() => expect(hecho).toBeEnabled())
  await userEvent.click(hecho)
  const detalle = 'el operario declaró «hecho» y reed_bloqueo = abierto, se esperaba cerrado'
  await screen.findByText(detalle)
  await waitFor(() => expect(dicho).toEqual([detalle]))
  await userEvent.click(within(fila('Cortar la energía y bloquear con candado')).getByRole('button', { name: 'Ya lo hice' }))
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
  await screen.findByText('a la palabra de OP1')
  await waitFor(() => expect(within(fila('Retirar la guarda')).getByText('Saca la guarda que cubre el rodillo.')).toBeInTheDocument())
  expect(dicho).toHaveLength(1)
})

it('alerta-seguridad: the lockout-tag banner appears, speaks, and goes when the sensor clears', async () => {
  abrir('alerta-seguridad')
  await entrar()
  const texto = 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.'
  const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
  expect(within(banner).getByText('Peligro')).toBeInTheDocument()
  expect(within(banner).getByText(texto)).toBeInTheDocument()
  await waitFor(() => expect(dicho).toContain(texto))
  await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
})

it('camara-no: a camera conflict is shown but not spoken', async () => {
  abrir('camara-no')
  await entrar()
  const conflicto = 'el operario declaró «hecho» y la cámara responde que no (62%)'
  const hecho = await screen.findByRole('button', { name: 'Hecho' })
  for (let i = 0; i < 4 && !screen.queryByText(conflicto); i++) {
    await waitFor(() => expect(hecho).toBeEnabled())
    await userEvent.click(hecho)
  }
  await screen.findByText(conflicto)
  expect(dicho).toEqual([])
})

it('sin-senal: Hecho without a reading says the signal does not arrive', async () => {
  abrir('sin-senal')
  await entrar()
  const hecho = await screen.findByRole('button', { name: 'Hecho' })
  await waitFor(() => expect(hecho).toBeEnabled())
  await userEvent.click(hecho)
  await screen.findByText('No llega la señal del sensor')
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
  const hecho = await screen.findByRole('button', { name: 'Hecho' })
  await waitFor(() => expect(hecho).toBeEnabled())
  await userEvent.click(hecho)
  expect(await screen.findByText('la pauta ya está completa')).toBeInTheDocument()
  expect(screen.queryByText('Comprobando…')).toBeNull()
  await new Promise((r) => setTimeout(r, 100))
  expect(intentos).toBe(1)
  await userEvent.click(screen.getByRole('button', { name: 'Entendido' }))
  expect(screen.queryByText('la pauta ya está completa')).toBeNull()
})

it('api-caida: the strip shows while down, the stream comes back, nothing is spoken twice', async () => {
  abrir('api-caida')
  await entrar()
  expect(await screen.findByText('Sin conexión, reintentando', {}, { timeout: 2000 })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Hecho' })).toBeDisabled()
  await waitFor(() => expect(screen.queryByText('Sin conexión, reintentando')).toBeNull(), { timeout: 5000 })
  await waitFor(() => expect(screen.getByRole('button', { name: 'Hecho' })).toBeEnabled())
  expect(dicho).toEqual([])
}, 10_000)

it('an unknown OT says so instead of retrying forever', async () => {
  abrir('feliz', 'ot-99')
  expect(await screen.findByText('Esta OT no existe')).toBeInTheDocument()
})
