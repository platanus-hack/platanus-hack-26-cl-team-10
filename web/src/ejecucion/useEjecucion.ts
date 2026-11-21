// Une la máquina de estados con la API: el WebSocket de la OT, los GET que refrescan,
// las acciones del operario, la voz y la pantalla encendida.

import { useCallback, useEffect, useReducer, useRef, useState, useSyncExternalStore } from 'react'
import { api, ApiError, urlStream } from '../api/cliente'
import { cierraSolo } from '../api/pauta'
import type { Deteccion, Pauta } from '../api/tipos'
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

  // La pauta trae la instrucción y cómo se cierra cada paso.
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
    const reintento = setTimeout(() => void abrirSesion(), tiempos.reintentoSesionMs)
    return () => clearTimeout(reintento)
  }, [fallosSesion, sesionDesde, abrirSesion])

  /** Dentro de un toque: desbloquea el audio (si hace falta) y une la OT con el edge. */
  const comenzar = useCallback(async () => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    await abrirSesion()
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
    await abrirSesion()
  }, [otId, usuario.id, abrirSesion])

  return {
    s,
    pauta,
    audio,
    vistas,
    sesionAbierta: sesionDesde !== null,
    sesionDesde,
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
