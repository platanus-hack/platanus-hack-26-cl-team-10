// Las pautas reales del repo (datos/), con los mismos valores por defecto que pone la API al
// leerlas (app/contratos.py, Paso.desde_dict). La correa es la de los tests; LOTO, la del demo
// con ESP32 y cámara, se elige con ?pauta=loto.

import type { Pauta, PasoPauta, TipoEvidencia } from '../api/tipos'
import correa from '../../../datos/pauta-correa.json'
import loto from '../../../datos/pauta-loto.json'

type PasoCrudo = Omit<Partial<PasoPauta>, 'tipo_evidencia'> & { tipo_evidencia: string }
type PautaCruda = { id: string; nombre: string; version: number; equipo: string; pasos: unknown[] }

function normalizar(crudo: PautaCruda): Pauta {
  return {
    id: crudo.id,
    nombre: crudo.nombre,
    version: crudo.version,
    equipo: crudo.equipo,
    pasos: (crudo.pasos as PasoCrudo[]).map((p) => ({
      id: p.id!,
      orden: p.orden!,
      titulo: p.titulo!,
      instruccion: p.instruccion!,
      tipo_evidencia: p.tipo_evidencia as TipoEvidencia,
      capa_minima: p.capa_minima!,
      control_critico: p.control_critico ?? false,
      pregunta_visual: p.pregunta_visual ?? null,
      sensor: p.sensor ?? null,
      deteccion: p.deteccion ?? null,
    })),
  }
}

export const PAUTA_DEMO: Pauta = normalizar(correa)
export const PAUTA_LOTO: Pauta = normalizar(loto)

/** ?pauta=loto elige la pauta del demo con ESP32 y cámara; si no, la correa. */
export function pautaDeLaUrl(search: string): Pauta {
  return new URLSearchParams(search).get('pauta') === 'loto' ? PAUTA_LOTO : PAUTA_DEMO
}
