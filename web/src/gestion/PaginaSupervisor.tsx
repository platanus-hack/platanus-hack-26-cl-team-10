import { Alert, Anchor, Button, Card, Group, Modal, Paper, Progress, Radio, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { IconAlertTriangle, IconEye, IconPlus, IconRefresh, IconUser } from '@tabler/icons-react'
import { useCallback, useEffect, useMemo, useRef, useState, type MouseEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api/cliente'
import type { EstadoGeneral, OtPedida, PautaResumen, Persona } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { recordarNombres, useNombres } from '../sesion/usuarios'
import { campana } from './campana'
import { avisoDe, enGrupos, ESTADOS, incidentesDe, puedeAsignarse, type Incidente } from './estados'
import industrial from './industrial.module.css'
import estilos from './TarjetaOt.module.css'
import { Encabezado, EstadoLista, FranjaDesactualizada, Pagina, VerificacionBadge } from './ui'
import { mensajeDe, useOts, type OtVista } from './useOts'
import { Recomendaciones } from './Recomendaciones'
import { useRecomendaciones } from './useRecomendaciones'

/** Los operadores de la empresa (`GET /cliente/operadores`), con sus nombres para toda la pantalla. */
function useOperadores() {
  const [operadores, setOperadores] = useState<Persona[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const recargar = useCallback(async () => {
    try {
      const ps = await api.listarOperadores()
      recordarNombres(ps)
      setOperadores(ps)
      setError(null)
    } catch (e) {
      setError(mensajeDe(e))
    }
  }, [])
  useEffect(() => {
    void Promise.resolve().then(recargar)
  }, [recargar])
  return { operadores, error, recargar }
}

type Operadores = { lista: Persona[] | null; error: string | null }

const CONTADORES: { titulo: string; estados: EstadoGeneral[]; color: string }[] = [
  { titulo: 'Por asignar', estados: ['sin_asignar'], color: 'roca' },
  { titulo: 'Entregadas', estados: ['entregada'], color: 'precaucion' },
  { titulo: 'En curso', estados: ['asignada', 'en_ejecucion'], color: 'accion' },
  { titulo: 'Completas', estados: ['completa'], color: 'verificado' },
]

function Contadores({ ots }: { ots: OtVista[] }) {
  return (
    <ul className={industrial.celdas}>
      {CONTADORES.map((c) => {
        const n = ots.filter((o) => c.estados.includes(o.estado)).length
        return (
          <li key={c.titulo} className={industrial.celda} data-color style={{ ['--color-celda' as string]: `var(--f-${c.color})` }}>
            <p className={industrial.rotulo}>{c.titulo}</p>
            <p className={industrial.numero} aria-label={`${c.titulo}: ${n}`}>
              {n}
            </p>
          </li>
        )
      })}
    </ul>
  )
}

function Avance({ ot }: { ot: OtVista }) {
  const a = ot.avance
  if (!a) return <Text c="roca.6">—</Text>
  return (
    <Stack gap={4} miw={110}>
      <Text size="sm" fw={700}>
        {a.cerrados}/{a.total} pasos
      </Text>
      <Progress
        value={a.total ? (a.cerrados / a.total) * 100 : 0}
        color={ESTADOS[ot.estado].color}
        size="sm"
        aria-label={`Avance de ${ot.ot}: ${a.cerrados} de ${a.total}`}
      />
    </Stack>
  )
}

function Operador({ ot }: { ot: OtVista }) {
  const nombreDe = useNombres()
  if (ot.operador) return <Text fw={600}>{nombreDe(ot.operador)}</Text>
  const entregado = ot.entregada_por ? `Turno entregado por ${nombreDe(ot.entregada_por)}` : 'Turno entregado'
  return (
    <Text c="roca.6" fs="italic">
      {ot.estado === 'entregada' ? entregado : 'Nadie'}
    </Text>
  )
}

/** Un botón por operador de la empresa: con dos en el demo, asignar es un solo clic. */
function Asignar({ ot, operadores, onListo }: { ot: OtVista; operadores: Operadores; onListo: () => Promise<void> }) {
  const [enviando, setEnviando] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  if (!puedeAsignarse(ot.estado)) return <Text c="roca.6">—</Text>
  if (!operadores.lista) {
    return (
      <Text size="sm" c={operadores.error ? 'peligro' : 'roca.6'}>
        {operadores.error ? 'No se pudo cargar a los operadores' : 'Cargando operadores…'}
      </Text>
    )
  }

  const asignar = async (operador: string) => {
    setEnviando(operador)
    setError(null)
    try {
      // Quién asigna lo sabe la API por el token, y queda en la bitácora de la OT.
      await api.asignar(ot.ot, operador)
      await onListo()
    } catch (e) {
      setError(mensajeDe(e))
      // Un 409 suele decir que la OT cambió (otra pestaña u otro supervisor): se trae lo último.
      await onListo()
    } finally {
      setEnviando(null)
    }
  }

  const verbo = ot.estado === 'entregada' ? 'Reasignar' : 'Asignar'
  return (
    <Stack gap={4}>
      <Group gap={6}>
        <Text size="sm" fw={600} c="roca.7">
          {verbo} a
        </Text>
        {operadores.lista.map((u) => (
          <Button
            key={u.id}
            size="xs"
            loading={enviando === u.id}
            disabled={enviando !== null && enviando !== u.id}
            onClick={() => void asignar(u.id)}
            aria-label={`${verbo} ${ot.ot} a ${u.nombre}`}
          >
            {u.nombre}
          </Button>
        ))}
      </Group>
      {error && (
        <Text size="sm" c="peligro" role="alert">
          {error}
        </Text>
      )}
    </Stack>
  )
}

const rutaDe = (ot: string) => `/supervisor/ot/${encodeURIComponent(ot)}`

/** El id de la OT lleva a su vista en vivo: cámara, sensores y bitácora. */
function IdOt({ ot }: { ot: string }) {
  return (
    <Anchor component={Link} to={rutaDe(ot)} fw={500} ff="var(--f-mono)" c="var(--f-accion-texto)" underline="hover" style={{ letterSpacing: '0.06em' }}>
      {ot.toUpperCase()}
    </Anchor>
  )
}

function Ver({ ot, ancho = false }: { ot: OtVista; ancho?: boolean }) {
  const enVivo = ot.estado === 'en_ejecucion'
  return (
    <Button component={Link} to={rutaDe(ot.ot)} variant="default" size="xs" fullWidth={ancho} leftSection={<IconEye size={16} />} aria-label={`Ver ${ot.ot}`}>
      {enVivo ? 'Ver en vivo' : 'Ver bitácora'}
    </Button>
  )
}

/** Lo que pide mirar ya: OT abiertas en «detente». Cada una lleva a su vista en vivo. */
function BarraIncidentes({ incidentes }: { incidentes: Incidente[] }) {
  const nombreDe = useNombres()
  if (incidentes.length === 0) return null
  return (
    <Paper radius="md" p="md" bg="peligro.6" role="alert" aria-label="Incidentes en curso">
      <Stack gap="sm">
        <Group gap="xs" c="var(--f-peligro-sobre)">
          <IconAlertTriangle size={24} />
          <Text fw={900} size="lg" c="var(--f-peligro-sobre)">
            {incidentes.length === 1 ? 'Un incidente en curso' : `${incidentes.length} incidentes en curso`}
          </Text>
        </Group>
        {incidentes.map((i) => (
          <Paper key={i.ot} radius="sm" p="sm">
            <Group justify="space-between" wrap="nowrap" gap="md">
              <Stack gap={2}>
                <Text fw={800}>
                  {i.ot.toUpperCase()}
                  {i.operador ? `, ${nombreDe(i.operador)}` : ''}
                </Text>
                <Text size="sm">{i.que}</Text>
              </Stack>
              <Button component={Link} to={rutaDe(i.ot)} variant="default" leftSection={<IconEye size={18} />} style={{ flexShrink: 0 }} aria-label={`Ver ${i.ot} en vivo`}>
                Ver en vivo
              </Button>
            </Group>
          </Paper>
        ))}
      </Stack>
    </Paper>
  )
}

/** Suena una vez por incidente nuevo; los que ya estaban al entrar no suenan. */
function useCampanaDeIncidentes(incidentes: Incidente[] | null) {
  const vistos = useRef<Set<string> | null>(null)
  useEffect(() => {
    if (!incidentes) return
    const claves = new Set(incidentes.map((i) => `${i.ot}:${i.que}`))
    if (vistos.current && [...claves].some((k) => !vistos.current!.has(k))) campana.sonar()
    vistos.current = claves
  }, [incidentes])
  // El primer toque en la página deja el audio listo, por si se entró recargando.
  useEffect(() => {
    const preparar = () => campana.preparar()
    window.addEventListener('pointerdown', preparar, { once: true })
    return () => window.removeEventListener('pointerdown', preparar)
  }, [])
}

/**
 * Una OT en su tarjeta. Si la estación avisa algo, la tarjeta se enciende (amarillo o rojo) y dice
 * por qué. Un clic en cualquier parte abre su vista en vivo; los botones y los enlaces hacen lo suyo.
 */
function TarjetaOt({ ot: o, operadores, onListo }: { ot: OtVista; operadores: Operadores; onListo: () => Promise<void> }) {
  const navigate = useNavigate()
  const aviso = avisoDe(o)
  const abrir = (e: MouseEvent<HTMLElement>) => {
    if (!(e.target as HTMLElement).closest('a, button')) void navigate(rutaDe(o.ot))
  }
  return (
    <Card withBorder radius="md" padding="md" className={estilos.tarjeta} data-nivel={aviso?.nivel} onClick={abrir}>
      <Stack gap="sm" flex={1}>
        <Group justify="space-between" wrap="nowrap" align="flex-start">
          <IdOt ot={o.ot} />
          {o.calificacion && <VerificacionBadge nivel={o.calificacion.nivel} />}
        </Group>
        <div>
          <Text fw={600}>{o.avance?.nombre ?? o.pauta}</Text>
          <Text size="sm" c="roca.6">
            {o.equipo}
          </Text>
        </div>
        {aviso && (
          <Text size="sm" fw={700}>
            {aviso.que}
          </Text>
        )}
        <Group justify="space-between" align="flex-end" wrap="nowrap" mt="auto">
          <Group gap={6} wrap="nowrap">
            <IconUser size={18} aria-hidden style={{ flexShrink: 0 }} />
            <Operador ot={o} />
          </Group>
          <Avance ot={o} />
        </Group>
        {puedeAsignarse(o.estado) ? <Asignar ot={o} operadores={operadores} onListo={onListo} /> : <Ver ot={o} ancho />}
      </Stack>
    </Card>
  )
}

/** Las OT en grupos, con las que se ejecutan ahora arriba. */
function Grupos({ ots, operadores, onListo }: { ots: OtVista[]; operadores: Operadores; onListo: () => Promise<void> }) {
  return (
    <Stack gap="xl">
      {enGrupos(ots).map((g) => (
        <Stack key={g.titulo} component="section" aria-label={g.titulo} gap="sm">
          <Title order={3} className={industrial.seccion}>
            {g.titulo}
            <span className={industrial.dato}>{g.ots.length}</span>
          </Title>
          <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="md">
            {g.ots.map((o) => (
              <TarjetaOt key={o.ot} ot={o} operadores={operadores} onListo={onListo} />
            ))}
          </SimpleGrid>
        </Stack>
      ))}
    </Stack>
  )
}

/** El supervisor pide una OT de una de las pautas de su empresa; nace sin operador. */
function PedirOt({ onPedida }: { onPedida: (o: OtPedida) => Promise<void> }) {
  const [abierto, setAbierto] = useState(false)
  const [pautas, setPautas] = useState<PautaResumen[] | null>(null)
  const [elegida, setElegida] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const abrir = () => {
    setAbierto(true)
    setElegida(null)
    setError(null)
    api.listarPautas().then(setPautas, (e: unknown) => setError(mensajeDe(e)))
  }

  const pedir = async () => {
    if (!elegida) return
    setEnviando(true)
    setError(null)
    try {
      const o = await api.pedirOt(elegida)
      setAbierto(false)
      await onPedida(o)
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <Button leftSection={<IconPlus size={16} />} onClick={abrir}>
        Pedir OT
      </Button>
      <Modal opened={abierto} onClose={() => setAbierto(false)} title="Pedir una OT" centered size="lg">
        <Stack gap="md">
          <Text c="roca.7">Elige qué trabajo hay que hacer. La OT queda por asignar.</Text>
          {pautas === null && !error && <Text c="roca.6">Cargando pautas…</Text>}
          {pautas && pautas.length === 0 && <Text c="roca.6">Tu empresa no tiene pautas habilitadas.</Text>}
          {pautas && pautas.length > 0 && (
            <Radio.Group value={elegida} onChange={setElegida} label="Pauta" name="pauta">
              <Stack gap="sm" mt="xs">
                {pautas.map((p) => (
                  <Radio key={p.id} value={p.id} label={p.nombre} description={`${p.equipo}, ${p.pasos} pasos`} />
                ))}
              </Stack>
            </Radio.Group>
          )}
          {error && (
            <Text c="peligro" role="alert">
              {error}
            </Text>
          )}
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setAbierto(false)}>
              Cancelar
            </Button>
            <Button onClick={() => void pedir()} loading={enviando} disabled={!elegida}>
              Pedir esta OT
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  )
}

export function PaginaSupervisor() {
  const usuario = useSesion()
  const { ots, error, recargar } = useOts()
  const operadores = useOperadores()
  const incidentes = useMemo(() => (ots ? incidentesDe(ots) : null), [ots])
  useCampanaDeIncidentes(incidentes)
  const recomendaciones = useRecomendaciones()
  const [pedida, setPedida] = useState<OtPedida | null>(null)
  if (!usuario) return null

  const lista = ots ?? []
  const deOperadores: Operadores = { lista: operadores.operadores, error: operadores.error }
  const actualizar = () => {
    void recargar()
    void recomendaciones.recargar()
    if (!operadores.operadores) void operadores.recargar()
  }
  const alPedir = async (o: OtPedida) => {
    setPedida(o)
    await recargar()
  }

  return (
    <>
      <Encabezado usuario={usuario} seccion="Supervisión" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="lg">
          <Group justify="space-between">
            <Title order={2} className={industrial.titular}>
              Órdenes de trabajo
            </Title>
            <Group gap="sm">
              <Button variant="default" leftSection={<IconRefresh size={16} />} onClick={actualizar}>
                Actualizar
              </Button>
              <PedirOt onPedida={alPedir} />
            </Group>
          </Group>
          <BarraIncidentes incidentes={incidentes ?? []} />
          <Recomendaciones recomendaciones={recomendaciones.recomendaciones} quitar={recomendaciones.quitar} />
          {pedida && (
            <Alert color="verificado" variant="light" withCloseButton onClose={() => setPedida(null)} closeButtonLabel="Cerrar aviso">
              Pediste la {pedida.ot.toUpperCase()}, {pedida.nombre}. Queda por asignar.
            </Alert>
          )}
          {ots && <Contadores ots={ots} />}
          <EstadoLista
            cargando={ots === null}
            error={error}
            vacia={lista.length === 0}
            textoVacia="No hay órdenes de trabajo abiertas."
            onReintentar={() => void recargar()}
          />
          <Grupos ots={lista} operadores={deOperadores} onListo={recargar} />
        </Stack>
      </Pagina>
    </>
  )
}
