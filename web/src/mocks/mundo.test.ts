import type { EstadoPasoApi, MensajeStream } from '../api/tipos'
import { ErrorMock, Mundo } from './mundo'
import { PAUTA_DEMO, PAUTA_LOTO } from './pauta'

const pauta = PAUTA_DEMO
const paso = (id: string) => pauta.pasos.find((p) => p.id === id)!

function nuevo() {
  const m = new Mundo(pauta)
  m.crearOt('ot-1', 'operario:1')
  return m
}

const veredicto = (m: Mundo, paso_id: string, estado: EstadoPasoApi, capa: number | null = 1) =>
  m.agregar('ot-1', { tipo: 'veredicto', actor: 'sistema', detalle: `${paso_id} ${estado}`, paso_id, estado, capa })

const alerta = (m: Mundo) => m.agregar('ot-1', { tipo: 'alerta', actor: 'sistema', detalle: 'GUARDA ABIERTA', estado: 'en_conflicto', capa: 1 })

it('starts at the first step with an ot_abierta event', () => {
  const m = nuevo()
  expect(m.estado('ot-1').paso_actual).toBe('p1')
  expect(m.snapshot('ot-1', 0).bitacora.map((e) => e.tipo)).toEqual(['ot_abierta'])
})

it('the last verdict of a step wins', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'en_conflicto')
  veredicto(m, 'p1', 'verificado')
  expect(m.estado('ot-1').pasos[0]).toMatchObject({ estado: 'verificado', detalle: 'p1 verificado', capa: 1 })
})

it('is complete when every step is verified', () => {
  const m = nuevo()
  for (const p of pauta.pasos) veredicto(m, p.id, 'verificado')
  expect(m.estado('ot-1')).toMatchObject({ completa: true, paso_actual: null })
})

it('alerta_resuelta removes the alert', () => {
  const m = nuevo()
  const a = alerta(m)
  expect(m.alertasActivas('ot-1').map((e) => e.id)).toEqual([a.id])
  m.agregar('ot-1', { tipo: 'alerta_resuelta', actor: 'sistema', detalle: 'normalizada', capa: 1, evidencia: { resuelve: a.id } })
  expect(m.alertasActivas('ot-1')).toEqual([])
})

it('publishes evento then calificacion_ot', () => {
  const m = nuevo()
  const recibidos: MensajeStream[] = []
  m.suscribir('ot-1', (msg) => recibidos.push(msg))
  alerta(m)
  expect(recibidos.map((r) => r.tipo)).toEqual(['evento', 'calificacion_ot'])
  const c = recibidos[1]
  expect(c.tipo === 'calificacion_ot' && c.calificacion.nivel).toBe('error')
})

it('grades the OT by its worst live part, errors first', () => {
  const m = nuevo()
  expect(m.calificacion('ot-1')).toEqual({ nivel: 'ok', certeza: 1, capa: null, motivos: ['sin nada que calificar'], avisos: [] })
  veredicto(m, 'p1', 'verificado')
  veredicto(m, 'p3', 'en_conflicto', 3)
  alerta(m)
  const c = m.calificacion('ot-1')
  expect(c.nivel).toBe('error')
  expect(c.avisos.map((a) => a.nivel)).toEqual(['error', 'warning'])
})

it('snapshot honours desde', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'verificado')
  const ultimo = veredicto(m, 'p2', 'verificado')
  expect(m.snapshot('ot-1', ultimo.id - 1).bitacora.map((e) => e.id)).toEqual([ultimo.id])
})

it('calls alCambiarPaso when the current step moves', () => {
  const m = nuevo()
  const vistos: string[] = []
  m.alCambiarPaso = (_ot, p) => vistos.push(p.id)
  veredicto(m, 'p1', 'en_conflicto')
  veredicto(m, 'p1', 'verificado')
  expect(vistos).toEqual(['p2'])
})

describe('confirmar', () => {
  it('closes the current step on a person word, keeping who, why and what the sensor read', () => {
    const m = nuevo()
    m.leer('reed_bloqueo', 'abierto')
    const r = m.confirmar('ot-1', 'p1', 'supervisor:1', 'el reed está dañado; el candado está puesto, lo vi')
    expect(r).toMatchObject({ paso: 'p1', estado: 'verificado', capa: null, interrumpe: false })
    const ev = m.eventos('ot-1').at(-1)!
    expect(ev).toMatchObject({
      tipo: 'veredicto',
      actor: 'supervisor:1',
      estado: 'verificado',
      capa: null,
      declarado: 'el reed está dañado; el candado está puesto, lo vi',
      evidencia: { tipo: 'persona', motivo: 'el reed está dañado; el candado está puesto, lo vi', contra: { sensor: 'reed_bloqueo', valor: 'abierto', espera: 'cerrado' } },
      detalle: 'supervisor:1 confirma «Cortar la energía y bloquear con candado» contra la evidencia (reed_bloqueo = abierto, se esperaba cerrado): el reed está dañado; el candado está puesto, lo vi',
      calificacion: { nivel: 'warning' },
    })
    expect(m.estado('ot-1').paso_actual).toBe('p2')
  })

  it('refuses what the API refuses', () => {
    const m = nuevo()
    const regla = (fn: () => unknown) => {
      try {
        fn()
      } catch (e) {
        return e instanceof ErrorMock ? [e.status, e.message] : e
      }
      return 'no falló'
    }
    expect(regla(() => m.confirmar('ot-1', 'p2', 'operario:1', 'x'))).toEqual([409, 'solo se confirma el paso en curso (p1): el orden lo impone la app'])
    expect(regla(() => m.confirmar('ot-1', 'p1', '', 'x'))).toEqual([409, 'un paso lo confirma una persona, no el sistema'])
    expect(regla(() => m.confirmar('ot-1', 'p1', 'operario:1', ' '))).toEqual([409, 'confirmar contra la evidencia necesita un motivo'])
    expect(regla(() => m.confirmar('ot-1', 'p9', 'operario:1', 'x'))).toEqual([404, 'paso p9'])
  })
})

describe('skip warnings', () => {
  it('saltar opens an ORDEN INVERTIDO alert that names both steps', () => {
    const m = nuevo()
    const a = m.saltar('ot-1', paso('p1'), paso('p2'))
    expect(a).toMatchObject({
      tipo: 'alerta',
      capa: 1,
      estado: 'en_conflicto',
      detalle: 'ORDEN INVERTIDO: «Retirar la guarda» (guarda = abierta) antes de «Cortar la energía y bloquear con candado».',
      evidencia: { tipo: 'orden', adelantado: 'p2', pendiente: 'p1', sensor: 'guarda', valor: 'abierta', clave: 'orden:p2' },
      calificacion: { nivel: 'error' },
    })
  })

  it('doing the skipped step resolves the warning', () => {
    const m = nuevo()
    const a = m.saltar('ot-1', paso('p1'), paso('p2'))
    veredicto(m, 'p1', 'verificado')
    expect(m.alertasActivas('ot-1')).toEqual([])
    expect(m.eventos('ot-1').at(-1)).toMatchObject({
      tipo: 'alerta_resuelta',
      evidencia: { resuelve: a.id, tipo: 'orden' },
      detalle: `Orden resuelto: se hizo el paso saltado (p1). ${a.detalle}`,
    })
  })

  it('confirming the skipped step resolves it and says who', () => {
    const m = nuevo()
    const a = m.saltar('ot-1', paso('p1'), paso('p2'))
    m.confirmar('ot-1', 'p1', 'operario:1', 'puse el candado')
    expect(m.alertasActivas('ot-1')).toEqual([])
    expect(m.eventos('ot-1').at(-1)?.detalle).toBe(`Orden resuelto: se hizo el paso saltado (p1, lo confirmó operario:1). ${a.detalle}`)
  })
})

it('a lost control opens and resolves with its sensor', () => {
  const m = nuevo()
  veredicto(m, 'p1', 'verificado')
  const a = m.perderControl('ot-1', paso('p1'))
  expect(a).toMatchObject({
    detalle: 'CONTROL PERDIDO: «Cortar la energía y bloquear con candado» se deshizo (reed_bloqueo = abierto, exige cerrado).',
    evidencia: { tipo: 'control', paso: 'p1', sensor: 'reed_bloqueo', valor: 'abierto', clave: 'control:p1' },
    calificacion: { nivel: 'error' },
  })
  m.reponerControl('ot-1', a)
  expect(m.alertasActivas('ot-1')).toEqual([])
  expect(m.eventos('ot-1').at(-1)?.detalle).toBe(`Control repuesto con reed_bloqueo = cerrado: ${a.detalle}`)
})

it('derives the general state of each OT', () => {
  const m = nuevo()
  m.crearOt('ot-2', null)
  const general = (id: string) => m.resumenes().find((r) => r.ot === id)?.estado_general
  expect(general('ot-1')).toBe('asignada')
  expect(general('ot-2')).toBe('sin_asignar')
  veredicto(m, 'p1', 'verificado')
  expect(general('ot-1')).toBe('en_ejecucion')
  m.agregar('ot-1', { tipo: 'relevo_entregado', actor: 'operario:1', detalle: 'resumen' })
  m.asignar('ot-1', null)
  expect(general('ot-1')).toBe('entregada')
  m.asignar('ot-1', 'operario:2')
  expect(general('ot-1')).toBe('en_ejecucion')
})

it('lists OTs with the fields of GET /ots, for either pauta', () => {
  expect(nuevo().resumenes()[0]).toMatchObject({
    ot: 'ot-1',
    pauta: 'pauta-correa-ct-01',
    version: 1,
    equipo: 'correa CT-01',
    paso_actual: 'p1',
    completa: false,
    operador: 'operario:1',
  })
  const loto = new Mundo(PAUTA_LOTO)
  loto.crearOt('ot-1', null)
  expect(loto.resumenes()[0]).toMatchObject({ pauta: 'pauta-loto-escritorio', paso_actual: 'l1' })
})
