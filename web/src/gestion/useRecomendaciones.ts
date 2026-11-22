import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/cliente'
import type { Mejora } from '../api/tipos'
import { campana } from './campana'
import { RECARGA_MS } from './useOts'

/**
 * Las recomendaciones que Factum avisó: propuestas abiertas con `detectada`, la más nueva primero. Factum avisa apenas un
 * paso se vuelve recurrente (app/servicios.py, `_vigilar_patrones`); acá se lee cada `cadaMs`, como las OT. Suena una vez
 * por recomendación que aparece con la página abierta; las que ya estaban al entrar se muestran sin sonar.
 */
export function useRecomendaciones(cadaMs: number = RECARGA_MS) {
  const [mejoras, setMejoras] = useState<Mejora[] | null>(null)
  const recargar = useCallback(async () => {
    try {
      setMejoras(await api.listarMejoras())
    } catch {
      // Si la API no responde, la franja de la lista de OT ya lo dice; se queda la última lista.
    }
  }, [])
  useEffect(() => {
    void Promise.resolve().then(recargar)
    const id = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(id)
  }, [recargar, cadaMs])

  const recomendaciones = useMemo(
    () =>
      (mejoras ?? [])
        .filter((m) => m.detectada && m.estado === 'abierta')
        .sort((a, b) => b.detectada!.ts.localeCompare(a.detectada!.ts)),
    [mejoras],
  )

  const vistas = useRef<Set<string> | null>(null)
  useEffect(() => {
    if (mejoras === null) return
    const ids = new Set(recomendaciones.map((m) => m.id))
    if (vistas.current && [...ids].some((id) => !vistas.current!.has(id))) campana.sonar()
    vistas.current = ids
  }, [mejoras, recomendaciones])

  const quitar = useCallback((id: string) => setMejoras((ms) => ms?.filter((m) => m.id !== id) ?? ms), [])
  return { recomendaciones, recargar, quitar }
}
