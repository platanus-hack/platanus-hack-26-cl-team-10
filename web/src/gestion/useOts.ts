import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, api } from '../api/cliente'
import type { CalificacionOt, EstadoGeneral, OtResumen } from '../api/tipos'
import { avanceDe, avanceDelResumen, estadoDe, type Avance } from './estados'

/** `calificacion`: todo bien, atención o detente (`GET /cliente/ots/{id}`); null si no se pidió o aún no llega. */
export type OtVista = OtResumen & { estado: EstadoGeneral; avance: Avance | null; calificacion: CalificacionOt | null }

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
 * El avance sale de la misma lista (`cerrados`/`total`) y los nombres de `GET /cliente/pautas`, una
 * vez. Solo las OT abiertas de `detalleDe` (el operador que mira) se leen una por una, para mostrar
 * en qué paso siguen.
 *
 * Con `calificar` (el supervisor), cada OT trae su calificación. Para no pedir todas en cada vuelta:
 * las que están en ejecución se piden siempre, porque ahí aparecen los incidentes; las demás, solo
 * cuando su resumen cambia. Las sin asignar no se califican.
 */
export function useOts(
  cadaMs: number = RECARGA_MS,
  limiteMs: number = LIMITE_MS,
  detalleDe: string | null = null,
  calificar = false,
) {
  const [ots, setOts] = useState<OtVista[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const ultimaPedida = useRef(0)
  const nombres = useRef(new Map<string, string>())
  const calificaciones = useRef(new Map<string, { clave: string; c: CalificacionOt }>())

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
      const calificadas = Promise.all(
        lista.map(async (o) => {
          if (!calificar || o.estado_general === 'sin_asignar') return
          const clave = [o.estado_general, o.cerrados, o.paso_actual, o.operador].join('|')
          const antes = calificaciones.current.get(o.ot)
          if (antes && antes.clave === clave && o.estado_general !== 'en_ejecucion') return
          try {
            const d = await conLimite(api.leerOtCliente(o.ot), limiteMs)
            calificaciones.current.set(o.ot, { clave, c: d.calificacion })
          } catch {
            // Se queda con la última: una calificación vieja es mejor que ninguna.
          }
        }),
      )
      const [, avances] = await Promise.all([nombresListos, detalles, calificadas])
      if (pedida !== ultimaPedida.current) return
      setOts(
        lista.map((o, i) => ({
          ...o,
          estado: estadoDe(o),
          avance: avances[i] ?? avanceDelResumen(o, nombres.current),
          calificacion: o.estado_general === 'sin_asignar' ? null : (calificaciones.current.get(o.ot)?.c ?? null),
        })),
      )
      setError(null)
    } catch (e) {
      if (pedida === ultimaPedida.current) setError(mensajeDe(e))
    }
  }, [limiteMs, detalleDe, calificar])

  useEffect(() => {
    void Promise.resolve().then(recargar)
    const reloj = setInterval(() => void recargar(), cadaMs)
    return () => clearInterval(reloj)
  }, [recargar, cadaMs])

  return { ots, error, recargar }
}
