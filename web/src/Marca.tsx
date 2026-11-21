import { MARCA } from './tema'

// «Factum» en matriz de puntos, calcado de project-logo.png: cada # es un punto.
const LETRAS = [
  ['####', '#...', '#...', '###.', '#...', '#...'],
  ['.....', '.###.', '....#', '.####', '#...#', '.##.#'],
  ['.....', '.####', '#....', '#....', '#...#', '.###.'],
  ['.#..', '####', '.#..', '.#..', '.#..', '..##'],
  ['.....', '#...#', '#...#', '#...#', '#..##', '.##.#'],
  ['.........', '#.##..##.', '##..##..#', '#...#...#', '#...#...#', '#...#...#'],
]

// Las medidas del arte, en sus píxeles (1000 × 1000).
const CRUZ = 97 // alto y ancho de la cruz, que es también el alto de la marca
const TRAZO = 10
const PASO = 15.8 // de un punto al siguiente
const RADIO = 7.7
const PRIMER_PUNTO = { x: 171, y: 8 }
const ENTRE_LETRAS = 35 // del último punto de una letra al primero de la siguiente

const n = (v: number) => Math.round(v * 10) / 10
const punto = (cx: number, cy: number) =>
  `M${n(cx - RADIO)} ${n(cy)}a${RADIO} ${RADIO} 0 1 0 ${2 * RADIO} 0a${RADIO} ${RADIO} 0 1 0 ${-2 * RADIO} 0`

function trazar() {
  let d = ''
  let x = PRIMER_PUNTO.x
  for (const letra of LETRAS) {
    letra.forEach((fila, j) =>
      [...fila].forEach((c, i) => {
        if (c === '#') d += punto(x + i * PASO, PRIMER_PUNTO.y + j * PASO)
      }),
    )
    x += (letra[0].length - 1) * PASO + ENTRE_LETRAS
  }
  return { puntos: d, ancho: n(x - ENTRE_LETRAS + RADIO) }
}

const { puntos: PUNTOS, ancho: ANCHO } = trazar()
const CRUZ_D = `M${CRUZ / 2} 0V${CRUZ}M0 ${CRUZ / 2}H${CRUZ}`

/**
 * La marca: la cruz y «Factum», siempre juntas y sobre tinta. La cruz sola en una barra se lee
 * como un botón de «agregar».
 */
export function Marca({ alto = 20 }: { alto?: number }) {
  return (
    <svg
      role="img"
      aria-label="Factum"
      viewBox={`0 0 ${ANCHO} ${CRUZ}`}
      width={n((alto * ANCHO) / CRUZ)}
      height={alto}
      style={{ display: 'block', flexShrink: 0 }}
    >
      <path d={CRUZ_D} stroke={MARCA.lima} strokeWidth={TRAZO} fill="none" />
      <path d={PUNTOS} fill={MARCA.hueso} />
    </svg>
  )
}
