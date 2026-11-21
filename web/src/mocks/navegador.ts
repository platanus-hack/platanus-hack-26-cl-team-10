// Arranca el mock en el navegador (VITE_MOCK=1). El escenario sale de ?escenario= y el usuario de ?como=.

import { setupWorker } from 'msw/browser'
import { PAUTA_DEMO } from './pauta'
import { guardarSesion } from '../sesion/sesion'
import { ESCENARIOS, escenarioDeLaUrl, sesionDeLaUrl } from './escenarios'
import { crearHandlers } from './handlers'
import { Mundo } from './mundo'

export async function iniciarMock(): Promise<void> {
  const usuario = sesionDeLaUrl(location.search)
  if (usuario) guardarSesion(usuario)

  const nombre = escenarioDeLaUrl(location.search)
  const escenario = ESCENARIOS[nombre]!
  const mundo = new Mundo(PAUTA_DEMO)
  escenario.preparar(mundo)

  const worker = setupWorker(...crearHandlers(mundo, escenario, (ms, fn) => void setTimeout(fn, ms)))
  await worker.start({ onUnhandledRequest: 'bypass', quiet: true })
  console.info(`[mock] escenario «${nombre}»${usuario ? ` como ${usuario.nombre}` : ''}`)
}
