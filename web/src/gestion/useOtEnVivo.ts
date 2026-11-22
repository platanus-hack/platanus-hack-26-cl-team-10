// Lo que el supervisor ve de una OT, en vivo y sin tocar nada: el stream de la OT (estado,
// alertas, bitácora, sesión, sensores y lo que ve la cámara), su resumen y su pauta.
// No abre sesión ni declara: mirar no cambia la bitácora. Tampoco habla, salvo en el demo (config.VOZ_EN).

import { useCallback, useEffect, useReducer, useRef, useState } from 'react'
import { api, ApiError, urlStream } from '../api/cliente'
import type { Deteccion, OtDetalle, Pauta, Sesion } from '../api/tipos'
import { config } from '../config'
import { inicial, reducir } from '../ejecucion/estado'
import { conectarStream } from '../ejecucion/stream'
import { useAvisosEnVoz } from '../ejecucion/useAvisosEnVoz'

export type Acceso = 'verificando' | 'ok' | 'denegado'

/** Sin detecciones nuevas en este tiempo, lo que se veía es viejo y se borra (como en el monitor). */
export const VISTAS_VIVEN_MS = 1000

/**
 * Lo que se sabe de un sensor. `enVivo` es falso mientras el valor sea solo el que trajo el
 * snapshot: es lo último que el servidor guardó, quizá hace horas. `serie` son sus últimas
 * lecturas en vivo, si son números, para dibujar hacia dónde va.
 */
export type Lectura = { valor: string; enVivo: boolean; serie: number[] }
/** Cuántas lecturas guarda la serie: lo que el monitor muestra de la temperatura. */
export const SERIE_MAX = 90

const numero = (valor: string): number | null => (valor.trim() !== '' && Number.isFinite(Number(valor)) ? Number(valor) : null)

export function useOtEnVivo(otId: string) {
  const [s, dispatch] = useReducer(reducir, inicial)
  const [acceso, setAcceso] = useState<Acceso>('verificando')
  const [detalle, setDetalle] = useState<OtDetalle | null>(null)
  const [pauta, setPauta] = useState<Pauta | null>(null)
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [sensores, setSensores] = useState<Record<string, Lectura>>({})
  const [vistas, setVistas] = useState<Deteccion[]>([])
  const borrarVistas = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const actual = useRef(s)
  useEffect(() => {
    actual.current = s
  }, [s])

  // SOLO PARA EL DEMO: los avisos en voz suenan en esta vista, así no hace falta una ventana del operario abierta.
  useAvisosEnVoz(s, dispatch, config.VOZ_EN === 'supervisor')

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
              // Al reconectar se conserva la serie, pero todo vuelve a ser «guardado» hasta que llegue una lectura.
              setSensores((antes) =>
                Object.fromEntries(Object.entries(m.sensores ?? {}).map(([id, valor]) => [id, { valor: String(valor), enVivo: false, serie: antes[id]?.serie ?? [] }])),
              )
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
              setSensores((antes) => {
                const valor = String(m.valor)
                const previa = antes[m.sensor_id]
                const n = numero(valor)
                // Un sensor de texto que repite su valor no cambia nada; un número siempre suma a la serie.
                if (n === null && previa?.enVivo && previa.valor === valor) return antes
                const serie = n === null ? [] : [...(previa?.serie ?? []), n].slice(-SERIE_MAX)
                return { ...antes, [m.sensor_id]: { valor, enVivo: true, serie } }
              })
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
