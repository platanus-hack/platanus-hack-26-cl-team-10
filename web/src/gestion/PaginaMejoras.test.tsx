// La página de mejoras del supervisor contra el mock (MSW en Node).

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import { cerrarSolo, declararFeliz, ESCENARIOS, otsBase, salto, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { entrarComo, SUPERVISORA } from '../mocks/personas'
import { tema } from '../tema'
import { PaginaMejoras } from './PaginaMejoras'

const sinEspera: Temporizador = () => {}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

let m: Mundo
const { pendiente, adelantado } = salto(PAUTA_DEMO)!

/** El operario hace un paso posterior antes del control crítico y después lo corrige. */
function desviar(otId: string) {
  m.saltar(otId, pendiente, adelantado)
  cerrarSolo(m, otId, pendiente)
}

function abrir(preparar: () => void = () => {}) {
  m = new Mundo(PAUTA_DEMO)
  otsBase(m)
  preparar()
  server.resetHandlers(...crearHandlers(m, ESCENARIOS.feliz!, sinEspera))
  entrarComo(SUPERVISORA)
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter initialEntries={['/supervisor/mejoras']}>
        <Routes>
          <Route path="/supervisor/mejoras" element={<PaginaMejoras cadaMs={40} />} />
          <Route path="/supervisor" element={<p>lista</p>} />
        </Routes>
      </MemoryRouter>
    </MantineProvider>,
  )
}

const propuesta = () => screen.findByRole('article', { name: `Propuesta para «${adelantado.titulo}»` })

it('with no proposals it says how one is born', async () => {
  abrir()
  expect(await screen.findByText(/Todavía no hay propuestas/)).toBeInTheDocument()
  expect(screen.getByText(/nace cuando el mismo paso se desvía en dos o más OT/)).toBeInTheDocument()
})

it('a proposal shows the step, in how many OTs it deviated and what to review, never who', async () => {
  abrir(() => {
    desviar('ot-12')
    desviar('ot-13')
  })
  const p = await propuesta()
  expect(within(p).getByRole('heading', { name: adelantado.titulo })).toBeInTheDocument()
  expect(within(p).getByText('2 de 3 OT')).toBeInTheDocument()
  expect(within(p).getByText(/con 2 operarios distintos/)).toBeInTheDocument()
  expect(within(p).getByText('Por revisar')).toBeInTheDocument()
  expect(within(p).getByText(/^El paso se hace antes de su turno/)).toBeInTheDocument()
  expect(within(p).getByText('Se hizo antes de su turno (2)')).toBeInTheDocument()
  expect(p).not.toHaveTextContent(/Ana Rojas|Bruno Díaz/)
  // Estaba cuando se abrió la página: no es nueva.
  expect(within(p).queryByText('Nueva')).not.toBeInTheDocument()
})

it('applying accepts the proposal, says who did it and that Factum builds the next version', async () => {
  const user = userEvent.setup()
  abrir(() => {
    desviar('ot-12')
    desviar('ot-13')
  })
  const p = await propuesta()
  expect(within(p).getByText('Factum arma la versión siguiente con este cambio y la aprueba.')).toBeInTheDocument()
  await user.click(within(p).getByRole('button', { name: 'Aplicar' }))

  expect(await within(p).findByText('Aceptada')).toBeInTheDocument()
  expect(within(p).getByText(/^Aceptada por Carla Muñoz a las \d{2}:\d{2}/)).toBeInTheDocument()
  expect(within(p).queryByRole('button', { name: 'Aplicar' })).not.toBeInTheDocument()
  expect(m.revisionDe(`${PAUTA_DEMO.id}:v${PAUTA_DEMO.version}:${adelantado.id}`)).toMatchObject({ decision: 'aceptar', por: 'supervisor:oculta' })
})

it('discarding asks why first', async () => {
  const user = userEvent.setup()
  abrir(() => {
    desviar('ot-12')
    desviar('ot-13')
  })
  const p = await propuesta()
  await user.click(within(p).getByRole('button', { name: 'Descartar' }))

  const confirmar = within(p).getByRole('button', { name: 'Descartar la propuesta' })
  expect(confirmar).toBeDisabled()
  await user.type(within(p).getByRole('textbox', { name: 'Por qué se descarta' }), 'ya se corrigió en terreno')
  await user.click(confirmar)

  expect(await within(p).findByText('Descartada')).toBeInTheDocument()
  expect(within(p).getByText(/ya se corrigió en terreno/)).toBeInTheDocument()
})

it('a proposal born while the page is open shows up on its own, marked as new', async () => {
  abrir(() => desviar('ot-12'))
  expect(await screen.findByText(/Todavía no hay propuestas/)).toBeInTheDocument()

  // La segunda OT se desvía en el mismo paso: el servidor ya la cuenta como propuesta.
  desviar('ot-13')
  const p = await propuesta()
  expect(within(p).getByText('Nueva')).toBeInTheDocument()
  await waitFor(() => expect(screen.queryByText(/Todavía no hay propuestas/)).not.toBeInTheDocument())
})

it('the summary: complete OTs, how many with no deviations and what closed the steps', async () => {
  abrir(() => {
    for (const paso of PAUTA_DEMO.pasos) declararFeliz(m, 'ot-12', paso, 'operario:1')
    desviar('ot-13')
  })
  const resumen = await screen.findByRole('region', { name: 'Resumen' })
  const dato = (nombre: string) => within(resumen).getByText(nombre).closest('div')!
  await waitFor(() => expect(dato('OT completas')).toHaveTextContent('1'))
  expect(dato('Completas sin desviaciones')).toHaveTextContent('1')
  expect(dato('Propuestas por revisar')).toHaveTextContent('0')
  expect(within(resumen).getByText('Pasos cerrados con sensor o cámara')).toBeInTheDocument()
})

it('«Ver el cambio» shows each step before and after, why, citing the OTs, and that it keeps the critical controls', async () => {
  const user = userEvent.setup()
  abrir(() => {
    desviar('ot-12')
    desviar('ot-13')
  })
  const p = await propuesta()
  await user.click(within(p).getByRole('button', { name: 'Ver el cambio' }))

  const cambio = await within(p).findByRole('region', { name: 'Cambio propuesto' })
  expect(within(cambio).getByText(`De la versión ${PAUTA_DEMO.version} a la ${PAUTA_DEMO.version + 1}`)).toBeInTheDocument()
  expect(within(cambio).getByText('Reescribe un paso')).toBeInTheDocument()
  expect(within(cambio).getByText('Antes')).toBeInTheDocument()
  expect(within(cambio).getByText(adelantado.instruccion)).toBeInTheDocument()
  expect(within(cambio).getByText(/No sigas al paso siguiente hasta que este quede verificado/)).toBeInTheDocument()
  expect(within(cambio).getByText(/En ot-12 y ot-13 el paso dio señales/)).toBeInTheDocument()
  expect(within(cambio).getByText('El validador lo revisó: no saca ningún control crítico.')).toBeInTheDocument()

  await user.click(within(p).getByRole('button', { name: 'Ocultar el cambio' }))
  expect(within(p).queryByRole('region', { name: 'Cambio propuesto' })).not.toBeInTheDocument()
})

it('a proposal with nothing to change in the pauta says why, and has no Aplicar nor change to see', async () => {
  abrir(() => {
    m.mejoras = [{
      id: `${PAUTA_DEMO.id}:v${PAUTA_DEMO.version}:${adelantado.id}`, tipo: 'desviacion', conformidad: null,
      pauta: PAUTA_DEMO.id, nombre: PAUTA_DEMO.nombre, version: PAUTA_DEMO.version, paso: adelantado.id, titulo: adelantado.titulo,
      control_critico: adelantado.control_critico, ejecuciones: 3, ots_con_senal: 2, operarios_distintos: 2,
      senales: { seguridad: 0, orden: 0, control: 0, conflicto: 0, persona: 2, observacion: 0 }, observaciones: [],
      motivo: '', sugerencia: 'La evidencia no vio el paso y una persona lo confirmó.', recurrencia: null, detectada: null,
      ots: ['ot-12', 'ot-13'], aplicable: false,
      por_que_no: 'La evidencia no vio el paso y una persona lo confirmó: hay que revisar el sensor o la cámara, no la pauta.',
      estado: 'abierta', revision: null, validacion: null,
    }]
  })
  const p = await propuesta()
  expect(within(p).getByText(/hay que revisar el sensor o la cámara, no la pauta/)).toBeInTheDocument()
  expect(within(p).queryByRole('button', { name: 'Aplicar' })).not.toBeInTheDocument()
  expect(within(p).queryByRole('button', { name: 'Ver el cambio' })).not.toBeInTheDocument()
  expect(within(p).getByRole('button', { name: 'Descartar' })).toBeInTheDocument()
})
