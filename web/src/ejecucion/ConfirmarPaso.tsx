import { Button, Group, Stack, Text, Textarea, type MantineColor } from '@mantine/core'
import { useState } from 'react'

/** Motivos de un toque: con guantes, escribir cuesta. */
const MOTIVOS_RAPIDOS = ['El sensor no lo marca', 'La cámara no lo ve', 'Lo revisé en persona']

/**
 * «Ya lo hice»: la persona confirma el paso aunque la evidencia no lo muestre
 * (POST /ot/{id}/pasos/{paso}/confirmar). La API exige un motivo y lo deja a su nombre.
 */
export function ConfirmarPaso({
  onConfirmar,
  color = 'roca',
  habilitado = true,
}: {
  onConfirmar(motivo: string): void
  color?: MantineColor
  habilitado?: boolean
}) {
  const [abierto, setAbierto] = useState(false)
  const [motivo, setMotivo] = useState('')
  const cerrar = () => {
    setAbierto(false)
    setMotivo('')
  }

  if (!abierto)
    return (
      <Button variant="outline" color={color} size="md" disabled={!habilitado} onClick={() => setAbierto(true)}>
        Ya lo hice
      </Button>
    )

  return (
    <Stack gap="xs">
      <Text size="sm" fw={600}>
        ¿Por qué no se marca? Queda registrado a tu nombre.
      </Text>
      <Group gap={6}>
        {MOTIVOS_RAPIDOS.map((m) => (
          <Button key={m} size="compact-sm" variant={motivo === m ? 'filled' : 'light'} color="roca" onClick={() => setMotivo(m)}>
            {m}
          </Button>
        ))}
      </Group>
      <Textarea label="Motivo" placeholder="O escríbelo con tus palabras" value={motivo} onChange={(e) => setMotivo(e.currentTarget.value)} rows={2} />
      <Group grow>
        <Button
          size="md"
          color={color}
          disabled={!motivo.trim() || !habilitado}
          onClick={() => {
            onConfirmar(motivo.trim())
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
