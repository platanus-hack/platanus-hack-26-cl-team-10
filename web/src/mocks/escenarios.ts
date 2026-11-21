// Escenarios del mock: qué hace la API en cada caso que el front tiene que aguantar.
// Se elige con ?escenario=<nombre>; la pauta, con ?pauta=loto. (?como=<actor> lo maneja
// sesion/sesion.ts, con o sin mock.) Los escenarios no nombran pasos: sirven para cualquier pauta.

import { cierraSolo } from '../api/pauta'
import type { EstadoPasoApi, Evento, Pauta, PasoPauta, RespuestaDeclarar } from '../api/tipos'
import type { Mundo } from './mundo'

export type Temporizador = (ms: number, fn: () => void) => void

export type Escenario = {
  preparar(m: Mundo): void
  alAbrirSesion?(m: Mundo, otId: string, t: Temporizador): void
  alAvanzar?(m: Mundo, otId: string, paso: PasoPauta, t: Temporizador): void
  alDeclarar(m: Mundo, otId: string, paso: PasoPauta, actor: string, t: Temporizador): RespuestaDeclarar
  /** Al arrancar el mock, sin que nadie abra nada: lo que pasa en otras OT mientras el supervisor mira. */
  alIniciar?(m: Mundo, t: Temporizador): void
}

export type NombreEscenario =
  | 'feliz'
  | 'warn-corregido'
  | 'warn-sobrescrito'
  | 'alerta-seguridad'
  | 'control-perdido'
  | 'camara-no'
  | 'sin-senal'
  | 'relevo'
  | 'api-caida'
  | 'completa'
  | 'incidente'

export const SENSOR_TARDA_MS = 4000
export const CAMARA_TARDA_MS = 5000

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
  return m.agregar(otId, { tipo: 'veredicto', actor: 'sistema', paso_id: paso.id, estado, capa, detalle, evidencia })
}

export function respuesta(ev: Evento): RespuestaDeclarar {
  return {
    paso: ev.paso_id ?? '',
    estado: ev.estado ?? 'no_verificado',
    capa: ev.capa,
    detalle: ev.detalle,
    interrumpe: ev.calificacion?.nivel === 'error',
    evidencia: ev.evidencia,
    calificacion: ev.calificacion,
  }
}

export function declaracion(m: Mundo, otId: string, paso: PasoPauta, actor: string): void {
  m.agregar(otId, { tipo: 'declaracion', actor, paso_id: paso.id, declarado: 'hecho', detalle: `declara sobre «${paso.titulo}»` })
}

const cerrado = (m: Mundo, otId: string, paso: PasoPauta) =>
  m.estado(otId).pasos.find((p) => p.id === paso.id)?.estado === 'verificado'

/** El sensor del paso llega con el valor esperado. No hace nada si el paso ya se cerró. */
export function cerrarPorSensor(m: Mundo, otId: string, paso: PasoPauta): void {
  if (!paso.sensor || cerrado(m, otId, paso)) return
  const { id, espera } = paso.sensor
  m.leer(id, espera)
  veredicto(m, otId, paso, 'verificado', 1, `${id} = ${espera}, que es lo que el paso exige`, { tipo: 'sensor', id, valor: espera, espera })
}

/** El modelo del edge ve (o deja de ver) la clase del paso: capa 2, sin que nadie hable. */
export function cerrarPorCamara(m: Mundo, otId: string, paso: PasoPauta): void {
  if (!paso.deteccion || cerrado(m, otId, paso)) return
  const { clase, presente } = paso.deteccion
  veredicto(m, otId, paso, 'verificado', 2, `la cámara ${presente ? 've' : 'ya no ve'} ${clase} (92%)`, {
    tipo: 'deteccion', clase, presente, conf: 0.92,
  })
}

/** Lo que cierra el paso sin el operario, según su evidencia. */
export function cerrarSolo(m: Mundo, otId: string, paso: PasoPauta): void {
  if (paso.sensor) cerrarPorSensor(m, otId, paso)
  else if (paso.deteccion) cerrarPorCamara(m, otId, paso)
}

/** Un paso cerrado sin pasar por el tiempo de espera, para preparar OT ya avanzadas. */
function cerrarYa(m: Mundo, otId: string, paso: PasoPauta): void {
  if (cierraSolo(paso)) cerrarSolo(m, otId, paso)
  else if (paso.tipo_evidencia === 'camara') veredicto(m, otId, paso, 'verificado', 3, 'la cámara responde que sí (91%)', { tipo: 'camara', respuesta: true, confianza: 0.91 })
  else veredicto(m, otId, paso, 'verificado', null, 'lo cerró una persona declarando «hecho»')
}

/** «Hecho» en el camino feliz: se declara y la evidencia lo confirma. */
export function declararFeliz(m: Mundo, otId: string, paso: PasoPauta, actor: string): RespuestaDeclarar {
  declaracion(m, otId, paso, actor)
  switch (paso.tipo_evidencia) {
    case 'sensor': {
      const { id, espera } = paso.sensor!
      m.leer(id, espera)
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
  const lista = (ps: typeof est.pasos) => ps.map((p) => p.id).join(', ') || 'ninguno'
  const cerrados = est.pasos.filter((p) => p.estado === 'verificado')
  const porPersona = cerrados.filter((p) => p.evidencia?.tipo === 'persona')
  const sigue = est.paso_actual ? `Retomar desde ${est.paso_actual}.` : 'La pauta está completa.'
  return (
    `${est.pauta} sobre ${est.equipo}. Verificados por la evidencia: ${lista(cerrados.filter((p) => !porPersona.includes(p)))}. ` +
    `Confirmados por una persona: ${lista(porPersona)}. ${sigue}`
  )
}

/**
 * Dónde se puede saltar un paso en esta pauta: el primer control crítico, mientras un paso
 * posterior con sensor se hace antes (app/reglas.py, desviacion_de_orden).
 */
export function salto(pauta: Pauta): { pendiente: PasoPauta; adelantado: PasoPauta } | null {
  for (const pendiente of pauta.pasos) {
    if (!pendiente.control_critico) continue
    const adelantado = pauta.pasos.find((p) => p.orden > pendiente.orden && p.sensor)
    if (adelantado) return { pendiente, adelantado }
  }
  return null
}

const primeraVez = (m: Mundo, otId: string, paso: PasoPauta) =>
  !m.eventos(otId).some((e) => e.tipo === 'veredicto' && e.paso_id === paso.id)

const yaHubo = (m: Mundo, otId: string, tipo: string) =>
  m.eventos(otId).some((e) => e.tipo === 'alerta' && e.evidencia?.tipo === tipo)

const ALERTA_GUARDA = 'GUARDA ABIERTA CON ENERGÍA VIVA. Detener y aislar la energía antes de continuar.'

/**
 * La guarda se abre con la energía viva: alerta de seguridad (capa 1, «detente»). Se resuelve sola
 * cuando el sensor se corrige, a los `resolverEnMs`: confirmar a mano no la apaga.
 */
function alertaDeGuarda(m: Mundo, otId: string, t: Temporizador, resolverEnMs: number): void {
  m.leer('guarda', 'abierta')
  m.leer('energia', 'viva')
  const a = m.agregar(otId, {
    tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1, detalle: ALERTA_GUARDA,
    evidencia: { tipo: 'sensor', guarda: 'abierta', energia: 'viva', clave: `seguridad:${ALERTA_GUARDA}` },
  })
  t(resolverEnMs, () => {
    if (!m.alertasActivas(otId).some((x) => x.id === a.id)) return
    m.leer('energia', 'cortada')
    m.agregar(otId, {
      tipo: 'alerta_resuelta', actor: 'sistema', capa: 1, detalle: `Se normalizó con energia = cortada: ${ALERTA_GUARDA}`,
      evidencia: { resuelve: a.id, tipo: 'sensor', sensores: { guarda: 'abierta', energia: 'cortada' } },
    })
  })
}

const feliz: Escenario = {
  preparar: (m) => otsBase(m),
  alAvanzar(m, otId, paso, t) {
    if (paso.sensor) t(SENSOR_TARDA_MS, () => cerrarPorSensor(m, otId, paso))
    else if (paso.deteccion) t(CAMARA_TARDA_MS, () => cerrarPorCamara(m, otId, paso))
  },
  alDeclarar: (m, otId, paso, actor) => declararFeliz(m, otId, paso, actor),
}

/** Igual que el camino feliz, salvo lo que se cambia. */
const como = (cambios: Partial<Escenario>): Escenario => ({ ...feliz, ...cambios })

/** El operario hace un paso posterior antes del control crítico: la API avisa el salto (capa 1). */
function conSalto(arreglarSolo: boolean): Escenario['alAvanzar'] {
  return (m, otId, paso, t) => {
    const s = salto(m.pauta)
    if (!s || paso.id !== s.pendiente.id) return feliz.alAvanzar!(m, otId, paso, t)
    if (yaHubo(m, otId, 'orden')) return
    t(3000, () => {
      if (yaHubo(m, otId, 'orden') || cerrado(m, otId, paso)) return
      m.saltar(otId, s.pendiente, s.adelantado)
      // Corregido: el operario vuelve y hace el paso saltado; su evidencia lo cierra.
      if (arreglarSolo) t(5000, () => cerrarSolo(m, otId, s.pendiente))
    })
  }
}

export const ESCENARIOS: Partial<Record<NombreEscenario, Escenario>> = {
  feliz,

  'warn-corregido': como({ alAvanzar: conSalto(true) }),

  'warn-sobrescrito': como({ alAvanzar: conSalto(false) }),

  'alerta-seguridad': como({
    alAbrirSesion(m, otId, t) {
      if (yaHubo(m, otId, 'sensor')) return
      t(8000, () => alertaDeGuarda(m, otId, t, 10_000))
    },
  }),

  'control-perdido': como({
    alAvanzar(m, otId, paso, t) {
      feliz.alAvanzar!(m, otId, paso, t)
      // El primer control crítico con sensor ya verificado se deshace al pasar al paso siguiente.
      const control = m.pauta.pasos.find((p) => p.control_critico && p.sensor)
      if (!control || paso.orden !== control.orden + 1 || yaHubo(m, otId, 'control')) return
      t(3000, () => {
        const a = m.perderControl(otId, control)
        t(8000, () => m.reponerControl(otId, a))
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

  // Sensor caído y cámara sin vista: nada se cierra solo. El operario confirma con un motivo.
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
      const [a, b, c] = m.pauta.pasos
      cerrarYa(m, 'ot-12', a)
      m.confirmar('ot-12', b.id, 'operario:1', 'lo hice; la evidencia no lo marcaba')
      cerrarYa(m, 'ot-12', c)
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
      for (const p of m.pauta.pasos) cerrarYa(m, 'ot-12', p)
    },
  }),

  // Para el supervisor: la OT de Bruno va por el paso 3 en la estación y, a los 8 s, se abre la
  // guarda con la energía viva. Se normaliza sola a los 40 s. /supervisor?escenario=incidente
  incidente: como({
    preparar(m) {
      otsBase(m)
      m.abrirSesion('ot-13', 'edge-1', 'operario:2')
      const [a, b] = m.pauta.pasos
      cerrarYa(m, 'ot-13', a)
      cerrarYa(m, 'ot-13', b)
    },
    alIniciar(m, t) {
      t(8000, () => alertaDeGuarda(m, 'ot-13', t, 40_000))
    },
  }),
}

// ─── La URL ─────────────────────────────────────────────────────────────────

export function escenarioDeLaUrl(search: string): NombreEscenario {
  const nombre = new URLSearchParams(search).get('escenario') as NombreEscenario | null
  return nombre && ESCENARIOS[nombre] ? nombre : 'feliz'
}
