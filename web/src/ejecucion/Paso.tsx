import { Group, Loader, Paper, Stack, Text, ThemeIcon, type MantineColor } from '@mantine/core'
import { IconAntennaBarsOff, IconCheck, IconCircleDashed, IconHandFinger, IconX } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import type { PasoEstado, PasoPauta } from '../api/tipos'
import type { EstadoUi } from './estado'
import { YaLoHice } from './YaLoHice'

type Props = {
  paso: PasoEstado
  pauta: PasoPauta | undefined
  ui: EstadoUi
  cerradoPor: string | null
  onYaLoHice(nota?: string): void
}

// Colores de FRONTEND.md §4: cada color significa una sola cosa.
function colorDe(ui: EstadoUi, capa: number | null): MantineColor {
  switch (ui) {
    case 'verificado':
    case 'sobrescrito':
      return 'verificado'
    case 'warn':
      return capa === 1 ? 'peligro' : 'precaucion'
    case 'sin_senal':
      return 'precaucion'
    case 'en_curso':
    case 'comprobando':
      return 'accion'
    case 'pendiente':
      return 'roca'
  }
}

const ICONO: Record<EstadoUi, ReactNode> = {
  verificado: <IconCheck size={20} />,
  sobrescrito: <IconCheck size={20} />,
  warn: <IconX size={20} />,
  sin_senal: <IconAntennaBarsOff size={20} />,
  en_curso: <IconHandFinger size={20} />,
  comprobando: <Loader size={16} color="white" />,
  pendiente: <IconCircleDashed size={20} />,
}

export function Paso({ paso, pauta, ui, cerradoPor, onYaLoHice }: Props) {
  const color = colorDe(ui, paso.capa)
  const activo = ui !== 'pendiente' && ui !== 'verificado'
  // Sobrescrito: cerrado, pero cuenta como warn → borde de precaución.
  const borde = ui === 'sobrescrito' ? 'precaucion' : color

  return (
    <Paper
      withBorder
      radius="sm"
      p="sm"
      bg="white"
      style={{ borderLeft: `6px solid var(--mantine-color-${borde}-6)`, opacity: ui === 'pendiente' ? 0.7 : 1 }}
    >
      <Group align="flex-start" wrap="nowrap" gap="sm">
        <ThemeIcon color={color} variant={ui === 'pendiente' ? 'light' : 'filled'} size="lg" radius="xl">
          {ICONO[ui]}
        </ThemeIcon>
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text fw={activo ? 700 : 500} size="md" c={ui === 'pendiente' ? 'roca.6' : undefined}>
            {paso.orden}. {paso.titulo}
          </Text>
          {ui === 'en_curso' && pauta && <Text size="sm">{pauta.instruccion}</Text>}
          {ui === 'comprobando' && <Text size="sm" c="accion.6">Comprobando…</Text>}
          {ui === 'sobrescrito' && cerradoPor && (
            <Text size="sm" c="precaucion.9">
              a la palabra de {cerradoPor}
            </Text>
          )}
          {ui === 'warn' && paso.detalle && (
            <Text size="sm" fw={600} c={paso.capa === 1 ? 'peligro.7' : 'precaucion.9'}>
              {paso.detalle}
            </Text>
          )}
          {ui === 'sin_senal' && (
            <Text size="sm" fw={600} c="precaucion.9">
              No llega la señal del sensor
            </Text>
          )}
          {(ui === 'warn' || ui === 'sin_senal') && <YaLoHice color={color} onConfirmar={onYaLoHice} />}
        </Stack>
      </Group>
    </Paper>
  )
}
