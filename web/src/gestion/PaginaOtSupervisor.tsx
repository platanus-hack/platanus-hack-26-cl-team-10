import { Badge, Box, Button, Center, Group, Loader, Paper, ScrollArea, SimpleGrid, Stack, Table, Text, ThemeIcon, Title } from '@mantine/core'
import {
  IconAlertTriangle,
  IconArrowLeft,
  IconCheck,
  IconCircleDashed,
  IconHandStop,
  IconPointFilled,
  IconVideoOff,
  IconX,
} from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router'
import type { EstadoOt, Evento, Pauta, PasoEstado } from '../api/tipos'
import { config } from '../config'
import { queDice, tituloDe } from '../ejecucion/alertas'
import { FranjaSinConexion } from '../ejecucion/Avisos'
import { cerradoPor, type Conexion } from '../ejecucion/estado'
import { useSesion } from '../sesion/sesion'
import { nombreDe, type Usuario } from '../sesion/usuarios'
import { estadoDe } from './estados'
import { Encabezado, EstadoBadge, Pagina, VerificacionBadge } from './ui'
import { useOtEnVivo } from './useOtEnVivo'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })

/** /supervisor/ot/:id — una OT en vivo para el supervisor: cámara, sensores, pasos y bitácora. Solo mira. */
export function PaginaOtSupervisor() {
  const { id = '' } = useParams()
  const usuario = useSesion()
  if (!usuario) return null
  return <VistaOt key={id} otId={id} usuario={usuario} />
}

function EnVivo({ conexion }: { conexion: Conexion }) {
  const vivo = conexion === 'en_vivo'
  return (
    <Group gap={4} wrap="nowrap" aria-label={vivo ? 'Conectado en vivo' : 'Conectando'}>
      <IconPointFilled size={18} color={`var(--mantine-color-${vivo ? 'verificado' : 'precaucion'}-6)`} />
      <Text size="sm" fw={700} c={vivo ? 'verificado.7' : 'precaucion.8'}>
        {vivo ? 'En vivo' : 'Conectando…'}
      </Text>
    </Group>
  )
}

/** Las alertas abiertas, arriba y en rojo. «Ver en la bitácora» lleva a su evento. */
function Incidentes({ alertas, ot, onVer }: { alertas: Evento[]; ot: EstadoOt | null; onVer(id: number): void }) {
  if (alertas.length === 0) return null
  return (
    <Stack gap="sm" role="alert" aria-label="Alertas abiertas">
      {alertas.map((a) => {
        const { texto, ayuda } = queDice(a, ot)
        return (
          <Paper key={a.id} radius="md" p="md" bg="peligro.6" c="white">
            <Group justify="space-between" wrap="nowrap" align="flex-start" gap="md">
              <Group gap="sm" wrap="nowrap" align="flex-start">
                <IconAlertTriangle size={28} style={{ flexShrink: 0 }} />
                <Stack gap={2}>
                  <Text fw={900} size="lg">
                    {tituloDe(a)}, desde las {hora(a.ts)}
                  </Text>
                  <Text fw={600}>{texto}</Text>
                  {ayuda && <Text size="sm">{ayuda}</Text>}
                </Stack>
              </Group>
              <Button variant="white" color="peligro" onClick={() => onVer(a.id)} style={{ flexShrink: 0 }}>
                Ver en la bitácora
              </Button>
            </Group>
          </Paper>
        )
      })}
    </Stack>
  )
}

/** El video que la estación manda al servidor (`/edge/{id}/video.mjpg`), si la OT corre en una. */
function Camara({ edgeId, vistas }: { edgeId: string | null; vistas: { clase: string; conf: number }[] }) {
  const [fallo, setFallo] = useState(false)
  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Group justify="space-between">
          <Title order={3} size="h4">
            Cámara de la estación
          </Title>
          {edgeId && (
            <Badge color="peligro" variant="filled" leftSection={<IconPointFilled size={12} />}>
              {edgeId}
            </Badge>
          )}
        </Group>
        <Box pos="relative" bg="dark.7" style={{ aspectRatio: '4 / 3', borderRadius: 'var(--mantine-radius-sm)', overflow: 'hidden' }}>
          <Center pos="absolute" inset={0} p="md">
            <Stack align="center" gap={4}>
              <IconVideoOff size={32} color="var(--mantine-color-gray-5)" />
              <Text c="gray.4" ta="center" size="sm">
                {!edgeId
                  ? 'Esta OT no está corriendo en una estación ahora. No hay video en vivo.'
                  : fallo
                    ? `No llega el video de ${edgeId}.`
                    : `Esperando el video de ${edgeId}…`}
              </Text>
            </Stack>
          </Center>
          {edgeId && !fallo && (
            <img
              src={`${config.API_URL}/edge/${encodeURIComponent(edgeId)}/video.mjpg`}
              alt={`Video en vivo de ${edgeId}`}
              onError={() => setFallo(true)}
              style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'contain' }}
            />
          )}
        </Box>
        {edgeId && (
          <Text size="sm" c="roca.7">
            {vistas.length ? `La cámara ve: ${vistas.map((v) => `${v.clase} (${Math.round(v.conf * 100)}%)`).join(', ')}` : 'La cámara no reconoce nada ahora.'}
          </Text>
        )}
      </Stack>
    </Paper>
  )
}

const NOMBRE_SENSOR: Record<string, string> = {
  energia: 'Energía',
  guarda: 'Guarda',
  bloqueo: 'Bloqueo',
  reed_bloqueo: 'Candado',
  operario: 'Persona junto a la máquina',
  equipo: 'Equipo',
  temp_c: 'Temperatura (°C)',
  hum_pct: 'Humedad (%)',
  dist_cm: 'Distancia (cm)',
  tierra: 'Puesta a tierra',
  tension: 'Tensión',
  seccionador: 'Seccionador',
  zona: 'Zona',
  implementos: 'Implementos',
}

/** Las lecturas de la estación. El sensor que espera el paso en curso va marcado. */
function Sensores({ sensores, ot, pauta }: { sensores: Record<string, string>; ot: EstadoOt | null; pauta: Pauta | null }) {
  const actual = pauta?.pasos.find((p) => p.id === ot?.paso_actual)
  const espera = actual?.sensor ?? null
  const filas = Object.entries(sensores).sort(([a], [b]) => Number(b === espera?.id) - Number(a === espera?.id) || a.localeCompare(b))
  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Title order={3} size="h4">
          Sensores
        </Title>
        {filas.length === 0 ? (
          <Text c="roca.6" size="sm">
            Todavía no llega ninguna lectura de la estación.
          </Text>
        ) : (
          <Table verticalSpacing={6} aria-label="Lecturas de la estación">
            <Table.Tbody>
              {filas.map(([id, valor]) => {
                const esperado = espera?.id === id
                const calza = esperado && espera.espera === valor
                return (
                  <Table.Tr key={id} bg={esperado ? (calza ? 'verificado.0' : 'precaucion.0') : undefined}>
                    <Table.Td>
                      <Text size="sm" fw={600}>
                        {NOMBRE_SENSOR[id] ?? id}
                      </Text>
                      {esperado && (
                        <Text size="xs" c="roca.7">
                          El paso {actual!.orden} espera «{espera.espera}»
                        </Text>
                      )}
                    </Table.Td>
                    <Table.Td ta="right">
                      <Group gap={4} justify="flex-end" wrap="nowrap">
                        {esperado && (calza ? <IconCheck size={16} color="var(--mantine-color-verificado-7)" /> : <IconX size={16} color="var(--mantine-color-precaucion-8)" />)}
                        <Text fw={800}>{valor}</Text>
                      </Group>
                    </Table.Td>
                  </Table.Tr>
                )
              })}
            </Table.Tbody>
          </Table>
        )}
      </Stack>
    </Paper>
  )
}

function IconoPaso({ paso, actual }: { paso: PasoEstado; actual: boolean }) {
  if (paso.estado === 'verificado')
    return (
      <ThemeIcon size={26} radius="xl" color="verificado">
        <IconCheck size={16} />
      </ThemeIcon>
    )
  if (paso.estado === 'en_conflicto')
    return (
      <ThemeIcon size={26} radius="xl" color="peligro">
        <IconHandStop size={16} />
      </ThemeIcon>
    )
  return (
    <ThemeIcon size={26} radius="xl" color={actual ? 'accion' : 'gray'} variant={actual ? 'filled' : 'light'}>
      <IconCircleDashed size={16} />
    </ThemeIcon>
  )
}

function Pasos({ ot, bitacora }: { ot: EstadoOt; bitacora: Evento[] }) {
  const cerrados = ot.pasos.filter((p) => p.estado === 'verificado').length
  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Group justify="space-between">
          <Title order={3} size="h4">
            Pasos
          </Title>
          <Text fw={800}>
            {cerrados}/{ot.pasos.length}
          </Text>
        </Group>
        <Stack gap={6}>
          {ot.pasos.map((p) => {
            const actual = p.id === ot.paso_actual
            const por = p.estado === 'verificado' ? cerradoPor(bitacora, p.id) : null
            return (
              <Group key={p.id} gap="sm" wrap="nowrap" align="flex-start" p={4} bg={actual ? 'accion.0' : undefined} style={{ borderRadius: 'var(--mantine-radius-sm)' }}>
                <IconoPaso paso={p} actual={actual} />
                <Stack gap={0}>
                  <Text size="sm" fw={actual ? 800 : 600} c={p.estado === 'no_verificado' && !actual ? 'roca.6' : undefined}>
                    {p.orden}. {p.titulo}
                  </Text>
                  {actual && (
                    <Text size="xs" c="accion.7" fw={700}>
                      En curso
                    </Text>
                  )}
                  {por && (
                    <Text size="xs" c="roca.7">
                      Confirmado por {nombreDe(por)}
                    </Text>
                  )}
                </Stack>
              </Group>
            )
          })}
        </Stack>
      </Stack>
    </Paper>
  )
}

/** Cómo se llama cada evento de la bitácora para el supervisor. */
function etiquetaDe(ev: Evento): string {
  switch (ev.tipo) {
    case 'ot_abierta':
      return 'OT abierta'
    case 'ot_asignada':
      return 'OT asignada'
    case 'paso_iniciado':
      return 'Paso iniciado'
    case 'declaracion':
      return 'Declaración'
    case 'veredicto':
      if (ev.evidencia?.tipo === 'persona') return 'Confirmado por una persona'
      return ev.estado === 'verificado' ? 'Paso verificado' : ev.estado === 'en_conflicto' ? 'Conflicto' : 'Sin verificar'
    case 'alerta':
      return tituloDe(ev)
    case 'alerta_resuelta':
      return 'Alerta resuelta'
    case 'relevo_entregado':
      return 'Turno entregado'
    case 'relevo_recibido':
      return 'Turno recibido'
    case 'propuesta_pauta':
      return 'Propuesta de pauta'
  }
}

function colorDe(ev: Evento): string {
  if (ev.tipo === 'alerta_resuelta') return 'verificado'
  if (ev.calificacion?.nivel === 'error' || ev.tipo === 'alerta') return 'peligro'
  if (ev.calificacion?.nivel === 'warning') return 'precaucion'
  return 'roca'
}

/** Todo lo que pasó en la OT, lo último arriba. Una alerta abierta se marca; la elegida, más. */
function Bitacora({ bitacora, ot, abiertas, elegido }: { bitacora: Evento[]; ot: EstadoOt | null; abiertas: Set<number>; elegido: number | null }) {
  const eventos = [...bitacora].sort((a, b) => b.id - a.id)
  const orden = (pasoId: string | null) => ot?.pasos.find((p) => p.id === pasoId)?.orden
  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Group justify="space-between">
          <Title order={3} size="h4">
            Bitácora
          </Title>
          <Text size="sm" c="roca.6">
            {eventos.length} eventos
          </Text>
        </Group>
        <ScrollArea.Autosize mah={560} type="auto" offsetScrollbars>
          <Stack gap={6} component="ol" style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Bitácora de la OT">
            {eventos.map((ev) => {
              const color = colorDe(ev)
              const abierta = abiertas.has(ev.id)
              const n = orden(ev.paso_id)
              return (
                <Box
                  key={ev.id}
                  component="li"
                  id={`bitacora-${ev.id}`}
                  p="xs"
                  bg={elegido === ev.id ? 'peligro.1' : abierta ? 'peligro.0' : undefined}
                  style={{
                    borderLeft: `4px solid var(--mantine-color-${color}-6)`,
                    borderRadius: 'var(--mantine-radius-sm)',
                    outline: elegido === ev.id ? '2px solid var(--mantine-color-peligro-6)' : undefined,
                  }}
                >
                  <Group gap="xs" wrap="nowrap" justify="space-between">
                    <Text size="sm" fw={800} c={color === 'roca' ? undefined : `${color}.8`}>
                      {etiquetaDe(ev)}
                      {n ? `, paso ${n}` : ''}
                      {abierta ? ' (abierta)' : ''}
                    </Text>
                    <Text size="xs" c="roca.6" style={{ fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>
                      {hora(ev.ts)}
                    </Text>
                  </Group>
                  <Text size="sm">{ev.detalle}</Text>
                  <Text size="xs" c="roca.6">
                    {ev.actor === 'sistema' ? 'Sistema' : nombreDe(ev.actor)}
                  </Text>
                </Box>
              )
            })}
          </Stack>
        </ScrollArea.Autosize>
      </Stack>
    </Paper>
  )
}

function VistaOt({ otId, usuario }: { otId: string; usuario: Usuario }) {
  const v = useOtEnVivo(otId)
  const { s } = v
  const [elegido, setElegido] = useState<number | null>(null)

  useEffect(() => {
    if (elegido === null) return
    document.getElementById(`bitacora-${elegido}`)?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  }, [elegido])

  const volver = (
    <Button component={Link} to="/supervisor" variant="subtle" color="dark" px={0} w="fit-content" leftSection={<IconArrowLeft size={18} />}>
      Supervisión
    </Button>
  )

  if (v.acceso === 'denegado' || s.conexion === 'no_existe') {
    return (
      <>
        <Encabezado usuario={usuario} seccion="Supervisión" />
        <Pagina>
          <Stack gap="md" align="flex-start">
            {volver}
            <Title order={2}>Esta OT no está en tu empresa</Title>
            <Text c="roca.6">No existe o es de otra empresa. Revisa el enlace o vuelve a la lista.</Text>
          </Stack>
        </Pagina>
      </>
    )
  }

  const ot = s.ot
  const calificacion = s.calificacion ?? v.detalle?.calificacion ?? null
  const nombre = v.pauta ? `${v.pauta.nombre} v${v.pauta.version}` : (ot?.pauta ?? '')
  const enEstacion = v.sesion && v.sesion.ot_id === otId ? v.sesion.edge_id : null
  const abiertas = new Set(s.alertas.map((a) => a.id))

  return (
    <>
      <Encabezado usuario={usuario} seccion="Supervisión" />
      {s.conexion === 'reconectando' && <FranjaSinConexion />}
      <Pagina>
        <Stack gap="lg">
          <Stack gap="xs">
            {volver}
            <Group justify="space-between" align="flex-start">
              <Stack gap={4}>
                <Group gap="sm">
                  <Title order={2}>{otId.toUpperCase()}</Title>
                  {v.detalle && <EstadoBadge estado={estadoDe(v.detalle)} />}
                  {calificacion && <VerificacionBadge nivel={calificacion.nivel} />}
                </Group>
                <Text fw={600}>{nombre}</Text>
                <Text size="sm" c="roca.6">
                  {ot ? `Equipo ${ot.equipo}` : ''}
                  {v.detalle?.operador ? `. Operador: ${nombreDe(v.detalle.operador)}` : v.detalle ? '. Sin operador' : ''}
                </Text>
              </Stack>
              <EnVivo conexion={s.conexion} />
            </Group>
          </Stack>

          <Incidentes alertas={s.alertas} ot={ot} onVer={setElegido} />

          {!ot ? (
            <Center py="xl">
              <Stack align="center" gap="xs">
                <Loader />
                <Text c="roca.6">Conectando con la OT…</Text>
              </Stack>
            </Center>
          ) : (
            <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" style={{ alignItems: 'start' }}>
              <Stack gap="lg">
                <Camara edgeId={enEstacion} vistas={v.vistas} />
                {enEstacion && <Sensores sensores={v.sensores} ot={ot} pauta={v.pauta} />}
              </Stack>
              <Stack gap="lg">
                <Pasos ot={ot} bitacora={s.bitacora} />
                <Bitacora bitacora={s.bitacora} ot={ot} abiertas={abiertas} elegido={elegido} />
              </Stack>
            </SimpleGrid>
          )}
        </Stack>
      </Pagina>
    </>
  )
}
