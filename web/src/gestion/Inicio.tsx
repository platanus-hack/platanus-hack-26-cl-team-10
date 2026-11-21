import { Navigate } from 'react-router'
import { useSesion } from '../sesion/sesion'
import { inicioDe } from './estados'

/** `/` y cualquier ruta desconocida: al dashboard del rol, o al login sin sesión. */
export function Inicio() {
  const usuario = useSesion()
  return <Navigate to={usuario ? inicioDe(usuario.rol) : '/login'} replace />
}
