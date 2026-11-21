import { PAUTA_DEMO } from './pauta'
import { ESCENARIOS, escenarioDeLaUrl, sesionDeLaUrl, type Temporizador } from './escenarios'
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

  it('sesionDeLaUrl signs in a known demo user only', () => {
    expect(sesionDeLaUrl('?escenario=relevo&como=operario:2')?.nombre).toBe('OP2')
    expect(sesionDeLaUrl('?como=intruso')).toBeNull()
    expect(sesionDeLaUrl('')).toBeNull()
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
