import { createTheme, type MantineColorsTuple } from '@mantine/core'

// Colores de seguridad industrial (ISO 3864, ANSI Z535). Ver knowledge/architecture/FRONTEND.md §4.
// Nadie escribe un hex fuera de este archivo.

const accion: MantineColorsTuple = ['#ebf1f7', '#d1dfec', '#adc6de', '#85a9cd', '#5c8cbc', '#2e6caa', '#004C97', '#004180', '#00356a', '#002a53']
const verificado: MantineColorsTuple = ['#ebf5ef', '#d1e9dc', '#add8c1', '#85c4a2', '#5cb083', '#2e9a60', '#00843D', '#007034', '#005c2b', '#004922']
const precaucion: MantineColorsTuple = ['#fffbeb', '#fff7d1', '#fff0ad', '#ffe985', '#ffe25c', '#ffd92e', '#FFD100', '#d9b200', '#b29200', '#7A5C00']
const peligro: MantineColorsTuple = ['#fbecee', '#f5d4d9', '#edb3bc', '#e58c9b', '#dc6679', '#d23b54', '#C8102E', '#aa0e27', '#8c0b20', '#6e0919']
const roca: MantineColorsTuple = ['#f2f3f4', '#e1e3e5', '#cbced1', '#b0b5ba', '#969ca3', '#79818a', '#5B6570', '#4d565f', '#40474e', '#32383e']

export const tema = createTheme({
  primaryColor: 'accion',
  primaryShade: 6,
  // Un solo radio para tarjetas, botones y campos: las pantallas de Diego y las de Dani se ven iguales.
  defaultRadius: 'md',
  colors: { accion, verificado, precaucion, peligro, roca },
  black: '#1F262E',
  white: '#FFFFFF',
  autoContrast: true, // texto grafito sobre el amarillo, blanco sobre los demás
})

/** Fondo de la app (Polvo). */
export const FONDO = '#EDF0F2'
