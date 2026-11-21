// Escenarios del mock: qué hace la API en cada caso que el front tiene que aguantar.
// Se elige con ?escenario=<nombre>; ?como=<actor> entra como ese usuario del demo.

import type { EstadoPasoApi, Evento, PasoPauta, RespuestaDeclarar } from '../api/tipos'
import { USUARIOS, type Usuario } from '../sesion/usuarios'
import type { Mundo } from './mundo'

export type Temporizador = (ms: number, fn: () => void) => void

export type Escenario = {
  preparar(m: Mundo): void
  alAbrirSesion?(m: Mundo, otId: string, t: Temporizador): void
  alAvanzar?(m: Mundo, otId: string, paso: PasoPauta, t: Temporizador): void
  alDeclarar(m: Mundo, otId: string, paso: PasoPauta, actor: string, t: Temporizador): RespuestaDeclarar
}

export type NombreEscenario =
  | 'feliz'
  | 'warn-corregido'
  | 'warn-sobrescrito'
  | 'alerta-seguridad'
  | 'camara-no'
  | 'sin-senal'
  | 'relevo'
  | 'api-caida'
  | 'completa'

export const SENSOR_TARDA_MS = 4000

// ─── Piezas que reusan los escenarios ───────────────────────────────────────

export function veredicto(
  m: Mundo,
  otId: string,
  paso: PasoPauta,
  estado: EstadoPasoApi,
  capa: number | null,
  detalle: string,
  evidencia: Record<string, unknown> | null = null,
): Evento {
  return m.agregar(otId, { tipo: 'veredicto', actor: 'sistema', paso_id: paso.id, estado, capa, detalle, evidencia, declarado: 'hecho' })
}

export function respuesta(ev: Evento): RespuestaDeclarar {
  return {
    paso: ev.paso_id ?? '',
    estado: ev.estado ?? 'no_verificado',
    capa: ev.capa,
    detalle: ev.detalle,
    interrumpe: ev.calificacion?.nivel === 'error',
  }
}

export function declaracion(m: Mundo, otId: string, paso: PasoPauta, actor: string): void {
  m.agregar(otId, { tipo: 'declaracion', actor, paso_id: paso.id, declarado: 'hecho', detalle: `declara sobre «${paso.titulo}»` })
}

const cerrado = (m: Mundo, otId: string, paso: PasoPauta) =>
  ['verificado', 'sobrescrito'].includes(m.estado(otId).pasos.find((p) => p.id === paso.id)?.estado ?? '')

/** El sensor del paso llega con el valor esperado. No hace nada si el paso ya se cerró. */
export function cerrarPorSensor(m: Mundo, otId: string, paso: PasoPauta): void {
  if (!paso.sensor || cerrado(m, otId, paso)) return
  const { id, espera } = paso.sensor
  veredicto(m, otId, paso, 'verificado', 1, `${id} = ${espera}, que es lo que el paso exige`, { tipo: 'sensor', id, valor: espera, espera })
}

/** «Hecho» en el camino feliz: se declara y la evidencia lo confirma. */
export function declararFeliz(m: Mundo, otId: string, paso: PasoPauta, actor: string): RespuestaDeclarar {
  declaracion(m, otId, paso, actor)
  switch (paso.tipo_evidencia) {
    case 'sensor': {
      const { id, espera } = paso.sensor!
      return respuesta(veredicto(m, otId, paso, 'verificado', 1, `${id} = ${espera}, que es lo que el paso exige`, { tipo: 'sensor', id, valor: espera, espera }))
    }
    case 'camara':
      return respuesta(veredicto(m, otId, paso, 'verificado', 3, 'la cámara responde que sí (91%)', { tipo: 'camara', pregunta: paso.pregunta_visual, respuesta: true, confianza: 0.91 }))
    case 'confirmacion':
      return respuesta(veredicto(m, otId, paso, 'verificado', null, 'lo cerró una persona declarando «hecho»'))
  }
}

/** Las tres OT de siempre: la de OP1 es la del demo. */
export function otsBase(m: Mundo, operadorOt12 = 'operario:1'): void {
  m.crearOt('ot-12', operadorOt12)
  m.crearOt('ot-13', 'operario:2')
  m.crearOt('ot-14', null)
}

/** El resumen que la API redacta al entregar el turno. */
export function resumenDeRelevo(m: Mundo, otId: string): string {
  const est = m.estado(otId)
  const con = (e: string) => est.pasos.filter((p) => p.estado === e).map((p) => p.id).join(', ') || 'ninguno'
  const sigue = est.paso_actual ? `Retomar desde ${est.paso_actual}.` : 'La pauta está completa.'
  return `${est.pauta} sobre ${est.equipo}. Verificados: ${con('verificado')}. Sobrescritos: ${con('sobrescrito')}. ${sigue}`
}

const primeraVez = (m: Mundo, otId: string, paso: PasoPauta) =>
  !m.eventos(otId).some((e) => e.tipo === 'veredicto' && e.paso_id === paso.id)

const CONTRARIO: Record<string, string> = {
  cerrado: 'abierto', abierto: 'cerrado', cerrada: 'abierta', abierta: 'cerrada', viva: 'cortada', cortada: 'viva',
}

/** El operario dice «hecho» y el sensor dice lo contrario: conflicto de capa 1, que suena. */
function conflictoDeSensor(m: Mundo, otId: string, paso: PasoPauta, actor: string): RespuestaDeclarar {
  declaracion(m, otId, paso, actor)
  const { id, espera } = paso.sensor!
  const leido = CONTRARIO[espera] ?? 'otro'
  return respuesta(veredicto(m, otId, paso, 'en_conflicto', 1,
    `el operario declaró «hecho» y ${id} = ${leido}, se esperaba ${espera}`,
    { tipo: 'sensor', id, valor: leido, espera }))
}

const ALERTA_GUARDA = 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.'

const feliz: Escenario = {
  preparar: (m) => otsBase(m),
  alAvanzar(m, otId, paso, t) {
    if (paso.tipo_evidencia === 'sensor') t(SENSOR_TARDA_MS, () => cerrarPorSensor(m, otId, paso))
  },
  alDeclarar: (m, otId, paso, actor) => declararFeliz(m, otId, paso, actor),
}

/** Igual que el camino feliz, salvo lo que se cambia. */
const como = (cambios: Partial<Escenario>): Escenario => ({ ...feliz, ...cambios })

const sinCierreSoloEnP1: Escenario['alAvanzar'] = (m, otId, paso, t) => {
  if (paso.id !== 'p1') feliz.alAvanzar!(m, otId, paso, t)
}

export const ESCENARIOS: Partial<Record<NombreEscenario, Escenario>> = {
  feliz,

  'warn-corregido': como({
    alAvanzar: sinCierreSoloEnP1,
    alDeclarar(m, otId, paso, actor, t) {
      if (paso.id !== 'p1' || !primeraVez(m, otId, paso)) return declararFeliz(m, otId, paso, actor)
      const r = conflictoDeSensor(m, otId, paso, actor)
      t(5000, () => cerrarPorSensor(m, otId, paso))
      return r
    },
  }),

  'warn-sobrescrito': como({
    alAvanzar: sinCierreSoloEnP1,
    alDeclarar: (m, otId, paso, actor) =>
      paso.id === 'p1' ? conflictoDeSensor(m, otId, paso, actor) : declararFeliz(m, otId, paso, actor),
  }),

  'alerta-seguridad': como({
    alAbrirSesion(m, otId, t) {
      if (m.eventos(otId).some((e) => e.tipo === 'alerta')) return
      t(8000, () => {
        const a = m.agregar(otId, {
          tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: ALERTA_GUARDA,
          evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva' },
        })
        t(10_000, () => {
          if (!m.alertasActivas(otId).some((x) => x.id === a.id)) return
          m.agregar(otId, {
            tipo: 'alerta_resuelta', actor: 'sistema', capa: 1, detalle: `Se normalizó con energia = cortada: ${ALERTA_GUARDA}`,
            evidencia: { resuelve: a.id, tipo: 'sensor', sensores: { guarda: 'abierta', energia: 'cortada' } },
          })
        })
      })
    },
  }),

  'camara-no': como({
    alDeclarar(m, otId, paso, actor) {
      if (paso.tipo_evidencia !== 'camara' || !primeraVez(m, otId, paso)) return declararFeliz(m, otId, paso, actor)
      declaracion(m, otId, paso, actor)
      return respuesta(veredicto(m, otId, paso, 'en_conflicto', 3,
        'el operario declaró «hecho» y la cámara responde que no (62%)',
        { tipo: 'camara', pregunta: paso.pregunta_visual, respuesta: false, confianza: 0.62 }))
    },
  }),

  'sin-senal': como({
    alAvanzar: () => {},
    alDeclarar(m, otId, paso, actor) {
      if (paso.tipo_evidencia !== 'sensor') return declararFeliz(m, otId, paso, actor)
      declaracion(m, otId, paso, actor)
      const { id, espera } = paso.sensor!
      return respuesta(veredicto(m, otId, paso, 'no_verificado', 1, `sin lectura de ${id}`, { tipo: 'sensor', id, valor: null, espera }))
    },
  }),

  relevo: como({
    preparar(m) {
      otsBase(m, 'operario:2')
      const [p1, p2, p3] = m.pauta.pasos
      cerrarPorSensor(m, 'ot-12', p1)
      m.agregar('ot-12', {
        tipo: 'sobrescritura', actor: 'operario:1', paso_id: p2.id, estado: 'sobrescrito', declarado: 'saqué la guarda, el sensor no marcaba',
        detalle: `operario:1 dice que hizo «${p2.titulo}»`,
      })
      veredicto(m, 'ot-12', p3, 'verificado', 3, 'la cámara responde que sí (91%)', { tipo: 'camara', respuesta: true, confianza: 0.91 })
      m.agregar('ot-12', { tipo: 'relevo_entregado', actor: 'operario:1', detalle: resumenDeRelevo(m, 'ot-12') })
    },
  }),

  'api-caida': como({
    alAbrirSesion(m, _otId, t) {
      t(5000, () => {
        m.caido = true
        t(15_000, () => {
          m.caido = false
        })
      })
    },
  }),

  completa: como({
    preparar(m) {
      otsBase(m)
      for (const p of m.pauta.pasos) {
        if (p.sensor) cerrarPorSensor(m, 'ot-12', p)
        else veredicto(m, 'ot-12', p, 'verificado', p.tipo_evidencia === 'camara' ? 3 : null, 'verificado')
      }
    },
  }),
}

// ─── La URL ─────────────────────────────────────────────────────────────────

export function escenarioDeLaUrl(search: string): NombreEscenario {
  const nombre = new URLSearchParams(search).get('escenario') as NombreEscenario | null
  return nombre && ESCENARIOS[nombre] ? nombre : 'feliz'
}

export function sesionDeLaUrl(search: string): Usuario | null {
  const como = new URLSearchParams(search).get('como')
  return USUARIOS.find((u) => u.id === como) ?? null
}
