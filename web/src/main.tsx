import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { config } from './config'
import { guardarSesion, sesionDeLaUrl } from './sesion/sesion'

async function arrancar() {
  // Login falso por URL mientras no esté la pantalla de Diego: /ot/ot-12?como=operario:1
  const usuario = sesionDeLaUrl(location.search)
  if (usuario) guardarSesion(usuario)
  if (config.MOCK) {
    const { iniciarMock } = await import('./mocks/navegador')
    await iniciarMock()
  }
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
}

void arrancar()
