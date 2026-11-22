// El reporte de una OT contra el mock (MSW en Node): las mejoras sugeridas que deja.

import { MantineProvider } from '@mantine/core'
import { render, screen, within } from '@testing-library/react'
import { setupServer } from 'msw/node'
import { MemoryRouter } from 'react-router'
import { cerrarSolo, ESCENARIOS, otsBase, salto, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { entrarComo, SUPERVISORA } from '../mocks/personas'
import { tema } from '../tema'
import { Reporte } from './Reporte'

const sinEspera: Temporizador = () => {}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

const { pendiente, adelantado } = salto(PAUTA_DEMO)!

function abrir(otId: string, preparar: (m: Mundo) => void) {
  const m = new Mundo(PAUTA_DEMO)
  otsBase(m)
  preparar(m)
  server.resetHandlers(...crearHandlers(m, ESCENARIOS.feliz!, sinEspera))
  entrarComo(SUPERVISORA)
  render(
    <MantineProvider theme={tema}>
      <MemoryRouter>
        <Reporte otId={otId} alDia={0} />
      </MemoryRouter>
    </MantineProvider>,
  )
}

const desviar = (m: Mundo, otId: string) => {
  m.saltar(otId, pendiente, adelantado)
  cerrarSolo(m, otId, pendiente)
}

it('puts the suggested improvements on top, with the change, why, how it will be measured, and a link to review them', async () => {
  abrir('ot-12', (m) => {
    desviar(m, 'ot-12')
    desviar(m, 'ot-13')
  })
  const seccion = await screen.findByRole('region', { name: 'Mejoras sugeridas' })
  expect(within(seccion).getByText(new RegExp(`^Reescribe «${adelantado.titulo}»`))).toBeInTheDocument()
  expect(within(seccion).getByText(/no se hizo como dice la pauta en 2 de \d+ trabajos\./)).toBeInTheDocument()
  expect(within(seccion).getByText(/^Hoy falla en 2 de \d+ trabajos\./)).toBeInTheDocument()
  expect(within(seccion).queryByText(/mediana|desvío|p_valor/)).toBeNull()
  expect(within(seccion).getByRole('link', { name: 'Revisarlas en mejoras' })).toHaveAttribute('href', '/supervisor/mejoras')
})

it('with nothing to suggest there is no section', async () => {
  abrir('ot-12', () => {})
  expect(await screen.findByRole('region', { name: 'Reporte de la OT' })).toBeInTheDocument()
  expect(screen.queryByRole('region', { name: 'Mejoras sugeridas' })).not.toBeInTheDocument()
})
