// La pantalla de ejecución entera contra el mock (MSW en Node, HTTP y WebSocket).
// Los tiempos de los escenarios corren 100 veces más rápido.

import { MantineProvider } from '@mantine/core'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { MemoryRouter, Route, Routes } from 'react-router'
import type { Pauta } from '../api/tipos'
import { config } from '../config'
import { ESCENARIOS, type NombreEscenario, type Temporizador } from '../mocks/escenarios'
import { crearHandlers } from '../mocks/handlers'
import { Mundo } from '../mocks/mundo'
import { PAUTA_DEMO, PAUTA_LOTO } from '../mocks/pauta'
import { guardarSesion } from '../sesion/sesion'
import { USUARIOS } from '../sesion/usuarios'
import { tema } from '../tema'
import { PaginaOt } from './PaginaOt'
import { tiempos } from './useEjecucion'
import { voz } from './voz'

const rapido: Temporizador = (ms, fn) => {
  setTimeout(fn, ms / 100)
}

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())

const tiemposOriginales = { ...tiempos }
afterEach(() => {
  Object.assign(tiempos, tiemposOriginales)
  vi.restoreAllMocks()
})

let m: Mundo
let dicho: string[]

function abrir(escenario: NombreEscenario, { ot = 'ot-12', usuario = USUARIOS[1], pauta = PAUTA_DEMO }: { ot?: string; usuario?: (typeof USUARIOS)[number]; pauta?: Pauta } = {}) {
  m = new Mundo(pauta)
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
  const boton = await screen.findByRole('button', { name: /^(Comenzar|Continuar|Entregar turno)$/ })
  if (boton.textContent !== 'Entregar turno') await userEvent.click(boton)
  await screen.findByRole('button', { name: 'Entregar turno' })
}

/** La tarjeta de un paso, por su título. */
const fila = (titulo: string) => screen.getByText(new RegExp(`^\\d\\. ${titulo}$`)).closest('.mantine-Paper-root') as HTMLElement
const enFila = (titulo: string, texto: string | RegExp) => within(fila(titulo)).queryByText(texto)
const boton = (nombre: string) => screen.queryByRole('button', { name: nombre })

describe('steps close on their own; Hecho only where the API needs it', () => {
  it('feliz (correa): sensor steps close alone, Hecho appears only on the camera and confirmation steps, and the OT completes', async () => {
    abrir('feliz')
    await entrar()
    await waitFor(() => expect(m.resumenes()[0].estado_general).toBe('en_ejecucion'))
    // p1 y p2 se cierran solos; p3 es de cámara sin detección: ahí aparece «Hecho».
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    await waitFor(() => expect(enFila('Cambiar el rodillo', 'por la cámara')).not.toBeNull())
    // p4 y p5 se cierran solos; p6 es de confirmación.
    await waitFor(() => expect(enFila('Prueba de detención', 'Cuando lo termines, toca «Hecho».')).not.toBeNull(), { timeout: 2000 })
    await userEvent.click(screen.getByRole('button', { name: 'Hecho' }))
    expect(await screen.findByText('OT completa')).toBeInTheDocument()
    // Solo se declaró donde la API lo necesita: la cámara sin detección y la confirmación.
    expect(m.eventos('ot-12').filter((e) => e.tipo === 'declaracion').map((e) => e.paso_id)).toEqual(['p3', 'p6'])
    expect(dicho).toEqual([])
  }, 10_000)

  it('feliz (LOTO): the whole OT closes with no button pressed', async () => {
    abrir('feliz', { pauta: PAUTA_LOTO })
    await entrar()
    expect(enFila('Poner el dispositivo de bloqueo', /./)).not.toBeNull()
    expect(await screen.findByText('OT completa', {}, { timeout: 4000 })).toBeInTheDocument()
    expect(m.eventos('ot-12').some((e) => e.tipo === 'declaracion')).toBe(false)
  }, 10_000)
})

describe('when the API warns that a step was skipped', () => {
  it('warn-sobrescrito: the skip is shown and spoken once; «Ya lo hice» with a reason confirms the step', async () => {
    abrir('warn-sobrescrito')
    await entrar()
    const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
    expect(within(banner).getByText('Paso saltado')).toBeInTheDocument()
    expect(enFila('Cortar la energía y bloquear con candado', 'Te saltaste este paso: hiciste «Retirar la guarda» antes.')).not.toBeNull()
    await waitFor(() => expect(dicho).toEqual(['Oye, te saltaste el paso 1: Cortar la energía y bloquear con candado. Hazlo antes de seguir.']))
    await userEvent.click(within(fila('Cortar la energía y bloquear con candado')).getByRole('button', { name: 'Ya lo hice' }))
    await userEvent.click(screen.getByRole('button', { name: 'El sensor no lo marca' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'Confirmado por OP1: «El sensor no lo marca»')).not.toBeNull())
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull())
    expect(m.eventos('ot-12').some((e) => e.evidencia?.tipo === 'persona' && e.actor === 'operario:1')).toBe(true)
    expect(dicho).toHaveLength(1)
  })

  it('warn-corregido: doing the skipped step clears the warning by itself', async () => {
    abrir('warn-corregido')
    await entrar()
    await screen.findByRole('alert', {}, { timeout: 2000 })
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'por sensor')).not.toBeNull())
  })
})

describe('other alerts', () => {
  it('alerta-seguridad: the lockout tag appears, is spoken in plain words, has nothing to override, and clears with the sensor', async () => {
    abrir('alerta-seguridad')
    await entrar()
    const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
    expect(within(banner).getByText('Peligro')).toBeInTheDocument()
    expect(within(banner).queryAllByRole('button')).toEqual([])
    await waitFor(() => expect(dicho).toContain('Guarda abierta con energía viva. Detener y aislar la energía antes de continuar.'))
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
  })

  it('control-perdido: the undone control is named and spoken, then clears', async () => {
    abrir('control-perdido')
    await entrar()
    const banner = await screen.findByRole('alert', {}, { timeout: 2000 })
    expect(within(banner).getByText('Control perdido')).toBeInTheDocument()
    await waitFor(() => expect(dicho).toEqual(['Oye, se deshizo el paso 1: Cortar la energía y bloquear con candado. Vuelve a dejarlo como estaba.']))
    await waitFor(() => expect(screen.queryByRole('alert')).toBeNull(), { timeout: 2000 })
  })

  it('camara-no: a camera conflict is shown but not spoken, and offers to try again or to confirm', async () => {
    abrir('camara-no')
    await entrar()
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    await waitFor(() => expect(enFila('Cambiar el rodillo', 'La cámara no lo ve (62 % de certeza). Revisa y toca «Hecho» de nuevo, o confírmalo si ya lo hiciste.')).not.toBeNull())
    expect(within(fila('Cambiar el rodillo')).getByRole('button', { name: 'Hecho' })).toBeInTheDocument()
    expect(within(fila('Cambiar el rodillo')).getByRole('button', { name: 'Ya lo hice' })).toBeInTheDocument()
    expect(dicho).toEqual([])
  })

  it('sin-senal: after the wait, a step whose evidence never comes offers «Ya lo hice»', async () => {
    tiempos.esperaEvidenciaMs = 100
    abrir('sin-senal')
    await entrar()
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', 'Todavía no se marca.')).not.toBeNull())
    await userEvent.click(within(fila('Cortar la energía y bloquear con candado')).getByRole('button', { name: 'Ya lo hice' }))
    await userEvent.type(screen.getByLabelText('Motivo'), 'el reed está dañado; el candado está puesto')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    await waitFor(() => expect(enFila('Cortar la energía y bloquear con candado', /^Confirmado por OP1/)).not.toBeNull())
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
    await userEvent.click(await screen.findByRole('button', { name: 'Hecho' }, { timeout: 2000 }))
    expect(await screen.findByText('la pauta ya está completa')).toBeInTheDocument()
    expect(screen.queryByText('Comprobando…')).toBeNull()
    await new Promise((r) => setTimeout(r, 100))
    expect(intentos).toBe(1)
    await userEvent.click(screen.getByRole('button', { name: 'Entendido' }))
    expect(screen.queryByText('la pauta ya está completa')).toBeNull()
  })

  it('api-caida: the strip shows while down, writes are disabled, and nothing is spoken twice', async () => {
    abrir('api-caida')
    await entrar()
    expect(await screen.findByText('Sin conexión, reintentando', {}, { timeout: 2000 })).toBeInTheDocument()
    expect(boton('Entregar turno')).toBeDisabled()
    await waitFor(() => expect(screen.queryByText('Sin conexión, reintentando')).toBeNull(), { timeout: 5000 })
    await waitFor(() => expect(boton('Entregar turno')).toBeEnabled())
    expect(dicho).toEqual([])
  }, 10_000)
})

describe('handover and navigation', () => {
  it('relevo: OP2 reads the briefing, signs it and continues at step 4', async () => {
    abrir('relevo', { usuario: USUARIOS[2] })
    expect(await screen.findByText('Relevo de turno')).toBeInTheDocument()
    expect(screen.getByText(/confirmado por OP1/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Recibido' }))
    await screen.findByRole('button', { name: 'Entregar turno' })
    expect(enFila('Reinstalar la guarda', 'Vuelve a montar la guarda y asegúrala.')).not.toBeNull()
    expect(enFila('Retirar la guarda', /^Confirmado por OP1/)).not.toBeNull()
    expect(m.eventos('ot-12').map((e) => [e.tipo, e.actor])).toContainEqual(['relevo_recibido', 'operario:2'])
    expect(m.resumenes()[0].operador).toBe('operario:2')
  })

  it('the operator who handed over does not get the briefing', async () => {
    abrir('relevo', { usuario: USUARIOS[1] })
    await screen.findByRole('button', { name: /^(Comenzar|Continuar|Entregar turno)$/ })
    expect(screen.queryByText('Relevo de turno')).toBeNull()
  })

  it('Entregar turno asks first, hands over and goes back to the list', async () => {
    abrir('feliz')
    await entrar()
    await userEvent.click(screen.getByRole('button', { name: 'Entregar turno' }))
    expect(screen.getByText('¿Entregar el turno?')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(m.eventos('ot-12').some((e) => e.tipo === 'relevo_entregado')).toBe(false)
    await userEvent.click(screen.getByRole('button', { name: 'Entregar turno' }))
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
    expect(m.resumenes()[0]).toMatchObject({ operador: null, estado_general: 'entregada' })
  })

  it('«Mis OT» goes back to the list without handing over', async () => {
    abrir('feliz')
    await entrar()
    await userEvent.click(screen.getByRole('link', { name: 'Mis OT' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
    expect(m.eventos('ot-12').some((e) => e.tipo === 'relevo_entregado')).toBe(false)
  })

  it('completa: shows the closing counts and the way back', async () => {
    abrir('completa')
    expect(await screen.findByText('OT completa')).toBeInTheDocument()
    expect(screen.getByText('6 de 6 pasos verificados')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('link', { name: 'Volver a mis OT' }))
    expect(await screen.findByText('mis OT')).toBeInTheDocument()
  })

  it('Recibido shows why the handover could not be signed', async () => {
    abrir('relevo', { usuario: USUARIOS[2] })
    server.use(http.post(`${config.API_URL}/ot/:id/relevo/recibir`, () => HttpResponse.json({ regla: 'el turno ya fue recibido' }, { status: 409 })))
    await userEvent.click(await screen.findByRole('button', { name: 'Recibido' }))
    expect(await screen.findByText('el turno ya fue recibido')).toBeInTheDocument()
    expect(screen.getByText('Relevo de turno')).toBeInTheDocument()
  })

  it('a failed session opening is retried until it works', async () => {
    tiempos.reintentoSesionMs = 100
    abrir('feliz')
    server.use(http.post(`${config.API_URL}/ot/:id/sesion`, () => HttpResponse.error(), { once: true }))
    await entrar()
    expect(await screen.findByText('Sin conexión, reintentando')).toBeInTheDocument()
    await waitFor(() => expect(m.snapshot('ot-12', 0).sesion).not.toBeNull())
  })

  it('an unknown OT says so and offers the way back', async () => {
    abrir('feliz', { ot: 'ot-99' })
    expect(await screen.findByText('Esta OT no existe')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Volver a mis OT' })).toBeInTheDocument()
  })
})
