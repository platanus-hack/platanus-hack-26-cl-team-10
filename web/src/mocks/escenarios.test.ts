import { PAUTA_DEMO } from './pauta'
import { ESCENARIOS, escenarioDeLaUrl, type Temporizador } from './escenarios'
import { Mundo } from './mundo'

const pauta = PAUTA_DEMO
const t: Temporizador = (ms, fn) => {
  setTimeout(fn, ms)
}
const paso = (id: string) => pauta.pasos.find((p) => p.id === id)!

function preparado(nombre: keyof typeof ESCENARIOS = 'feliz') {
  const m = new Mundo(pauta)
  ESCENARIOS[nombre]!.preparar(m)
  return m
}

beforeEach(() => vi.useFakeTimers())
afterEach(() => vi.useRealTimers())

describe('url', () => {
  it('escenarioDeLaUrl falls back to feliz', () => {
    expect(escenarioDeLaUrl('?escenario=nope')).toBe('feliz')
    expect(escenarioDeLaUrl('')).toBe('feliz')
    expect(escenarioDeLaUrl('?escenario=feliz')).toBe('feliz')
  })
})

describe('feliz', () => {
  it('prepares three OTs: OP1, OP2 and one unassigned', () => {
    const m = preparado()
    expect(m.resumenes().map((r) => [r.ot, r.operador])).toEqual([
      ['ot-12', 'operario:1'],
      ['ot-13', 'operario:2'],
      ['ot-14', null],
    ])
  })

  it('a sensor step closes alone 4 s after it becomes current', () => {
    const m = preparado()
    ESCENARIOS.feliz!.alAvanzar!(m, 'ot-12', paso('p1'), t)
    vi.advanceTimersByTime(3999)
    expect(m.estado('ot-12').pasos[0].estado).toBe('no_verificado')
    vi.advanceTimersByTime(1)
    expect(m.estado('ot-12').pasos[0]).toMatchObject({
      estado: 'verificado',
      capa: 1,
      detalle: 'reed_bloqueo = cerrado, que es lo que el paso exige',
    })
  })

  it('does not close a sensor step that was already closed meanwhile', () => {
    const m = preparado()
    ESCENARIOS.feliz!.alAvanzar!(m, 'ot-12', paso('p1'), t)
    ESCENARIOS.feliz!.alDeclarar(m, 'ot-12', paso('p1'), 'operario:1', t)
    const antes = m.eventos('ot-12').length
    vi.advanceTimersByTime(4000)
    expect(m.eventos('ot-12').length).toBe(antes)
  })

  it('Hecho records the declaration and verifies by evidence type', () => {
    const m = preparado()
    const r = ESCENARIOS.feliz!.alDeclarar(m, 'ot-12', paso('p3'), 'operario:1', t)
    expect(r).toMatchObject({ paso: 'p3', estado: 'verificado', capa: 3, interrumpe: false })
    const [declaracion, veredicto] = m.eventos('ot-12').slice(-2)
    expect(declaracion).toMatchObject({ tipo: 'declaracion', actor: 'operario:1', paso_id: 'p3', declarado: 'hecho', detalle: 'declara sobre «Cambiar el rodillo»' })
    expect(veredicto).toMatchObject({ tipo: 'veredicto', estado: 'verificado', capa: 3, evidencia: { tipo: 'camara', respuesta: true, confianza: 0.91 } })
    expect(ESCENARIOS.feliz!.alDeclarar(m, 'ot-12', paso('p6'), 'operario:1', t)).toMatchObject({ estado: 'verificado', capa: null })
  })
})

describe('the execution scenarios', () => {
  const declarar = (m: Mundo, nombre: keyof typeof ESCENARIOS, id: string) =>
    ESCENARIOS[nombre]!.alDeclarar(m, 'ot-12', paso(id), 'operario:1', t)
  const estadoDe = (m: Mundo, id: string) => m.estado('ot-12').pasos.find((p) => p.id === id)!

  it('every name resolves from the URL', () => {
    for (const n of ['warn-corregido', 'warn-sobrescrito', 'alerta-seguridad', 'camara-no', 'sin-senal', 'relevo', 'api-caida', 'completa'])
      expect(escenarioDeLaUrl(`?escenario=${n}`)).toBe(n)
  })

  it('warn-corregido: conflict, then the sensor closes it after 5 s', () => {
    const m = preparado('warn-corregido')
    ESCENARIOS['warn-corregido']!.alAvanzar?.(m, 'ot-12', paso('p1'), t)
    const r = declarar(m, 'warn-corregido', 'p1')
    expect(r).toMatchObject({
      estado: 'en_conflicto',
      capa: 1,
      interrumpe: true,
      detalle: 'el operario declaró «hecho» y reed_bloqueo = abierto, se esperaba cerrado',
    })
    vi.advanceTimersByTime(4999)
    expect(estadoDe(m, 'p1').estado).toBe('en_conflicto')
    vi.advanceTimersByTime(1)
    expect(estadoDe(m, 'p1').estado).toBe('verificado')
  })

  it('warn-sobrescrito: the conflict stays until the operator overrides it', () => {
    const m = preparado('warn-sobrescrito')
    ESCENARIOS['warn-sobrescrito']!.alAvanzar?.(m, 'ot-12', paso('p1'), t)
    expect(declarar(m, 'warn-sobrescrito', 'p1')).toMatchObject({ estado: 'en_conflicto', interrumpe: true })
    vi.advanceTimersByTime(60_000)
    expect(estadoDe(m, 'p1').estado).toBe('en_conflicto')
  })

  it('warn-sobrescrito: later sensor steps still close alone', () => {
    const m = preparado('warn-sobrescrito')
    ESCENARIOS['warn-sobrescrito']!.alAvanzar?.(m, 'ot-12', paso('p2'), t)
    vi.advanceTimersByTime(4000)
    expect(estadoDe(m, 'p2').estado).toBe('verificado')
  })

  it('alerta-seguridad: error alert at 8 s, resolved at 18 s', () => {
    const m = preparado('alerta-seguridad')
    ESCENARIOS['alerta-seguridad']!.alAbrirSesion!(m, 'ot-12', t)
    vi.advanceTimersByTime(8000)
    const [a] = m.alertasActivas('ot-12')
    expect(a).toMatchObject({
      capa: 1,
      estado: 'en_conflicto',
      detalle: 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.',
      evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva' },
      calificacion: { nivel: 'error' },
    })
    vi.advanceTimersByTime(10_000)
    expect(m.alertasActivas('ot-12')).toEqual([])
    expect(m.eventos('ot-12').at(-1)).toMatchObject({ tipo: 'alerta_resuelta', evidencia: { resuelve: a.id } })
  })

  it('alerta-seguridad: an overwritten alert is not resolved again', () => {
    const m = preparado('alerta-seguridad')
    ESCENARIOS['alerta-seguridad']!.alAbrirSesion!(m, 'ot-12', t)
    vi.advanceTimersByTime(8000)
    const [a] = m.alertasActivas('ot-12')
    m.agregar('ot-12', { tipo: 'sobrescritura', actor: 'operario:1', detalle: 'ya lo corrigió', evidencia: { alerta_id: a.id } })
    vi.advanceTimersByTime(10_000)
    expect(m.eventos('ot-12').some((e) => e.tipo === 'alerta_resuelta')).toBe(false)
  })

  it('camara-no: the first camera answer is a silent conflict, the second verifies', () => {
    const m = preparado('camara-no')
    expect(declarar(m, 'camara-no', 'p3')).toMatchObject({
      estado: 'en_conflicto',
      capa: 3,
      interrumpe: false,
      detalle: 'el operario declaró «hecho» y la cámara responde que no (62%)',
    })
    expect(m.eventos('ot-12').at(-1)).toMatchObject({ evidencia: { tipo: 'camara', respuesta: false, confianza: 0.62 }, calificacion: { nivel: 'warning' } })
    expect(declarar(m, 'camara-no', 'p3')).toMatchObject({ estado: 'verificado', capa: 3 })
  })

  it('sin-senal: sensor steps never close alone and Hecho finds no reading', () => {
    const m = preparado('sin-senal')
    ESCENARIOS['sin-senal']!.alAvanzar?.(m, 'ot-12', paso('p1'), t)
    vi.advanceTimersByTime(60_000)
    expect(estadoDe(m, 'p1').estado).toBe('no_verificado')
    expect(declarar(m, 'sin-senal', 'p1')).toMatchObject({ estado: 'no_verificado', capa: 1, detalle: 'sin lectura de reed_bloqueo', interrumpe: false })
  })

  it('relevo: starts at p4 with a pending handover from OP1 to OP2', () => {
    const m = preparado('relevo')
    expect(m.operador('ot-12')).toBe('operario:2')
    expect(m.estado('ot-12').paso_actual).toBe('p4')
    expect(estadoDe(m, 'p2')).toMatchObject({ estado: 'sobrescrito' })
    const ultimo = m.eventos('ot-12').at(-1)!
    expect(ultimo).toMatchObject({ tipo: 'relevo_entregado', actor: 'operario:1' })
    expect(ultimo.detalle).toMatch(/p1, p3/)
    expect(ultimo.detalle).toMatch(/p2/)
    expect(ultimo.detalle).toMatch(/Retomar desde p4/)
  })

  it('api-caida: down at 5 s, back 15 s later', () => {
    const m = preparado('api-caida')
    ESCENARIOS['api-caida']!.alAbrirSesion!(m, 'ot-12', t)
    vi.advanceTimersByTime(5000)
    expect(m.caido).toBe(true)
    vi.advanceTimersByTime(15_000)
    expect(m.caido).toBe(false)
  })

  it('completa: the OT starts complete', () => {
    expect(preparado('completa').estado('ot-12').completa).toBe(true)
  })
})
