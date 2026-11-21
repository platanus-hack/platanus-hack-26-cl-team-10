import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../api/cliente'
import type { EstadoGeneral, OtResumen } from '../api/tipos'
import { avanceDe, estadoDe, type Avance } from './estados'

export type OtVista = OtResumen & { estado: EstadoGeneral; avance: Avance | null }

export const RECARGA_MS = 5000
/** Menor que RECARGA_MS: una recarga colgada falla antes de que empiece la siguiente. */
export const LIMITE_MS = 4000

export function mensajeDe(e: unknown): string {
  return e instanceof ApiError ? e.message : 'Algo salió mal al hablar con la API'
}

// El cliente compartido no pone timeout a las lecturas; acá se acota sin tocarlo.
function conLimite<T>(promesa: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolver, rechazar) => {
    const reloj = setTimeout(() => rechazar(new ApiError(0, 'timeout', 'La API no respondió a tiempo')), ms)
    promesa.then(
      (v) => {
        clearTimeout(reloj)
        resolver(v)
      },
      (e: unknown) => {
        clearTimeout(reloj)
        rechazar(e)
      },
    )
  })
}

/**
 * Las OT con su avance, recargadas cada `cadaMs`: el operador las cambia desde otro dispositivo.
 * Si falla una recarga, se mantiene la última lista y se informa el error.
 */
export function useOts(cadaMs: number = RECARGA_MS, limiteMs: number = LIMITE_MS) {
  const [ots, setOts] = useState<OtVista[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const ultimaPedida = useRef(0)

  const recargar = useCallback(async () => {
    const pedida = ++ultimaPedida.current
    try {
      const lista = await conLimite(api.listarOts(), limiteMs)
      // El avance es un adorno: si falla para una OT, esa OT se muestra sin avance.
      const avances = await Promise.all(
        lista.map((o) => conLimite(api.leerOt(o.ot), limiteMs).then(avanceDe, () => null)),
      )
      if (pedida !== ultimaPedida.current) return
      setOts(lista.map((o, i) => ({ ...o, estado: estadoDe(o), avance: avances[i] })))
      setError(null)
    } catch (e) {
      if (pedida === ultimaPedida.current) setError(mensajeDe(e))
    }
  }, [limiteMs])

  useEffect(() => {
    void Promise.resolve().then(recargar)
    const reloj = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(reloj)
  }, [recargar, cadaMs])

  return { ots, error, recargar }
}
