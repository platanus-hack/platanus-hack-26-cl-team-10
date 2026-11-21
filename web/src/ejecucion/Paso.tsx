import { Button, Group, Loader, Paper, Stack, Text, ThemeIcon, type MantineColor } from '@mantine/core'
import { IconAlertTriangle, IconAntennaBarsOff, IconCheck, IconCircleDashed, IconHandFinger, IconUserCheck } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { cierraSolo, pideHecho, sePuedeConfirmar } from '../api/pauta'
import type { Deteccion, PasoEstado, PasoPauta } from '../api/tipos'
import { ConfirmarPaso } from './ConfirmarPaso'
import type { EstadoUi } from './estado'

type Props = {
  paso: PasoEstado
  pauta: PasoPauta | undefined
  ui: EstadoUi
  /** Por qué el paso está en warn: el salto o el detalle del veredicto. */
  aviso: string | null
  /** Quién lo confirmó contra la evidencia, ya con su nombre corto. */
  cerradoPor: string | null
  /** Sin conexión, nada que escriba en la API. */
  habilitado: boolean
  /** Lo que ve la cámara del edge ahora, para el paso de cámara en curso. */
  vistas?: Deteccion[]
  onHecho(): void
  onConfirmar(motivo: string): void
}

const COMO_SE_CERRO: Record<string, string> = { '1': 'por sensor', '2': 'por la cámara', '3': 'por la cámara' }

// Colores de FRONTEND.md §4: cada color significa una sola cosa.
function colorDe(ui: EstadoUi, paso: PasoEstado): MantineColor {
  switch (ui) {
    case 'verificado':
    case 'confirmado':
      return 'verificado'
    case 'warn':
      // Un salto o un conflicto de capa 1 es peligro; el de la cámara, precaución.
      return paso.estado === 'en_conflicto' && paso.capa !== 1 ? 'precaucion' : 'peligro'
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
  confirmado: <IconUserCheck size={20} />,
  warn: <IconAlertTriangle size={20} />,
  sin_senal: <IconAntennaBarsOff size={20} />,
  en_curso: <IconHandFinger size={20} />,
  comprobando: <Loader size={16} color="white" />,
  pendiente: <IconCircleDashed size={20} />,
}

function comoSeCierra(p: PasoPauta): string {
  if (p.tipo_evidencia === 'sensor') return 'Se cierra solo cuando el sensor lo marque.'
  if (cierraSolo(p)) return 'Se cierra solo cuando la cámara lo vea.'
  if (p.tipo_evidencia === 'camara') return 'Al tocar «Hecho», la cámara lo revisa.'
  return 'Cuando lo termines, toca «Hecho».'
}

export function Paso({ paso, pauta, ui, aviso, cerradoPor, habilitado, vistas = [], onHecho, onConfirmar }: Props) {
  const color = colorDe(ui, paso)
  const activo = ui !== 'pendiente' && ui !== 'verificado' && ui !== 'confirmado'
  // Confirmado por una persona: cerrado, pero cuenta como warn → borde de precaución.
  const borde = ui === 'confirmado' ? 'precaucion' : color
  const conHecho = !!pauta && pideHecho(pauta)
  const confirmable = !pauta || sePuedeConfirmar(pauta)
  const motivo = typeof paso.evidencia?.motivo === 'string' ? paso.evidencia.motivo : null
  const camaraEnVivo = ui === 'en_curso' && !!pauta?.deteccion && vistas.length > 0

  const hecho = (
    <Button size="lg" color="accion" disabled={!habilitado} onClick={onHecho}>
      Hecho
    </Button>
  )

  return (
    <Paper
      withBorder
      p="sm"
      bg="white"
      style={{ borderLeft: `6px solid var(--mantine-color-${borde}-6)`, opacity: ui === 'pendiente' ? 0.7 : 1 }}
    >
      <Group align="flex-start" wrap="nowrap" gap="sm">
        <ThemeIcon color={color} variant={ui === 'pendiente' ? 'light' : 'filled'} size="lg" radius="xl">
          {ICONO[ui]}
        </ThemeIcon>
        <Stack gap={6} style={{ flex: 1, minWidth: 0 }}>
          <Text fw={activo ? 700 : 500} size="md" c={ui === 'pendiente' ? 'roca.6' : undefined}>
            {paso.orden}. {paso.titulo}
          </Text>

          {ui === 'en_curso' && pauta && (
            <>
              <Text size="sm">{pauta.instruccion}</Text>
              <Text size="sm" c="roca.7">
                {comoSeCierra(pauta)}
              </Text>
              {camaraEnVivo && (
                <Text size="sm" c="accion.7" fw={600}>
                  La cámara ve: {vistas.map((v) => v.clase).join(', ')}
                </Text>
              )}
              {conHecho && <Group>{hecho}</Group>}
            </>
          )}

          {ui === 'comprobando' && (
            <Text size="sm" c="accion.7" fw={600}>
              Comprobando…
            </Text>
          )}

          {ui === 'warn' && aviso && (
            <Text size="sm" fw={700} c={color === 'peligro' ? 'peligro.7' : 'precaucion.9'}>
              {aviso}
            </Text>
          )}

          {ui === 'sin_senal' && (
            <Stack gap={2}>
              <Text size="sm" fw={700} c="precaucion.9">
                Todavía no se marca.
              </Text>
              {confirmable && (
                <Text size="sm" c="roca.7">
                  Si ya lo hiciste y la evidencia no lo ve, confírmalo con un motivo.
                </Text>
              )}
            </Stack>
          )}

          {(ui === 'warn' || ui === 'sin_senal') && (
            <Group gap="sm" align="flex-start">
              {conHecho && hecho}
              {confirmable && <ConfirmarPaso color={color === 'peligro' ? 'peligro' : 'dark'} habilitado={habilitado} onConfirmar={onConfirmar} />}
            </Group>
          )}

          {ui === 'confirmado' && (
            <Text size="sm" c="precaucion.9" fw={600}>
              {motivo ? `Confirmado por ${cerradoPor ?? 'una persona'}: «${motivo}»` : `Confirmado por ${cerradoPor ?? 'una persona'}`}
            </Text>
          )}

          {ui === 'verificado' && (
            <Text size="xs" c="roca.6">
              {COMO_SE_CERRO[String(paso.capa)] ?? 'por una persona'}
            </Text>
          )}
        </Stack>
      </Group>
    </Paper>
  )
}
