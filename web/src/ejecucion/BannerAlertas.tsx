import { Box, Group, Paper, Stack, Text } from '@mantine/core'
import { IconAlertTriangle } from '@tabler/icons-react'
import type { Evento } from '../api/tipos'
import { YaLoHice } from './YaLoHice'

/**
 * Las alertas activas. Una de nivel error se ve como una tarjeta de bloqueo (LOTO):
 * franja roja con «Peligro» en blanco y el cuerpo blanco. Una de nivel warning, en amarillo.
 */
export function BannerAlertas({ alertas, onYaLoHice }: { alertas: Evento[]; onYaLoHice(alertaId: number, nota?: string): void }) {
  if (alertas.length === 0) return null
  return (
    <Stack gap="sm" role="alert">
      {alertas.map((a) =>
        a.calificacion?.nivel === 'error' ? (
          <Paper key={a.id} withBorder radius="sm" bg="white" style={{ overflow: 'hidden', borderColor: 'var(--mantine-color-peligro-6)', borderWidth: 3 }}>
            <Box bg="peligro.6" px="md" py={8}>
              <Group gap={8}>
                <IconAlertTriangle size={26} color="white" />
                <Text c="white" fw={900} size="xl">
                  Peligro
                </Text>
              </Group>
            </Box>
            <Stack p="md" gap="sm">
              <Text fw={700} size="lg">
                {a.detalle}
              </Text>
              <YaLoHice color="peligro" onConfirmar={(nota) => onYaLoHice(a.id, nota)} />
            </Stack>
          </Paper>
        ) : (
          <Paper key={a.id} radius="sm" bg="precaucion.6" p="md">
            <Stack gap="sm">
              <Group gap={8} wrap="nowrap">
                <IconAlertTriangle size={22} />
                <Text fw={700}>{a.detalle}</Text>
              </Group>
              <YaLoHice color="dark" onConfirmar={(nota) => onYaLoHice(a.id, nota)} />
            </Stack>
          </Paper>
        ),
      )}
    </Stack>
  )
}
