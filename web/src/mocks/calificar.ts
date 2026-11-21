// Imita app/scoring.py: solo la capa 1 llega a error; cámara y señales, a lo más a warning.

import type { Calificacion, Evento, Nivel } from '../api/tipos'

export type Graduable = Pick<Evento, 'tipo' | 'estado' | 'capa' | 'detalle' | 'evidencia'>

export function calificarEvento(ev: Graduable): Calificacion | null {
  const con = (nivel: Nivel, certeza = 1, motivos = [ev.detalle]): Calificacion => ({ nivel, certeza, capa: ev.capa, motivos })
  const conflicto = ev.estado === 'en_conflicto'

  switch (ev.tipo) {
    case 'alerta_resuelta':
      return con('ok')
    case 'alerta':
      return con(ev.capa === 1 ? 'error' : 'warning')
    case 'sobrescritura':
      return con('warning')
    case 'veredicto':
      if (ev.capa === 1) return con(conflicto ? 'error' : 'ok')
      if (ev.capa === 3) {
        const confianza = typeof ev.evidencia?.confianza === 'number' ? ev.evidencia.confianza : 1
        return con(conflicto ? 'warning' : 'ok', confianza)
      }
      if (ev.capa === 2) return con(conflicto ? 'warning' : 'ok')
      return con('ok', 1, [ev.detalle, 'lo cerró una persona, no un sensor'])
    default:
      return null
  }
}
