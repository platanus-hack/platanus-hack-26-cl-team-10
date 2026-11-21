// La vista en vivo del supervisor contra el mock (MSW en Node, HTTP y WebSocket).

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import { config } from '../config'
import { ESCENARIOS, type NombreEscenario, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { entrarComo, SUPERVISORA } from '../mocks/personas'
import { tema } from '../tema'
import { PaginaOtSupervisor } from './PaginaOtSupervisor'

const sinEspera: Temporizador = () => {}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
afterEach(() => vi.restoreAllMocks())

let m: Mundo

function abrir(ot: string, escenario: NombreEscenario = 'feliz') {
  m = new Mundo(PAUTA_DEMO)
  const e = ESCENARIOS[escenario]!
  e.preparar(m)
  server.resetHandlers(...crearHandlers(m, e, sinEspera))
  entrarComo(SUPERVISORA)
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter initialEntries={[`/supervisor/ot/${ot}`]}>
        <Routes>
          <Route path="/supervisor/ot/:id" element={<PaginaOtSupervisor />} />
          <Route path="/supervisor" element={<p>lista</p>} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

const bitacora = () => screen.getByRole('list', { name: 'Bitácora de la OT' })
const sensores = () => screen.getByRole('list', { name: 'Lecturas de la estación' })
/** La ficha de un sensor, por su nombre. */
const sensor = (nombre: string) => within(sensores()).getByText(nombre).closest('li')!

it('a running OT: its camera, the sensors with what the step expects, the steps and the log', async () => {
  abrir('ot-13', 'incidente')
  expect(await screen.findByText('En vivo')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'OT-13' })).toBeInTheDocument()
  expect(await screen.findByLabelText('Operador')).toHaveTextContent('Bruno Díaz')
  expect(screen.getByText(/^En la estación edge-1 desde las \d{2}:\d{2}$/)).toBeInTheDocument()

  const video = screen.getByRole('img', { name: 'Video en vivo de edge-1' })
  expect(video).toHaveAttribute('src', `${config.API_URL}/edge/edge-1/video.mjpg`)
  // Sobre el video, en qué paso va.
  const camara = screen.getByRole('region', { name: 'Cámara de la estación' })
  expect(within(camara).getByText('Paso 3 de 6')).toBeInTheDocument()
  expect(within(camara).getByText('Cambiar el rodillo')).toBeInTheDocument()

  const guarda = sensor('Guarda')
  expect(within(guarda).getByText('abierta')).toBeInTheDocument()

  expect(screen.getByText('3. Cambiar el rodillo')).toBeInTheDocument()
  expect(screen.getByText('En curso')).toBeInTheDocument()
  expect(within(bitacora()).getAllByRole('listitem').length).toBe(m.eventos('ot-13').length)
})

it('watching changes nothing: no session, no declaration', async () => {
  abrir('ot-12')
  expect(await screen.findByText('En vivo')).toBeInTheDocument()
  expect(m.sesionDe('ot-12')).toBeNull()
  expect(m.eventos('ot-12').map((e) => e.tipo)).toEqual(['ot_abierta'])
  expect(screen.getByText(/no está corriendo en una estación/)).toBeInTheDocument()
  expect(screen.queryByRole('list', { name: 'Lecturas de la estación' })).toBeNull()
})

it('an incident arrives live: red on top, marked open in the log, and «Ver en la bitácora» picks it', async () => {
  abrir('ot-13', 'incidente')
  await screen.findByText('En vivo')
  expect(screen.queryByRole('alert', { name: 'Alertas abiertas' })).toBeNull()

  m.leer('energia', 'viva')
  const alerta = m.agregar('ot-13', {
    tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA.',
    evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: 'seguridad:guarda' },
  })

  const arriba = await screen.findByRole('alert', { name: 'Alertas abiertas' })
  expect(within(arriba).getByText('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBeInTheDocument()
  expect(await screen.findByText('Detente')).toBeInTheDocument()
  // La lectura llega por el stream, sin recargar.
  await waitFor(() => expect(within(sensor('Energía')).getByText('viva')).toBeInTheDocument())

  const item = document.getElementById(`bitacora-${alerta.id}`)!
  expect(item).toHaveTextContent('Peligro (abierta)')
  await userEvent.click(within(arriba).getByRole('button', { name: 'Ver en la bitácora' }))
  await waitFor(() => expect(document.getElementById(`bitacora-${alerta.id}`)!.style.outline).toContain('solid'))

  // Se resuelve: sale de arriba y queda en la bitácora como resuelta.
  m.agregar('ot-13', { tipo: 'alerta_resuelta', actor: 'sistema', capa: 1, detalle: 'Se normalizó', evidencia: { resuelve: alerta.id } })
  await waitFor(() => expect(screen.queryByRole('alert', { name: 'Alertas abiertas' })).toBeNull())
  expect(within(bitacora()).getByText('Alerta resuelta')).toBeInTheDocument()
})

it('says why an OT is on «atención»: the reason, who says it and how sure', async () => {
  abrir('ot-13', 'atencion')
  expect(await screen.findByText('Atención')).toBeInTheDocument()
  const panel = await screen.findByRole('region', { name: 'Verificación' })
  expect(within(panel).getByText('La cámara no ve el rodillo nuevo en su lugar.')).toBeInTheDocument()
  expect(within(panel).getByText('Lo dice la cámara, con 100 % de certeza')).toBeInTheDocument()
  // No es una alerta: arriba no hay nada en rojo.
  expect(screen.queryByRole('alert', { name: 'Alertas abiertas' })).toBeNull()
})

it('an OT that goes well says so, with no warnings', async () => {
  abrir('ot-12')
  expect(await screen.findByText('Todo bien')).toBeInTheDocument()
  expect(within(await screen.findByRole('region', { name: 'Verificación' })).getByText('Sin avisos activos.')).toBeInTheDocument()
})

it('draws what the camera recognizes over the video, and clears it when the detections stop', async () => {
  abrir('ot-13', 'incidente')
  await screen.findByText('En vivo')
  m.ver('edge-1', [
    { clase: 'soda can', conf: 0.87, caja: [0.1, 0.2, 0.5, 0.6] },
    { clase: 'person', conf: 0.55, caja: [0.6, 0.1, 0.9, 0.95] },
  ])
  const polin = (await screen.findByText('polín 87 %')).parentElement!
  expect(polin).toHaveStyle({ left: '10%', top: '20%', width: '40%', height: '40%' })
  expect(polin).toHaveAttribute('data-seguro', 'true')
  expect(screen.getByText('person 55 %').parentElement).toHaveAttribute('data-seguro', 'false')
  // Sin detecciones nuevas, lo que se veía es viejo: se borra.
  await waitFor(() => expect(screen.queryByText('polín 87 %')).toBeNull(), { timeout: 2500 })
})

it('a number shows its unit and its trend; a reading that only came saved looks old until a new one arrives', async () => {
  abrir('ot-13', 'incidente')
  await screen.findByText('En vivo')
  // Lo que trajo el snapshot es lo último que el servidor guardó: no se sabe de cuándo.
  expect(within(sensor('Guarda')).getByText('Última lectura guardada')).toBeInTheDocument()

  for (const t of ['41.5', '40.9', '40.2']) m.leer('temp_c', t)
  await waitFor(() => expect(within(sensor('Temperatura')).getByText('40.2 °C')).toBeInTheDocument())
  expect(within(sensor('Temperatura')).getByRole('img', { name: 'Últimas lecturas de Temperatura' })).toBeInTheDocument()
  expect(within(sensor('Temperatura')).queryByText('Última lectura guardada')).toBeNull()

  m.leer('guarda', 'abierta')
  await waitFor(() => expect(within(sensor('Guarda')).queryByText('Última lectura guardada')).toBeNull())
  // Un sensor de texto no tiene tendencia.
  expect(within(sensor('Guarda')).queryByRole('img')).toBeNull()
})

it('shows the sensors of this pauta and the ones reading now, not every sensor the server remembers', async () => {
  abrir('ot-13', 'incidente')
  // La tabla de sensores del servidor es de todas las estaciones: esto quedó de otra pauta.
  m.leer('tierra', 'puesta')
  await screen.findByText('En vivo')
  expect(within(sensores()).getByText('Candado')).toBeInTheDocument()
  expect(within(sensores()).queryByText('Puesta a tierra')).toBeNull()

  m.leer('tierra', 'puesta')
  expect(await within(sensores()).findByText('Puesta a tierra')).toBeInTheDocument()
})

it('marks the sensor the step under way waits for, and whether it already reads that', async () => {
  abrir('ot-12', 'estacion-ocupada')
  m.abrirSesion('ot-12', 'edge-2', 'operario:1')
  await screen.findByText('En vivo')
  // El paso 1 espera el candado cerrado. El servidor guarda un «cerrado» de la OT de Bruno: no cuenta.
  expect(within(sensor('Candado')).getByText('El paso 1 espera «cerrado»')).toBeInTheDocument()
  expect(sensor('Candado')).toHaveAttribute('data-espera', 'falta')
  m.leer('reed_bloqueo', 'cerrado')
  await waitFor(() => expect(sensor('Candado')).toHaveAttribute('data-espera', 'calza'))
})

it('an OT of another company, or that does not exist, says so', async () => {
  abrir('ot-99')
  expect(await screen.findByText('Esta OT no está en tu empresa')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Supervisión' })).toHaveAttribute('href', '/supervisor')
})
