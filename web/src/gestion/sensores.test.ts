import { describe, expect, it } from 'vitest'
import { enPalabras, fraseCorta } from './sensores'

describe('enPalabras', () => {
  it('turns the old statistical anomaly text into plain words, with the sensor name and unit', () => {
    expect(enPalabras('dist_cm = 148.9, lejos de su mediana 102.3 (22.8 desvíos)')).toBe('Distancia 148.9 cm fuera de lo normal: lo habitual es 102.3 cm')
    expect(enPalabras('temp_c = 22, lejos de su mediana 24.8 (5.6 desvíos)')).toBe('Temperatura 22 °C fuera de lo normal: lo habitual es 24.8 °C')
  })

  it('leaves any other text as it is', () => {
    expect(enPalabras('GUARDA ABIERTA CON ENERGÍA VIVA.')).toBe('GUARDA ABIERTA CON ENERGÍA VIVA.')
  })
})

describe('fraseCorta', () => {
  it('keeps the first sentence, in plain case', () => {
    expect(fraseCorta('PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO. Alejarse; cortar la corriente.')).toBe('Persona junto a la máquina con el motor encendido')
    expect(fraseCorta('dist_cm = 148.9, lejos de su mediana 102.3 (22.8 desvíos)')).toBe('Distancia 148.9 cm fuera de lo normal: lo habitual es 102.3 cm')
  })
})
