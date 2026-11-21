import { Button, Container, Group, Paper, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import { IconAlertTriangle, IconCheck, IconHandFinger, IconUserCheck } from '@tabler/icons-react'
import type { EstadoOt, Evento } from '../api/tipos'
import { nombreDe } from '../sesion/usuarios'
import { cerradoPor } from './estado'

const COMO: Record<string, string> = { '1': 'por sensor', '2': 'por la cámara', '3': 'por la cámara' }

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' })

type Props = {
  ot: EstadoOt
  bitacora: Evento[]
  alertas: Evento[]
  relevo: { resumen: string; entregado_por: string; ts: string }
  onRecibido(): void
}

/** Lo que lee el que llega antes de seguir: qué está cerrado y cómo, qué warns hereda y desde dónde sigue. */
export function Briefing({ ot, bitacora, alertas, relevo, onRecibido }: Props) {
  const cerrados = ot.pasos.filter((p) => p.estado === 'verificado')
  const enConflicto = ot.pasos.filter((p) => p.estado === 'en_conflicto')
  const sigue = ot.pasos.find((p) => p.id === ot.paso_actual)

  return (
    <Container size={560} px="md" py="lg">
      <Stack gap="md">
        <Stack gap={2}>
          <Title order={2}>Relevo de turno</Title>
          <Text c="roca.6">
            Entregado por {nombreDe(relevo.entregado_por)} a las {hora(relevo.ts)}
          </Text>
        </Stack>

        <Paper withBorder p="md" bg="white">
          <Text>{relevo.resumen}</Text>
        </Paper>

        <Stack gap={6}>
          {cerrados.map((p) => {
            const porPersona = p.evidencia?.tipo === 'persona'
            const actor = porPersona ? cerradoPor(bitacora, p.id) : null
            return (
              <Group key={p.id} gap="sm" wrap="nowrap" align="flex-start">
                <ThemeIcon color="verificado" radius="xl" size="md" style={porPersona ? { outline: '3px solid var(--mantine-color-precaucion-6)' } : undefined}>
                  {porPersona ? <IconUserCheck size={16} /> : <IconCheck size={16} />}
                </ThemeIcon>
                <Stack gap={0}>
                  <Text size="sm" fw={600}>
                    {p.orden}. {p.titulo}
                  </Text>
                  <Text size="xs" fw={porPersona ? 600 : 400} c={porPersona ? 'precaucion.9' : 'roca.6'}>
                    {porPersona ? `confirmado por ${actor ? nombreDe(actor) : 'una persona'}` : COMO[String(p.capa)] ?? 'por una persona'}
                  </Text>
                </Stack>
              </Group>
            )
          })}
        </Stack>

        {(enConflicto.length > 0 || alertas.length > 0) && (
          <Paper p="md" bg="precaucion.6">
            <Stack gap={6}>
              <Group gap={6}>
                <IconAlertTriangle size={20} />
                <Text fw={800}>Avisos que heredas</Text>
              </Group>
              {enConflicto.map((p) => (
                <Text key={p.id} size="sm">
                  {p.orden}. {p.titulo}: {p.detalle}
                </Text>
              ))}
              {alertas.map((a) => (
                <Text key={a.id} size="sm" fw={700}>
                  {a.detalle}
                </Text>
              ))}
            </Stack>
          </Paper>
        )}

        {sigue && (
          <Group gap="sm" wrap="nowrap">
            <ThemeIcon color="accion" radius="xl" size="lg">
              <IconHandFinger size={20} />
            </ThemeIcon>
            <Text fw={800} size="lg">
              Sigue en: {sigue.orden}. {sigue.titulo}
            </Text>
          </Group>
        )}

        <Button size="xl" h={72} fullWidth onClick={onRecibido}>
          Recibido
        </Button>
      </Stack>
    </Container>
  )
}
