import { describe, expect, it } from 'vitest'
import { enPalabras } from './sensores'

describe('enPalabras', () => {
  it('turns the old statistical anomaly text into plain words, with the sensor name and unit', () => {
    expect(enPalabras('dist_cm = 148.9, lejos de su mediana 102.3 (22.8 desvíos)')).toBe('Distancia 148.9 cm fuera de lo normal: lo habitual es 102.3 cm')
    expect(enPalabras('temp_c = 22, lejos de su mediana 24.8 (5.6 desvíos)')).toBe('Temperatura 22 °C fuera de lo normal: lo habitual es 24.8 °C')
  })

  it('leaves any other text as it is', () => {
    expect(enPalabras('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBe('GUARDA ABIERTA CON ENERGÍA VIVA.')
  })
})
