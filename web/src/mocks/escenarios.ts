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

const feliz: Escenario = {
  preparar: (m) => otsBase(m),
  alAvanzar(m, otId, paso, t) {
    if (paso.tipo_evidencia === 'sensor') t(SENSOR_TARDA_MS, () => cerrarPorSensor(m, otId, paso))
  },
  alDeclarar: (m, otId, paso, actor) => declararFeliz(m, otId, paso, actor),
}

export const ESCENARIOS: Partial<Record<NombreEscenario, Escenario>> = { feliz }

// ─── La URL ─────────────────────────────────────────────────────────────────

export function escenarioDeLaUrl(search: string): NombreEscenario {
  const nombre = new URLSearchParams(search).get('escenario') as NombreEscenario | null
  return nombre && ESCENARIOS[nombre] ? nombre : 'feliz'
}

export function sesionDeLaUrl(search: string): Usuario | null {
  const como = new URLSearchParams(search).get('como')
  return USUARIOS.find((u) => u.id === como) ?? null
}
