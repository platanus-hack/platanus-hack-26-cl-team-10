// El mundo del mock: OTs en memoria con una bitácora que solo agrega, como la API real.
// El estado de cada OT se calcula leyendo sus eventos; nada se edita.

import type {
  Calificacion,
  CalificacionOt,
  EstadoGeneral,
  EstadoOt,
  Evento,
  MensajeStream,
  OtResumen,
  PasoEstado,
  PasoPauta,
  Pauta,
  RespuestaConfirmar,
  Sesion,
  Snapshot,
} from '../api/tipos'
import { calificarEvento } from './calificar'

export type NuevoEvento = Pick<Evento, 'tipo' | 'actor' | 'detalle'> &
  Partial<Pick<Evento, 'paso_id' | 'estado' | 'capa' | 'declarado' | 'evidencia'>>

type OtMock = { id: string; eventos: Evento[]; operador: string | null; sesion: Sesion | null; abiertaEn: string }

const GRAVEDAD = { ok: 0, warning: 1, error: 2 } as const

/** Lo que la API responde con 404 o 409; el handler lo traduce. */
export class ErrorMock extends Error {
  status: 404 | 409
  constructor(status: 404 | 409, mensaje: string) {
    super(mensaje)
    this.status = status
  }
}

/** El valor contrario al que el paso espera: lo que marca un sensor cuando el paso no está hecho. */
export const CONTRARIO: Record<string, string> = {
  cerrado: 'abierto', abierto: 'cerrado', cerrada: 'abierta', abierta: 'cerrada', viva: 'cortada', cortada: 'viva',
  presente: 'ausente', ausente: 'presente', frio: 'caliente', caliente: 'frio',
}

export class Mundo {
  readonly pauta: Pauta
  alCambiarPaso: ((otId: string, paso: PasoPauta) => void) | null = null
  /** Avisos de que la API «se cayó»: los handlers cierran los WebSocket abiertos. */
  readonly alCaer = new Set<() => void>()
  private _caido = false

  get caido(): boolean {
    return this._caido
  }

  set caido(valor: boolean) {
    const cae = valor && !this._caido
    this._caido = valor
    if (cae) for (const fn of this.alCaer) fn()
  }

  private ots = new Map<string, OtMock>()
  private siguienteId = 1
  /** La última lectura de cada sensor, como db.sensores en la API. */
  private lecturas = new Map<string, string>()
  private suscriptores = new Map<string, Set<(m: MensajeStream) => void>>()

  constructor(pauta: Pauta) {
    this.pauta = { ...pauta, pasos: [...pauta.pasos].sort((a, b) => a.orden - b.orden) }
  }

  existe(otId: string): boolean {
    return this.ots.has(otId)
  }

  private ot(otId: string): OtMock {
    const ot = this.ots.get(otId)
    if (!ot) throw new Error(`OT ${otId} no existe`)
    return ot
  }

  paso(pasoId: string): PasoPauta | undefined {
    return this.pauta.pasos.find((p) => p.id === pasoId)
  }

  /** El id de una OT pedida sin id, como catalogo._id_de_ot: ot-0004 si ya hay tres. */
  idNuevo(): string {
    let n = this.ots.size + 1
    while (this.ots.has(`ot-${String(n).padStart(4, '0')}`)) n++
    return `ot-${String(n).padStart(4, '0')}`
  }

  crearOt(id: string, operador: string | null): void {
    this.ots.set(id, { id, eventos: [], operador, sesion: null, abiertaEn: new Date().toISOString() })
    const { nombre, version, equipo } = this.pauta
    this.agregar(id, { tipo: 'ot_abierta', actor: 'sistema', detalle: `OT abierta desde ${nombre} v${version} sobre ${equipo}` })
  }

  agregar(otId: string, nuevo: NuevoEvento): Evento {
    const ot = this.ot(otId)
    const antes = this.estado(otId).paso_actual
    const base = {
      paso_id: null,
      estado: null,
      capa: null,
      declarado: null,
      evidencia: null,
      ...nuevo,
    }
    const ev: Evento = { ...base, id: this.siguienteId++, ot_id: otId, ts: new Date().toISOString(), calificacion: calificarEvento(base) }
    ot.eventos.push(ev)
    this.publicar(otId, { tipo: 'evento', evento: ev })
    this.publicar(otId, { tipo: 'calificacion_ot', calificacion: this.calificacion(otId) })

    // Como _resolver_orden: hacer el paso saltado cierra su aviso de orden.
    if (ev.tipo === 'veredicto' && ev.estado === 'verificado' && ev.paso_id) {
      const por = ev.evidencia?.tipo === 'persona' ? `lo confirmó ${ev.actor}` : ''
      this.resolverOrden(otId, ev.paso_id, por)
    }

    const despues = this.estado(otId).paso_actual
    if (despues && despues !== antes) {
      const paso = this.paso(despues)
      if (paso) this.alCambiarPaso?.(otId, paso)
    }
    return ev
  }

  eventos(otId: string): Evento[] {
    return [...this.ot(otId).eventos]
  }

  /** Por paso, manda el último veredicto. */
  private ultimosPorPaso(otId: string): Map<string, Evento> {
    const ultimo = new Map<string, Evento>()
    for (const ev of this.ot(otId).eventos) if (ev.paso_id && ev.estado) ultimo.set(ev.paso_id, ev)
    return ultimo
  }

  estado(otId: string): EstadoOt {
    const ultimo = this.ultimosPorPaso(otId)
    const pasos: PasoEstado[] = this.pauta.pasos.map((p) => {
      const u = ultimo.get(p.id)
      return {
        id: p.id,
        orden: p.orden,
        titulo: p.titulo,
        estado: u?.estado ?? 'no_verificado',
        control_critico: p.control_critico,
        capa: u?.capa ?? null,
        evidencia: u?.evidencia ?? null,
        detalle: u?.detalle ?? null,
      }
    })
    const actual = pasos.find((p) => p.estado !== 'verificado')
    const con = (e: string) => pasos.filter((p) => p.estado === e).map((p) => p.id)
    return {
      pauta: `${this.pauta.nombre} v${this.pauta.version}`,
      equipo: this.pauta.equipo,
      paso_actual: actual?.id ?? null,
      completa: !actual,
      pasos,
      verificados: con('verificado'),
      en_conflicto: con('en_conflicto'),
      pendientes: con('no_verificado'),
    }
  }

  alertasActivas(otId: string): Evento[] {
    const eventos = this.ot(otId).eventos
    const cerradas = new Set<unknown>()
    for (const e of eventos) {
      if (e.tipo === 'alerta_resuelta') cerradas.add(e.evidencia?.resuelve)
    }
    return eventos.filter((e) => e.tipo === 'alerta' && !cerradas.has(e.id))
  }

  calificacion(otId: string): CalificacionOt {
    const partes: Calificacion[] = [
      ...[...this.ultimosPorPaso(otId).values()].map((e) => e.calificacion),
      ...this.alertasActivas(otId).map((e) => e.calificacion),
    ].filter((c): c is Calificacion => c !== null)

    const avisos = partes
      .filter((c) => c.nivel !== 'ok')
      .sort((a, b) => GRAVEDAD[b.nivel] - GRAVEDAD[a.nivel] || a.certeza - b.certeza)
    const peor: Calificacion = avisos[0] ??
      [...partes].sort((a, b) => a.certeza - b.certeza)[0] ?? { nivel: 'ok', certeza: 1, capa: null, motivos: ['sin nada que calificar'] }
    return { ...peor, avisos }
  }

  snapshot(otId: string, desde: number): Snapshot {
    const ot = this.ot(otId)
    return {
      tipo: 'snapshot',
      ot: otId,
      estado: this.estado(otId),
      calificacion: this.calificacion(otId),
      alertas_activas: this.alertasActivas(otId),
      sesion: ot.sesion,
      video: null,
      sensores: Object.fromEntries(this.lecturas),
      bitacora: ot.eventos.filter((e) => e.id > desde),
    }
  }

  sesionDe(otId: string): Sesion | null {
    return this.ot(otId).sesion
  }

  operador(otId: string): string | null {
    return this.ot(otId).operador
  }

  asignar(otId: string, operador: string | null): void {
    this.ot(otId).operador = operador
  }

  /** Lo que la estación ejecuta ahora, o null si está libre. */
  sesionDeEdge(edgeId: string): Sesion | null {
    for (const ot of this.ots.values()) if (ot.sesion?.edge_id === edgeId) return ot.sesion
    return null
  }

  /** Una estación ejecuta una sola OT: la que la tenía la pierde (app/servicios.py, iniciar_sesion). */
  abrirSesion(otId: string, edgeId: string, operario: string): Sesion {
    for (const ot of this.ots.values()) if (ot.id !== otId && ot.sesion?.edge_id === edgeId) ot.sesion = null
    const sesion: Sesion = { edge_id: edgeId, ot_id: otId, operario, desde: new Date().toISOString() }
    this.ot(otId).sesion = sesion
    this.publicar(otId, { tipo: 'sesion', sesion, video: null })
    return sesion
  }

  /** El relevo entregado que nadie ha recibido todavía, si la OT quedó sin operador. */
  private entrega(ot: OtMock): Evento | null {
    const i = ot.eventos.findLastIndex((e) => e.tipo === 'relevo_entregado')
    if (ot.operador || i < 0 || ot.eventos.some((e, j) => j > i && e.tipo === 'relevo_recibido')) return null
    return ot.eventos[i]
  }

  private estadoGeneral(ot: OtMock): EstadoGeneral {
    if (this.estado(ot.id).completa) return 'completa'
    if (this.entrega(ot)) return 'entregada'
    if (!ot.operador) return 'sin_asignar'
    if (ot.sesion || ot.eventos.some((e) => e.tipo === 'veredicto')) return 'en_ejecucion'
    return 'asignada'
  }

  // Como un ítem de GET /ots (app/catalogo.py, _resumen).
  resumenes(): OtResumen[] {
    return [...this.ots.values()].map((ot) => {
      const e = this.estado(ot.id)
      const estadoGeneral = this.estadoGeneral(ot)
      return {
        ot: ot.id,
        pauta: this.pauta.id,
        version: this.pauta.version,
        equipo: this.pauta.equipo,
        abierta_en: ot.abiertaEn,
        paso_actual: e.paso_actual,
        completa: e.completa,
        operador: ot.operador,
        estado_general: estadoGeneral,
        entregada_por: estadoGeneral === 'entregada' ? (this.entrega(ot)?.actor ?? null) : null,
        cerrados: e.pasos.filter((p) => p.estado === 'verificado').length,
        total: e.pasos.length,
      }
    })
  }

  // ─── Sensores, orden, controles y confirmación por persona (app/servicios.py) ───

  /** Una lectura de la estación. Llega al stream de cada OT que una estación está ejecutando. */
  leer(sensorId: string, valor: string): void {
    this.lecturas.set(sensorId, valor)
    for (const ot of this.ots.values()) {
      if (!ot.sesion) continue
      this.publicar(ot.id, { tipo: 'lectura', edge_id: ot.sesion.edge_id, sensor_id: sensorId, valor, ts: new Date().toISOString() })
    }
  }

  lectura(sensorId: string): string | null {
    return this.lecturas.get(sensorId) ?? null
  }

  /** POST /ot/{id}/pasos/{paso}/confirmar, con las reglas de servicios.confirmar_por_persona. */
  confirmar(otId: string, pasoId: string, actor: string, motivo: string): RespuestaConfirmar {
    const paso = this.paso(pasoId)
    if (!paso) throw new ErrorMock(404, `paso ${pasoId}`)
    const actual = this.estado(otId).paso_actual
    if (!actual) throw new ErrorMock(409, 'la pauta ya está completa')
    if (paso.id !== actual) throw new ErrorMock(409, `solo se confirma el paso en curso (${actual}): el orden lo impone la app`)
    if (paso.tipo_evidencia === 'confirmacion') throw new ErrorMock(409, `«${paso.titulo}» es de confirmación: se cierra declarando`)
    if (!actor || actor === 'sistema') throw new ErrorMock(409, 'un paso lo confirma una persona, no el sistema')
    if (!motivo.trim()) throw new ErrorMock(409, 'confirmar contra la evidencia necesita un motivo')

    const valor = paso.sensor ? this.lectura(paso.sensor.id) : null
    const contra = paso.sensor ? { sensor: paso.sensor.id, valor, espera: paso.sensor.espera } : { camara: paso.pregunta_visual }
    const que = paso.sensor ? `${paso.sensor.id} = ${valor}, se esperaba ${paso.sensor.espera}` : 'la cámara no lo confirmó'
    const ev = this.agregar(otId, {
      tipo: 'veredicto', actor, paso_id: paso.id, estado: 'verificado', capa: null, declarado: motivo,
      evidencia: { tipo: 'persona', motivo, contra },
      detalle: `${actor} confirma «${paso.titulo}» contra la evidencia (${que}): ${motivo}`,
    })
    return {
      paso: paso.id, estado: 'verificado', capa: null, detalle: ev.detalle, interrumpe: false,
      evidencia: ev.evidencia, calificacion: ev.calificacion, calificacion_ot: this.calificacion(otId),
    }
  }

  /** Una lectura cierra un paso posterior mientras el actual, un control crítico, sigue abierto. */
  saltar(otId: string, pendiente: PasoPauta, adelantado: PasoPauta): Evento {
    const sensor = adelantado.sensor!
    this.leer(sensor.id, sensor.espera)
    return this.agregar(otId, {
      tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1,
      detalle: `ORDEN INVERTIDO: «${adelantado.titulo}» (${sensor.id} = ${sensor.espera}) antes de «${pendiente.titulo}».`,
      evidencia: {
        tipo: 'orden', adelantado: adelantado.id, pendiente: pendiente.id, sensor: sensor.id, valor: sensor.espera,
        clave: `orden:${adelantado.id}`,
      },
    })
  }

  private resolverOrden(otId: string, pasoId: string, por: string): void {
    for (const a of this.alertasActivas(otId)) {
      if (a.evidencia?.tipo !== 'orden' || a.evidencia.pendiente !== pasoId) continue
      this.agregar(otId, {
        tipo: 'alerta_resuelta', actor: 'sistema', capa: 1,
        detalle: `Orden resuelto: se hizo el paso saltado (${pasoId}${por ? `, ${por}` : ''}). ${a.detalle}`,
        evidencia: { resuelve: a.id, tipo: 'orden', sensor: a.evidencia.sensor, valor: a.evidencia.valor },
      })
    }
  }

  /** Un control crítico ya verificado se deshace: su sensor vuelve al valor contrario. */
  perderControl(otId: string, paso: PasoPauta): Evento {
    const { id, espera } = paso.sensor!
    const valor = CONTRARIO[espera] ?? 'otro'
    this.leer(id, valor)
    return this.agregar(otId, {
      tipo: 'alerta', actor: 'sistema', estado: 'en_conflicto', capa: 1,
      detalle: `CONTROL PERDIDO: «${paso.titulo}» se deshizo (${id} = ${valor}, exige ${espera}).`,
      evidencia: { tipo: 'control', paso: paso.id, sensor: id, valor, clave: `control:${paso.id}` },
    })
  }

  reponerControl(otId: string, alerta: Evento): void {
    const paso = this.paso(String(alerta.evidencia?.paso))
    if (!paso?.sensor || !this.alertasActivas(otId).some((a) => a.id === alerta.id)) return
    const { id, espera } = paso.sensor
    this.leer(id, espera)
    this.agregar(otId, {
      tipo: 'alerta_resuelta', actor: 'sistema', capa: 1,
      detalle: `Control repuesto con ${id} = ${espera}: ${alerta.detalle}`,
      evidencia: { resuelve: alerta.id, tipo: 'control', sensor: id, valor: espera },
    })
  }

  suscribir(otId: string, fn: (m: MensajeStream) => void): () => void {
    const set = this.suscriptores.get(otId) ?? new Set()
    set.add(fn)
    this.suscriptores.set(otId, set)
    return () => set.delete(fn)
  }

  private publicar(otId: string, m: MensajeStream): void {
    for (const fn of this.suscriptores.get(otId) ?? []) fn(m)
  }
}
