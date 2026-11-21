import { useEffect } from 'react'

/** Pantalla encendida mientras `activo`: con la pantalla bloqueada el celular corta el WebSocket y no suena. */
export function useWakeLock(activo: boolean): void {
  useEffect(() => {
    if (!activo || typeof navigator === 'undefined' || !('wakeLock' in navigator)) return
    let candado: WakeLockSentinel | null = null
    let vivo = true

    const pedir = async () => {
      try {
        const nuevo = await navigator.wakeLock.request('screen')
        if (vivo) candado = nuevo
        else void nuevo.release()
      } catch {
        // Sin permiso o sin HTTPS: la pantalla puede apagarse; no hay nada más que hacer.
      }
    }
    // El navegador suelta el candado al ocultar la pestaña: se pide de nuevo al volver.
    const alVolver = () => {
      if (document.visibilityState === 'visible') void pedir()
    }

    void pedir()
    document.addEventListener('visibilitychange', alVolver)
    return () => {
      vivo = false
      document.removeEventListener('visibilitychange', alVolver)
      void candado?.release().catch(() => {})
    }
  }, [activo])
}
