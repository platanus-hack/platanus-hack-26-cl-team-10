import { Alert, Box, Button, Group, Stack, Text } from '@mantine/core'
import { IconWifiOff } from '@tabler/icons-react'

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
