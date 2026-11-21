// Une la máquina de estados con la API: el WebSocket de la OT, los GET que refrescan,
// las acciones del operario, la voz y la pantalla encendida.

import { useCallback, useEffect, useReducer, useRef, useState, useSyncExternalStore } from 'react'
import { api, ApiError, urlStream } from '../api/cliente'
import type { Pauta } from '../api/tipos'
import { config } from '../config'
import type { Usuario } from '../sesion/usuarios'
import { inicial, reducir } from './estado'
import { conectarStream } from './stream'
import { useWakeLock } from './useWakeLock'
import { voz } from './voz'

const REINTENTO_SESION_MS = 3000

function mensajeDe(e: unknown): string {
  if (e instanceof ApiError) return e.tipo === 'regla' && e.regla ? e.regla : e.message
  return 'Algo falló. Intenta de nuevo.'
}

export function useEjecucion(otId: string, usuario: Usuario) {
  const [s, dispatch] = useReducer(reducir, inicial)
  const [pauta, setPauta] = useState<Pauta | null>(null)
  const [sesionDesde, setSesionDesde] = useState<number | null>(null)
  const audio = useSyncExternalStore(voz.alCambiar, voz.estado)

  // Lo que leen los callbacks sin volver a crearse en cada render.
  const actual = useRef(s)
  useEffect(() => {
    actual.current = s
  }, [s])

  const refrescar = useCallback(() => {
    api.leerOt(otId).then(
      (estado) => dispatch({ tipo: 'estado', estado }),
      () => {},
    )
  }, [otId])

  // La pauta trae la instrucción y el tipo de evidencia de cada paso.
  useEffect(() => {
    let vivo = true
    ;(async () => {
      try {
        const resumen = (await api.listarOts()).find((o) => o.ot === otId)
        if (!resumen) return
        const p = await api.leerPauta(resumen.pauta, resumen.version)
        if (vivo) setPauta(p)
      } catch {
        // Sin pauta la pantalla igual funciona: solo no muestra la instrucción.
      }
    })()
    return () => {
      vivo = false
    }
  }, [otId])

  // Escuchar no necesita un toque: se conecta al entrar.
  useEffect(
    () =>
      conectarStream(
        (desde) => urlStream(config.API_URL, otId, desde),
        () => actual.current.ultimoId,
        {
          mensaje(m, esInicial) {
            switch (m.tipo) {
              case 'snapshot':
                dispatch({ tipo: 'snapshot', snapshot: m, inicial: esInicial })
                break
              case 'evento':
                dispatch({ tipo: 'evento', evento: m.evento })
                if (m.evento.paso_id) refrescar()
                break
              case 'calificacion_ot':
                dispatch({ tipo: 'calificacion', calificacion: m.calificacion })
                break
            }
          },
          conexion: (conexion) => dispatch({ tipo: 'conexion', conexion }),
        },
      ),
    [otId, refrescar],
  )

  // Cada evento de nivel error suena una vez, en orden.
  useEffect(() => {
    if (s.porSonar.length === 0) return
    for (const ev of s.porSonar) voz.decir(ev.detalle)
    dispatch({ tipo: 'sonado', ids: s.porSonar.map((e) => e.id) })
  }, [s.porSonar])

  useWakeLock(sesionDesde !== null && !s.ot?.completa)

  // Sin sesión las lecturas del edge no llegan a la OT: si abrirla falla, se reintenta.
  const [fallosSesion, setFallosSesion] = useState(0)
  const abrirSesion = useCallback(async () => {
    try {
      await api.abrirSesion(otId, config.EDGE_ID, usuario.id)
      setSesionDesde((d) => d ?? Date.now())
    } catch (e) {
      dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      setFallosSesion((n) => n + 1)
    }
  }, [otId, usuario.id])
  useEffect(() => {
    if (fallosSesion === 0 || sesionDesde !== null) return
    const reintento = setTimeout(() => void abrirSesion(), REINTENTO_SESION_MS)
    return () => clearTimeout(reintento)
  }, [fallosSesion, sesionDesde, abrirSesion])

  /** Dentro de un toque: desbloquea el audio (si hace falta) y une la OT con el edge. */
  const comenzar = useCallback(async () => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    await abrirSesion()
  }, [abrirSesion])

  const hecho = useCallback(async () => {
    const { ot, pendiente } = actual.current
    const pasoId = ot?.paso_actual
    if (!pasoId || pendiente) return
    dispatch({ tipo: 'hecho_enviado', pasoId })
    try {
      const r = await api.declarar(otId, usuario.id, 'hecho')
      dispatch({ tipo: 'hecho_respondido', pasoId, estado: r.estado })
    } catch (e) {
      if (e instanceof ApiError && e.tipo === 'timeout') dispatch({ tipo: 'hecho_sin_respuesta', pasoId })
      else dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
    }
    refrescar()
  }, [otId, usuario.id, refrescar])

  const sobrescribir = useCallback(
    async (cuerpo: { paso_id?: string; alerta_id?: number; nota?: string }) => {
      try {
        await api.sobrescribir(otId, { actor: usuario.id, ...cuerpo })
      } catch (e) {
        dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      }
      refrescar()
    },
    [otId, usuario.id, refrescar],
  )

  const yaLoHice = useCallback((pasoId: string, nota?: string) => sobrescribir({ paso_id: pasoId, nota }), [sobrescribir])
  const yaLoHiceAlerta = useCallback((alertaId: number, nota?: string) => sobrescribir({ alerta_id: alertaId, nota }), [sobrescribir])

  /** Devuelve true si el turno quedó entregado. */
  const entregarTurno = useCallback(async (): Promise<boolean> => {
    try {
      await api.entregarTurno(otId, usuario.id)
      return true
    } catch (e) {
      dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      return false
    }
  }, [otId, usuario.id])

  /** Dentro de un toque («Recibido»): firma el relevo y sigue desde el paso actual. */
  const recibirTurno = useCallback(async () => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    try {
      await api.recibirTurno(otId, usuario.id)
    } catch (e) {
      dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      return
    }
    await abrirSesion()
  }, [otId, usuario.id, abrirSesion])

  return {
    s,
    pauta,
    audio,
    sesionAbierta: sesionDesde !== null,
    sesionDesde,
    comenzar,
    hecho,
    yaLoHice,
    yaLoHiceAlerta,
    entregarTurno,
    recibirTurno,
    probarAudio: () => voz.probar(),
    verMensaje: () => dispatch({ tipo: 'mensaje_visto' }),
  }
}

export type Ejecutor = ReturnType<typeof useEjecucion>
