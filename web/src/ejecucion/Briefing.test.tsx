import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ESCENARIOS } from '../mocks/escenarios'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { PERSONAS } from '../mocks/personas'
import { recordarNombres } from '../sesion/usuarios'
import { tema } from '../tema'
import { Briefing } from './Briefing'
import { relevoPendiente } from './estado'

function pintar(conAlerta = false) {
  recordarNombres(PERSONAS)
  const m = new Mundo(PAUTA_DEMO)
  ESCENARIOS.relevo!.preparar(m)
  if (conAlerta)
    m.agregar('ot-12', { tipo: 'alerta', actor: 'sistema', capa: 1, estado: 'en_conflicto', detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA.' })
  const bitacora = m.eventos('ot-12')
  const onRecibido = vi.fn()
  render(
    <MantineProvider theme={tema}>
      <Briefing ot={m.estado('ot-12')} bitacora={bitacora} alertas={m.alertasActivas('ot-12')} relevo={relevoPendiente(bitacora)!} onRecibido={onRecibido} />
    </MantineProvider>,
  )
  return onRecibido
}

it('lists how each step closed and where to resume', () => {
  pintar()
  expect(screen.getByText('Relevo de turno')).toBeInTheDocument()
  expect(screen.getByText(/Entregado por Ana Rojas a las \d\d:\d\d/)).toBeInTheDocument()
  expect(screen.getByText(/por sensor/)).toBeInTheDocument()
  expect(screen.getByText(/por la cámara/)).toBeInTheDocument()
  expect(screen.getByText(/confirmado por Ana Rojas/)).toBeInTheDocument()
  expect(screen.getByText(/Sigue en: 4\. Reinstalar la guarda/)).toBeInTheDocument()
  expect(screen.getByText(/Retomar desde p4/)).toBeInTheDocument()
})

it('shows inherited warnings', () => {
  pintar(true)
  expect(screen.getByText('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBeInTheDocument()
})

it('Recibido calls onRecibido', async () => {
  const onRecibido = pintar()
  await userEvent.click(screen.getByRole('button', { name: 'Recibido' }))
  expect(onRecibido).toHaveBeenCalledOnce()
})
