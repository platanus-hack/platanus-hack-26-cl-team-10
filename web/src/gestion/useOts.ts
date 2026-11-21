import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../api/cliente'
import type { CalificacionOt, EstadoGeneral, OtResumen } from '../api/tipos'
import { avanceDe, avanceDelResumen, estadoDe, type Avance } from './estados'

/** `calificacion`: todo bien, atención o detente, como la trae `GET /cliente/ots`; null en las sin asignar. */
export type OtVista = Omit<OtResumen, 'calificacion'> & { estado: EstadoGeneral; avance: Avance | null; calificacion: CalificacionOt | null }

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
 *
 * El avance y la calificación salen de la misma lista (`cerrados`/`total`, `calificacion`) y los
 * nombres de `GET /cliente/pautas`, una vez. Solo las OT abiertas de `detalleDe` (el operador que
 * mira) se leen una por una, para mostrar en qué paso siguen.
 */
export function useOts(cadaMs: number = RECARGA_MS, limiteMs: number = LIMITE_MS, detalleDe: string | null = null) {
  const [ots, setOts] = useState<OtVista[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const ultimaPedida = useRef(0)
  const nombres = useRef(new Map<string, string>())

  const recargar = useCallback(async () => {
    const pedida = ++ultimaPedida.current
    try {
      const lista = await conLimite(api.listarOts(), limiteMs)
      // Los nombres y el paso en curso son un adorno: si fallan, la OT se muestra igual.
      const nombresListos = lista.every((o) => nombres.current.has(o.pauta))
        ? Promise.resolve()
        : conLimite(api.listarPautas(), limiteMs).then(
            (ps) => ps.forEach((p) => nombres.current.set(p.id, p.nombre)),
            () => {},
          )
      const detalles = Promise.all(
        lista.map((o) =>
          detalleDe && o.operador === detalleDe && !o.completa
            ? conLimite(api.leerOt(o.ot), limiteMs).then(avanceDe, () => null)
            : null,
        ),
      )
      const [, avances] = await Promise.all([nombresListos, detalles])
      if (pedida !== ultimaPedida.current) return
      setOts(
        lista.map((o, i) => ({
          ...o,
          estado: estadoDe(o),
          avance: avances[i] ?? avanceDelResumen(o, nombres.current),
          calificacion: o.estado_general === 'sin_asignar' ? null : (o.calificacion ?? null),
        })),
      )
      setError(null)
    } catch (e) {
      if (pedida === ultimaPedida.current) setError(mensajeDe(e))
    }
  }, [limiteMs, detalleDe])

  useEffect(() => {
    void Promise.resolve().then(recargar)
    const reloj = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(reloj)
  }, [recargar, cadaMs])

  return { ots, error, recargar }
}
