import { useMemo, useSyncExternalStore } from 'react'
import { config } from '../config'
import { recordarNombres, type Usuario } from './usuarios'

// Con y sin mock se guarda aparte: el token del mock no sirve contra el servidor, ni al revés.
const CLAVE = config.MOCK ? 'factum.sesion.mock' : 'factum.sesion'
const EVENTO = 'factum:sesion'
const MOTIVO = 'factum.salida'

/** Lo que queda guardado al entrar (`POST /auth/entrar`): quién es, su token y cuándo vence. */
export type SesionGuardada = { usuario: Usuario; token: string; expira: string }

const ROLES = new Set(['supervisor', 'operador'])

function leerCruda(): string | null {
  try {
    return localStorage.getItem(CLAVE)
  } catch {
    return null
  }
}

function desdeCruda(cruda: string | null): SesionGuardada | null {
  if (!cruda) return null
  try {
    const s = JSON.parse(cruda) as Partial<SesionGuardada>
    const u = s.usuario
    if (!u || typeof u.id !== 'string' || typeof u.nombre !== 'string' || !ROLES.has(u.rol)) return null
    if (typeof s.token !== 'string' || !s.token || typeof s.expira !== 'string') return null
    // Un token vencido no sirve: se vuelve a entrar.
    if (!(Date.parse(s.expira) > Date.now())) return null
    return s as SesionGuardada
  } catch {
    return null
  }
}

export function leerSesion(): Usuario | null {
  return desdeCruda(leerCruda())?.usuario ?? null
}

/** El token para `Authorization: Bearer`, si hay sesión vigente. */
export function tokenDeSesion(): string | null {
  return desdeCruda(leerCruda())?.token ?? null
}

export function guardarSesion(s: SesionGuardada): void {
  recordarNombres([s.usuario])
  try {
    localStorage.setItem(CLAVE, JSON.stringify(s))
    sessionStorage.removeItem(MOTIVO)
  } catch {
    // Sin almacenamiento (modo privado): la sesión dura lo que dura la pestaña.
  }
  window.dispatchEvent(new Event(EVENTO))
}

/** `vencida`: la API rechazó el token; el login lo dice una vez. */
export function cerrarSesion(motivo?: 'vencida'): void {
  try {
    localStorage.removeItem(CLAVE)
    if (motivo) sessionStorage.setItem(MOTIVO, motivo)
  } catch {
    // nada que borrar
  }
  window.dispatchEvent(new Event(EVENTO))
}

/** Por qué se cerró la última sesión, si la cerró la API. Se lee una vez. */
export function motivoDeSalida(): 'vencida' | null {
  try {
    const motivo = sessionStorage.getItem(MOTIVO)
    sessionStorage.removeItem(MOTIVO)
    return motivo === 'vencida' ? motivo : null
  } catch {
    return null
  }
}

function suscribir(avisar: () => void): () => void {
  window.addEventListener(EVENTO, avisar)
  window.addEventListener('storage', avisar)
  return () => {
    window.removeEventListener(EVENTO, avisar)
    window.removeEventListener('storage', avisar)
  }
}

/** El usuario actual; se actualiza al entrar o salir, también desde otra pestaña. */
export function useSesion(): Usuario | null {
  const cruda = useSyncExternalStore(suscribir, leerCruda)
  return useMemo(() => {
    const s = desdeCruda(cruda)
    if (s) recordarNombres([s.usuario])
    return s?.usuario ?? null
  }, [cruda])
}
