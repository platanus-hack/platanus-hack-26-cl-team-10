import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/cliente'
import type { ResumenMejoras } from '../api/tipos'
import { campana } from './campana'
import { useAlVolver } from './useOts'

/** El resumen de mejoras pesa más que la lista y cambia menos: se lee cada 5 s. */
const RECARGA_MEJORAS_MS = 5000

/**
 * El aviso de mejoras: por pauta, la versión siguiente que Factum armaría con lo que ya avisó (`GET /cliente/mejoras/resumen`).
 * Se lee cada `cadaMs`, como las OT. Suena una vez cuando aparece una propuesta nueva con la página abierta; lo que ya
 * estaba al entrar se muestra sin sonar.
 */
export function useRecomendaciones(cadaMs: number = RECARGA_MEJORAS_MS) {
  const [resumen, setResumen] = useState<ResumenMejoras[] | null>(null)
  const recargar = useCallback(async () => {
    try {
      setResumen(await api.resumenDeMejoras())
    } catch {
      // Si la API no responde, la franja de la lista de OT ya lo dice; se queda el último resumen.
    }
  }, [])
  useEffect(() => {
    void Promise.resolve().then(recargar)
    const id = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(id)
  }, [recargar, cadaMs])
  useAlVolver(recargar)

  const vistas = useRef<Set<string> | null>(null)
  useEffect(() => {
    if (resumen === null) return
    const ids = new Set(resumen.flatMap((r) => r.propuestas))
    if (vistas.current && [...ids].some((id) => !vistas.current!.has(id))) campana.sonar()
    vistas.current = ids
  }, [resumen])

  const quitar = useCallback((pauta: string) => setResumen((rs) => rs?.filter((r) => r.pauta !== pauta) ?? rs), [])
  return { recomendaciones: resumen ?? [], recargar, quitar }
}
