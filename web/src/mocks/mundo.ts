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
  Sesion,
  Snapshot,
} from '../api/tipos'
import { calificarEvento } from './calificar'

export type NuevoEvento = Pick<Evento, 'tipo' | 'actor' | 'detalle'> &
  Partial<Pick<Evento, 'paso_id' | 'estado' | 'capa' | 'declarado' | 'evidencia'>>

type OtMock = { id: string; eventos: Evento[]; operador: string | null; sesion: Sesion | null; abiertaEn: string }

const GRAVEDAD = { ok: 0, warning: 1, error: 2 } as const

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

  /** Por paso, manda el último evento que trae estado (veredicto o sobrescritura). */
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
    const actual = pasos.find((p) => p.estado !== 'verificado' && p.estado !== 'sobrescrito')
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
      if (e.tipo === 'sobrescritura' && e.evidencia?.alerta_id != null) cerradas.add(e.evidencia.alerta_id)
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
      sensores: {},
      bitacora: ot.eventos.filter((e) => e.id > desde),
    }
  }

  operador(otId: string): string | null {
    return this.ot(otId).operador
  }

  asignar(otId: string, operador: string | null): void {
    this.ot(otId).operador = operador
  }

  abrirSesion(otId: string, edgeId: string, operario: string): Sesion {
    const sesion: Sesion = { edge_id: edgeId, ot_id: otId, operario, desde: new Date().toISOString() }
    this.ot(otId).sesion = sesion
    this.publicar(otId, { tipo: 'sesion', sesion, video: null })
    return sesion
  }

  private estadoGeneral(ot: OtMock): EstadoGeneral {
    if (this.estado(ot.id).completa) return 'completa'
    const ultimoEntregado = ot.eventos.findLastIndex((e) => e.tipo === 'relevo_entregado')
    const recibidoDespues = ot.eventos.some((e, i) => i > ultimoEntregado && e.tipo === 'relevo_recibido')
    if (!ot.operador && ultimoEntregado >= 0 && !recibidoDespues) return 'entregada'
    if (!ot.operador) return 'sin_asignar'
    if (ot.sesion || ot.eventos.some((e) => e.tipo === 'veredicto' || e.tipo === 'sobrescritura')) return 'en_ejecucion'
    return 'asignada'
  }

  resumenes(): OtResumen[] {
    return [...this.ots.values()].map((ot) => {
      const e = this.estado(ot.id)
      return {
        ot: ot.id,
        pauta: this.pauta.id,
        version: this.pauta.version,
        equipo: this.pauta.equipo,
        abierta_en: ot.abiertaEn,
        paso_actual: e.paso_actual,
        completa: e.completa,
        operador: ot.operador,
        estado_general: this.estadoGeneral(ot),
      }
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
