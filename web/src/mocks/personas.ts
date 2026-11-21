// Las personas del mock: las mismas de la minera ficticia Oculta en la semilla del servidor
// (datos/ots-semilla.json), con sus ids. En el mock todas entran con la clave CLAVE_MOCK; las
// claves del servidor de verdad no van en el repo.

import type { Persona } from '../api/tipos'
import { guardarSesion } from '../sesion/sesion'
import { recordarNombres, usuarioDe, type Usuario } from '../sesion/usuarios'

export const CLAVE_MOCK = 'demo'
const DURACION_MS = 12 * 60 * 60 * 1000

const OCULTA = { id: 'oculta', nombre: 'Oculta', industria: 'minería' }

export const PERSONAS: Persona[] = [
  { id: 'supervisor:oculta', nombre: 'Carla Muñoz', usuario: 'carla.munoz@oculta.example', rol: 'supervisor', cliente: OCULTA },
  { id: 'operario:1', nombre: 'Ana Rojas', usuario: 'ana.rojas@oculta.example', rol: 'operador', cliente: OCULTA },
  { id: 'operario:2', nombre: 'Bruno Díaz', usuario: 'bruno.diaz@oculta.example', rol: 'operador', cliente: OCULTA },
]

export const [SUPERVISORA, ANA, BRUNO] = PERSONAS as [Persona, Persona, Persona]

const PREFIJO = 'mock.'

export const tokenMock = (personaId: string): string => `${PREFIJO}${personaId}`

/** La persona dueña de una cabecera `Authorization: Bearer mock.<id>`, o null. */
export function personaDeCabecera(authorization: string | null): Persona | null {
  const [tipo, token] = (authorization ?? '').split(' ')
  if (tipo?.toLowerCase() !== 'bearer' || !token?.startsWith(PREFIJO)) return null
  return PERSONAS.find((p) => p.id === token.slice(PREFIJO.length)) ?? null
}

export const expiraMock = (): string => new Date(Date.now() + DURACION_MS).toISOString()

/** Entra como una persona del mock, sin pasar por el login. En el mock se conocen todos los nombres. */
export function entrarComo(p: Persona): Usuario {
  const usuario = usuarioDe(p)
  recordarNombres(PERSONAS)
  guardarSesion({ usuario, token: tokenMock(p.id), expira: expiraMock() })
  return usuario
}

/** `?como=operario:1` entra como esa persona (solo con mock): sirve para los enlaces del demo. */
export function entrarDesdeLaUrl(search: string): Usuario | null {
  const como = new URLSearchParams(search).get('como')
  const p = PERSONAS.find((x) => x.id === como)
  return p ? entrarComo(p) : null
}
