import { useEffect, useRef } from 'react'
import { campana } from './campana'
import type { Incidente } from './estados'

/** La vista en vivo de una OT, para el supervisor. */
export const rutaDe = (ot: string) => `/supervisor/ot/${encodeURIComponent(ot)}`

/** Suena una vez por incidente nuevo; los que ya estaban al entrar no suenan. */
export function useCampanaDeIncidentes(incidentes: Incidente[] | null) {
  const vistos = useRef<Set<string> | null>(null)
  useEffect(() => {
    if (!incidentes) return
    const claves = new Set(incidentes.map((i) => `${i.ot}:${i.que}`))
    if (vistos.current && [...claves].some((k) => !vistos.current!.has(k))) campana.sonar()
    vistos.current = claves
  }, [incidentes])
  // El primer toque en la página deja el audio listo, por si se entró recargando.
  useEffect(() => {
    const preparar = () => campana.preparar()
    window.addEventListener('pointerdown', preparar, { once: true })
    return () => window.removeEventListener('pointerdown', preparar)
  }, [])
}
