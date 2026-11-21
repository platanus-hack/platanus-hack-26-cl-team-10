import { MantineProvider } from '@mantine/core'
import { render, screen, within } from '@testing-library/react'
import type { EstadoOt, Evento } from '../api/tipos'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO } from '../mocks/pauta'
import { tema } from '../tema'
import { BannerAlertas } from './BannerAlertas'

function pintar(armar: (m: Mundo) => void) {
  const m = new Mundo(PAUTA_DEMO)
  m.crearOt('ot-12', 'operario:1')
  armar(m)
  const ot: EstadoOt = m.estado('ot-12')
  const alertas: Evento[] = m.alertasActivas('ot-12')
  render(
    <MantineProvider theme={tema}>
      <BannerAlertas alertas={alertas} ot={ot} />
    </MantineProvider>,
  )
}

const paso = (id: string) => PAUTA_DEMO.pasos.find((p) => p.id === id)!

it('a skipped step says what was done early and where to fix it', () => {
  pintar((m) => m.saltar('ot-12', paso('p1'), paso('p2')))
  const banner = screen.getByRole('alert')
  expect(within(banner).getByText('Paso saltado')).toBeInTheDocument()
  expect(within(banner).getByText('Hiciste «Retirar la guarda» antes de «Cortar la energía y bloquear con candado».')).toBeInTheDocument()
  expect(within(banner).getByText('Haz el paso 1 o, si ya lo hiciste, confírmalo en el paso.')).toBeInTheDocument()
})

it('a lost control names the step that came undone', () => {
  pintar((m) => {
    m.agregar('ot-12', { tipo: 'veredicto', actor: 'sistema', paso_id: 'p1', estado: 'verificado', capa: 1, detalle: 'ok' })
    m.perderControl('ot-12', paso('p1'))
  })
  expect(screen.getByText('Control perdido')).toBeInTheDocument()
  expect(screen.getByText('«Cortar la energía y bloquear con candado» se deshizo. Vuelve a dejarlo como estaba.')).toBeInTheDocument()
})

it('a safety alert is a lockout tag that clears with its sensor, with nothing to override', () => {
  pintar((m) =>
    m.agregar('ot-12', {
      tipo: 'alerta', actor: 'sistema', capa: 1, estado: 'en_conflicto',
      detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.',
      evidencia: { tipo: 'sensor', clave: 'seguridad:GUARDA ABIERTA CON ENERGÍA VIVA.' },
    }),
  )
  expect(screen.getByText('Peligro')).toBeInTheDocument()
  expect(screen.getByText('GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.')).toBeInTheDocument()
  expect(screen.getByText('Se apaga sola cuando el sensor lo vea corregido.')).toBeInTheDocument()
  expect(screen.queryAllByRole('button')).toEqual([])
})

it('a signal warning is a caution, in yellow', () => {
  pintar((m) =>
    m.agregar('ot-12', { tipo: 'alerta', actor: 'sistema', capa: 2, estado: 'en_conflicto', detalle: 'vibracion fuera de lo normal', evidencia: { clave: 'senal:vibracion' } }),
  )
  expect(screen.getByText('Precaución')).toBeInTheDocument()
  expect(screen.getByText('vibracion fuera de lo normal')).toBeInTheDocument()
})

it('no alerts, no banner', () => {
  pintar(() => {})
  expect(screen.queryByRole('alert')).toBeNull()
})
