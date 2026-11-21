// Une la máquina de estados con la API: el WebSocket de la OT, los GET que refrescan,
// las acciones del operario, la voz y la pantalla encendida.

import { useCallback, useEffect, useReducer, useRef, useState, useSyncExternalStore } from 'react'
import { api, ApiError, urlStream } from '../api/cliente'
import { cierraSolo } from '../api/pauta'
import type { Deteccion, Pauta, Sesion } from '../api/tipos'
import { config } from '../config'
import type { Usuario } from '../sesion/usuarios'
import { inicial, reducir, saltoDe, textoParaVoz } from './estado'
import { conectarStream } from './stream'
import { useWakeLock } from './useWakeLock'
import { voz } from './voz'

/** Tiempos de la pantalla. Los tests los acortan. */
export const tiempos = {
  /** Si abrir la sesión falla, se reintenta: sin sesión las lecturas del edge no llegan a la OT. */
  reintentoSesionMs: 3000,
  /** Cuánto espera un paso que se cierra solo antes de ofrecer «Ya lo hice» (sensor caído, cámara sin vista). */
  esperaEvidenciaMs: 20_000,
}

function mensajeDe(e: unknown): string {
  if (e instanceof ApiError) return e.tipo === 'regla' && e.regla ? e.regla : e.message
  return 'Algo falló. Intenta de nuevo.'
}

/** 403 al abrir la sesión: la estación ejecuta la OT de otra empresa, que no se toma. */
const ESTACION_AJENA = 'La estación está ocupada con una OT de otra empresa. Pide que la liberen; esta OT parte sola apenas quede libre.'

const mismasClases = (a: Deteccion[], b: Deteccion[]) =>
  a.length === b.length && a.every((d, i) => d.clase === b[i].clase)

export function useEjecucion(otId: string, usuario: Usuario) {
  const [s, dispatch] = useReducer(reducir, inicial)
  const [pauta, setPauta] = useState<Pauta | null>(null)
  const [sesionDesde, setSesionDesde] = useState<number | null>(null)
  /** Lo último que vio la cámara del edge, para mostrarlo en el paso de cámara en curso. */
  const [vistas, setVistas] = useState<Deteccion[]>([])
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

  // Primero, si la OT es de esta persona: `GET /cliente/ots/{id}` responde 404 si no es de su
  // empresa o no está asignada a ella. Hasta saberlo no se abre la sesión. Si la API no responde,
  // la pantalla sigue: las rutas de la OT están abiertas y el control de verdad es del servidor.
  const [acceso, setAcceso] = useState<'verificando' | 'ok' | 'denegado'>('verificando')
  // Después, la pauta: trae la instrucción y cómo se cierra cada paso.
  useEffect(() => {
    let vivo = true
    ;(async () => {
      let resumen
      try {
        resumen = await api.leerOtCliente(otId)
      } catch (e) {
        if (!vivo) return
        const ajena = e instanceof ApiError && (e.tipo === 'no_existe' || e.tipo === 'permiso')
        setAcceso(ajena ? 'denegado' : 'ok')
        return
      }
      if (!vivo) return
      setAcceso('ok')
      try {
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
              case 'detecciones':
                setVistas((antes) => (mismasClases(antes, m.objetos) ? antes : m.objetos))
                break
            }
          },
          conexion: (conexion) => dispatch({ tipo: 'conexion', conexion }),
        },
      ),
    [otId, refrescar],
  )

  // Cada evento que tiene que sonar (ver debeSonar) suena una vez, en orden, dicho como frase.
  useEffect(() => {
    if (s.porSonar.length === 0) return
    for (const ev of s.porSonar) voz.decir(textoParaVoz(ev, actual.current.ot))
    dispatch({ tipo: 'sonado', ids: s.porSonar.map((e) => e.id) })
  }, [s.porSonar])

  useWakeLock(sesionDesde !== null && !s.ot?.completa)

  // Un paso que se cierra solo y lleva rato sin evidencia: se ofrece confirmarlo a mano.
  const pasoActual = s.ot?.pasos.find((p) => p.id === s.ot?.paso_actual)
  const pasoEnPauta = pauta?.pasos.find((p) => p.id === pasoActual?.id)
  const esperando =
    sesionDesde !== null &&
    !!pasoActual &&
    pasoActual.estado === 'no_verificado' &&
    !!pasoEnPauta &&
    cierraSolo(pasoEnPauta) &&
    !saltoDe(s, pasoActual.id)
  const pasoEsperando = esperando ? pasoActual.id : null
  useEffect(() => {
    if (!pasoEsperando) return
    const reloj = setTimeout(() => dispatch({ tipo: 'espera_vencida', pasoId: pasoEsperando }), tiempos.esperaEvidenciaMs)
    return () => clearTimeout(reloj)
  }, [pasoEsperando])

  // Abrir la sesión une la OT con la estación (`POST /cliente/ots/{id}/sesion`). Si falla, se
  // reintenta sola cada tantos segundos, siempre sin `tomar`: quitarle la estación a otra OT es un
  // toque de la persona («Tomar la estación»), porque esa OT deja de recibir sus sensores.
  const [fallosSesion, setFallosSesion] = useState(0)
  /** La otra OT que ejecuta la estación, mientras esta espera. */
  const [estacionOcupada, setEstacionOcupada] = useState<Sesion | null>(null)
  const [tomando, setTomando] = useState(false)
  const abrirSesion = useCallback(
    async (tomar: boolean) => {
      try {
        await api.abrirSesion(otId, config.EDGE_ID, tomar)
        setEstacionOcupada(null)
        setSesionDesde((d) => d ?? Date.now())
        return
      } catch (e) {
        if (e instanceof ApiError && e.tipo === 'regla') {
          // Un 409 puede ser la estación ocupada: se pregunta cuál OT la tiene. La regla de la API
          // está escrita para quien la llama, no para el operario, así que no se muestra.
          const ocupante = await api.leerSesionEdge(config.EDGE_ID).catch(() => undefined)
          if (ocupante === undefined) {
            setFallosSesion((n) => n + 1)
            return
          }
          if (ocupante && ocupante.ot_id !== otId) {
            setEstacionOcupada(ocupante)
            setFallosSesion((n) => n + 1)
            return
          }
          // Otra regla (la OT ya está completa): se muestra y no se reintenta.
          setEstacionOcupada(null)
          dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
          return
        }
        if (e instanceof ApiError && e.tipo === 'permiso') {
          setEstacionOcupada(null)
          dispatch({ tipo: 'error', mensaje: ESTACION_AJENA })
        } else {
          dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
        }
        // La OT que no es suya o el login vencido no se arreglan reintentando.
        if (e instanceof ApiError && (e.tipo === 'no_existe' || e.tipo === 'sesion')) return
        setFallosSesion((n) => n + 1)
      }
    },
    [otId],
  )
  useEffect(() => {
    if (fallosSesion === 0 || sesionDesde !== null) return
    const reintento = setTimeout(() => void abrirSesion(false), tiempos.reintentoSesionMs)
    return () => clearTimeout(reintento)
  }, [fallosSesion, sesionDesde, abrirSesion])

  /** Dentro de un toque: desbloquea el audio (si hace falta) y une la OT con el edge. */
  const comenzar = useCallback(async () => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    await abrirSesion(false)
  }, [abrirSesion])

  /** «Tomar la estación»: el único camino que manda `tomar`. */
  const tomarEstacion = useCallback(async () => {
    setTomando(true)
    try {
      await abrirSesion(true)
    } finally {
      setTomando(false)
    }
  }, [abrirSesion])

  /** «Hecho» en un paso que se cierra declarando (confirmación, o cámara que se juzga al declarar). */
  const hecho = useCallback(
    async (pasoId: string) => {
      if (actual.current.pendiente) return
      dispatch({ tipo: 'hecho_enviado', pasoId })
      try {
        const r = await api.declarar(otId, usuario.id, 'hecho', pasoId)
        dispatch({ tipo: 'hecho_respondido', pasoId, estado: r.estado })
      } catch (e) {
        if (e instanceof ApiError && e.tipo === 'timeout') dispatch({ tipo: 'hecho_sin_respuesta', pasoId })
        else dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      }
      refrescar()
    },
    [otId, usuario.id, refrescar],
  )

  /** «Ya lo hice»: la persona confirma el paso en curso contra la evidencia, con un motivo. */
  const confirmar = useCallback(
    async (pasoId: string, motivo: string) => {
      try {
        await api.confirmarPaso(otId, pasoId, usuario.id, motivo)
      } catch (e) {
        dispatch({ tipo: 'error', mensaje: mensajeDe(e) })
      }
      refrescar()
    },
    [otId, usuario.id, refrescar],
  )

  /** «Escuchar de nuevo» en el aviso: es un toque, así que también desbloquea el audio si hacía falta. */
  const escucharAviso = useCallback(async (texto: string) => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    voz.decir(texto)
  }, [])

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
    await abrirSesion(false)
  }, [otId, usuario.id, abrirSesion])

  return {
    s,
    /** Si esta persona puede abrir la OT: `denegado` si no es suya. */
    acceso,
    pauta,
    audio,
    vistas,
    sesionAbierta: sesionDesde !== null,
    sesionDesde,
    /** La otra OT que ejecuta la estación, mientras esta espera para empezar. */
    estacionOcupada: sesionDesde === null ? estacionOcupada : null,
    tomandoEstacion: tomando,
    tomarEstacion,
    comenzar,
    hecho,
    confirmar,
    entregarTurno,
    recibirTurno,
    probarAudio: () => voz.probar(),
    verMensaje: () => dispatch({ tipo: 'mensaje_visto' }),
    /** El aviso que está en grande sobre la pantalla, si hay uno. */
    aviso: s.enPantalla[0] ?? null,
    escucharAviso,
    cerrarAviso: (id: number) => dispatch({ tipo: 'aviso_cerrado', id }),
  }
}

export type Ejecutor = ReturnType<typeof useEjecucion>
