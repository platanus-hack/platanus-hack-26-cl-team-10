import { Button, Group, Stack, Textarea, type MantineColor } from '@mantine/core'
import { useState } from 'react'

/** «Ya lo hice»: el operario dice que sí lo hizo (un falso positivo). Nota opcional, sin diálogos del navegador. */
export function YaLoHice({ onConfirmar, color = 'roca' }: { onConfirmar(nota?: string): void; color?: MantineColor }) {
  const [abierto, setAbierto] = useState(false)
  const [nota, setNota] = useState('')
  const cerrar = () => {
    setAbierto(false)
    setNota('')
  }

  if (!abierto)
    return (
      <Button variant="outline" color={color} size="md" onClick={() => setAbierto(true)}>
        Ya lo hice
      </Button>
    )

  return (
    <Stack gap="xs">
      <Textarea placeholder="Nota (opcional)" value={nota} onChange={(e) => setNota(e.currentTarget.value)} rows={2} />
      <Group grow>
        <Button
          size="md"
          color={color}
          onClick={() => {
            onConfirmar(nota.trim() || undefined)
            cerrar()
          }}
        >
          Confirmar
        </Button>
        <Button size="md" variant="default" onClick={cerrar}>
          Cancelar
        </Button>
      </Group>
    </Stack>
  )
}
