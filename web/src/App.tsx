import '@mantine/core/styles.css'
import './index.css'
import { MantineProvider } from '@mantine/core'
import { BrowserRouter, Route, Routes } from 'react-router'
import { PaginaOt } from './ejecucion/PaginaOt'
import { Inicio } from './gestion/Inicio'
import { PaginaLogin } from './gestion/PaginaLogin'
import { PaginaOperador } from './gestion/PaginaOperador'
import { PaginaSupervisor } from './gestion/PaginaSupervisor'
import { RequiereRol } from './sesion/RequiereRol'
import { FONDO, tema } from './tema'

// Rutas. Gestión (Diego) en gestion/, ejecución (Dani) en ejecucion/.
export default function App() {
  return (
    <MantineProvider theme={tema} forceColorScheme="light">
      <div style={{ minHeight: '100vh', background: FONDO }}>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<PaginaLogin />} />
            <Route
              path="/supervisor"
              element={
                <RequiereRol rol="supervisor">
                  <PaginaSupervisor />
                </RequiereRol>
              }
            />
            <Route
              path="/operador"
              element={
                <RequiereRol rol="operador">
                  <PaginaOperador />
                </RequiereRol>
              }
            />
            <Route
              path="/ot/:id"
              element={
                <RequiereRol rol="operador">
                  <PaginaOt />
                </RequiereRol>
              }
            />
            <Route path="*" element={<Inicio />} />
          </Routes>
        </BrowserRouter>
      </div>
    </MantineProvider>
  )
}
