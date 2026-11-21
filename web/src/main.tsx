import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { config } from './config'

async function arrancar() {
  // Con el servidor se entra por el login. Con mock, además, por URL: /ot/ot-12?como=operario:1
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
