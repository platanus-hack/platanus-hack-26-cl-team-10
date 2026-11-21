import { useEffect, useState } from 'react'
import { api } from '../api/cliente'
import { recordarNombres } from './usuarios'

/**
 * Los nombres de la empresa (`GET /cliente/personas`), para que `nombreDe` diga «Ana Rojas» y no
 * «Operario 1» en la pantalla que lo usa. Los lee cualquier persona, también un operador. Si la
 * API no los da (un servidor anterior, o sin conexión), quedan los ids legibles.
 */
export function useNombres(): void {
  const [, setListos] = useState(false)
  useEffect(() => {
    let vivo = true
    api.listarPersonas().then(
      (personas) => {
        recordarNombres(personas)
        if (vivo) setListos(true)
      },
      () => {},
    )
    return () => {
      vivo = false
    }
  }, [])
}
