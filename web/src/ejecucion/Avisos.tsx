import { Alert, Box, Button, Group, Stack, Text } from '@mantine/core'
import { IconWifiOff } from '@tabler/icons-react'
import { useState } from 'react'
import type { Sesion } from '../api/tipos'
import { nombreDe } from '../sesion/usuarios'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })

/** La franja amarilla mientras el WebSocket se reconecta. */
export function FranjaSinConexion() {
  return (
    <Box bg="precaucion.6" px="md" py={8}>
      <Group gap="xs" justify="center">
        <IconWifiOff size={18} />
        <Text fw={700}>Sin conexión, reintentando</Text>
      </Group>
    </Box>
  )
}

/** Por qué no se pudo lo que el operario pidió (un 409 trae la regla tal cual). */
export function MensajeError({ mensaje, onVisto }: { mensaje: string; onVisto(): void }) {
  return (
    <Alert color="precaucion" variant="light" title="No se pudo">
      <Stack gap="xs" align="flex-start">
        <Text size="sm">{mensaje}</Text>
        <Button size="xs" variant="default" onClick={onVisto}>
          Entendido
        </Button>
      </Stack>
    </Alert>
  )
}

/**
 * La estación ejecuta otra OT. Esta OT parte sola si la estación queda libre; tomarla es un toque
 * de la persona, porque la otra OT deja de recibir sus sensores.
 */
export function EstacionOcupada({ sesion, onTomar }: { sesion: Sesion; onTomar(): Promise<void> }) {
  const [tomando, setTomando] = useState(false)
  const tomar = async () => {
    setTomando(true)
    try {
      await onTomar()
    } finally {
      setTomando(false)
    }
  }
  return (
    <Alert color="precaucion" variant="light" title="La estación está ocupada">
      <Stack gap="xs" align="flex-start">
        <Text size="sm">
          Ejecuta la OT {sesion.ot_id.toUpperCase()} con {nombreDe(sesion.operario)}, desde las {hora(sesion.desde)}. Esta OT
          parte sola apenas quede libre.
        </Text>
        <Text size="sm">Si la tomas, esa OT deja de recibir sus sensores.</Text>
        <Button size="sm" color="precaucion" loading={tomando} onClick={() => void tomar()}>
          Tomar la estación
        </Button>
      </Stack>
    </Alert>
  )
}
