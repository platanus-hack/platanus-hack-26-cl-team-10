import type { Pauta } from '../api/tipos'
import { ESCENARIOS, escenarioDeLaUrl, salto, type NombreEscenario, type Temporizador } from './escenarios'
import { Mundo } from './mundo'
import { PAUTA_DEMO, PAUTA_LOTO, pautaDeLaUrl } from './pauta'

const t: Temporizador = (ms, fn) => {
  setTimeout(fn, ms)
}

function preparado(nombre: NombreEscenario = 'feliz', pauta: Pauta = PAUTA_DEMO) {
  const m = new Mundo(pauta)
  const e = ESCENARIOS[nombre]!
  e.preparar(m)
  // Como los handlers: cada paso que pasa a ser el actual arranca sus temporizadores.
  m.alCambiarPaso = (ot, paso) => e.alAvanzar?.(m, ot, paso, t)
  return { m, e }
}

/** Abrir la sesión de ot-12, como POST /ot/{id}/sesion. */
function sesion(m: Mundo, nombre: NombreEscenario) {
  const e = ESCENARIOS[nombre]!
  e.alAbrirSesion?.(m, 'ot-12', t)
  const actual = m.estado('ot-12').paso_actual
  if (actual) e.alAvanzar?.(m, 'ot-12', m.paso(actual)!, t)
}

const estadoDe = (m: Mundo, id: string) => m.estado('ot-12').pasos.find((p) => p.id === id)!

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())

describe('url', () => {
  it('every scenario resolves from the URL, anything else is feliz', () => {
    for (const n of Object.keys(ESCENARIOS)) expect(escenarioDeLaUrl(`?escenario=${n}`)).toBe(n)
    expect(escenarioDeLaUrl('?escenario=nope')).toBe('feliz')
    expect(escenarioDeLaUrl('')).toBe('feliz')
  })

  it('?pauta=loto picks the LOTO pauta', () => {
    expect(pautaDeLaUrl('?pauta=loto').id).toBe('pauta-loto-escritorio')
    expect(pautaDeLaUrl('').id).toBe('pauta-correa-ct-01')
  })

  it('the skip happens on the first critical step, before a later sensor step', () => {
    expect(salto(PAUTA_DEMO)).toMatchObject({ pendiente: { id: 'p1' }, adelantado: { id: 'p2' } })
    expect(salto(PAUTA_LOTO)).toMatchObject({ pendiente: { id: 'l2' }, adelantado: { id: 'l3' } })
  })
})

describe('feliz', () => {
  it('prepares three OTs: OP1, OP2 and one unassigned', () => {
    const { m } = preparado()
    expect(m.resumenes().map((r) => [r.ot, r.operador])).toEqual([
      ['ot-12', 'operario:1'],
      ['ot-13', 'operario:2'],
      ['ot-14', null],
    ])
  })

  it('sensor steps close alone; a camera step without detection waits for Hecho', () => {
    const { m } = preparado()
    sesion(m, 'feliz')
    vi.advanceTimersByTime(4000)
    expect(estadoDe(m, 'p1')).toMatchObject({ estado: 'verificado', capa: 1, detalle: 'reed_bloqueo = cerrado, que es lo que el paso exige' })
    vi.advanceTimersByTime(4000)
    expect(estadoDe(m, 'p2').estado).toBe('verificado')
    vi.advanceTimersByTime(60_000)
    expect(m.estado('ot-12').paso_actual).toBe('p3')
  })

  it('Hecho records the declaration and verifies by evidence type', () => {
    const { m, e } = preparado()
    const r = e.alDeclarar(m, 'ot-12', PAUTA_DEMO.pasos[2], 'operario:1', t)
    expect(r).toMatchObject({ paso: 'p3', estado: 'verificado', capa: 3, interrumpe: false })
    const [declaracion, veredicto] = m.eventos('ot-12').slice(-2)
    expect(declaracion).toMatchObject({ tipo: 'declaracion', actor: 'operario:1', paso_id: 'p3', declarado: 'hecho', detalle: 'declara sobre «Cambiar el rodillo»' })
    expect(veredicto).toMatchObject({ tipo: 'veredicto', estado: 'verificado', capa: 3, evidencia: { tipo: 'camara', respuesta: true, confianza: 0.91 } })
  })

  it('the LOTO pauta runs end to end with no Hecho at all', () => {
    const { m } = preparado('feliz', PAUTA_LOTO)
    sesion(m, 'feliz')
    vi.advanceTimersByTime(60_000)
    expect(m.estado('ot-12').completa).toBe(true)
    expect(m.eventos('ot-12').some((e) => e.tipo === 'declaracion')).toBe(false)
    expect(estadoDe(m, 'l2')).toMatchObject({ capa: 2, evidencia: { tipo: 'deteccion', clase: 'mouse', presente: true } })
  })
})

describe('skips', () => {
  it('warn-corregido: the skip warning is spoken, then doing the step resolves it', () => {
    const { m } = preparado('warn-corregido')
    sesion(m, 'warn-corregido')
    vi.advanceTimersByTime(3000)
    const [a] = m.alertasActivas('ot-12')
    expect(a).toMatchObject({ evidencia: { tipo: 'orden', pendiente: 'p1', adelantado: 'p2' }, calificacion: { nivel: 'error' } })
    expect(estadoDe(m, 'p1').estado).toBe('no_verificado')
    vi.advanceTimersByTime(5000)
    expect(estadoDe(m, 'p1').estado).toBe('verificado')
    expect(m.alertasActivas('ot-12')).toEqual([])
  })

  it('warn-sobrescrito: nothing closes the skipped step until a person confirms it', () => {
    const { m } = preparado('warn-sobrescrito')
    sesion(m, 'warn-sobrescrito')
    vi.advanceTimersByTime(60_000)
    expect(m.alertasActivas('ot-12')).toHaveLength(1)
    expect(estadoDe(m, 'p1').estado).toBe('no_verificado')
    m.confirmar('ot-12', 'p1', 'operario:1', 'puse el candado; el reed no marca')
    expect(m.alertasActivas('ot-12')).toEqual([])
  })

  it('a skip warning is raised once even if the session opens again', () => {
    const { m } = preparado('warn-sobrescrito')
    sesion(m, 'warn-sobrescrito')
    vi.advanceTimersByTime(3000)
    sesion(m, 'warn-sobrescrito')
    vi.advanceTimersByTime(3000)
    expect(m.eventos('ot-12').filter((e) => e.tipo === 'alerta')).toHaveLength(1)
  })

  it('the LOTO skip is on the lockout step, by the temperature sensor', () => {
    const { m } = preparado('warn-sobrescrito', PAUTA_LOTO)
    sesion(m, 'warn-sobrescrito')
    vi.advanceTimersByTime(60_000)
    expect(m.alertasActivas('ot-12')[0].detalle).toBe(
      'ORDEN INVERTIDO: «Verificar energía cero: equipo frío» (equipo = frio) antes de «Poner el dispositivo de bloqueo».',
    )
  })
})

describe('alerts', () => {
  it('alerta-seguridad: error alert at 8 s, resolved by the sensor at 18 s', () => {
    const { m } = preparado('alerta-seguridad')
    sesion(m, 'alerta-seguridad')
    vi.advanceTimersByTime(8000)
    const [a] = m.alertasActivas('ot-12')
    expect(a).toMatchObject({
      capa: 1,
      detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.',
      evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva' },
      calificacion: { nivel: 'error' },
    })
    expect(String(a.evidencia?.clave)).toMatch(/^seguridad:/)
    vi.advanceTimersByTime(10_000)
    expect(m.alertasActivas('ot-12')).toEqual([])
    expect(m.eventos('ot-12').at(-1)).toMatchObject({ tipo: 'alerta_resuelta', evidencia: { resuelve: a.id } })
  })

  it('control-perdido: the verified lockout comes undone, then is put back', () => {
    const { m } = preparado('control-perdido')
    sesion(m, 'control-perdido')
    vi.advanceTimersByTime(4000 + 3000)
    const [a] = m.alertasActivas('ot-12')
    expect(a).toMatchObject({ evidencia: { tipo: 'control', paso: 'p1' }, calificacion: { nivel: 'error' } })
    vi.advanceTimersByTime(8000)
    expect(m.alertasActivas('ot-12')).toEqual([])
  })
})

describe('the other execution scenarios', () => {
  it('camara-no: the first camera answer is a silent conflict, the second verifies', () => {
    const { m, e } = preparado('camara-no')
    const p3 = PAUTA_DEMO.pasos[2]
    expect(e.alDeclarar(m, 'ot-12', p3, 'operario:1', t)).toMatchObject({
      estado: 'en_conflicto',
      capa: 3,
      interrumpe: false,
      detalle: 'el operario declaró «hecho» y la cámara responde que no (62%)',
    })
    expect(m.eventos('ot-12').at(-1)).toMatchObject({ evidencia: { tipo: 'camara', respuesta: false, confianza: 0.62 }, calificacion: { nivel: 'warning' } })
    expect(e.alDeclarar(m, 'ot-12', p3, 'operario:1', t)).toMatchObject({ estado: 'verificado', capa: 3 })
  })

  it('sin-senal: nothing closes alone', () => {
    const { m } = preparado('sin-senal')
    sesion(m, 'sin-senal')
    vi.advanceTimersByTime(60_000)
    expect(estadoDe(m, 'p1').estado).toBe('no_verificado')
    expect(m.eventos('ot-12').filter((e) => e.tipo === 'veredicto')).toEqual([])
  })

  it('relevo: OP2 has it at step 4, step 2 was confirmed by OP1, the handover is pending', () => {
    const { m } = preparado('relevo')
    expect(m.operador('ot-12')).toBe('operario:2')
    expect(m.estado('ot-12').paso_actual).toBe('p4')
    expect(estadoDe(m, 'p2')).toMatchObject({ estado: 'verificado', evidencia: { tipo: 'persona' } })
    const ultimo = m.eventos('ot-12').at(-1)!
    expect(ultimo).toMatchObject({ tipo: 'relevo_entregado', actor: 'operario:1' })
    expect(ultimo.detalle).toBe(
      'Cambio de rodillo en correa transportadora v1 sobre correa CT-01. Verificados por la evidencia: p1, p3. Confirmados por una persona: p2. Retomar desde p4.',
    )
  })

  it('relevo works on the LOTO pauta too', () => {
    const { m } = preparado('relevo', PAUTA_LOTO)
    expect(m.estado('ot-12').paso_actual).toBe('l4')
  })

  it('api-caida: down at 5 s, back 15 s later', () => {
    const { m } = preparado('api-caida')
    sesion(m, 'api-caida')
    vi.advanceTimersByTime(5000)
    expect(m.caido).toBe(true)
    vi.advanceTimersByTime(15_000)
    expect(m.caido).toBe(false)
  })

  it('completa: the OT starts complete, on either pauta', () => {
    expect(preparado('completa').m.estado('ot-12').completa).toBe(true)
    expect(preparado('completa', PAUTA_LOTO).m.estado('ot-12').completa).toBe(true)
  })
})
