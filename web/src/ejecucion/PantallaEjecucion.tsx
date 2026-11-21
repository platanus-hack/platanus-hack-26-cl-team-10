import { Badge, Box, Button, Container, Group, Paper, Stack, Text } from '@mantine/core'
import { IconVolume, IconVolumeOff } from '@tabler/icons-react'
import { useEffect, useState, type ReactNode } from 'react'
import type { Nivel } from '../api/tipos'
import { nombreDe } from '../sesion/usuarios'
import { FranjaSinConexion, MensajeError } from './Avisos'
import { BannerAlertas } from './BannerAlertas'
import { avance, cerradoPor, estadoUi } from './estado'
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
      <Container size={560} p={0}>
        <Group justify="space-between" align="flex-start" wrap="nowrap">
          <Stack gap={2} style={{ minWidth: 0 }}>
            <Group gap="xs">
              <Text fw={900} size="xl">
                {otId.toUpperCase()}
              </Text>
              <Badge color={nivel.color} size="lg" radius="sm">
                {nivel.texto}
              </Badge>
            </Group>
            <Text size="sm" fw={600}>
              {ot.pauta}
            </Text>
            <Text size="sm" c="roca.6">
              {ot.equipo}
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
        <Group gap="xs" mt={6}>
          {e.audio === 'activo' ? <IconVolume size={18} /> : <IconVolumeOff size={18} color="var(--mantine-color-peligro-6)" />}
          <Text size="sm" fw={600} c={e.audio === 'activo' ? undefined : 'peligro.7'}>
            {e.audio === 'activo' ? 'Audio activo' : 'Audio bloqueado'}
          </Text>
          <Button size="compact-sm" variant="subtle" onClick={e.probarAudio}>
            Probar audio
          </Button>
        </Group>
      </Container>
    </Paper>
  )
}

export function PantallaEjecucion({ otId, e, pie }: { otId: string; e: Ejecutor; pie?: ReactNode }) {
  const { s, pauta } = e
  const ot = s.ot!
  const quienCerro = (pasoId: string) => {
    const actor = cerradoPor(s.bitacora, pasoId)
    return actor ? nombreDe(actor) : null
  }
  const puedeDeclarar = !!ot.paso_actual && !s.pendiente && s.conexion === 'en_vivo'

  return (
    <Box pb={170}>
      <Cabecera otId={otId} e={e} />
      {s.conexion === 'reconectando' && <FranjaSinConexion />}
      <Container size={560} px="md" pt="md">
        <Stack gap="sm">
          <BannerAlertas alertas={s.alertas} onYaLoHice={e.yaLoHiceAlerta} />
          {s.mensaje && <MensajeError mensaje={s.mensaje} onVisto={e.verMensaje} />}
          {ot.pasos.map((p) => (
            <Paso
              key={p.id}
              paso={p}
              pauta={pauta?.pasos.find((x) => x.id === p.id)}
              ui={estadoUi(p, s)}
              cerradoPor={quienCerro(p.id)}
              onYaLoHice={(nota) => void e.yaLoHice(p.id, nota)}
            />
          ))}
        </Stack>
      </Container>
      <Box
        pos="fixed"
        bottom={0}
        left={0}
        right={0}
        bg="white"
        style={{ borderTop: '1px solid var(--mantine-color-roca-2)', paddingBottom: 'env(safe-area-inset-bottom)', zIndex: 10 }}
      >
        <Container size={560} px="md" py="sm">
          <Stack gap="xs">
            <Button size="xl" h={64} fullWidth disabled={!puedeDeclarar} loading={!!s.pendiente} onClick={() => void e.hecho()}>
              Hecho
            </Button>
            {pie}
          </Stack>
        </Container>
      </Box>
    </Box>
  )
}
