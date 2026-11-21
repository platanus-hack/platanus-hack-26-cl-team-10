import type { Persona, Rol } from '../api/tipos'

export type { Rol }

/** Quién usa el front. `id` es el actor que viaja a la API (formato de la bitácora). */
export type Usuario = { id: string; nombre: string; rol: Rol; cliente?: { id: string; nombre: string } }

/** Lo que el front guarda de la persona que entró. */
export function usuarioDe(p: Persona): Usuario {
  return { id: p.id, nombre: p.nombre, rol: p.rol, cliente: { id: p.cliente.id, nombre: p.cliente.nombre } }
}

// Los nombres que el front conoce: el de quien entró y los de su empresa (`GET /cliente/personas`,
// que lee cualquiera de sus personas; ver useNombres).
const nombres = new Map<string, string>()

export function recordarNombres(personas: { id: string; nombre: string }[]): void {
  for (const p of personas) nombres.set(p.id, p.nombre)
}

/**
 * El nombre de un actor de la bitácora. Si el front no lo conoce, se lee del id:
 * «operario:2» es «Operario 2»; «sistema» queda tal cual.
 */
export function nombreDe(actor: string): string {
  const conocido = nombres.get(actor)
  if (conocido) return conocido
  const [rol, resto] = actor.split(':', 2)
  if (!resto) return actor
  return `${rol.charAt(0).toUpperCase()}${rol.slice(1)} ${resto}`
}
