// Los nombres de la empresa (`GET /cliente/personas`), una vez por sesión: al entrar, o al abrir
// el front con una sesión guardada. Sirven para mostrar «Ana Rojas» donde la bitácora dice `operario:1`.

import { useEffect } from 'react'
import { api } from '../api/cliente'
import { tokenDeSesion, useSesion } from './sesion'
import { recordarNombres } from './usuarios'

/** El token con que ya se pidieron: otra persona que entra los vuelve a pedir. */
let pedidosCon: string | null = null

export function useNombresDeLaEmpresa(): void {
  const usuario = useSesion()
  useEffect(() => {
    const token = tokenDeSesion()
    if (!usuario || !token || token === pedidosCon) return
    pedidosCon = token
    // Son un adorno: si fallan, el nombre se lee del id y se reintenta en la próxima pantalla.
    api.listarPersonas().then(recordarNombres, () => {
      if (pedidosCon === token) pedidosCon = null
    })
  }, [usuario])
}

/** Sin pantalla: va una vez en la raíz de la app. */
export function NombresDeLaEmpresa() {
  useNombresDeLaEmpresa()
  return null
}
