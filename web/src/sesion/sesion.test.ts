import { cerrarSesion, guardarSesion, leerSesion, sesionDeLaUrl } from './sesion'
import { USUARIOS, nombreDe } from './usuarios'

it('round-trips the session through localStorage', () => {
  guardarSesion(USUARIOS[1])
  expect(leerSesion()).toEqual({ id: 'operario:1', nombre: 'OP1', rol: 'operador' })
  cerrarSesion()
  expect(leerSesion()).toBeNull()
})

it('returns null on corrupt storage', () => {
  localStorage.setItem('factum.sesion', '{')
  expect(leerSesion()).toBeNull()
})

it('names actors', () => {
  expect(nombreDe('operario:2')).toBe('OP2')
  expect(nombreDe('sistema')).toBe('sistema')
})

it('sesionDeLaUrl signs in a known demo user only, in any mode', () => {
  expect(sesionDeLaUrl('?escenario=relevo&como=operario:2')?.nombre).toBe('OP2')
  expect(sesionDeLaUrl('?como=intruso')).toBeNull()
  expect(sesionDeLaUrl('')).toBeNull()
})
