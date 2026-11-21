import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { RequiereRol } from './RequiereRol'
import { guardarSesion } from './sesion'
import { USUARIOS } from './usuarios'

function rutas() {
  return (
    <MemoryRouter initialEntries={['/ot/ot-12']}>
      <Routes>
        <Route path="/login" element={<p>login</p>} />
        <Route path="/ot/:id" element={<RequiereRol rol="operador"><p>ejecución</p></RequiereRol>} />
      </Routes>
    </MemoryRouter>
  )
}

it('sends a visitor without session to /login', () => {
  render(rutas())
  expect(screen.getByText('login')).toBeInTheDocument()
})

it('sends a supervisor away from an operator route', () => {
  guardarSesion(USUARIOS[0])
  render(rutas())
  expect(screen.getByText('login')).toBeInTheDocument()
})

it('lets an operator in', () => {
  guardarSesion(USUARIOS[2])
  render(rutas())
  expect(screen.getByText('ejecución')).toBeInTheDocument()
})
