import { Alert, Badge, Button, CloseButton, Group, Modal, Pagination, Progress, Radio, SegmentedControl, Select, Stack, Table, Text, TextInput, Title, Tooltip, VisuallyHidden } from '@mantine/core'
import { IconPlus, IconSearch } from '@tabler/icons-react'
import { useCallback, useEffect, useMemo, useState, type MouseEvent } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { api } from '../api/cliente'
import type { OtPedida, PautaResumen, Persona } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { recordarNombres, useNombres } from '../sesion/usuarios'
import { fraseCorta } from './sensores'
import { IdOt } from './incidentes'
import { rutaDe, useCampanaDeIncidentes } from './rutaDeOt'
import { avisoDe, enGrupos, ESTADOS, incidentesDe, puedeAsignarse, VERIFICACION } from './estados'
import industrial from './industrial.module.css'
import estilos from './TarjetaOt.module.css'
import { Encabezado, EstadoLista, FranjaDesactualizada, Pagina, VerificacionBadge } from './ui'
import { LIMITE_MS, mensajeDe, RECARGA_MS, useOts, type OtVista } from './useOts'

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

const POR_PAGINA = 25
type Filtro = 'activas' | 'alerta' | 'por_asignar' | 'completas'

/** Asignar o reasignar con un selector que se busca escribiendo: sirve igual con dos operarios que con cientos. */
function Asignar({ ot, operadores, onListo }: { ot: OtVista; operadores: Operadores; onListo: () => Promise<void> }) {
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  if (!operadores.lista) {
    return (
      <Text size="sm" c={operadores.error ? 'peligro' : 'roca.6'}>
        {operadores.error ? 'No se pudo cargar a los operadores' : 'Cargando operadores…'}
      </Text>
    )
  }
  const verbo = ot.estado === 'entregada' ? 'Reasignar' : 'Asignar'
  const asignar = async (operador: string | null) => {
    if (!operador) return
    setEnviando(true)
    setError(null)
    try {
      // Quién asigna lo sabe la API por el token, y queda en la bitácora de la OT.
      await api.asignar(ot.ot, operador)
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      // Un 409 suele decir que la OT cambió (otra pestaña u otro supervisor): se trae lo último.
      await onListo()
      setEnviando(false)
    }
  }
  return (
    <Stack gap={2}>
      <Select
        size="xs"
        w={200}
        placeholder={`${verbo} a…`}
        aria-label={`${verbo} ${ot.ot}`}
        data={operadores.lista.map((u) => ({ value: u.id, label: u.nombre }))}
        searchable
        nothingFoundMessage="Nadie con ese nombre"
        disabled={enviando}
        value={null}
        onChange={(v) => void asignar(v)}
        comboboxProps={{ withinPortal: false }}
      />
      {error && (
        <Text size="xs" c="peligro" role="alert">
          {error}
        </Text>
      )}
    </Stack>
  )
}

/** Una OT en una fila: cómo va, quién la tiene, en qué paso. Toda la fila abre su vista en vivo. */
function FilaOt({ ot: o, operadores, onListo }: { ot: OtVista; operadores: Operadores; onListo: () => Promise<void> }) {
  const navigate = useNavigate()
  const aviso = avisoDe(o)
  const a = o.avance
  const abrir = (e: MouseEvent<HTMLElement>) => {
    if (!(e.target as HTMLElement).closest('a, button, input, [role="listbox"]')) void navigate(rutaDe(o.ot))
  }
  return (
    <Table.Tr className={estilos.fila} data-nivel={aviso?.nivel} onClick={abrir}>
      <Table.Td w={130}>
        {o.calificacion ? (
          aviso ? (
            <Tooltip label={fraseCorta(aviso.que)} multiline w={280} withArrow>
              <span aria-label={`${VERIFICACION[aviso.nivel].etiqueta}: ${aviso.que}`} style={{ display: 'inline-flex' }}>
                <VerificacionBadge nivel={o.calificacion.nivel} size="sm" />
              </span>
            </Tooltip>
          ) : (
            <VerificacionBadge nivel={o.calificacion.nivel} size="sm" />
          )
        ) : (
          <Text size="xs" c="dimmed">
            {ESTADOS[o.estado].etiqueta}
          </Text>
        )}
      </Table.Td>
      <Table.Td w={100}>
        <IdOt ot={o.ot} />
      </Table.Td>
      <Table.Td>
        <Operador ot={o} />
      </Table.Td>
      <Table.Td maw={280}>
        <Text size="sm" truncate>
          {a?.nombre ?? o.pauta}
        </Text>
      </Table.Td>
      <Table.Td w={220}>
        {a ? (
          <Stack gap={2}>
            <Group gap={8} wrap="nowrap">
              <Progress
                value={a.total ? (a.cerrados / a.total) * 100 : 0}
                color={aviso ? (aviso.nivel === 'error' ? 'peligro' : 'precaucion') : ESTADOS[o.estado].color}
                size="sm"
                style={{ flex: 1 }}
                aria-label={`Avance de ${o.ot}: ${a.cerrados} de ${a.total}`}
              />
              <Text size="xs" fw={700} style={{ whiteSpace: 'nowrap' }}>
                {a.cerrados}/{a.total} pasos
              </Text>
            </Group>
            {o.estado === 'en_ejecucion' && a.pasoActual && (
              <Text size="xs" c="dimmed" truncate>
                Paso {a.pasoActual}
              </Text>
            )}
          </Stack>
        ) : (
          <Text c="roca.6">—</Text>
        )}
      </Table.Td>
      <Table.Td w={220}>{puedeAsignarse(o.estado) && <Asignar ot={o} operadores={operadores} onListo={onListo} />}</Table.Td>
    </Table.Tr>
  )
}

/**
 * Todas las OT en una tabla, pensada para cientos: lo que avisa arriba, un buscador (OT, operario o pauta), filtros
 * por estado y páginas de 25. Las completas quedan en su filtro, fuera de la vista de todos los días.
 */
function TablaOts({ ots, operadores, onListo }: { ots: OtVista[]; operadores: Operadores; onListo: () => Promise<void> }) {
  const nombreDe = useNombres()
  const [filtro, setFiltro] = useState<Filtro>('activas')
  const [busca, setBusca] = useState('')
  const [pagina, setPagina] = useState(1)
  // ?pauta=… llega desde Protocolos («Ver sus OT»): la tabla muestra solo las OT de esa pauta, hasta que se quita.
  const [params, setParams] = useSearchParams()
  const pauta = params.get('pauta')
  const ordenadas = enGrupos(ots)
    .flatMap((g) => g.ots)
    .filter((o) => !pauta || o.pauta === pauta)
  const nombreDePauta = pauta ? (ots.find((o) => o.pauta === pauta)?.avance?.nombre?.replace(/ v\d+$/, '') ?? pauta) : null
  const de: Record<Filtro, OtVista[]> = {
    activas: ordenadas.filter((o) => o.estado !== 'completa'),
    alerta: ordenadas.filter((o) => o.estado === 'en_ejecucion' && avisoDe(o)),
    por_asignar: ordenadas.filter((o) => puedeAsignarse(o.estado)),
    completas: ordenadas.filter((o) => o.estado === 'completa'),
  }
  const q = busca.trim().toLowerCase()
  const visibles = de[filtro].filter(
    (o) => !q || [o.ot, o.operador ? nombreDe(o.operador) : '', o.avance?.nombre ?? o.pauta].some((t) => t.toLowerCase().includes(q)),
  )
  const paginas = Math.max(1, Math.ceil(visibles.length / POR_PAGINA))
  const actual = Math.min(pagina, paginas)
  const etiqueta = (nombre: string, f: Filtro) => `${nombre} (${de[f].length})`
  return (
    <Stack gap="sm">
      <Group justify="space-between" gap="sm">
        <SegmentedControl
          aria-label="Qué OT ver"
          value={filtro}
          onChange={(v) => {
            setFiltro(v as Filtro)
            setPagina(1)
          }}
          data={[
            { value: 'activas', label: etiqueta('Activas', 'activas') },
            { value: 'alerta', label: etiqueta('Con alerta', 'alerta') },
            { value: 'por_asignar', label: etiqueta('Por asignar', 'por_asignar') },
            { value: 'completas', label: etiqueta('Completas', 'completas') },
          ]}
        />
        {pauta && (
          <Badge
            size="lg"
            variant="light"
            radius="sm"
            tt="none"
            rightSection={
              <CloseButton size="xs" aria-label="Ver las OT de todas las pautas" onClick={() => setParams({})} />
            }
          >
            Pauta: {nombreDePauta}
          </Badge>
        )}
        <TextInput
          aria-label="Buscar OT, operario o pauta"
          placeholder="Buscar OT, operario o pauta"
          leftSection={<IconSearch size={16} />}
          value={busca}
          onChange={(e) => {
            setBusca(e.currentTarget.value)
            setPagina(1)
          }}
          w={{ base: '100%', sm: 300 }}
        />
      </Group>
      <Table.ScrollContainer minWidth={900}>
        <Table aria-label="Órdenes de trabajo" verticalSpacing="sm" highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th className={industrial.rotulo}>Cómo va</Table.Th>
              <Table.Th className={industrial.rotulo}>OT</Table.Th>
              <Table.Th className={industrial.rotulo}>Operario</Table.Th>
              <Table.Th className={industrial.rotulo}>Pauta</Table.Th>
              <Table.Th className={industrial.rotulo}>Avance</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {visibles.slice((actual - 1) * POR_PAGINA, actual * POR_PAGINA).map((o) => (
              <FilaOt key={o.ot} ot={o} operadores={operadores} onListo={onListo} />
            ))}
          </Table.Tbody>
        </Table>
      </Table.ScrollContainer>
      {visibles.length === 0 && (
        <Text c="dimmed" ta="center" py="md">
          {q ? 'Nada coincide con la búsqueda.' : filtro === 'alerta' ? 'Ninguna OT tiene alertas ahora.' : 'No hay OT aquí.'}
        </Text>
      )}
      {paginas > 1 && (
        <Group justify="space-between">
          <Text size="sm" c="dimmed">
            {visibles.length} OT
          </Text>
          <Pagination total={paginas} value={actual} onChange={setPagina} size="sm" />
        </Group>
      )}
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
  const { ots, error, recargar } = useOts(RECARGA_MS, LIMITE_MS, 'en_ejecucion')
  const operadores = useOperadores()
  const incidentes = useMemo(() => (ots ? incidentesDe(ots) : null), [ots])
  useCampanaDeIncidentes(incidentes)
  const [pedida, setPedida] = useState<OtPedida | null>(null)
  if (!usuario) return null

  const lista = ots ?? []
  const deOperadores: Operadores = { lista: operadores.operadores, error: operadores.error }
  const alPedir = async (o: OtPedida) => {
    setPedida(o)
    await recargar()
  }

  return (
    <>
      <Encabezado usuario={usuario} seccion="Órdenes de trabajo" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="lg">
          <Group justify="space-between" align="center">
            <VisuallyHidden>
              <Title order={2}>Órdenes de trabajo</Title>
            </VisuallyHidden>
            <span />
            <PedirOt onPedida={alPedir} />
          </Group>
          {pedida && (
            <Alert color="verificado" variant="light" withCloseButton onClose={() => setPedida(null)} closeButtonLabel="Cerrar aviso">
              Pediste la {pedida.ot.toUpperCase()}, {pedida.nombre}. Queda por asignar.
            </Alert>
          )}
          <EstadoLista
            cargando={ots === null}
            error={error}
            vacia={lista.length === 0}
            textoVacia="No hay órdenes de trabajo abiertas."
            onReintentar={() => void recargar()}
          />
          {lista.length > 0 && <TablaOts ots={lista} operadores={deOperadores} onListo={recargar} />}
        </Stack>
      </Pagina>
    </>
  )
}
