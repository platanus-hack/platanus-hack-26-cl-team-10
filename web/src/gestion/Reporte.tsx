import { Alert, Anchor, Box, Center, Collapse, Group, Loader, Paper, Stack, Table, Text, Title, UnstyledButton } from '@mantine/core'
import { IconCamera, IconCheck, IconChevronRight, IconGauge, IconMessage, IconUser, IconWifiOff } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { api } from '../api/cliente'
import type { CierreReporte, DesviacionReporte, PasoReporte, ReporteOt } from '../api/tipos'
import industrial from './industrial.module.css'
import { enPalabras, NOMBRE_CLASE, NOMBRE_SENSOR } from './sensores'
import { mensajeDe } from './useOts'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })

/** Cuánto duró algo: en una estación los pasos toman segundos, no minutos. */
function duracion(segundos: number): string {
  const s = Math.max(0, Math.round(segundos))
  return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`
}
const entre = (desde: string, hasta: string) => duracion((Date.parse(hasta) - Date.parse(desde)) / 1000)
const certeza = (c: number | null) => (c === null ? '' : ` (${Math.round(c * 100)} %)`)

const ICONO: Record<CierreReporte['con'], typeof IconCheck> = {
  sensor: IconGauge,
  detector: IconCamera,
  camara: IconCamera,
  persona: IconUser,
  palabra: IconMessage,
}

/** Con qué se cerró el paso, dicho para una persona. */
function conQue(c: CierreReporte): string {
  switch (c.con) {
    case 'sensor':
      return `Sensor: ${NOMBRE_SENSOR[c.sensor ?? ''] ?? c.sensor} = ${c.leido}`
    case 'detector':
      return `Cámara: ${c.presente === false ? 'ya no ve' : 've'} ${NOMBRE_CLASE[c.clase ?? ''] ?? c.clase}${certeza(c.confianza)}`
    case 'camara':
      return `Cámara: responde que ${c.respuesta === false ? 'no' : 'sí'}${certeza(c.confianza)}`
    case 'persona':
      return `Una persona, contra la evidencia${c.motivo ? `: ${c.motivo}` : ''}`
    case 'palabra':
      return 'La palabra del operario'
  }
}

function Cierre({ p }: { p: PasoReporte }) {
  if (!p.cerrado_con) {
    return <Text c={p.estado === 'en_conflicto' ? 'precaucion.8' : 'roca.6'}>{p.estado === 'en_conflicto' ? 'En conflicto' : 'Pendiente'}</Text>
  }
  const Icono = ICONO[p.cerrado_con.con]
  // Lo que cerró una persona contra la evidencia se distingue: es lo que conviene mirar.
  const porPersona = p.cerrado_con.con === 'persona'
  return (
    <Group gap={6} wrap="nowrap" align="flex-start">
      <Icono size={18} style={{ flexShrink: 0, marginTop: 2 }} color={`var(--mantine-color-${porPersona ? 'precaucion-8' : 'verificado-7'})`} />
      <Text>{conQue(p.cerrado_con)}</Text>
    </Group>
  )
}

function Dato({ nombre, valor }: { nombre: string; valor: string }) {
  return (
    <li className={industrial.celda}>
      <p className={industrial.rotulo}>{nombre}</p>
      <p className={industrial.numero}>{valor}</p>
    </li>
  )
}

/** Una vez que pasó: la hora, qué decía (en palabras) y si se corrigió. */
function Vez({ d }: { d: DesviacionReporte }) {
  // Un conflicto entre la palabra y la evidencia no se «resuelve»: el paso se cierra después o queda así.
  const cierre = d.clase === 'conflicto' ? null : d.resuelta ? `Se corrigió en ${entre(d.abierta, d.resuelta)}` : 'Sigue abierta'
  return (
    <Group component="li" gap="md" wrap="nowrap" align="baseline" py={4}>
      <Text size="sm" c="roca.7" style={{ whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>
        {hora(d.abierta)}
      </Text>
      <Text size="sm" style={{ flex: 1 }}>
        {enPalabras(d.detalle)}
      </Text>
      {cierre && (
        <Text size="sm" fw={600} c={d.resuelta ? 'roca.7' : 'precaucion.8'} style={{ whiteSpace: 'nowrap' }}>
          {cierre}
        </Text>
      )}
    </Group>
  )
}

/** Las veces que pasó lo mismo en el mismo paso, juntas y plegadas: el título dice qué, dónde y cuántas veces. */
function GrupoDeDesviaciones({ que, ds }: { que: string; ds: DesviacionReporte[] }) {
  const [abierto, setAbierto] = useState(false)
  const grave = ds.some((d) => d.clase === 'seguridad')
  const abiertas = ds.filter((d) => d.clase !== 'conflicto' && !d.resuelta).length
  return (
    <Box component="li" style={{ borderLeft: `4px solid var(--mantine-color-${grave ? 'peligro' : 'precaucion'}-6)` }} bg={grave ? 'peligro.0' : 'precaucion.0'}>
      <UnstyledButton onClick={() => setAbierto((a) => !a)} aria-expanded={abierto} w="100%" p="sm">
        <Group justify="space-between" wrap="nowrap" gap="sm">
          <Group gap={6} wrap="nowrap">
            <IconChevronRight size={16} aria-hidden style={{ transform: abierto ? 'rotate(90deg)' : 'none', transition: 'transform 200ms ease' }} />
            <Text fw={700}>{que}</Text>
          </Group>
          <Text size="sm" c="roca.7" style={{ whiteSpace: 'nowrap' }}>
            {ds.length === 1 ? '1 vez' : `${ds.length} veces`}
            {abiertas > 0 ? ` · ${abiertas} sin corregir` : ''}
          </Text>
        </Group>
      </UnstyledButton>
      <Collapse expanded={abierto} transitionDuration={200} keepMounted keepMountedMode="display-none">
        <Box component="ul" px="sm" pb="sm" m={0} style={{ listStyle: 'none' }}>
          {ds.map((d) => (
            <Vez key={d.evento} d={d} />
          ))}
        </Box>
      </Collapse>
    </Box>
  )
}

/**
 * El reporte de la OT: qué cerró cada paso, qué se desvió y cuánto tardó en corregirse. Lo arma
 * el servidor leyendo la bitácora; aquí solo se muestra. Se vuelve a pedir cuando llegan eventos
 * (`alDia` es cuántos hay), así sirve también para una OT en curso.
 */
export function Reporte({ otId, alDia }: { otId: string; alDia: number }) {
  const [r, setR] = useState<ReporteOt | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let vivo = true
    api.leerReporte(otId).then(
      (nuevo) => {
        if (!vivo) return
        setR(nuevo)
        setError(null)
      },
      (e: unknown) => vivo && setError(mensajeDe(e)),
    )
    return () => {
      vivo = false
    }
  }, [otId, alDia])

  if (!r) {
    return error ? (
      <Alert color="peligro" variant="light" icon={<IconWifiOff />} title="No se pudo cargar el reporte">
        {error}
      </Alert>
    ) : (
      <Center py="xl">
        <Loader aria-label="Cargando el reporte" />
      </Center>
    )
  }

  const { resultado, personas, tiempos } = r
  const estado = !r.completa ? 'En curso' : resultado.sin_desviaciones ? 'Completa, sin desviaciones' : 'Completa, con desviaciones'
  const grupos = new Map<string, DesviacionReporte[]>()
  for (const d of r.desviaciones) {
    const orden = r.pasos.find((p) => p.paso === d.paso)?.orden
    const clave = `${d.que}${orden ? `, en el paso ${orden}` : ''}`
    grupos.set(clave, [...(grupos.get(clave) ?? []), d])
  }
  return (
    <section aria-label="Reporte de la OT">
      <Stack gap="lg">
        <Group justify="space-between" align="flex-start" gap="md">
          <Stack gap={2}>
            <Title order={3} className={industrial.seccion}>
              Reporte de la OT
            </Title>
            <p className={industrial.titular}>{estado}</p>
            <Text size="sm" c="roca.7" mt={6}>
              Armado desde la bitácora, con {r.eventos.total} eventos. Nadie lo escribió.
            </Text>
          </Stack>

        </Group>

        <ul className={industrial.celdas}>
          <Dato nombre="Pasos verificados" valor={`${resultado.pasos_verificados} de ${resultado.pasos}`} />
          <Dato nombre="Desviaciones" valor={String(resultado.desviaciones)} />
          <Dato nombre="Cerrados por una persona" valor={String(resultado.confirmados_por_persona)} />
          <Dato nombre="Duración" valor={tiempos.inicio && tiempos.fin ? entre(tiempos.inicio, tiempos.fin) : tiempos.inicio ? 'Sin terminar' : 'Sin empezar'} />
        </ul>

        {r.mejoras.length > 0 && (
          <Paper component="section" aria-label="Mejoras sugeridas" withBorder radius="md" p="md" style={{ borderLeft: '4px solid var(--mantine-color-mejora-6)' }}>
            <Stack gap="md">
              <Group justify="space-between">
                <Title order={4} className={industrial.seccion} m={0}>
                  Qué cambiaría Factum en la pauta
                </Title>
                <Anchor component={Link} to="/supervisor/mejoras" size="sm">
                  Revisarlas en mejoras
                </Anchor>
              </Group>
              {r.mejoras.map((x) => (
                <Stack key={x.propuesta} gap={4}>
                  <Text fw={700}>{x.cambios_resumen[0] ?? x.titulo}</Text>
                  {x.cambios_resumen.slice(1).map((c) => (
                    <Text key={c} fw={700}>
                      {c}
                    </Text>
                  ))}
                  <Text size="sm">
                    <Text span fw={600} c="roca.7">
                      Por qué:{' '}
                    </Text>
                    {x.porque}
                  </Text>
                  <Text size="sm">
                    <Text span fw={600} c="roca.7">
                      Cómo se sabrá si funcionó:{' '}
                    </Text>
                    {x.como_se_mide}
                  </Text>
                  {!x.aplicable && x.por_que_no && (
                    <Text size="sm" c="roca.7">
                      No se cambia en la pauta: {x.por_que_no}
                    </Text>
                  )}
                </Stack>
              ))}
            </Stack>
          </Paper>
        )}

        <Text size="sm" c="roca.7">
          La pidió {personas.pidio}. {personas.a_cargo ? `A cargo de ${personas.a_cargo}.` : 'Sin operador a cargo.'}
          {personas.ejecutaron.length > 0 ? ` La ejecutó ${personas.ejecutaron.join(', ')}.` : ''}
        </Text>

        <Table.ScrollContainer minWidth={640}>
          <Table aria-label="Pasos" verticalSpacing="sm" highlightOnHover={false}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th className={industrial.rotulo}>Paso</Table.Th>
                <Table.Th className={industrial.rotulo}>Lo cerró</Table.Th>
                <Table.Th className={industrial.rotulo}>Hora</Table.Th>
                <Table.Th className={industrial.rotulo}>Tardó</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {r.pasos.map((p) => (
                <Table.Tr key={p.paso}>
                  <Table.Td>
                    <Text fw={700}>
                      {p.orden}. {p.titulo}
                    </Text>
                    {p.control_critico && (
                      <Text size="xs" c="roca.7">
                        Control crítico
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td>
                    <Cierre p={p} />
                    {p.intentos > 1 && (
                      <Text size="xs" c="roca.7">
                        Al intento {p.intentos}
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td style={{ fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>{p.hora ? hora(p.hora) : ''}</Table.Td>
                  <Table.Td style={{ fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>{p.segundos === null ? '' : duracion(p.segundos)}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>

        <Stack gap="xs">
          <Title order={4} className={industrial.seccion}>
            Desviaciones
            {r.desviaciones.length > 0 && <span className={industrial.dato}>{r.desviaciones.length}</span>}
          </Title>
          {r.desviaciones.length === 0 ? (
            <Text c="roca.7">Ninguna: cada paso se hizo en su turno y con su evidencia.</Text>
          ) : (
            <Stack gap={6} component="ul" style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Desviaciones">
              {[...grupos].map(([que, ds]) => (
                <GrupoDeDesviaciones key={que} que={que} ds={ds} />
              ))}
            </Stack>
          )}
        </Stack>

        {r.observaciones.length > 0 && (
          <Stack gap="xs">
            <Title order={4} className={industrial.seccion}>
              Lo que observó el operario
            </Title>
            <Stack gap={6} component="ul" style={{ listStyle: 'none', margin: 0, padding: 0 }} aria-label="Observaciones">
              {r.observaciones.map((o) => (
                <Box key={o.evento} component="li">
                  <Text fs="italic">«{o.texto}»</Text>
                  <Text size="sm" c="roca.7">
                    {o.quien}, a las {hora(o.hora)}
                  </Text>
                </Box>
              ))}
            </Stack>
          </Stack>
        )}
      </Stack>
    </section>
  )
}
