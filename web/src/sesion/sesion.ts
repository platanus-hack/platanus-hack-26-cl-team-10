import { useMemo, useSyncExternalStore } from 'react'
import { USUARIOS, type Usuario } from './usuarios'

const CLAVE = 'factum.sesion'
const EVENTO = 'factum:sesion'

function leerCruda(): string | null {
  try {
    return localStorage.getItem(CLAVE)
  } catch {
    return null
  }
}

function desdeCruda(cruda: string | null): Usuario | null {
  if (!cruda) return null
  try {
    const u = JSON.parse(cruda) as Partial<Usuario>
    return USUARIOS.find((x) => x.id === u.id) ?? null
  } catch {
    return null
  }
}

export function leerSesion(): Usuario | null {
  return desdeCruda(leerCruda())
}

export function guardarSesion(u: Usuario): void {
  try {
    localStorage.setItem(CLAVE, JSON.stringify(u))
  } catch {
    // Sin almacenamiento (modo privado): la sesión dura lo que dura la pestaña.
  }
  window.dispatchEvent(new Event(EVENTO))
}

export function cerrarSesion(): void {
  try {
    localStorage.removeItem(CLAVE)
  } catch {
    // nada que borrar
  }
  window.dispatchEvent(new Event(EVENTO))
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
  return useMemo(() => desdeCruda(cruda), [cruda])
}
