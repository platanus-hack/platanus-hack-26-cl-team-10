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

  it('what the camera sees goes by the name the crew uses, in any text of the server', () => {
    expect(enPalabras('el modelo del edge ya no ve red soda can en 5 cuadros seguidos, y ve green soda can en su lugar')).toBe(
      'el modelo del edge ya no ve polín rojo en 5 cuadros seguidos, y ve polín verde en su lugar',
    )
    expect(enPalabras('el modelo del edge ve soda can en 5 cuadros seguidos (mín. 91%)')).toBe('el modelo del edge ve polín en 5 cuadros seguidos (mín. 91%)')
    // Lo que el detector no llama polín queda igual.
    expect(enPalabras('el modelo del edge ve mouse en 5 cuadros seguidos')).toBe('el modelo del edge ve mouse en 5 cuadros seguidos')
  })
})

describe('fraseCorta', () => {
  it('keeps the first sentence, in plain case', () => {
    expect(fraseCorta('PERSONA JUNTO A LA MÁQUINA CON EL MOTOR ENCENDIDO. Alejarse; cortar la corriente.')).toBe('Persona junto a la máquina con el motor encendido')
    expect(fraseCorta('dist_cm = 148.9, lejos de su mediana 102.3 (22.8 desvíos)')).toBe('Distancia 148.9 cm fuera de lo normal: lo habitual es 102.3 cm')
  })
})
