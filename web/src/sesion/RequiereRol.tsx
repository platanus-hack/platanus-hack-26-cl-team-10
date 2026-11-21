import type { ReactNode } from 'react'
import { Navigate } from 'react-router'
import { useSesion } from './sesion'
import type { Rol } from './usuarios'

/** Sin una sesión del rol pedido, manda al login (la pantalla es de Diego). */
export function RequiereRol({ rol, children }: { rol: Rol; children: ReactNode }) {
  const usuario = useSesion()
  if (!usuario || usuario.rol !== rol) return <Navigate to="/login" replace />
  return <>{children}</>
}
