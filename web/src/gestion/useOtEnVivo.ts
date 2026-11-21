// Lo que el supervisor ve de una OT, en vivo y sin tocar nada: el stream de la OT (estado,
// alertas, bitácora, sesión, sensores y lo que ve la cámara), su resumen y su pauta.
// No abre sesión, no declara y no habla: mirar no cambia la bitácora.

import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { api, ApiError, urlStream } from '../api/cliente'
import type { Deteccion, OtDetalle, Pauta, Sesion } from '../api/tipos'
import { config } from '../config'
import { inicial, reducir } from '../ejecucion/estado'
import { conectarStream } from '../ejecucion/stream'

export type Acceso = 'verificando' | 'ok' | 'denegado'

/** Sin detecciones nuevas en este tiempo, lo que se veía es viejo y se borra (como en el monitor). */
export const VISTAS_VIVEN_MS = 1000

export function useOtEnVivo(otId: string) {
  const [s, dispatch] = useReducer(reducir, inicial)
  const [acceso, setAcceso] = useState<Acceso>('verificando')
  const [detalle, setDetalle] = useState<OtDetalle | null>(null)
  const [pauta, setPauta] = useState<Pauta | null>(null)
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [sensores, setSensores] = useState<Record<string, string>>({})
  const [vistas, setVistas] = useState<Deteccion[]>([])
  const borrarVistas = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const actual = useRef(s)
  useEffect(() => {
    actual.current = s
  }, [s])

  // El resumen dice de quién es y en qué estado general va; lo cambian eventos como el relevo.
  const leerDetalle = useCallback(async (): Promise<OtDetalle | null> => {
    try {
      const d = await api.leerOtCliente(otId)
      setDetalle(d)
      setAcceso('ok')
      return d
    } catch (e) {
      const ajena = e instanceof ApiError && (e.tipo === 'no_existe' || e.tipo === 'permiso')
      // Sin respuesta no se puede comprobar: se mira igual, las rutas de la OT están abiertas.
      setAcceso((antes) => (ajena ? 'denegado' : antes === 'verificando' ? 'ok' : antes))
      return null
    }
  }, [otId])

  useEffect(() => {
    let vivo = true
    ;(async () => {
      const d = await leerDetalle()
      if (!d || !vivo) return
      try {
        const p = await api.leerPauta(d.pauta, d.version)
        if (vivo) setPauta(p)
      } catch {
        // Sin pauta se ve igual; solo falta qué espera cada sensor.
      }
    })()
    return () => {
      vivo = false
    }
  }, [leerDetalle])

  const refrescarEstado = useCallback(() => {
    api.leerOt(otId).then(
      (estado) => dispatch({ tipo: 'estado', estado }),
      () => {},
    )
  }, [otId])

  useEffect(() => {
    if (acceso !== 'ok') return
    const cerrar = conectarStream(
      (desde) => urlStream(config.API_URL, otId, desde),
      () => actual.current.ultimoId,
      {
        mensaje(m, esInicial) {
          switch (m.tipo) {
            case 'snapshot':
              dispatch({ tipo: 'snapshot', snapshot: m, inicial: esInicial })
              setSesion(m.sesion)
              setSensores(m.sensores ?? {})
              break
            case 'evento':
              dispatch({ tipo: 'evento', evento: m.evento })
              if (m.evento.paso_id) refrescarEstado()
              if (['ot_asignada', 'relevo_entregado', 'relevo_recibido'].includes(m.evento.tipo)) void leerDetalle()
              break
            case 'calificacion_ot':
              dispatch({ tipo: 'calificacion', calificacion: m.calificacion })
              break
            case 'sesion':
              setSesion(m.sesion)
              break
            case 'lectura':
              setSensores((antes) => (antes[m.sensor_id] === m.valor ? antes : { ...antes, [m.sensor_id]: m.valor }))
              break
            case 'detecciones':
              setVistas(m.objetos)
              clearTimeout(borrarVistas.current)
              borrarVistas.current = setTimeout(() => setVistas([]), VISTAS_VIVEN_MS)
              break
          }
        },
        conexion: (conexion) => dispatch({ tipo: 'conexion', conexion }),
      },
    )
    return () => {
      cerrar()
      clearTimeout(borrarVistas.current)
    }
  }, [acceso, otId, refrescarEstado, leerDetalle])

  return { s, acceso, detalle, pauta, sesion, sensores, vistas }
}
