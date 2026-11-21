// Los nombres de la empresa llegan una vez por sesión y la pantalla los muestra apenas llegan.

import { act, render, screen, waitFor } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { config } from '../config'
import { ANA, BRUNO, entrarComo } from '../mocks/personas'
import { useNombresDeLaEmpresa } from './nombres'
import { recordarNombres, useNombres } from './usuarios'

const server = setupServer()
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterAll(() => server.close())
afterEach(() => server.resetHandlers())

function Pantalla({ actor }: { actor: string }) {
  useNombresDeLaEmpresa()
  const nombreDe = useNombres()
  return <p>{nombreDe(actor)}</p>
}

it('loads the names once per session, and a name on screen changes when they arrive', async () => {
  let pedidos = 0
  server.use(
    http.get(`${config.API_URL}/cliente/personas`, ({ request }) => {
      pedidos++
      expect(request.headers.get('authorization')).toBe('Bearer mock.operario:1')
      return HttpResponse.json([{ id: 'operario:9', nombre: 'Luis Pérez', rol: 'operador' }])
    }),
  )
  entrarComo(ANA)
  const { unmount } = render(<Pantalla actor="operario:9" />)
  expect(screen.getByText('Operario 9')).toBeInTheDocument()
  expect(await screen.findByText('Luis Pérez')).toBeInTheDocument()
  unmount()

  render(<Pantalla actor="operario:9" />)
  expect(screen.getByText('Luis Pérez')).toBeInTheDocument()
  await new Promise((r) => setTimeout(r, 20))
  expect(pedidos).toBe(1)
})

it('a failure is not an error on screen: the name stays readable from the id', async () => {
  server.use(http.get(`${config.API_URL}/cliente/personas`, () => HttpResponse.json({ login: 'no' }, { status: 500 })))
  entrarComo(BRUNO)
  render(<Pantalla actor="operario:7" />)
  await new Promise((r) => setTimeout(r, 20))
  expect(screen.getByText('Operario 7')).toBeInTheDocument()
})

it('names recorded by anyone else also reach the screen (no session: nothing is asked)', async () => {
  render(<Pantalla actor="operario:8" />)
  expect(screen.getByText('Operario 8')).toBeInTheDocument()
  act(() => recordarNombres([{ id: 'operario:8', nombre: 'Marta Soto' }]))
  await waitFor(() => expect(screen.getByText('Marta Soto')).toBeInTheDocument())
})
