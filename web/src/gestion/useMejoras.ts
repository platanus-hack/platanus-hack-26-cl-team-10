import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api/cliente'
import type { Mejora } from '../api/tipos'
import { mensajeDe } from './useOts'

export const RECARGA_MEJORAS_MS = 3000

/**
 * Las propuestas de mejora de la empresa, recargadas cada `cadaMs`. El servidor las calcula al
 * leer la bitácora: una nace en cuanto la segunda OT se desvía en el mismo paso, sin que nadie
 * la cree. `nuevas` son las que nacieron mientras esta pantalla estaba abierta.
 */
export function useMejoras(cadaMs: number = RECARGA_MEJORAS_MS) {
  const [mejoras, setMejoras] = useState<Mejora[] | null>(null)
  const [nuevas, setNuevas] = useState<ReadonlySet<string>>(new Set())
  const [error, setError] = useState<string | null>(null)
  /** Las que ya existían en la primera carga. */
  const conocidas = useRef<Set<string> | null>(null)
  const ultimaPedida = useRef(0)

  const recargar = useCallback(async () => {
    const pedida = ++ultimaPedida.current
    try {
      const lista = await api.listarMejoras()
      if (pedida !== ultimaPedida.current) return
      const antes = (conocidas.current ??= new Set(lista.map((p) => p.id)))
      const nacidas = lista.filter((p) => !antes.has(p.id)).map((p) => p.id)
      setNuevas((previas) => (nacidas.every((id) => previas.has(id)) ? previas : new Set([...previas, ...nacidas])))
      setMejoras(lista)
      setError(null)
    } catch (e) {
      if (pedida === ultimaPedida.current) setError(mensajeDe(e))
    }
  }, [])

  useEffect(() => {
    void Promise.resolve().then(recargar)
    const reloj = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(reloj)
  }, [recargar, cadaMs])

  return { mejoras, nuevas, error, recargar }
}
