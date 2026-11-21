export type Rol = 'supervisor' | 'operador'

/** `id` es el actor que viaja a la API (formato de la bitácora). */
export type Usuario = { id: string; nombre: string; rol: Rol }

export const USUARIOS: Usuario[] = [
  { id: 'supervisor:1', nombre: 'Supervisor', rol: 'supervisor' },
  { id: 'operario:1', nombre: 'OP1', rol: 'operador' },
  { id: 'operario:2', nombre: 'OP2', rol: 'operador' },
]

/** El nombre corto de un actor de la bitácora; si no es un usuario del demo, el actor tal cual. */
export function nombreDe(actor: string): string {
  return USUARIOS.find((u) => u.id === actor)?.nombre ?? actor
}
