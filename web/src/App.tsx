import '@mantine/core/styles.css'
import './index.css'
import { MantineProvider } from '@mantine/core'
import { BrowserRouter, Route, Routes } from 'react-router'
import { PaginaOt } from './ejecucion/PaginaOt'
import { RequiereRol } from './sesion/RequiereRol'
import { FONDO, tema } from './tema'

// Rutas. Diego agrega /login, /supervisor, /operador y / (sus pantallas viven en gestion/).
export default function App() {
  return (
    <MantineProvider theme={tema} forceColorScheme="light">
      <div style={{ minHeight: '100vh', background: FONDO }}>
        <BrowserRouter>
          <Routes>
            <Route
              path="/ot/:id"
              element={
                <RequiereRol rol="operador">
                  <PaginaOt />
                </RequiereRol>
              }
            />
          </Routes>
        </BrowserRouter>
      </div>
    </MantineProvider>
  )
}
