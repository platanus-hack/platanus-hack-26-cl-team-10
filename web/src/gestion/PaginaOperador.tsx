import { Button, Card, Group, Progress, Stack, Text, Title } from '@mantine/core'
import { IconPlayerPlay } from '@tabler/icons-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { desbloquearAudio } from '../ejecucion/voz'
import { useSesion } from '../sesion/sesion'
import { ESTADOS } from './estados'
import { EstadoBadge, Encabezado, EstadoLista, FranjaDesactualizada, Pagina } from './ui'
import { LIMITE_MS, RECARGA_MS, useOts, type OtVista } from './useOts'

const ORDEN_OPERADOR = ['en_ejecucion', 'asignada', 'completa'] as const
/** Si el navegador nunca resuelve play(), se entra igual: la ejecución pide el toque que falte. */
const ESPERA_AUDIO_MS = 1500

function TarjetaOt({
  ot,
  abriendo,
  bloqueada,
  onAbrir,
}: {
  ot: OtVista
  abriendo: boolean
  bloqueada: boolean
  onAbrir: () => void
}) {
  const a = ot.avance
  return (
    <Card withBorder radius="md" padding="lg">
      <Stack gap="sm">
        <Group justify="space-between" wrap="nowrap">
          <Text fw={800} size="lg">
            {ot.ot.toUpperCase()}
          </Text>
          <EstadoBadge estado={ot.estado} />
        </Group>
        <Stack gap={2}>
          <Text fw={700}>{a?.nombre ?? ot.pauta}</Text>
          <Text size="sm" c="roca.6">
            Equipo {ot.equipo}
          </Text>
        </Stack>
        {a && (
          <Stack gap={4}>
            <Group justify="space-between">
              <Text size="sm" c="roca.7">
                {ot.estado === 'completa' ? 'Pasos cerrados' : a.pasoActual ? `Sigue en: ${a.pasoActual}` : 'Avance'}
              </Text>
              <Text size="sm" fw={700}>
                {a.cerrados}/{a.total}
              </Text>
            </Group>
            <Progress
              value={a.total ? (a.cerrados / a.total) * 100 : 0}
              color={ESTADOS[ot.estado].color}
              aria-label={`Avance ${a.cerrados} de ${a.total}`}
            />
          </Stack>
        )}
        {ot.estado === 'completa' ? (
          <Button component={Link} to={`/ot/${encodeURIComponent(ot.ot)}`} variant="default" size="lg" fullWidth>
            Ver resumen
          </Button>
        ) : (
          <Button size="lg" fullWidth leftSection={<IconPlayerPlay size={20} />} loading={abriendo} disabled={bloqueada} onClick={onAbrir}>
            {ot.estado === 'en_ejecucion' ? 'Continuar' : 'Comenzar'}
          </Button>
        )}
      </Stack>
    </Card>
  )
}

/** Solo las OT del operador. Es un filtro del front, no un control de acceso (PRD §8). */
export function PaginaOperador() {
  const usuario = useSesion()
  const navigate = useNavigate()
  // Sus OT abiertas se leen una por una para mostrar en qué paso siguen.
  const { ots, error, recargar } = useOts(RECARGA_MS, LIMITE_MS, usuario?.id ?? null)
  const [abriendo, setAbriendo] = useState<string | null>(null)
  if (!usuario) return null

  const mias = (ots ?? [])
    .filter((o) => o.operador === usuario.id)
    .flatMap((o) => {
      const i = ORDEN_OPERADOR.indexOf(o.estado as (typeof ORDEN_OPERADOR)[number])
      return i < 0 ? [] : [{ o, i }]
    })
    .sort((a, b) => a.i - b.i || a.o.ot.localeCompare(b.o.ot))
    .map(({ o }) => o)

  // El toque desbloquea el audio del celular (Dani, ejecucion/voz.ts): así la ejecución
  // abre la sesión sin pedir otro toque.
  const abrir = async (otId: string) => {
    if (abriendo) return
    setAbriendo(otId)
    await Promise.race([desbloquearAudio(), new Promise<void>((listo) => setTimeout(listo, ESPERA_AUDIO_MS))])
    navigate(`/ot/${encodeURIComponent(otId)}`)
  }

  return (
    <>
      <Encabezado usuario={usuario} seccion="Mis OT" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="md" maw={560} mx="auto">
          <Title order={2}>Mis órdenes de trabajo</Title>
          <EstadoLista
            cargando={ots === null}
            error={error}
            vacia={mias.length === 0}
            textoVacia="No tienes OT asignadas. Cuando el supervisor te asigne una, aparece acá."
            onReintentar={() => void recargar()}
          />
          {mias.map((o) => (
            <TarjetaOt
              key={o.ot}
              ot={o}
              abriendo={abriendo === o.ot}
              bloqueada={abriendo !== null && abriendo !== o.ot}
              onAbrir={() => void abrir(o.ot)}
            />
          ))}
        </Stack>
      </Pagina>
    </>
  )
}
