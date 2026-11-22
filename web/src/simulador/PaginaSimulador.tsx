import { Box, useMantineTheme } from '@mantine/core'
import { useMemo } from 'react'
import { config } from '../config'
import { Encabezado } from '../gestion/ui'
import { useSesion } from '../sesion/sesion'
import { FONDO, tema, variablesDelTema } from '../tema'

// El simulador es una página estática (public/simulador.html): el motor de reglas y la escena 3D en
// JavaScript, sin build. Esta pantalla le pone la banda de la marca y le pasa la URL de la API y los
// colores de tema.ts, para que ningún hex se escriba fuera de ahí. La sesión la lee del mismo
// localStorage: entra a la base como la persona que ya entró a la app.
const ALTO_BANDA = 56

const tono = (color: string, i: number): string => tema.colors?.[color]?.[i] ?? ''

export function PaginaSimulador() {
  const usuario = useSesion()
  const temaCompleto = useMantineTheme()
  const src = useMemo(() => {
    // FONDO es una variable CSS que la página del iframe no tiene: va su valor en claro.
    const colores = {
      grafito: tema.black ?? '',
      blanco: tema.white ?? '',
      fondo: variablesDelTema(temaCompleto).light['--factum-fondo'] ?? '',
      roca: tono('roca', 6),
      roca2: tono('roca', 2),
      roca1: tono('roca', 1),
      roca0: tono('roca', 0),
      accion: tono('accion', 6),
      accion1: tono('accion', 1),
      accion0: tono('accion', 0),
      verificado: tono('verificado', 6),
      verificado0: tono('verificado', 0),
      precaucion: tono('precaucion', 6),
      precaucionTexto: tono('precaucion', 9),
      precaucion0: tono('precaucion', 0),
      peligro: tono('peligro', 6),
      peligro0: tono('peligro', 0),
    }
    const q = new URLSearchParams({
      embebido: '1',
      api: config.API_URL,
      sesion: config.MOCK ? 'factum.sesion.mock' : 'factum.sesion',
      tema: JSON.stringify(colores),
    })
    return `/simulador.html?${q.toString()}${window.location.hash}`
  }, [temaCompleto])
  if (!usuario) return null
  return (
    <>
      <Encabezado usuario={usuario} seccion="Simulador" />
      <Box
        component="iframe"
        src={src}
        title="Simulador de Factum: la ejecución de una OT, contra la base"
        style={{ display: 'block', width: '100%', height: `calc(100vh - ${ALTO_BANDA}px)`, border: 0, background: FONDO }}
      />
    </>
  )
}
