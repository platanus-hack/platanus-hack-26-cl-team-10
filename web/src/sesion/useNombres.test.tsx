import { render, screen } from '@testing-library/react'
import { api } from '../api/cliente'
import { useNombres } from './useNombres'
import { nombreDe } from './usuarios'

afterEach(() => vi.restoreAllMocks())

function Relevo({ actor }: { actor: string }) {
  useNombres()
  return <p>Entregado por {nombreDe(actor)}</p>
}

it('an operator sees the name of a colleague once the API gives the names of the company', async () => {
  vi.spyOn(api, 'listarPersonas').mockResolvedValue([{ id: 'operario:71', nombre: 'Zoe Paz', rol: 'operador' }])
  render(<Relevo actor="operario:71" />)
  expect(screen.getByText('Entregado por Operario 71')).toBeInTheDocument()
  expect(await screen.findByText('Entregado por Zoe Paz')).toBeInTheDocument()
})

it('keeps the readable id when the API has no names to give', async () => {
  const pedir = vi.spyOn(api, 'listarPersonas').mockRejectedValue(new Error('sin ruta'))
  render(<Relevo actor="operario:72" />)
  await pedir.mock.results[0]?.value.catch(() => {})
  expect(screen.getByText('Entregado por Operario 72')).toBeInTheDocument()
})
