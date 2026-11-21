// Cómo se le dice al operario cada alerta: el banner y el aviso en pantalla usan lo mismo.

import type { EstadoOt, Evento } from '../api/tipos'
import { tipoDeAlerta, type TipoAlerta } from './estado'

const TITULO: Record<TipoAlerta, string> = {
  seguridad: 'Peligro',
  orden: 'Paso saltado',
  control: 'Control perdido',
  senal: 'Precaución',
  otra: 'Peligro',
}

/** El título de un aviso: el de su clase de alerta; un conflicto de un paso es «Peligro». */
export const tituloDe = (ev: Evento): string => (ev.tipo === 'alerta' ? TITULO[tipoDeAlerta(ev)] : 'Peligro')

/** Qué pasó, en palabras del operario. Si la alerta no trae lo que hace falta, su detalle tal cual. */
export function queDice(a: Evento, ot: EstadoOt | null): { texto: string; ayuda: string | null } {
  const paso = (id: unknown) => ot?.pasos.find((p) => p.id === id)
  switch (tipoDeAlerta(a)) {
    case 'orden': {
      const pendiente = paso(a.evidencia?.pendiente)
      const adelantado = paso(a.evidencia?.adelantado)
      if (pendiente && adelantado)
        return {
          texto: `Hiciste «${adelantado.titulo}» antes de «${pendiente.titulo}».`,
          ayuda: `Haz el paso ${pendiente.orden} o, si ya lo hiciste, confírmalo en el paso.`,
        }
      return { texto: a.detalle, ayuda: null }
    }
    case 'control': {
      const p = paso(a.evidencia?.paso)
      return { texto: p ? `«${p.titulo}» se deshizo. Vuelve a dejarlo como estaba.` : a.detalle, ayuda: 'Se apaga sola cuando el sensor lo vea de vuelta.' }
    }
    case 'seguridad':
      return { texto: a.detalle, ayuda: 'Se apaga sola cuando el sensor lo vea corregido.' }
    default:
      return { texto: a.detalle, ayuda: null }
  }
}
