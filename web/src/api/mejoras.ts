// Qué deja una OT en su bitácora que apunta a mejorar la pauta (app/mejora.py, _senales).

import type { Evento, SenalMejora } from './tipos'

/** Las observaciones de estas categorías alimentan las propuestas; `equipo` habla de la máquina. */
export const ALIMENTAN_MEJORAS = ['pauta', 'seguridad']

/**
 * Las señales de cada paso en una OT: una alerta de orden o de control perdido, un conflicto entre
 * la palabra y la evidencia, un paso que confirmó una persona y lo que observó el operario.
 * Una alerta de seguridad cuenta en el paso que estaba en curso cuando se dio el peligro, que el servidor
 * guarda en `evidencia.paso` (servicios._seguridad): acercarse con el motor encendido cuenta en «Apagar el motor».
 */
export function senalesDe(bitacora: Evento[]): Map<string, Partial<Record<SenalMejora, number>>> {
  const porPaso = new Map<string, Partial<Record<SenalMejora, number>>>()
  const sumar = (paso: string | null, senal: SenalMejora) => {
    if (!paso) return
    const cuenta = porPaso.get(paso) ?? {}
    cuenta[senal] = (cuenta[senal] ?? 0) + 1
    porPaso.set(paso, cuenta)
  }
  for (const ev of bitacora) {
    if (ev.tipo === 'alerta') {
      // La clave de la alerta dice su clase y, en las de orden y control, el paso: `orden:p3`.
      const [clase, ...paso] = String(ev.evidencia?.clave ?? '').split(':')
      if (clase === 'orden' || clase === 'control') sumar(paso.join(':'), clase)
      else if (clase === 'seguridad' && typeof ev.evidencia?.paso === 'string') sumar(ev.evidencia.paso, 'seguridad')
    } else if (ev.tipo === 'veredicto' && ev.evidencia?.tipo === 'persona') sumar(ev.paso_id, 'persona')
    else if (ev.tipo === 'veredicto' && ev.estado === 'en_conflicto') sumar(ev.paso_id, 'conflicto')
    else if (ev.tipo === 'observacion' && ALIMENTAN_MEJORAS.includes(String(ev.evidencia?.categoria))) sumar(ev.paso_id, 'observacion')
  }
  return porPaso
}
