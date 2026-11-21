import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import type { PasoEstado } from '../api/tipos'
import { PAUTA_DEMO } from '../mocks/pauta'
import { tema } from '../tema'
import { Paso } from './Paso'

const pp1 = PAUTA_DEMO.pasos[0]
const p1: PasoEstado = {
  id: 'p1', orden: 1, titulo: pp1.titulo, estado: 'no_verificado', control_critico: true, capa: null, evidencia: null, detalle: null,
}

function pintar(props: Partial<ComponentProps<typeof Paso>> = {}) {
  const onYaLoHice = vi.fn()
  render(
    <MantineProvider theme={tema}>
      <Paso paso={p1} pauta={pp1} ui="pendiente" cerradoPor={null} onYaLoHice={onYaLoHice} {...props} />
    </MantineProvider>,
  )
  return onYaLoHice
}

it('warn shows the detail and sends the note on Confirmar', async () => {
  const onYaLoHice = pintar({ paso: { ...p1, estado: 'en_conflicto', capa: 1, detalle: 'reed_bloqueo = abierto' }, ui: 'warn' })
  expect(screen.getByText('reed_bloqueo = abierto')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Ya lo hice' }))
  await userEvent.type(screen.getByPlaceholderText('Nota (opcional)'), 'puse el candado')
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
  expect(onYaLoHice).toHaveBeenCalledWith('puse el candado')
})

it('an empty note is sent as no note', async () => {
  const onYaLoHice = pintar({ ui: 'sin_senal' })
  expect(screen.getByText('No llega la señal del sensor')).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Ya lo hice' }))
  await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
  expect(onYaLoHice).toHaveBeenCalledWith(undefined)
})

it('Cancelar closes the note without overriding', async () => {
  const onYaLoHice = pintar({ paso: { ...p1, estado: 'en_conflicto', detalle: 'x' }, ui: 'warn' })
  await userEvent.click(screen.getByRole('button', { name: 'Ya lo hice' }))
  await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
  expect(onYaLoHice).not.toHaveBeenCalled()
  expect(screen.queryByPlaceholderText('Nota (opcional)')).toBeNull()
})

it('sobrescrito says whose word closed it', () => {
  pintar({ paso: { ...p1, estado: 'sobrescrito' }, ui: 'sobrescrito', cerradoPor: 'OP1' })
  expect(screen.getByText('a la palabra de OP1')).toBeInTheDocument()
})

it('the current step shows its instruction', () => {
  pintar({ ui: 'en_curso' })
  expect(screen.getByText(pp1.instruccion)).toBeInTheDocument()
})

it('comprobando says it is checking', () => {
  pintar({ ui: 'comprobando' })
  expect(screen.getByText('Comprobando…')).toBeInTheDocument()
})

it('verificado and pendiente offer no Ya lo hice', () => {
  pintar({ paso: { ...p1, estado: 'verificado' }, ui: 'verificado' })
  expect(screen.queryByRole('button', { name: 'Ya lo hice' })).toBeNull()
})

it('pendiente offers no Ya lo hice either', () => {
  pintar({ ui: 'pendiente' })
  expect(screen.queryByRole('button', { name: 'Ya lo hice' })).toBeNull()
})
