// La pauta real del demo (datos/pauta-correa.json), con los mismos valores por defecto que
// pone la API al leerla (app/contratos.py, Paso.desde_dict).

import type { Pauta, PasoPauta, TipoEvidencia } from '../api/tipos'
import crudo from '../../../datos/pauta-correa.json'

type PasoCrudo = Omit<Partial<PasoPauta>, 'tipo_evidencia'> & { tipo_evidencia: string }

export const PAUTA_DEMO: Pauta = {
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
  })),
}
