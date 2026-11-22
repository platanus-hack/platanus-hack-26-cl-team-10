import { alpha, Badge, Box, Button, Center, Group, Loader, Paper, ScrollArea, SegmentedControl, SimpleGrid, Stack, Text, ThemeIcon, Title } from '@mantine/core'
import {
  IconAlertTriangle,
  IconArrowLeft,
  IconBulb,
  IconCheck,
  IconCircleDashed,
  IconHandStop,
  IconPointFilled,
  IconUser,
  IconVideoOff,
  IconX,
} from '@tabler/icons-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router'
import { senalesDe } from '../api/mejoras'
import type { Calificacion, CalificacionOt, Deteccion, EstadoOt, Evento, Mejora, Nivel, Pauta, PasoEstado } from '../api/tipos'
import { config } from '../config'
import { queDice, tituloDe } from '../ejecucion/alertas'
import { FranjaSinConexion } from '../ejecucion/Avisos'
import { cerradoPor, type Conexion } from '../ejecucion/estado'
import { useSesion } from '../sesion/sesion'
import { useNombres, type Usuario } from '../sesion/usuarios'
import { estadoDe } from './estados'
import { Reporte } from './Reporte'
import { NOMBRE_CLASE, NOMBRE_SENSOR, UNIDAD } from './sensores'
import { Encabezado, EstadoBadge, Pagina, VerificacionBadge } from './ui'
import { useMejoras } from './useMejoras'
import { useOtEnVivo, type Lectura } from './useOtEnVivo'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
const horaCorta = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hour12: false })

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

const rotuloDe = (v: Deteccion) => `${NOMBRE_CLASE[v.clase] ?? v.clase} ${Math.round(v.conf * 100)} %`
const enPorciento = (x: number) => `${+(x * 100).toFixed(2)}%`
/** Desde esta certeza la cámara está segura; bajo ella, la caja va en amarillo. */
const CERTEZA_SEGURA = 0.8

/** Lo que la cámara reconoce, dibujado sobre el video. Las cajas vienen de 0 a 1 respecto del cuadro. */
function Cajas({ vistas }: { vistas: Deteccion[] }) {
  return (
    <Box pos="absolute" inset={0} aria-hidden style={{ pointerEvents: 'none' }}>
      {vistas.map((v, i) => {
        if (v.caja?.length !== 4) return null
        const [x1, y1, x2, y2] = v.caja
        const seguro = v.conf >= CERTEZA_SEGURA
        const color = seguro ? 'var(--mantine-color-white)' : 'var(--mantine-color-precaucion-6)'
        return (
          <div
            key={i}
            data-seguro={seguro}
            style={{ position: 'absolute', left: enPorciento(x1), top: enPorciento(y1), width: enPorciento(x2 - x1), height: enPorciento(y2 - y1), border: `2px solid ${color}`, boxSizing: 'border-box' }}
          >
            <Text
              span
              size="xs"
              fw={800}
              c="black"
              px={6}
              pos="absolute"
              left={-2}
              // Pegada al borde de arriba del video, la etiqueta va por dentro para que no se corte.
              {...(y1 < 0.08 ? { top: -2 } : { bottom: '100%' })}
              style={{ background: color, whiteSpace: 'nowrap' }}
            >
              {rotuloDe(v)}
            </Text>
          </div>
        )
      })}
    </Box>
  )
}

/** En qué paso va, sobre el video: quien mira la cámara sabe qué debería estar viendo. */
function PasoSobreElVideo({ ot }: { ot: EstadoOt }) {
  const total = ot.pasos.length
  const actual = ot.pasos.find((p) => p.id === ot.paso_actual)
  return (
    <Box pos="absolute" left={0} right={0} bottom={0} px="sm" pb="xs" pt={40} c="white" style={{ background: `linear-gradient(transparent, ${alpha('var(--mantine-color-black)', 0.85)})`, pointerEvents: 'none' }}>
      <Text size="xs" fw={700}>
        {actual ? `Paso ${actual.orden} de ${total}` : 'Pauta completa'}
      </Text>
      <Text fw={800} lh={1.25}>
        {actual ? actual.titulo : `${total} de ${total} pasos verificados`}
      </Text>
    </Box>
  )
}

/**
 * El video que la estación manda al servidor (`/edge/{id}/video.mjpg`), si la OT corre en una.
 * Encima van lo que la cámara reconoce y el paso en curso; el marco toma el color de la verificación.
 */
function Camara({ edgeId, vistas, ot, nivel }: { edgeId: string | null; vistas: Deteccion[]; ot: EstadoOt; nivel: Nivel | null }) {
  const [video, setVideo] = useState<'esperando' | 'viendo' | 'fallo'>('esperando')
  const viendo = video === 'viendo'
  const marco = nivel === 'error' ? 'var(--mantine-color-peligro-6)' : nivel === 'warning' ? 'var(--mantine-color-precaucion-6)' : 'transparent'
  return (
    <Paper component="section" aria-label="Cámara de la estación" withBorder radius="md" p="md">
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
        {/* Sin video el recuadro guarda su lugar en 4:3; con video, el cuadro manda y las cajas calzan justo. */}
        <Box pos="relative" bg="dark.7" style={{ aspectRatio: viendo ? undefined : '4 / 3', border: `4px solid ${marco}`, borderRadius: 'var(--mantine-radius-sm)', overflow: 'hidden' }}>
          {!viendo && (
            <Center pos="absolute" inset={0} p="md">
              <Stack align="center" gap={4}>
                <IconVideoOff size={32} color="var(--mantine-color-gray-5)" />
                <Text c="gray.4" ta="center" size="sm">
                  {!edgeId
                    ? 'Esta OT no está corriendo en una estación ahora. No hay video en vivo.'
                    : video === 'fallo'
                      ? `No llega el video de ${edgeId}.`
                      : `Esperando el video de ${edgeId}…`}
                </Text>
              </Stack>
            </Center>
          )}
          {edgeId && video !== 'fallo' && (
            <img
              src={`${config.API_URL}/edge/${encodeURIComponent(edgeId)}/video.mjpg`}
              alt={`Video en vivo de ${edgeId}`}
              onLoad={() => setVideo('viendo')}
              onError={() => setVideo('fallo')}
              style={{ display: 'block', width: '100%', height: 'auto' }}
            />
          )}
          {edgeId && <Cajas vistas={vistas} />}
          {edgeId && <PasoSobreElVideo ot={ot} />}
        </Box>
        {edgeId && (
          <Text size="sm" c="roca.7">
            {vistas.length ? `La cámara ve: ${vistas.map(rotuloDe).join(', ')}` : 'La cámara no reconoce nada ahora.'}
          </Text>
        )}
      </Stack>
    </Paper>
  )
}

const QUIEN_LO_DICE: Record<number, string> = { 1: 'el sensor', 2: 'la cámara', 3: 'la cámara' }
const certezaDe = (c: Calificacion) => `${Math.round(c.certeza * 100)} % de certeza`

/** Por qué la OT dice «Atención» o «Detente»: cada aviso activo, quién lo dice y con cuánta certeza. */
function Verificacion({ calificacion }: { calificacion: CalificacionOt | null }) {
  return (
    <Paper component="section" aria-label="Verificación" withBorder radius="md" p="md">
      <Stack gap="sm">
        <Group justify="space-between">
          <Title order={3} size="h4">
            Verificación
          </Title>
          {/* Con avisos, cada uno trae su certeza; sin ellos, esta es la de «todo bien». */}
          {calificacion && calificacion.avisos.length === 0 && (
            <Text size="sm" c="roca.7" fw={600}>
              {certezaDe(calificacion)}
            </Text>
          )}
        </Group>
        {!calificacion || calificacion.avisos.length === 0 ? (
          <Text size="sm" c="roca.7">
            Sin avisos activos.
          </Text>
        ) : (
          <Stack gap={6} component="ul" style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Avisos activos">
            {calificacion.avisos.map((a, i) => {
              const color = a.nivel === 'error' ? 'peligro' : 'precaucion'
              const quien = a.capa ? QUIEN_LO_DICE[a.capa] : null
              return (
                <Box key={i} component="li" p="xs" bg={`${color}.0`} style={{ borderLeft: `4px solid var(--mantine-color-${color}-6)`, borderRadius: 'var(--mantine-radius-sm)' }}>
                  <Text size="sm" fw={700}>
                    {a.motivos.join(' · ')}
                  </Text>
                  <Text size="xs" c="roca.7">
                    {quien ? `Lo dice ${quien}, con ${certezaDe(a)}` : `Con ${certezaDe(a)}`}
                  </Text>
                </Box>
              )
            })}
          </Stack>
        )}
      </Stack>
    </Paper>
  )
}


/** Hacia dónde va un sensor numérico: sus últimas lecturas, de la más vieja a la más nueva. */
function Tendencia({ serie, nombre }: { serie: number[]; nombre: string }) {
  const min = Math.min(...serie)
  // Con menos de 2 unidades de diferencia la línea se ve plana: el ruido del sensor no parece un cambio.
  const tramo = Math.max(Math.max(...serie) - min, 2)
  const puntos = serie.map((v, i) => `${((100 * i) / (serie.length - 1)).toFixed(1)},${(28 - (26 * (v - min)) / tramo).toFixed(1)}`).join(' ')
  return (
    <svg viewBox="0 0 100 30" preserveAspectRatio="none" role="img" aria-label={`Últimas lecturas de ${nombre}`} style={{ display: 'block', width: '100%', height: 28 }}>
      <polyline points={puntos} fill="none" stroke="var(--mantine-color-roca-6)" strokeWidth={1.5} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
    </svg>
  )
}

/**
 * Las lecturas de la estación, una ficha por sensor: los de la pauta de esta OT y los que están
 * leyendo ahora (el servidor recuerda sensores de todas las estaciones). El que espera el paso
 * en curso va primero y marcado. Lo que solo trajo el snapshot se ve apagado hasta que llega
 * una lectura nueva.
 */
function Sensores({ sensores, ot, pauta }: { sensores: Record<string, Lectura>; ot: EstadoOt | null; pauta: Pauta | null }) {
  const actual = pauta?.pasos.find((p) => p.id === ot?.paso_actual)
  const espera = actual?.sensor ?? null
  // Sin la pauta no se sabe cuáles son de esta OT: se muestran todos.
  const ids = pauta
    ? [...new Set([...pauta.pasos.flatMap((p) => (p.sensor ? [p.sensor.id] : [])), ...Object.keys(sensores).filter((id) => sensores[id].enVivo)])]
    : Object.keys(sensores)
  const nombreDe = (id: string) => NOMBRE_SENSOR[id] ?? id
  const fichas = ids.sort(
    (a, b) =>
      Number(b === espera?.id) - Number(a === espera?.id) ||
      Number(sensores[b]?.enVivo ?? false) - Number(sensores[a]?.enVivo ?? false) ||
      nombreDe(a).localeCompare(nombreDe(b)),
  )
  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <Title order={3} size="h4">
          Sensores
        </Title>
        {fichas.length === 0 ? (
          <Text c="roca.6" size="sm">
            Todavía no llega ninguna lectura de la estación.
          </Text>
        ) : (
          <SimpleGrid cols={{ base: 2, lg: 3 }} spacing="sm" component="ul" style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Lecturas de la estación">
            {fichas.map((id) => {
              const l = sensores[id]
              const esperado = espera?.id === id
              // Solo cuenta una lectura de ahora: la guardada puede ser de otra OT o de hace horas.
              const calza = esperado && !!l?.enVivo && l.valor === espera.espera
              const color = calza ? 'verificado' : 'precaucion'
              const guardada = l && !l.enVivo
              return (
                <Paper
                  key={id}
                  component="li"
                  withBorder
                  radius="sm"
                  p="sm"
                  bg={esperado ? `${color}.0` : undefined}
                  data-espera={esperado ? (calza ? 'calza' : 'falta') : undefined}
                  style={esperado ? { borderLeft: `4px solid var(--mantine-color-${color}-6)` } : undefined}
                >
                  <Stack gap={2}>
                    <Text size="xs" fw={700} c="roca.7">
                      {nombreDe(id)}
                    </Text>
                    <Group gap={4} wrap="nowrap">
                      {esperado && (calza ? <IconCheck size={18} color="var(--mantine-color-verificado-7)" /> : <IconX size={18} color="var(--mantine-color-precaucion-8)" />)}
                      <Text size="xl" fw={800} lh={1.2} c={!l || guardada ? 'roca.6' : undefined} style={{ fontVariantNumeric: 'tabular-nums' }}>
                        {l ? (UNIDAD[id] ? `${l.valor} ${UNIDAD[id]}` : l.valor) : 'Sin dato'}
                      </Text>
                    </Group>
                    {l && l.serie.length > 1 && <Tendencia serie={l.serie} nombre={nombreDe(id)} />}
                    {esperado && (
                      <Text size="xs" c="roca.7">
                        El paso {actual!.orden} espera «{espera.espera}»
                      </Text>
                    )}
                    {guardada && (
                      <Text size="xs" c="roca.6">
                        Última lectura guardada
                      </Text>
                    )}
                  </Stack>
                </Paper>
              )
            })}
          </SimpleGrid>
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
  // Rojo solo si lo dice el sensor (capa 1); la duda de la cámara es amarilla, como en la lista.
  if (paso.estado === 'en_conflicto')
    return paso.capa === 1 ? (
      <ThemeIcon size={26} radius="xl" color="peligro">
        <IconHandStop size={16} />
      </ThemeIcon>
    ) : (
      <ThemeIcon size={26} radius="xl" color="precaucion">
        <IconAlertTriangle size={16} />
      </ThemeIcon>
    )
  return (
    <ThemeIcon size={26} radius="xl" color={actual ? 'accion' : 'gray'} variant={actual ? 'filled' : 'light'}>
      <IconCircleDashed size={16} />
    </ThemeIcon>
  )
}

function Pasos({ ot, bitacora }: { ot: EstadoOt; bitacora: Evento[] }) {
  const nombreDe = useNombres()
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
    case 'observacion':
      return 'Observación del operario'
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
  const nombreDe = useNombres()
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
                  bg={elegido === ev.id || abierta ? 'peligro.0' : undefined}
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

/**
 * Las propuestas de mejora que esta OT alimenta. Una nace sola cuando esta OT es la segunda en
 * desviarse en el mismo paso: se ve aquí en el momento, sin recargar.
 */
function PropuestasDeMejora({ propuestas, nuevas }: { propuestas: Mejora[]; nuevas: ReadonlySet<string> }) {
  if (propuestas.length === 0) return null
  return (
    <Stack gap="sm" role="status" aria-label="Propuesta de mejora">
      {propuestas.map((p) => (
        <Paper key={p.id} withBorder radius="md" p="md" bg="accion.0" style={{ borderLeft: '6px solid var(--mantine-color-accion-6)' }}>
          <Group justify="space-between" wrap="nowrap" align="flex-start" gap="md">
            <Group gap="sm" wrap="nowrap" align="flex-start">
              <IconBulb size={28} color="var(--mantine-color-accion-7)" style={{ flexShrink: 0 }} />
              <Stack gap={2}>
                <Text fw={900} size="lg">
                  {nuevas.has(p.id) ? 'Nació una propuesta para mejorar la pauta' : 'Esta OT alimenta una propuesta para mejorar la pauta'}
                </Text>
                <Text fw={600}>
                  «{p.titulo}» se desvió en {p.ots_con_senal} de {p.ejecuciones} OT de la versión {p.version}.
                </Text>
                <Text size="sm">{p.sugerencia}</Text>
              </Stack>
            </Group>
            <Button component={Link} to={`/supervisor/mejoras#${encodeURIComponent(p.id)}`} style={{ flexShrink: 0 }}>
              Revisar la propuesta
            </Button>
          </Group>
        </Paper>
      ))}
    </Stack>
  )
}

type Vista = 'vivo' | 'reporte'

function VistaOt({ otId, usuario }: { otId: string; usuario: Usuario }) {
  const nombreDe = useNombres()
  const v = useOtEnVivo(otId)
  const { s } = v
  const [elegido, setElegido] = useState<number | null>(null)
  const [elegida, setElegida] = useState<Vista | null>(null)
  const { mejoras, nuevas, recargar: recargarMejoras } = useMejoras()

  // Cada evento puede hacer nacer una propuesta: se pregunta en el momento, sin esperar la recarga.
  const eventos = s.bitacora.length
  useEffect(() => {
    void Promise.resolve().then(recargarMejoras)
  }, [eventos, recargarMejoras])
  const conSenal = useMemo(() => senalesDe(s.bitacora), [s.bitacora])

  useEffect(() => {
    if (elegido === null) return
    document.getElementById(`bitacora-${elegido}`)?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  }, [elegido])

  const volver = (
    <Button component={Link} to="/supervisor" variant="subtle" px={0} w="fit-content" leftSection={<IconArrowLeft size={18} />}>
      Todas las OT
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
  // Una OT que ya estaba completa al abrirla no tiene nada en vivo: se abre en su reporte.
  const vista: Vista = elegida ?? (v.detalle?.completa ? 'reporte' : 'vivo')
  const propuestas = (mejoras ?? []).filter(
    (p) => p.estado === 'abierta' && p.pauta === v.detalle?.pauta && p.version === v.detalle.version && conSenal.has(p.paso),
  )

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
                </Text>
                {/* Quién la ejecuta y dónde: lo primero que el supervisor quiere saber de una OT. */}
                {v.detalle && (
                  <Group gap={6} mt={6} wrap="nowrap" role="group" aria-label="Operador">
                    <IconUser size={22} aria-hidden style={{ flexShrink: 0 }} />
                    <Text size="lg" fw={800} fs={v.detalle.operador ? undefined : 'italic'} c={v.detalle.operador ? undefined : 'roca.6'}>
                      {v.detalle.operador ? nombreDe(v.detalle.operador) : 'Sin operador'}
                    </Text>
                  </Group>
                )}
                {enEstacion && v.sesion && (
                  <Text size="sm" c="roca.7">
                    En la estación {enEstacion} desde las {horaCorta(v.sesion.desde)}
                  </Text>
                )}
              </Stack>
              <Stack gap="xs" align="flex-end">
                <EnVivo conexion={s.conexion} />
                <SegmentedControl
                  aria-label="Qué ver de la OT"
                  value={vista}
                  onChange={(valor) => setElegida(valor as Vista)}
                  data={[
                    { value: 'vivo', label: 'Ejecución' },
                    { value: 'reporte', label: 'Reporte' },
                  ]}
                />
              </Stack>
            </Group>
          </Stack>

          <Incidentes
            alertas={s.alertas}
            ot={ot}
            onVer={(id) => {
              setElegida('vivo')
              setElegido(id)
            }}
          />
          <PropuestasDeMejora propuestas={propuestas} nuevas={nuevas} />

          {!ot ? (
            <Center py="xl">
              <Stack align="center" gap="xs">
                <Loader />
                <Text c="roca.6">Conectando con la OT…</Text>
              </Stack>
            </Center>
          ) : vista === 'reporte' ? (
            <Reporte otId={otId} alDia={eventos} />
          ) : (
            <>
              {ot.completa && (
                <Paper withBorder radius="md" p="md" bg="verificado.0" style={{ borderLeft: '6px solid var(--mantine-color-verificado-6)' }}>
                  <Group justify="space-between" wrap="nowrap" gap="md">
                    <Group gap="sm" wrap="nowrap">
                      <IconCheck size={28} color="var(--mantine-color-verificado-7)" style={{ flexShrink: 0 }} />
                      <Text fw={800} size="lg">
                        OT completa: los {ot.pasos.length} pasos quedaron verificados.
                      </Text>
                    </Group>
                    <Button color="verificado" onClick={() => setElegida('reporte')} style={{ flexShrink: 0 }}>
                      Ver el reporte
                    </Button>
                  </Group>
                </Paper>
              )}
              {/* Como el monitor: a un lado lo que se ve y cómo va; al otro, sensores y pasos; abajo, todo lo que pasó. */}
              <SimpleGrid cols={{ base: 1, md: 2 }} spacing="lg" style={{ alignItems: 'start' }}>
                <Stack gap="lg">
                  <Camara edgeId={enEstacion} vistas={v.vistas} ot={ot} nivel={calificacion?.nivel ?? null} />
                  <Verificacion calificacion={calificacion} />
                </Stack>
                <Stack gap="lg">
                  {enEstacion && <Sensores sensores={v.sensores} ot={ot} pauta={v.pauta} />}
                  <Pasos ot={ot} bitacora={s.bitacora} />
                </Stack>
              </SimpleGrid>
              <Bitacora bitacora={s.bitacora} ot={ot} abiertas={abiertas} elegido={elegido} />
            </>
          )}
        </Stack>
      </Pagina>
    </>
  )
}
