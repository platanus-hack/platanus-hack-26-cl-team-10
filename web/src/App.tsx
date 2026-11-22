import '@mantine/core/styles.css'
import './index.css'
// La letra de la marca (solo el eje de peso), servida por el front: sin pedirle nada a Google.
import '@fontsource-variable/bitcount-prop-single/wght.css'
import { MantineProvider } from '@mantine/core'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router'
import { PaginaOt } from './ejecucion/PaginaOt'
import { Inicio } from './gestion/Inicio'
import { PaginaLogin } from './gestion/PaginaLogin'
import { PaginaMejoras } from './gestion/PaginaMejoras'
import { PaginaHoy } from './gestion/PaginaHoy'
import { PaginaProtocolos } from './gestion/PaginaProtocolos'
import { PaginaOperador } from './gestion/PaginaOperador'
import { PaginaOtSupervisor } from './gestion/PaginaOtSupervisor'
import { PaginaSupervisor } from './gestion/PaginaSupervisor'
import { NombresDeLaEmpresa } from './sesion/nombres'
import { RequiereRol } from './sesion/RequiereRol'
import { PaginaSimulador } from './simulador/PaginaSimulador'
import { FONDO, tema, variablesDelTema } from './tema'

export default function App() {
  return (
    <BrowserRouter>
      <Rutas />
    </BrowserRouter>
  )
}

// Rutas. Gestión (Diego) en gestion/, ejecución (Dani) en ejecucion/.
function Rutas() {
  // Lo del supervisor y el login van en oscuro, con el lenguaje del monitor; lo del operario sigue
  // claro, que es lo que se lee en terreno.
  const { pathname } = useLocation()
  const oscuro = pathname.startsWith('/supervisor') || pathname === '/login'
  return (
    <MantineProvider theme={tema} forceColorScheme={oscuro ? 'dark' : 'light'} cssVariablesResolver={variablesDelTema}>
      <NombresDeLaEmpresa />
      <div className="fondo" style={{ minHeight: '100vh', backgroundColor: FONDO }}>
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
            path="/supervisor/hoy"
            element={
              <RequiereRol rol="supervisor">
                <PaginaHoy />
              </RequiereRol>
            }
          />
          <Route
            path="/supervisor/protocolos"
            element={
              <RequiereRol rol="supervisor">
                <PaginaProtocolos />
              </RequiereRol>
            }
          />
          <Route
            path="/supervisor/mejoras"
            element={
              <RequiereRol rol="supervisor">
                <PaginaMejoras />
              </RequiereRol>
            }
          />
          <Route
            path="/supervisor/ot/:id"
            element={
              <RequiereRol rol="supervisor">
                <PaginaOtSupervisor />
              </RequiereRol>
            }
          />
          <Route
            path="/simulador"
            element={
              <RequiereRol rol="supervisor">
                <PaginaSimulador />
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
      </div>
    </MantineProvider>
  )
}
