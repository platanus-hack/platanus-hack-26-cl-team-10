// Arranca el mock en el navegador (VITE_MOCK=1). El escenario sale de ?escenario= y la pauta de ?pauta=loto.

import { setupWorker } from 'msw/browser'
import { pautaDeLaUrl } from './pauta'
import { ESCENARIOS, escenarioDeLaUrl } from './escenarios'
import { crearHandlers } from './handlers'
import { Mundo } from './mundo'
import { entrarDesdeLaUrl, PERSONAS } from './personas'
import { recordarNombres } from '../sesion/usuarios'

export async function iniciarMock(): Promise<void> {
  // En el mock se conocen todas las personas; ?como=operario:1 entra sin pasar por el login.
  recordarNombres(PERSONAS)
  entrarDesdeLaUrl(location.search)
  const nombre = escenarioDeLaUrl(location.search)
  const escenario = ESCENARIOS[nombre]!
  const mundo = new Mundo(pautaDeLaUrl(location.search))
  escenario.preparar(mundo)

  const worker = setupWorker(...crearHandlers(mundo, escenario, (ms, fn) => void setTimeout(fn, ms)))
  await worker.start({ onUnhandledRequest: 'bypass', quiet: true })
  console.info(`[mock] escenario «${nombre}», pauta ${mundo.pauta.id}`)
}
