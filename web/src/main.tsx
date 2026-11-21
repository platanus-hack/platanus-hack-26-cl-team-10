import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import { config } from './config'

async function arrancar() {
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
