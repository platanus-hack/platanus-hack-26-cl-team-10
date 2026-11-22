import { createTheme, type CSSVariablesResolver, type MantineColorsTuple } from '@mantine/core'
import type { CSSProperties } from 'react'

// Colores de seguridad industrial (ISO 3864, ANSI Z535). Ver knowledge/architecture/FRONTEND.md §4.
// Nadie escribe un hex fuera de este archivo.

const accion: MantineColorsTuple = ['#ebf1f7', '#d1dfec', '#adc6de', '#85a9cd', '#5c8cbc', '#2e6caa', '#004C97', '#004180', '#00356a', '#002a53']
const verificado: MantineColorsTuple = ['#ebf5ef', '#d1e9dc', '#add8c1', '#85c4a2', '#5cb083', '#2e9a60', '#00843D', '#007034', '#005c2b', '#004922']
const precaucion: MantineColorsTuple = ['#fffbeb', '#fff7d1', '#fff0ad', '#ffe985', '#ffe25c', '#ffd92e', '#FFD100', '#d9b200', '#b29200', '#7A5C00']
const peligro: MantineColorsTuple = ['#fbecee', '#f5d4d9', '#edb3bc', '#e58c9b', '#dc6679', '#d23b54', '#C8102E', '#aa0e27', '#8c0b20', '#6e0919']
const roca: MantineColorsTuple = ['#f2f3f4', '#e1e3e5', '#cbced1', '#b0b5ba', '#969ca3', '#79818a', '#5B6570', '#4d565f', '#40474e', '#32383e']
// Los grises de la marca, del hueso a la tinta: lo que Mantine usa en oscuro para texto, bordes y fondos.
const tinta: MantineColorsTuple = ['#eef2e9', '#c3cbbd', '#9ca696', '#6f7869', '#3d4439', '#252a23', '#171b16', '#101310', '#0a0c0a', '#060706']

export const tema = createTheme({
  primaryColor: 'accion',
  primaryShade: 6,
  // Un solo radio para tarjetas, botones y campos: las pantallas de Diego y las de Dani se ven iguales.
  defaultRadius: 'md',
  colors: { accion, verificado, precaucion, peligro, roca, dark: tinta },
  black: '#1F262E',
  white: '#FFFFFF',
  autoContrast: true, // texto grafito sobre el amarillo, blanco sobre los demás
})

/** Fondo de la app: Polvo en claro, tinta en oscuro. */
export const FONDO = 'var(--factum-fondo)'

/**
 * Lo que cambia entre claro y oscuro. Las vistas del supervisor se proyectan, y van en oscuro como
 * las láminas y el monitor; las del operario siguen claras, que es lo que se lee en terreno.
 *
 * En oscuro los colores de seguridad no cambian (el tono 6 de cada uno). Cambian solo sus extremos:
 * el fondo teñido (tono 0) pasa a ser oscuro y los textos de color (tonos 7 a 9), claros. Así
 * ninguna pantalla tiene que saber en qué esquema está.
 *
 * Mantine usa esos mismos tonos por dentro en oscuro: el 0 para el texto de sus variantes claras
 * (insignias, botones sutiles) y el 7 para el botón relleno bajo el cursor. Por eso esos dos se
 * fijan aparte, con el color que tendrían sin el cambio.
 */
export const variablesDelTema: CSSVariablesResolver = () => ({
  variables: {},
  light: { '--factum-fondo': '#EDF0F2', '--factum-linea': 'transparent' },
  dark: {
    '--factum-fondo': '#0a0c0a',
    '--factum-linea': '#252a23',
    '--mantine-color-roca-6': '#9ca696',
    '--mantine-color-roca-7': '#b4bcae',
    '--mantine-color-roca-filled': roca[6],
    '--mantine-color-roca-filled-hover': roca[5],
    '--mantine-color-accion-0': '#0e1b2a',
    '--mantine-color-accion-7': '#8fb9e3',
    '--mantine-color-accion-8': '#a9c9ea',
    '--mantine-color-accion-filled-hover': accion[5],
    '--mantine-color-accion-light-color': accion[1],
    '--mantine-color-verificado-0': '#0b2014',
    '--mantine-color-verificado-7': '#6cc594',
    '--mantine-color-verificado-8': '#8dd3ac',
    '--mantine-color-verificado-filled-hover': verificado[5],
    '--mantine-color-verificado-light-color': verificado[1],
    '--mantine-color-precaucion-0': '#2a2300',
    '--mantine-color-precaucion-7': '#ffd92e',
    '--mantine-color-precaucion-8': '#ffe25c',
    '--mantine-color-precaucion-9': '#ffe985',
    '--mantine-color-precaucion-filled-hover': precaucion[5],
    '--mantine-color-precaucion-light-color': precaucion[1],
    '--mantine-color-peligro-0': '#2c0d13',
    '--mantine-color-peligro-7': '#f08f9d',
    '--mantine-color-peligro-8': '#f4a9b4',
    '--mantine-color-peligro-filled-hover': peligro[5],
    '--mantine-color-peligro-light-color': peligro[1],
  },
})

/**
 * La marca (project-logo.png): la cruz lima y «Factum» en matriz de puntos, sobre tinta.
 * Vive solo en la banda de arriba y en el login. Nunca dice un estado: eso es de los colores de seguridad.
 */
export const MARCA = {
  tinta: '#0a0c0a',
  lima: '#d4ff9e',
  hueso: '#eef2e9',
  /** Texto secundario sobre tinta. */
  tenue: '#9ca696',
} as const

/**
 * Donde vive la marca: fondo tinta y texto hueso. El foco del teclado va en lima, porque el
 * azul de acción no se ve sobre tinta.
 */
export const SOBRE_TINTA = {
  background: MARCA.tinta,
  color: MARCA.hueso,
  '--mantine-primary-color-filled': MARCA.lima,
} as CSSProperties

/** La letra de la marca, la misma del monitor: solo para frases grandes sobre tinta. */
export const TITULAR = "'Bitcount Prop Single Variable', ui-monospace, Menlo, monospace"
