// La vista en vivo del supervisor contra el mock (MSW en Node, HTTP y WebSocket).

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import { config } from '../config'
import { voz } from '../ejecucion/voz'
import { cerrarSolo, ESCENARIOS, salto, type NombreEscenario, type Temporizador } from '../mocks/escenarios'
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

// En el demo los avisos en voz suenan en esta vista (config.VOZ_EN); lo normal es que solo mire.
const vozEn = config.VOZ_EN
beforeEach(() => {
  config.VOZ_EN = 'supervisor'
})
afterAll(() => {
  config.VOZ_EN = vozEn
})

let m: Mundo

function abrir(ot: string, escenario: NombreEscenario = 'feliz', antes: () => void = () => {}) {
  m = new Mundo(PAUTA_DEMO)
  const e = ESCENARIOS[escenario]!
  e.preparar(m)
  antes()
  server.resetHandlers(...crearHandlers(m, e, sinEspera))
  entrarComo(SUPERVISORA)
  vi.spyOn(voz, 'decir').mockImplementation(() => {})
  vi.spyOn(voz, 'precalentar').mockResolvedValue()
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
// Los sensores van plegados: la lista está en la página aunque no se vea.
const sensores = () => screen.getByRole('list', { name: 'Lecturas de la estación', hidden: true })
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

  // Los pasos van numerados: los dos primeros verificados y el tercero en curso.
  const pasos = within(screen.getByRole('list', { name: 'Pasos de la OT' })).getAllByRole('listitem')
  expect(pasos).toHaveLength(6)
  expect(pasos[2]).toHaveTextContent('03')
  expect(pasos[2]).toHaveTextContent('Cambiar el rodillo')
  expect(pasos[2]).toHaveTextContent('En curso')
  expect(pasos[0]).toHaveTextContent('Verificado')
  expect(pasos[5]).toHaveTextContent('Pendiente')
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

it('an incident arrives live: a small red tag that opens the detail, marked open in the log, and «Ver en la bitácora» picks it', async () => {
  abrir('ot-13', 'incidente')
  await screen.findByText('En vivo')
  expect(screen.queryByRole('alert', { name: 'Alertas abiertas' })).toBeNull()

  m.leer('energia', 'viva')
  const alerta = m.agregar('ot-13', {
    tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA.',
    evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: 'seguridad:guarda' },
  })

  // Arriba queda una etiqueta roja chica; al tocarla, el detalle.
  const arriba = await screen.findByRole('alert', { name: 'Alertas abiertas' })
  expect(within(arriba).queryByText('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBeNull()
  await userEvent.click(within(arriba).getByRole('button', { expanded: false }))
  expect(await within(arriba).findByText('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBeInTheDocument()
  expect(await screen.findByText('Detente')).toBeInTheDocument()
  // La lectura llega por el stream, sin recargar.
  await waitFor(() => expect(within(sensor('Energía')).getByText('viva')).toBeInTheDocument())

  const item = document.getElementById(`bitacora-${alerta.id}`)!
  expect(item).toHaveTextContent('Peligro (abierta)')
  // jsdom no mide: el globo queda «oculto» hasta que se posiciona, aunque en el navegador se ve.
  await userEvent.click(within(arriba).getByRole('button', { name: 'Ver en la bitácora', hidden: true }))
  await waitFor(() => expect(document.getElementById(`bitacora-${alerta.id}`)).toHaveAttribute('data-elegido'))

  // Se resuelve: sale de arriba y queda en la bitácora como resuelta.
  m.agregar('ot-13', { tipo: 'alerta_resuelta', actor: 'sistema', capa: 1, detalle: 'Se normalizó', evidencia: { resuelve: alerta.id } })
  // Sale de arriba unos segundos después, para no parpadear si vuelve.
  await waitFor(() => expect(screen.queryByRole('alert', { name: 'Alertas abiertas' })).toBeNull(), { timeout: 5000 })
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
  expect(within(sensor('Temperatura')).getByRole('img', { name: 'Últimas lecturas de Temperatura', hidden: true })).toBeInTheDocument()
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

it('a small arrow next to the OT id goes back to the list', async () => {
  abrir('ot-13', 'incidente')
  expect(await screen.findByRole('link', { name: 'Volver a la lista de OT' })).toHaveAttribute('href', '/supervisor')
})

it('an OT of another company, or that does not exist, says so', async () => {
  abrir('ot-99')
  expect(await screen.findByText('Esta OT no está en tu empresa')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Todas las OT' })).toHaveAttribute('href', '/supervisor')
})

/** Cierra todos los pasos que faltan: los de sensor y detección con su evidencia, el resto con la cámara. */
function terminar(otId: string) {
  for (const paso of PAUTA_DEMO.pasos) {
    if (m.estado(otId).pasos.find((p) => p.id === paso.id)?.estado === 'verificado') continue
    if (paso.sensor || paso.deteccion) cerrarSolo(m, otId, paso)
    else m.agregar(otId, { tipo: 'veredicto', actor: 'sistema', paso_id: paso.id, estado: 'verificado', capa: 3, detalle: 'la cámara responde que sí', evidencia: { tipo: 'camara', respuesta: true, confianza: 0.9 } })
  }
}

describe('lo que la OT deja para mejorar la pauta', () => {
  const { pendiente, adelantado } = salto(PAUTA_DEMO)!
  const propuesta = () => screen.findByRole('status', { name: 'Propuesta de mejora' })

  it('the proposal waits for the OT to finish: while it runs only the alert shows, and at the end it appears on its own', async () => {
    abrir('ot-13', 'feliz', () => {
      // Otra OT ya se desvió ahí, y se corrigió.
      m.saltar('ot-12', pendiente, adelantado)
      cerrarSolo(m, 'ot-12', pendiente)
    })
    expect(await screen.findByText('En vivo')).toBeInTheDocument()

    // Esta es la segunda que se desvía en el mismo paso: el servidor ya cuenta la propuesta.
    m.saltar('ot-13', pendiente, adelantado)
    expect(await screen.findByRole('alert', { name: 'Alertas abiertas' })).toBeInTheDocument()
    await new Promise((listo) => setTimeout(listo, 150))
    expect(screen.queryByRole('status', { name: 'Propuesta de mejora' })).not.toBeInTheDocument()

    terminar('ot-13')
    const aviso = await propuesta()
    expect(within(aviso).getByText('Con esta OT nació una propuesta para mejorar la pauta')).toBeInTheDocument()
    // Primero que la OT terminó, después lo que dejó.
    const completa = screen.getByText(/^OT completa: los \d+ pasos quedaron verificados\.$/)
    expect(completa.compareDocumentPosition(aviso) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(within(aviso).getByText(`«${adelantado.titulo}» se desvió en 2 de 3 OT de la versión ${PAUTA_DEMO.version}.`)).toBeInTheDocument()
    const id = `${PAUTA_DEMO.id}:v${PAUTA_DEMO.version}:${adelantado.id}`
    expect(within(aviso).getByRole('link', { name: 'Revisar la propuesta' })).toHaveAttribute('href', `/supervisor/mejoras#${encodeURIComponent(id)}`)
  })

  it('an OT that finished with no deviation at that step does not show the proposal of the others', async () => {
    abrir('ot-14', 'feliz', () => {
      m.saltar('ot-12', pendiente, adelantado)
      m.saltar('ot-13', pendiente, adelantado)
    })
    expect(await screen.findByText('En vivo')).toBeInTheDocument()
    terminar('ot-14')
    expect(await screen.findByRole('button', { name: 'Ver el reporte' })).toBeInTheDocument()
    await new Promise((listo) => setTimeout(listo, 150))
    expect(screen.queryByRole('status', { name: 'Propuesta de mejora' })).not.toBeInTheDocument()
  })
})

describe('el reporte de la OT', () => {
  const reporte = () => screen.findByRole('region', { name: 'Reporte de la OT' })

  it('a complete OT opens on its report: what closed each step, with nobody writing it', async () => {
    abrir('ot-12', 'completa')
    const r = await reporte()
    expect(within(r).getByText(/^Armado desde la bitácora, con \d+ eventos\. Nadie lo escribió\.$/)).toBeInTheDocument()
    expect(within(r).getByText('Completa, sin desviaciones')).toBeInTheDocument()
    expect(within(r).getByText(`${PAUTA_DEMO.pasos.length} de ${PAUTA_DEMO.pasos.length}`)).toBeInTheDocument()

    const filas = within(within(r).getByRole('table', { name: 'Pasos' })).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(PAUTA_DEMO.pasos.length)
    const conSensor = PAUTA_DEMO.pasos.find((p) => p.sensor)!
    expect(filas[conSensor.orden - 1]).toHaveTextContent(`${conSensor.orden}. ${conSensor.titulo}`)
    expect(filas[conSensor.orden - 1]).toHaveTextContent(/Sensor: .+ = /)
  })

  it('a running OT shows the live view, and its report so far one tap away', async () => {
    const user = userEvent.setup()
    abrir('ot-13', 'incidente')
    expect(await screen.findByRole('region', { name: 'Cámara de la estación' })).toBeInTheDocument()
    await user.click(screen.getByRole('radio', { name: 'Reporte' }))

    const r = await reporte()
    expect(within(r).getByText('En curso')).toBeInTheDocument()
    expect(within(r).getByText('2 de 6')).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Cámara de la estación' })).not.toBeInTheDocument()
  })

  it('a deviation says what it was, at which step and how long it took to fix', async () => {
    const user = userEvent.setup()
    const { pendiente, adelantado } = salto(PAUTA_DEMO)!
    abrir('ot-12', 'feliz', () => {
      m.saltar('ot-12', pendiente, adelantado)
      cerrarSolo(m, 'ot-12', pendiente)
    })
    await user.click(await screen.findByRole('radio', { name: 'Reporte' }))

    const desviaciones = within(await reporte()).getByRole('list', { name: 'Desviaciones' })
    expect(within(desviaciones).getByText(`Orden invertido, en el paso ${adelantado.orden}`)).toBeInTheDocument()
    expect(within(desviaciones).getByText(/^Se corrigió en \d+ s$/)).toBeInTheDocument()
  })

  it('when the OT finishes while watching, it offers the report', async () => {
    const user = userEvent.setup()
    abrir('ot-13', 'incidente')
    expect(await screen.findByRole('region', { name: 'Cámara de la estación' })).toBeInTheDocument()
    expect(screen.getByText('En ejecución')).toBeInTheDocument()
    terminar('ot-13')
    const ver = await screen.findByRole('button', { name: 'Ver el reporte' })
    // El estado de arriba sigue a la OT: no se queda en «En ejecución».
    expect(screen.getByText('Completa')).toBeInTheDocument()
    expect(screen.queryByText('En ejecución')).not.toBeInTheDocument()
    await user.click(ver)
    expect(await reporte()).toBeInTheDocument()
  })
})

describe('the voice, only for the demo', () => {
  const guardaAbierta = () => {
    m.leer('energia', 'viva')
    m.agregar('ot-13', {
      tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA.',
      evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: 'seguridad:guarda' },
    })
  }

  it('the warnings sound on this view: an incident arriving live is spoken as an Alto, and the audio can be tried', async () => {
    const probar = vi.spyOn(voz, 'probar').mockImplementation(() => {})
    vi.spyOn(voz, 'desbloquear').mockResolvedValue()
    abrir('ot-13', 'incidente')
    await screen.findByText('En vivo')
    // Las frases de la OT se piden al abrirla, para que suenen sin esperar.
    await waitFor(() => expect(voz.precalentar).toHaveBeenCalled())
    // Lo que ya estaba en la bitácora al abrir no suena.
    expect(voz.decir).not.toHaveBeenCalled()

    guardaAbierta()
    await waitFor(() => expect(voz.decir).toHaveBeenCalledWith('Guarda abierta con energía viva.', { alto: true }))
    expect(voz.decir).toHaveBeenCalledTimes(1)

    await userEvent.click(screen.getByRole('button', { name: 'Probar audio' }))
    await waitFor(() => expect(probar).toHaveBeenCalled())
  })

  it('outside the demo the supervisor only watches: nothing is spoken and there is no audio to try', async () => {
    config.VOZ_EN = 'operario'
    abrir('ot-13', 'incidente')
    await screen.findByText('En vivo')
    guardaAbierta()
    await screen.findByRole('alert', { name: 'Alertas abiertas' })
    expect(voz.decir).not.toHaveBeenCalled()
    expect(voz.precalentar).not.toHaveBeenCalled()
    expect(screen.queryByRole('button', { name: 'Probar audio' })).toBeNull()
  })
})
