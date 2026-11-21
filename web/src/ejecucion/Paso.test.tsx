import { MantineProvider } from '@mantine/core'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ComponentProps } from 'react'
import type { PasoEstado, PasoPauta } from '../api/tipos'
import { PAUTA_DEMO, PAUTA_LOTO } from '../mocks/pauta'
import { tema } from '../tema'
import { Paso } from './Paso'

const enPauta = (id: string): PasoPauta => [...PAUTA_DEMO.pasos, ...PAUTA_LOTO.pasos].find((p) => p.id === id)!
const estado = (id: string, extra: Partial<PasoEstado> = {}): PasoEstado => {
  const p = enPauta(id)
  return { id, orden: p.orden, titulo: p.titulo, estado: 'no_verificado', control_critico: p.control_critico, capa: null, evidencia: null, detalle: null, ...extra }
}

function pintar(id: string, props: Partial<ComponentProps<typeof Paso>> = {}) {
  const onHecho = vi.fn()
  const onConfirmar = vi.fn()
  render(
    <MantineProvider theme={tema}>
      <Paso paso={estado(id)} pauta={enPauta(id)} ui="pendiente" aviso={null} cerradoPor={null} habilitado onHecho={onHecho} onConfirmar={onConfirmar} {...props} />
    </MantineProvider>,
  )
  return { onHecho, onConfirmar }
}

const boton = (nombre: string) => screen.queryByRole('button', { name: nombre })

describe('a step that closes on its own', () => {
  it('shows its instruction, says how it closes, and offers no button', () => {
    pintar('p1', { ui: 'en_curso' })
    expect(screen.getByText(enPauta('p1').instruccion)).toBeInTheDocument()
    expect(screen.getByText('Se cierra solo cuando el sensor lo marque.')).toBeInTheDocument()
    expect(boton('Hecho')).toBeNull()
    expect(boton('Ya lo hice')).toBeNull()
  })

  it('a camera step with a detection closes when the camera sees it, and says what it sees now', () => {
    pintar('l2', { ui: 'en_curso', vistas: [{ clase: 'mouse', conf: 0.92 }, { clase: 'cup', conf: 0.6 }] })
    expect(screen.getByText('Se cierra solo cuando la cámara lo vea.')).toBeInTheDocument()
    expect(screen.getByText('La cámara ve: mouse, cup')).toBeInTheDocument()
    expect(boton('Hecho')).toBeNull()
  })
})

describe('a step that closes by declaring', () => {
  it('a confirmation step offers Hecho', async () => {
    const { onHecho } = pintar('p6', { ui: 'en_curso' })
    await userEvent.click(boton('Hecho')!)
    expect(onHecho).toHaveBeenCalledOnce()
  })

  it('a camera step without a detection offers Hecho, which asks the camera', () => {
    pintar('p3', { ui: 'en_curso' })
    expect(boton('Hecho')).toBeInTheDocument()
    expect(screen.getByText('Al tocar «Hecho», la cámara lo revisa.')).toBeInTheDocument()
  })

  it('comprobando says it is checking', () => {
    pintar('p3', { ui: 'comprobando' })
    expect(screen.getByText('Comprobando…')).toBeInTheDocument()
    expect(boton('Hecho')).toBeNull()
  })
})

describe('when the API warns', () => {
  it('a skipped step shows why and asks for a reason before confirming', async () => {
    const { onConfirmar } = pintar('p1', { ui: 'warn', aviso: 'Te saltaste este paso: hiciste «Retirar la guarda» antes.' })
    expect(screen.getByText('Te saltaste este paso: hiciste «Retirar la guarda» antes.')).toBeInTheDocument()
    await userEvent.click(boton('Ya lo hice')!)
    expect(boton('Confirmar')).toBeDisabled()
    await userEvent.type(screen.getByLabelText('Motivo'), 'el reed está dañado; el candado está puesto')
    await userEvent.click(boton('Confirmar')!)
    expect(onConfirmar).toHaveBeenCalledWith('el reed está dañado; el candado está puesto')
  })

  it('a quick reason fills the motivo', async () => {
    const { onConfirmar } = pintar('p1', { ui: 'warn', aviso: 'x' })
    await userEvent.click(boton('Ya lo hice')!)
    await userEvent.click(boton('El sensor no lo marca')!)
    await userEvent.click(boton('Confirmar')!)
    expect(onConfirmar).toHaveBeenCalledWith('El sensor no lo marca')
  })

  it('Cancelar closes the reason without confirming', async () => {
    const { onConfirmar } = pintar('p1', { ui: 'warn', aviso: 'x' })
    await userEvent.click(boton('Ya lo hice')!)
    await userEvent.click(boton('Cancelar')!)
    expect(onConfirmar).not.toHaveBeenCalled()
    expect(screen.queryByLabelText('Motivo')).toBeNull()
  })

  it('a camera conflict offers to try again or to confirm', () => {
    pintar('p3', { paso: estado('p3', { estado: 'en_conflicto', capa: 3 }), ui: 'warn', aviso: 'la cámara responde que no (62%)' })
    expect(boton('Hecho')).toBeInTheDocument()
    expect(boton('Ya lo hice')).toBeInTheDocument()
  })

  it('no signal on a sensor step offers Ya lo hice', () => {
    pintar('p1', { ui: 'sin_senal' })
    expect(screen.getByText('Todavía no se marca.')).toBeInTheDocument()
    expect(boton('Ya lo hice')).toBeInTheDocument()
  })

  it('a confirmation step never offers Ya lo hice: it closes by declaring', () => {
    pintar('p6', { ui: 'sin_senal' })
    expect(boton('Ya lo hice')).toBeNull()
    expect(boton('Hecho')).toBeInTheDocument()
  })

  it('actions are disabled while the connection is down', () => {
    pintar('p3', { ui: 'warn', aviso: 'x', habilitado: false })
    expect(boton('Hecho')).toBeDisabled()
    expect(boton('Ya lo hice')).toBeDisabled()
  })
})

describe('a closed step', () => {
  it('confirmed by a person says who and why', () => {
    pintar('p1', {
      paso: estado('p1', { estado: 'verificado', evidencia: { tipo: 'persona', motivo: 'el reed está dañado' } }),
      ui: 'confirmado',
      cerradoPor: 'OP1',
    })
    expect(screen.getByText('Confirmado por OP1: «el reed está dañado»')).toBeInTheDocument()
  })

  it('verified says by what', () => {
    pintar('p1', { paso: estado('p1', { estado: 'verificado', capa: 1 }), ui: 'verificado' })
    expect(screen.getByText('por sensor')).toBeInTheDocument()
    expect(boton('Ya lo hice')).toBeNull()
  })

  it('a future step offers nothing', () => {
    pintar('p2', { ui: 'pendiente' })
    expect(screen.queryAllByRole('button')).toEqual([])
  })
})
