import {
  Badge,
  Button,
  createTheme,
  defaultVariantColorsResolver,
  parseThemeColor,
  rem,
  SegmentedControl,
  type CSSVariablesResolver,
  type MantineColorsTuple,
  type VariantColorsResolver,
} from '@mantine/core'
import type { CSSProperties } from 'react'

// Los colores, las letras y las formas de Factum. Ver knowledge/architecture/FRONTEND.md §4.
// Nadie escribe un hex fuera de este archivo.

// En claro (el operario, en terreno): colores de seguridad industrial, ISO 3864 y ANSI Z535.
const accion: MantineColorsTuple = ['#ebf1f7', '#d1dfec', '#adc6de', '#85a9cd', '#5c8cbc', '#2e6caa', '#004C97', '#004180', '#00356a', '#002a53']
const verificado: MantineColorsTuple = ['#ebf5ef', '#d1e9dc', '#add8c1', '#85c4a2', '#5cb083', '#2e9a60', '#00843D', '#007034', '#005c2b', '#004922']
const precaucion: MantineColorsTuple = ['#fffbeb', '#fff7d1', '#fff0ad', '#ffe985', '#ffe25c', '#ffd92e', '#FFD100', '#d9b200', '#b29200', '#7A5C00']
const peligro: MantineColorsTuple = ['#fbecee', '#f5d4d9', '#edb3bc', '#e58c9b', '#dc6679', '#d23b54', '#C8102E', '#aa0e27', '#8c0b20', '#6e0919']
const roca: MantineColorsTuple = ['#f2f3f4', '#e1e3e5', '#cbced1', '#b0b5ba', '#969ca3', '#79818a', '#5B6570', '#4d565f', '#40474e', '#32383e']
// Lo que las OT ya ejecutadas dicen de la pauta: las propuestas de mejora tienen su propio color.
const mejora: MantineColorsTuple = ['#f3f0ff', '#e5dbff', '#d0bfff', '#b197fc', '#9775fa', '#845ef7', '#6741d9', '#5f3dc4', '#5235ab', '#432c8c']
// Los grises de la marca, del hueso a la tinta: lo que Mantine usa en oscuro para texto, bordes y fondos.
const tinta: MantineColorsTuple = ['#eef2e9', '#c3cbbd', '#9ca696', '#6f7869', '#3d4439', '#252a23', '#171b16', '#101310', '#0a0c0a', '#060706']

/**
 * La marca (project-logo.png): la cruz lima y «Factum» en matriz de puntos, sobre tinta.
 * En oscuro el lima dice además «verificado»: es el único estado que comparte color con la marca.
 */
export const MARCA = {
  tinta: '#0a0c0a',
  lima: '#d4ff9e',
  hueso: '#eef2e9',
  /** Texto secundario sobre tinta. */
  tenue: '#9ca696',
} as const

/** La letra de la marca, la del monitor: títulos y valores grandes. */
export const TITULAR = "'Bitcount Prop Single Variable', ui-monospace, Menlo, monospace"
/** Rótulos, botones e insignias: monoespaciada, como en una lámina técnica. */
export const MONO = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"

/** Fondo de la app: Polvo en claro, tinta en oscuro. */
export const FONDO = 'var(--factum-fondo)'

/**
 * Donde vive la marca: fondo tinta y texto hueso. El foco del teclado va en lima, porque el
 * color de acción no se ve igual sobre tinta.
 */
export const SOBRE_TINTA = {
  background: MARCA.tinta,
  color: MARCA.hueso,
  '--mantine-primary-color-filled': MARCA.lima,
} as CSSProperties

/**
 * Los colores que dicen algo. Cada uno tiene cinco usos, y sus valores cambian con el esquema:
 * el color (relleno), bajo el cursor, el texto que va encima, un fondo teñido y el texto de color.
 *
 * - En claro, para el operario: los colores de seguridad ISO sobre blanco.
 * - En oscuro, para el supervisor y el login: la paleta del monitor. Lima para lo verificado,
 *   ámbar para el aviso y rojo para el peligro, más dos colores con la misma claridad que el
 *   lima: hielo para lo que se puede tocar y lo que está en curso, y lila para las mejoras.
 */
type Usos = { color: string; cursor: string; sobre: string; tenue: string; texto: string }
const CLARO: Record<string, Usos> = {
  accion: { color: accion[6], cursor: accion[7], sobre: '#FFFFFF', tenue: accion[0], texto: accion[7] },
  verificado: { color: verificado[6], cursor: verificado[7], sobre: '#FFFFFF', tenue: verificado[0], texto: verificado[7] },
  precaucion: { color: precaucion[6], cursor: precaucion[7], sobre: '#1F262E', tenue: precaucion[0], texto: precaucion[9] },
  peligro: { color: peligro[6], cursor: peligro[7], sobre: '#FFFFFF', tenue: peligro[0], texto: peligro[7] },
  roca: { color: roca[6], cursor: roca[7], sobre: '#FFFFFF', tenue: roca[0], texto: roca[7] },
  mejora: { color: mejora[6], cursor: mejora[7], sobre: '#FFFFFF', tenue: mejora[0], texto: mejora[7] },
}
const OSCURO: Record<string, Usos> = {
  accion: { color: '#9fe3ff', cursor: '#c4eeff', sobre: MARCA.tinta, tenue: '#0e1f28', texto: '#9fe3ff' },
  verificado: { color: MARCA.lima, cursor: '#e6ffc4', sobre: MARCA.tinta, tenue: '#17230c', texto: MARCA.lima },
  precaucion: { color: '#ffc24d', cursor: '#ffd27a', sobre: MARCA.tinta, tenue: '#2a1e06', texto: '#ffc24d' },
  peligro: { color: '#ff4433', cursor: '#ff6b5e', sobre: '#1a0402', tenue: '#2c0d0a', texto: '#ff7a6e' },
  roca: { color: '#3d4439', cursor: '#4a5245', sobre: MARCA.hueso, tenue: '#171b16', texto: MARCA.tenue },
  mejora: { color: '#c8b6ff', cursor: '#dccfff', sobre: MARCA.tinta, tenue: '#1b1730', texto: '#c8b6ff' },
}

const variablesDe = (usos: Record<string, Usos>) =>
  Object.fromEntries(
    Object.entries(usos).flatMap(([nombre, u]) => [
      [`--f-${nombre}`, u.color],
      [`--f-${nombre}-cursor`, u.cursor],
      [`--f-${nombre}-sobre`, u.sobre],
      [`--f-${nombre}-tenue`, u.tenue],
      [`--f-${nombre}-texto`, u.texto],
    ]),
  )

/**
 * En oscuro, los tonos de Mantine que las pantallas ya usan (`peligro.6`, `precaucion.0`,
 * `c="verificado.7"`) siguen a los usos de arriba: el 6 es el color, el 0 el fondo teñido y del 7
 * al 9 el texto. Así ninguna pantalla tiene que saber en qué esquema está.
 */
const tonosEnOscuro = Object.fromEntries(
  Object.keys(OSCURO)
    .filter((nombre) => nombre !== 'roca')
    .flatMap((nombre) => [
      [`--mantine-color-${nombre}-0`, `var(--f-${nombre}-tenue)`],
      [`--mantine-color-${nombre}-6`, `var(--f-${nombre})`],
      [`--mantine-color-${nombre}-7`, `var(--f-${nombre}-texto)`],
      [`--mantine-color-${nombre}-8`, `var(--f-${nombre}-texto)`],
      [`--mantine-color-${nombre}-9`, `var(--f-${nombre}-texto)`],
      [`--mantine-color-${nombre}-filled`, `var(--f-${nombre})`],
      [`--mantine-color-${nombre}-filled-hover`, `var(--f-${nombre}-cursor)`],
      [`--mantine-color-${nombre}-light`, `var(--f-${nombre}-tenue)`],
      [`--mantine-color-${nombre}-light-color`, `var(--f-${nombre}-texto)`],
      [`--mantine-color-${nombre}-text`, `var(--f-${nombre}-texto)`],
      [`--mantine-color-${nombre}-outline`, `var(--f-${nombre})`],
    ]),
)

export const variablesDelTema: CSSVariablesResolver = () => ({
  variables: { '--f-titular': TITULAR, '--f-mono': MONO },
  light: {
    '--factum-fondo': '#EDF0F2',
    '--f-vacio': '#1F262E',
    '--f-caja': '#FFFFFF',
    '--f-panel': '#FFFFFF',
    '--f-alto': roca[0],
    '--f-linea': roca[1],
    '--f-linea-2': roca[3],
    '--f-tenue': roca[6],
    '--f-trama': 'transparent',
    ...variablesDe(CLARO),
  },
  dark: {
    '--factum-fondo': MARCA.tinta,
    // El fondo del video sin imagen, un punto más negro que la tinta, y el color de una caja segura.
    '--f-vacio': '#050605',
    '--f-caja': MARCA.hueso,
    '--f-panel': '#101310',
    '--f-alto': '#171b16',
    '--f-linea': '#252a23',
    '--f-linea-2': '#3d4439',
    '--f-tenue': MARCA.tenue,
    '--f-trama': '#141813',
    ...variablesDe(OSCURO),
    ...tonosEnOscuro,
    // El texto secundario: el gris de roca no se lee sobre tinta.
    '--mantine-color-roca-6': MARCA.tenue,
    '--mantine-color-roca-7': '#b4bcae',
    '--mantine-color-roca-filled': 'var(--f-roca)',
    '--mantine-color-anchor': 'var(--f-accion-texto)',
  },
})

const CON_USOS = new Set(Object.keys(CLARO))

/**
 * Botones, insignias e íconos toman sus colores de los usos de arriba, no de un tono fijo: así el
 * texto sobre un relleno claro (lima, hielo) sale oscuro, y sobre uno oscuro (el azul ISO), claro.
 */
const variantes: VariantColorsResolver = (input) => {
  const porOmision = defaultVariantColorsResolver(input)
  const c = parseThemeColor({ color: input.color || input.theme.primaryColor, theme: input.theme })
  if (!c.isThemeColor || c.shade !== undefined || !CON_USOS.has(c.color)) return porOmision
  const v = (uso = '') => `var(--f-${c.color}${uso})`
  const sinBorde = `${rem(1)} solid transparent`
  switch (input.variant) {
    case 'filled':
      return { background: v(), hover: v('-cursor'), color: v('-sobre'), border: sinBorde }
    case 'light':
      return { background: v('-tenue'), hover: v('-tenue'), color: v('-texto'), border: sinBorde }
    case 'outline':
      return { background: 'transparent', hover: v('-tenue'), color: v('-texto'), border: `${rem(1)} solid ${v()}` }
    case 'subtle':
      return { background: 'transparent', hover: v('-tenue'), color: v('-texto'), border: sinBorde }
    default:
      return porOmision
  }
}

const ROTULO = { fontFamily: MONO, textTransform: 'uppercase', fontWeight: 500 } as const

export const tema = createTheme({
  primaryColor: 'accion',
  primaryShade: 6,
  // Esquinas casi rectas, como una lámina técnica: ningún radio pasa de unos pocos píxeles.
  radius: { xs: rem(1), sm: rem(2), md: rem(3), lg: rem(4), xl: rem(6) },
  defaultRadius: 'md',
  fontFamilyMonospace: MONO,
  colors: { accion, verificado, precaucion, peligro, roca, mejora, dark: tinta },
  black: '#1F262E',
  white: '#FFFFFF',
  autoContrast: true,
  variantColorResolver: variantes,
  components: {
    Button: Button.extend({ styles: { root: { ...ROTULO, letterSpacing: '0.06em' } } }),
    Badge: Badge.extend({ styles: { root: { ...ROTULO, letterSpacing: '0.09em' } } }),
    SegmentedControl: SegmentedControl.extend({ styles: { label: { ...ROTULO, letterSpacing: '0.06em', fontSize: rem(13) } } }),
  },
})
