import { apagar, MARCA, SATURACION } from './tema'

const canales = (hex: string) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16))
/** Qué tan lejos está un color del gris: la distancia entre su canal más alto y el más bajo. */
const color = (hex: string) => Math.max(...canales(hex)) - Math.min(...canales(hex))

it('at 1 a color stays as it is, and at 0 it turns grey', () => {
  for (const hex of ['#d4ff9e', '#9fe3ff', '#c8b6ff', '#ffc24d', '#ff4433']) {
    expect(apagar(hex, 1)).toBe(hex)
    expect(color(apagar(hex, 0))).toBeLessThanOrEqual(1)
  }
})

it('less saturation means less color, and a grey has none to lose', () => {
  expect(color(apagar('#9fe3ff', 0.5))).toBeLessThan(color('#9fe3ff'))
  expect(color(apagar('#9fe3ff', 0.25))).toBeLessThan(color(apagar('#9fe3ff', 0.5)))
  expect(apagar('#808080', 0.5)).toBe('#808080')
})

it('the lima of the brand follows the saturation of the dark views', () => {
  expect(MARCA.lima).toBe(apagar('#d4ff9e', SATURACION))
})
