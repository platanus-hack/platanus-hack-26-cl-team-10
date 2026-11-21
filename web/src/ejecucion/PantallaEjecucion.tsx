import { Badge, Box, Button, Container, Divider, Group, Paper, Progress, Stack, Text } from '@mantine/core'
import { IconVolume, IconVolumeOff } from '@tabler/icons-react'
import { useEffect, useState, type ReactNode } from 'react'
import type { Nivel } from '../api/tipos'
import { nombreDe, type Usuario } from '../sesion/usuarios'
import { FranjaSinConexion, MensajeError } from './Avisos'
import { BannerAlertas } from './BannerAlertas'
import { BarraOt } from './BarraOt'
import { avance, avisoDelPaso, cerradoPor, estadoUi } from './estado'
import { Paso } from './Paso'
import type { Ejecutor } from './useEjecucion'

const NIVEL: Record<Nivel, { color: string; texto: string }> = {
  ok: { color: 'verificado', texto: 'En orden' },
  warning: { color: 'precaucion', texto: 'Precaución' },
  error: { color: 'peligro', texto: 'Peligro' },
}

function useReloj(desde: number | null): string | null {
  const [ahora, setAhora] = useState(() => Date.now())
  useEffect(() => {
    if (desde === null) return
    const i = setInterval(() => setAhora(Date.now()), 1000)
    return () => clearInterval(i)
  }, [desde])
  if (desde === null) return null
  const seg = Math.max(0, Math.floor((ahora - desde) / 1000))
  return `${String(Math.floor(seg / 60)).padStart(2, '0')}:${String(seg % 60).padStart(2, '0')}`
}

function Cabecera({ otId, e }: { otId: string; e: Ejecutor }) {
  const ot = e.s.ot!
  const { hechos, total } = avance(ot)
  const nivel = NIVEL[e.s.calificacion?.nivel ?? 'ok']
  const reloj = useReloj(e.sesionDesde)

  return (
    <Paper radius={0} bg="white" px="md" py="sm" style={{ borderBottom: '1px solid var(--mantine-color-roca-2)' }}>
      <Stack gap={8} maw={560} mx="auto">
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Stack gap={2} style={{ minWidth: 0 }}>
            <Group gap="xs">
              <Text fw={900} size="xl">
                {otId.toUpperCase()}
              </Text>
              <Badge color={nivel.color} size="lg">
                {nivel.texto}
              </Badge>
            </Group>
            <Text size="sm" fw={600}>
              {ot.pauta}
            </Text>
            <Text size="sm" c="roca.6">
              Equipo {ot.equipo}
            </Text>
          </Stack>
          <Stack gap={0} align="flex-end">
            <Text fw={900} size="1.75rem" lh={1}>
              {hechos}/{total}
            </Text>
            {reloj && (
              <Text size="sm" c="roca.6" ff="monospace">
                {reloj}
              </Text>
            )}
          </Stack>
        </Group>
        <Progress value={total ? (hechos / total) * 100 : 0} color={ot.completa ? 'verificado' : 'accion'} aria-label={`Avance ${hechos} de ${total}`} />
        <Group gap="xs">
          {e.audio === 'activo' ? <IconVolume size={18} /> : <IconVolumeOff size={18} color="var(--mantine-color-peligro-6)" />}
          <Text size="sm" fw={600} c={e.audio === 'activo' ? undefined : 'peligro.7'}>
            {e.audio === 'activo' ? 'Audio activo' : 'Audio bloqueado'}
          </Text>
          <Button size="compact-sm" variant="subtle" onClick={e.probarAudio}>
            Probar audio
          </Button>
        </Group>
      </Stack>
    </Paper>
  )
}

/**
 * La OT en ejecución. Los pasos se cierran solos con su evidencia; el operario solo actúa donde
 * la API lo necesita: «Hecho» en un paso que se cierra declarando, y «Ya lo hice» cuando la API
 * avisa un paso saltado, un conflicto o una evidencia que no llega.
 */
export function PantallaEjecucion({ otId, usuario, e, pie }: { otId: string; usuario: Usuario; e: Ejecutor; pie?: ReactNode }) {
  const { s, pauta } = e
  const ot = s.ot!
  const habilitado = s.conexion === 'en_vivo' && !s.pendiente
  const quienCerro = (pasoId: string) => {
    const actor = cerradoPor(s.bitacora, pasoId)
    return actor ? nombreDe(actor) : null
  }

  return (
    <Box pb="xl">
      <BarraOt usuario={usuario} />
      <Cabecera otId={otId} e={e} />
      {s.conexion === 'reconectando' && <FranjaSinConexion />}
      <Container size={560} px="md" pt="md">
        <Stack gap="sm">
          <BannerAlertas alertas={s.alertas} ot={ot} />
          {s.mensaje && <MensajeError mensaje={s.mensaje} onVisto={e.verMensaje} />}
          {ot.pasos.map((p) => (
            <Paso
              key={p.id}
              paso={p}
              pauta={pauta?.pasos.find((x) => x.id === p.id)}
              ui={estadoUi(p, s)}
              aviso={avisoDelPaso(p, s)}
              cerradoPor={quienCerro(p.id)}
              habilitado={habilitado}
              vistas={p.id === ot.paso_actual ? e.vistas : undefined}
              onHecho={() => void e.hecho(p.id)}
              onConfirmar={(motivo) => void e.confirmar(p.id, motivo)}
            />
          ))}
          {pie && (
            <>
              <Divider my="xs" />
              {pie}
            </>
          )}
        </Stack>
      </Container>
    </Box>
  )
}
