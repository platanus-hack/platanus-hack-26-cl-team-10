import { Alert, Badge, Box, Button, Group, Paper, Stack, Text, Textarea, Title } from '@mantine/core'
import { IconArrowUpRight, IconBulb, IconCheck, IconHistory, IconWifiOff, IconX } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router'
import { api } from '../api/cliente'
import type { Borrador, CambioBorrador, DecisionMejora, EstadoMejora, Mejora, Metricas, SenalMejora } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { useNombres, type Usuario } from '../sesion/usuarios'
import industrial from './industrial.module.css'
import { Encabezado, Pagina } from './ui'
import { useMejoras } from './useMejoras'
import { mensajeDe } from './useOts'

const horaCorta = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hour12: false })
const numero = (n: number) => n.toLocaleString('es-CL', { maximumFractionDigits: 1 })

/** /supervisor/mejoras — lo que las OT ya ejecutadas dicen de las pautas, y lo que el supervisor decide. */
export function PaginaMejoras({ cadaMs }: { cadaMs?: number }) {
  const usuario = useSesion()
  if (!usuario) return null
  return <Vista usuario={usuario} cadaMs={cadaMs} />
}

const ESTADO: Record<EstadoMejora, { etiqueta: string; color: string; Icono: typeof IconCheck }> = {
  abierta: { etiqueta: 'Por revisar', color: 'mejora', Icono: IconBulb },
  aceptada: { etiqueta: 'Aceptada', color: 'verificado', Icono: IconCheck },
  descartada: { etiqueta: 'Descartada', color: 'roca', Icono: IconX },
  aplicada: { etiqueta: 'Aplicada en la versión nueva', color: 'verificado', Icono: IconArrowUpRight },
  superada: { etiqueta: 'Superada por una versión nueva', color: 'roca', Icono: IconHistory },
}

const SENAL: Record<SenalMejora, string> = {
  seguridad: 'Se dio una condición de peligro',
  orden: 'Se hizo antes de su turno',
  control: 'El control se deshizo',
  conflicto: 'La palabra y la evidencia no coinciden',
  persona: 'Lo confirmó una persona',
  observacion: 'Observaciones de operarios',
}

const VALIDACION = {
  mejoro: 'el paso dejó de desviarse',
  se_repite: 'el paso se sigue desviando',
  sin_datos: 'todavía no hay ejecuciones',
  sin_evidencia: 'bajó, pero con tan pocas OT todavía puede ser azar',
} as const

function Dato({ nombre, valor, detalle }: { nombre: string; valor: string; detalle?: string }) {
  return (
    <li className={industrial.celda}>
      <p className={industrial.rotulo}>{nombre}</p>
      <p className={industrial.numero}>{valor}</p>
      {detalle && <p className={industrial.celdaValor}>{detalle}</p>}
    </li>
  )
}

function Resumen({ k }: { k: Metricas | null }) {
  const pct = (n: number | null) => (n === null ? 'Sin datos' : `${numero(n)} %`)
  return (
    <section aria-label="Resumen">
      <ul className={industrial.celdas}>
        <Dato nombre="OT completas" valor={k ? String(k.cumplimiento.completas) : '…'} detalle={k ? `de ${k.ots.total} OT` : undefined} />
        <Dato
          nombre="Completas sin desviaciones"
          valor={k ? String(k.cumplimiento.sin_desviaciones) : '…'}
          detalle={k && k.cumplimiento.porcentaje !== null ? `${pct(k.cumplimiento.porcentaje)} de las completas` : undefined}
        />
        <Dato
          nombre="Pasos cerrados con sensor o cámara"
          valor={k ? pct(k.pasos.con_evidencia_objetiva_pct) : '…'}
          detalle={k ? `de ${k.pasos.verificados} pasos verificados` : undefined}
        />
        <Dato nombre="Propuestas por revisar" valor={k ? String(k.mejoras.abierta) : '…'} />
      </ul>
    </section>
  )
}

const CAMBIO: Record<CambioBorrador['tipo'], string> = { agrega: 'Agrega un paso', separa: 'Separa un paso', reescribe: 'Reescribe un paso' }

function Texto({ titulo, t }: { titulo: string; t: { titulo: string; instruccion: string } | null }) {
  return (
    <Box style={{ flex: 1, minWidth: 220 }}>
      <Text size="xs" fw={700} c="roca.7" tt="uppercase">
        {titulo}
      </Text>
      {t ? (
        <>
          <Text fw={700}>{t.titulo}</Text>
          <Text size="sm">{t.instruccion}</Text>
        </>
      ) : (
        <Text size="sm" c="roca.7">
          No existe: es un paso nuevo
        </Text>
      )}
    </Box>
  )
}

/** El cambio concreto a la pauta que haría aplicar la propuesta: antes y después de cada paso, con por qué. */
function CambioPropuesto({ p }: { p: Mejora }) {
  const [abierto, setAbierto] = useState(false)
  const [b, setB] = useState<Borrador | null>(null)
  const [error, setError] = useState<string | null>(null)

  const alternar = () => {
    setAbierto((a) => !a)
    if (b) return
    api.leerBorrador(p.id).then(setB, (e: unknown) => setError(mensajeDe(e)))
  }

  return (
    <Stack gap="xs">
      <Button variant="light" size="xs" w="fit-content" onClick={alternar} aria-expanded={abierto}>
        {abierto ? 'Ocultar el cambio' : 'Ver el cambio'}
      </Button>
      {abierto && error && (
        <Text size="sm" c="peligro" role="alert">
          {error}
        </Text>
      )}
      {abierto && b && (
        <Paper component="section" withBorder radius="md" p="md" aria-label="Cambio propuesto">
          <Stack gap="sm">
            <Text size="sm" c="roca.7">
              De la versión {b.desde_version} a la {b.version}
            </Text>
            {b.cambios.map((c, i) => (
              <Stack key={i} gap={6}>
                <Badge variant="light" radius="sm" w="fit-content">
                  {CAMBIO[c.tipo]}
                </Badge>
                <Group align="flex-start" gap="lg">
                  <Texto titulo="Antes" t={c.antes} />
                  <Texto titulo="Después" t={c.despues} />
                </Group>
                <Text size="sm">
                  <b>Por qué:</b> {c.porque}
                </Text>
              </Stack>
            ))}
            {!b.comprobacion ? null : b.comprobacion.valida ? (
              <Text size="sm" c="verificado.8">
                El validador lo revisó: no saca ningún control crítico.
              </Text>
            ) : (
              <Text size="sm" c="peligro" role="alert">
                El validador lo rechaza: la versión perdería un control crítico que hoy cumple.
              </Text>
            )}
          </Stack>
        </Paper>
      )}
    </Stack>
  )
}

/**
 * Aplicar es un toque: acepta la propuesta y Factum arma y aprueba la versión siguiente con su cambio. Sin cambio que
 * aplicar (el sensor, una escalada), se acepta para que Factum lo vea. Descartar pide antes el motivo.
 */
function Decidir({ p, alDecidir, alCancelar }: { p: Mejora; alDecidir(): void; alCancelar?: () => void }) {
  const [descartando, setDescartando] = useState(false)
  const [nota, setNota] = useState('')
  const [enviando, setEnviando] = useState<DecisionMejora | null>(null)
  const [error, setError] = useState<string | null>(null)

  const revisar = async (decision: DecisionMejora) => {
    setEnviando(decision)
    setError(null)
    try {
      await api.revisarMejora(p.id, decision, decision === 'descartar' ? nota : '')
      alDecidir()
    } catch (e) {
      setError(mensajeDe(e))
      setEnviando(null)
    }
  }

  return (
    <Stack gap="xs">
      {descartando ? (
        <>
          <Textarea label="Por qué se descarta" description="Queda en la revisión, con tu nombre y la hora." value={nota} onChange={(e) => setNota(e.currentTarget.value)} rows={2} autoFocus />
          <Group gap="sm">
            <Button color="peligro" disabled={!nota.trim()} loading={enviando === 'descartar'} onClick={() => void revisar('descartar')}>
              Descartar la propuesta
            </Button>
            <Button variant="default" onClick={() => setDescartando(false)}>
              Volver
            </Button>
          </Group>
        </>
      ) : (
        <Group gap="sm">
          <Button leftSection={<IconCheck size={18} />} loading={enviando === 'aceptar'} onClick={() => void revisar('aceptar')}>
            {p.aplicable ? 'Aplicar' : 'Aceptar'}
          </Button>
          <Button variant="default" onClick={() => setDescartando(true)}>
            Descartar
          </Button>
          {alCancelar && (
            <Button variant="subtle" onClick={alCancelar}>
              Dejarla como está
            </Button>
          )}
          <Text size="sm" c="roca.7">
            {p.aplicable
              ? 'Factum arma la versión siguiente con este cambio y la aprueba.'
              : 'Aceptarla la manda al equipo de Factum para la versión siguiente de la pauta.'}
          </Text>
        </Group>
      )}
      {error && (
        <Text size="sm" c="peligro" role="alert">
          {error}
        </Text>
      )}
    </Stack>
  )
}

function TarjetaMejora({ p, nueva, alDecidir }: { p: Mejora; nueva: boolean; alDecidir(): void }) {
  const nombreDe = useNombres()
  const [cambiando, setCambiando] = useState(false)
  const { etiqueta, color, Icono } = ESTADO[p.estado]
  const abierta = p.estado === 'abierta'
  const senales = (Object.keys(SENAL) as SenalMejora[]).filter((s) => p.senales[s] > 0)
  return (
    <Paper
      component="article"
      id={p.id}
      aria-label={`Propuesta para «${p.titulo}»`}
      withBorder
      radius="md"
      p="lg"
      style={abierta ? { boxShadow: 'inset 4px 0 var(--f-mejora)' } : undefined}
    >
      <Stack gap="md">
        <Group justify="space-between" align="flex-start" gap="lg">
          <Stack gap={6}>
            <Group gap="xs">
              <Badge color={color} variant={abierta ? 'filled' : 'light'} radius="sm" leftSection={<Icono size={14} stroke={2.5} />}>
                {etiqueta}
              </Badge>
              {nueva && (
                <Badge color="mejora" variant="outline" radius="sm">
                  Nueva
                </Badge>
              )}
              {p.control_critico && (
                <Badge color="peligro" variant="light" radius="sm">
                  Control crítico
                </Badge>
              )}
            </Group>
            <Title order={3} className={industrial.titular}>
              {p.titulo}
            </Title>
            <Text size="sm" c="roca.7">
              Un paso de {p.nombre}, versión {p.version}
            </Text>
          </Stack>
          <Stack gap={0}>
            <p className={industrial.numero}>
              {p.ots_con_senal} de {p.ejecuciones} OT
            </p>
            <Text size="sm" c="roca.7">
              dieron señales en este paso
              {p.operarios_distintos > 1 ? `, con ${p.operarios_distintos} operarios distintos` : ''}
            </Text>
          </Stack>
        </Group>

        <Group gap="xs">
          {senales.map((s) => (
            <Badge key={s} variant="default" radius="sm" tt="none" fw={600}>
              {SENAL[s]} ({p.senales[s]})
            </Badge>
          ))}
        </Group>

        <Box>
          <p className={industrial.rotulo}>Qué revisar</p>
          <Text>{p.sugerencia}</Text>
        </Box>

        {p.aplicable ? (
          <CambioPropuesto p={p} />
        ) : (
          p.por_que_no && (
            <Text size="sm" c="roca.7">
              <b>Sin cambio de pauta que aplicar:</b> {p.por_que_no}
            </Text>
          )
        )}

        {p.observaciones.length > 0 && (
          <Box>
            <p className={industrial.rotulo}>Lo que observaron los operarios</p>
            {p.observaciones.map((o, i) => (
              <Text key={i} fs="italic">
                «{o.texto}»
              </Text>
            ))}
          </Box>
        )}

        {p.validacion && (
          <Text size="sm">
            Con la versión {p.validacion.version_nueva}: {VALIDACION[p.validacion.resultado]} ({p.validacion.ots_con_senal} de {p.validacion.ejecuciones} OT con señal).
          </Text>
        )}

        {p.revision && (
          <Text size="sm" c="roca.7">
            {p.revision.decision === 'aceptar' ? 'Aceptada' : 'Descartada'} por {nombreDe(p.revision.por)} a las {horaCorta(p.revision.ts)}
            {p.revision.nota ? `: ${p.revision.nota}` : '.'}
          </Text>
        )}

        {abierta || cambiando ? (
          <Decidir
            p={p}
            alDecidir={() => {
              setCambiando(false)
              alDecidir()
            }}
            alCancelar={cambiando ? () => setCambiando(false) : undefined}
          />
        ) : (
          (p.estado === 'aceptada' || p.estado === 'descartada') && (
            <Button variant="subtle" size="xs" w="fit-content" px={0} onClick={() => setCambiando(true)}>
              Cambiar la decisión
            </Button>
          )
        )}
      </Stack>
    </Paper>
  )
}

function Vista({ usuario, cadaMs }: { usuario: Usuario; cadaMs?: number }) {
  const { mejoras, nuevas, error, recargar } = useMejoras(cadaMs)
  const [metricas, setMetricas] = useState<Metricas | null>(null)
  const { hash } = useLocation()
  const cargadas = mejoras !== null

  // Los números salen de la misma bitácora: se releen cada vez que llegan las propuestas.
  useEffect(() => {
    let vivo = true
    api.leerMetricas().then(
      (k) => vivo && setMetricas(k),
      () => {},
    )
    return () => {
      vivo = false
    }
  }, [mejoras])

  // Desde el aviso de una OT se llega con la propuesta en el enlace: se muestra esa.
  useEffect(() => {
    if (!cargadas || !hash) return
    document.getElementById(decodeURIComponent(hash.slice(1)))?.scrollIntoView?.({ block: 'center' })
  }, [cargadas, hash])

  return (
    <>
      <Encabezado usuario={usuario} seccion="Mejoras" />
      <Pagina>
        <Stack gap="lg">
          <Stack gap={4}>
            <Title order={2} className={industrial.titular}>
              Mejoras de las pautas
            </Title>
            <Text c="roca.7">Una propuesta nace cuando el mismo paso se desvía en dos o más OT. Se agrupa por paso y por pauta, nunca por persona.</Text>
          </Stack>

          <Resumen k={metricas} />

          {error && (
            <Alert color="peligro" variant="light" icon={<IconWifiOff />} title="No se pudieron cargar las propuestas">
              {error}
            </Alert>
          )}

          <Stack component="section" aria-label="Propuestas" gap="md">
            {mejoras?.length === 0 && (
              <Paper withBorder p="xl" radius="md">
                <Text ta="center" c="roca.7">
                  Todavía no hay propuestas. La primera aparecerá aquí sola, cuando un mismo paso se desvíe en dos OT.
                </Text>
              </Paper>
            )}
            {mejoras?.map((p) => (
              <TarjetaMejora key={p.id} p={p} nueva={nuevas.has(p.id)} alDecidir={() => void recargar()} />
            ))}
          </Stack>
        </Stack>
      </Pagina>
    </>
  )
}
