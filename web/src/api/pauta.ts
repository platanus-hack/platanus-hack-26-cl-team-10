// Cómo se cierra cada paso de una pauta. Lo usan la pantalla de ejecución y el mock.

import type { PasoPauta } from './tipos'

type ComoSeCierra = Pick<PasoPauta, 'tipo_evidencia' | 'deteccion'>

/** Se cierra solo con la evidencia: un sensor, o la cámara del edge cuando su modelo lo detecta. */
export const cierraSolo = (p: ComoSeCierra): boolean =>
  p.tipo_evidencia === 'sensor' || (p.tipo_evidencia === 'camara' && !!p.deteccion)

/** Se cierra con «Hecho»: un paso de confirmación, o uno de cámara que la API juzga al declarar. */
export const pideHecho = (p: ComoSeCierra): boolean => !cierraSolo(p)

/** La API no deja confirmar contra la evidencia un paso de confirmación: ese se cierra declarando. */
export const sePuedeConfirmar = (p: Pick<PasoPauta, 'tipo_evidencia'>): boolean => p.tipo_evidencia !== 'confirmacion'
