import { ANA, entrarDesdeLaUrl, PERSONAS } from '../mocks/personas'
import { cerrarSesion, guardarSesion, leerSesion, motivoDeSalida, tokenDeSesion } from './sesion'
import { nombreDe, recordarNombres, usuarioDe } from './usuarios'

const enUnaHora = () => new Date(Date.now() + 3600_000).toISOString()

it('round-trips the session and its token through localStorage', () => {
  guardarSesion({ usuario: usuarioDe(ANA), token: 't-ana', expira: enUnaHora() })
  expect(leerSesion()).toEqual({ id: 'operario:1', nombre: 'Ana Rojas', rol: 'operador', cliente: { id: 'oculta', nombre: 'Oculta' } })
  expect(tokenDeSesion()).toBe('t-ana')
  cerrarSesion()
  expect(leerSesion()).toBeNull()
  expect(tokenDeSesion()).toBeNull()
})

it('drops an expired session: the token no longer works', () => {
  guardarSesion({ usuario: usuarioDe(ANA), token: 't-ana', expira: new Date(Date.now() - 1000).toISOString() })
  expect(leerSesion()).toBeNull()
  expect(tokenDeSesion()).toBeNull()
})

it('ignores corrupt storage and the old session without a token', () => {
  localStorage.setItem('factum.sesion', '{')
  expect(leerSesion()).toBeNull()
  localStorage.setItem('factum.sesion', JSON.stringify({ id: 'operario:1', nombre: 'OP1', rol: 'operador' }))
  expect(leerSesion()).toBeNull()
})

it('tells the login once that the API closed the session', () => {
  guardarSesion({ usuario: usuarioDe(ANA), token: 't', expira: enUnaHora() })
  cerrarSesion('vencida')
  expect(motivoDeSalida()).toBe('vencida')
  expect(motivoDeSalida()).toBeNull()
  cerrarSesion()
  expect(motivoDeSalida()).toBeNull()
})

it('names known actors and reads the rest from the id', () => {
  recordarNombres(PERSONAS)
  expect(nombreDe('operario:2')).toBe('Bruno Díaz')
  expect(nombreDe('supervisor:B')).toBe('Supervisor B')
  expect(nombreDe('sistema')).toBe('sistema')
})

it('?como= signs in a mock person, with a token the mock accepts', () => {
  expect(entrarDesdeLaUrl('?escenario=relevo&como=operario:2')?.nombre).toBe('Bruno Díaz')
  expect(tokenDeSesion()).toBe('mock.operario:2')
  expect(entrarDesdeLaUrl('?como=intruso')).toBeNull()
  expect(entrarDesdeLaUrl('')).toBeNull()
})
