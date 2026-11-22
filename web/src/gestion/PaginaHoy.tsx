import { Anchor, Group, Paper, Progress, SimpleGrid, Stack, Text, Title, Tooltip, VisuallyHidden } from '@mantine/core'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { api } from '../api/cliente'
import type { Metricas } from '../api/tipos'
import { useSesion } from '../sesion/sesion'
import { useNombres } from '../sesion/usuarios'
import { avisoDe, enGrupos, incidentesDe, puedeAsignarse, VERIFICACION } from './estados'
import { BarraIncidentes, IdOt } from './incidentes'
import industrial from './industrial.module.css'
import { Recomendaciones } from './Recomendaciones'
import { rutaDe, useCampanaDeIncidentes } from './rutaDeOt'
import { fraseCorta } from './sensores'
import { EstadoLista, Encabezado, FranjaDesactualizada, Pagina, VerificacionBadge } from './ui'
import { LIMITE_MS, RECARGA_MS, useOts, type OtVista } from './useOts'
import { useRecomendaciones } from './useRecomendaciones'

const MAX_EN_CURSO = 8
const hoyLocal = () => new Date().toLocaleDateString('sv-SE') // AAAA-MM-DD, en la hora del supervisor

/** Lo de hoy en la empresa (`GET /cliente/metricas?desde=hoy`), releído cada 10 s. */
function useMetricasDeHoy() {
  const [m, setM] = useState<Metricas | null>(null)
  useEffect(() => {
    const leer = () => api.leerMetricas(hoyLocal()).then(setM, () => {})
    void leer()
    const reloj = setInterval(leer, 10_000)
    return () => clearInterval(reloj)
  }, [])
  return m
}

function Dato({ nombre, valor, color }: { nombre: string; valor: string; color?: string }) {
  return (
    <li className={industrial.celda} data-color={color ? '' : undefined} style={color ? { ['--color-celda' as string]: `var(--f-${color})` } : undefined}>
      <p className={industrial.rotulo}>{nombre}</p>
      <p className={industrial.numero} aria-label={`${nombre}: ${valor}`}>
        {valor}
      </p>
    </li>
  )
}

/** Una OT que corre ahora, en una línea: cómo va, quién, en qué paso. */
function EnCurso({ o }: { o: OtVista }) {
  const navigate = useNavigate()
  const nombreDe = useNombres()
  const aviso = avisoDe(o)
  const a = o.avance
  return (
    <Group
      component="li"
      wrap="nowrap"
      gap="sm"
      py={8}
      px="sm"
      onClick={(e) => !(e.target as HTMLElement).closest('a') && void navigate(rutaDe(o.ot))}
      style={{ cursor: 'pointer', borderTop: '1px solid var(--f-linea)', boxShadow: aviso ? `inset 3px 0 var(--mantine-color-${aviso.nivel === 'error' ? 'peligro' : 'precaucion'}-6)` : undefined }}
    >
      <IdOt ot={o.ot} />
      <Stack gap={0} style={{ flex: 1, minWidth: 0 }}>
        <Text size="sm" fw={600} truncate>
          {o.operador ? nombreDe(o.operador) : 'Sin operario'}
        </Text>
        <Text size="xs" c="dimmed" truncate>
          {a?.pasoActual ? `Paso ${a.pasoActual}` : (a?.nombre ?? o.pauta)}
        </Text>
      </Stack>
      {a && (
        <Progress
          w={90}
          value={a.total ? (a.cerrados / a.total) * 100 : 0}
          color={aviso ? (aviso.nivel === 'error' ? 'peligro' : 'precaucion') : 'accion'}
          size="sm"
          aria-label={`Avance de ${o.ot}: ${a.cerrados} de ${a.total}`}
        />
      )}
      {o.calificacion &&
        (aviso ? (
          <Tooltip label={fraseCorta(aviso.que)} multiline w={260} withArrow>
            <span aria-label={`${VERIFICACION[aviso.nivel].etiqueta}: ${aviso.que}`} style={{ display: 'inline-flex', flexShrink: 0 }}>
              <VerificacionBadge nivel={o.calificacion.nivel} size="sm" />
            </span>
          </Tooltip>
        ) : (
          <VerificacionBadge nivel={o.calificacion.nivel} size="sm" />
        ))}
    </Group>
  )
}

const CLASE: Record<string, string> = { seguridad: 'de seguridad', orden: 'de orden', control: 'de control', conflicto: 'de evidencia', persona: 'que cerró una persona' }

/** Cómo va el día, en frases: lo que se terminó, lo que se desvió y cuánto tarda. */
function ElDia({ m }: { m: Metricas | null }) {
  if (!m) return <Text c="dimmed">Cargando lo de hoy…</Text>
  const { cumplimiento: c, desviaciones: d } = m
  const clases = Object.entries(d.por_clase)
    .filter(([, n]) => n > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([k, n]) => `${n} ${CLASE[k] ?? k}`)
  const lineas = [
    c.completas
      ? `${c.sin_desviaciones} de ${c.completas} OT completas salieron sin desviaciones${c.porcentaje !== null ? ` (${Math.round(c.porcentaje)} %)` : ''}.`
      : 'Todavía no se completa ninguna OT hoy.',
    d.total ? `${d.total} ${d.total === 1 ? 'desviación' : 'desviaciones'}: ${clases.join(', ')}.` : 'Ninguna desviación hoy.',
    d.minutos_medios_para_resolver !== null ? `Una desviación se corrige en ${Math.round(d.minutos_medios_para_resolver)} min, en promedio.` : null,
    m.minutos_medios_de_ejecucion !== null ? `Una OT tarda ${Math.round(m.minutos_medios_de_ejecucion)} min, en promedio.` : null,
  ].filter(Boolean)
  return (
    <Stack gap={6}>
      {lineas.map((l) => (
        <Text key={l} size="sm">
          {l}
        </Text>
      ))}
    </Stack>
  )
}

/**
 * /supervisor/hoy — la portada del supervisor: los incidentes en curso, los números del día, lo que corre ahora (lo
 * que avisa primero) y las mejoras que propone Factum. La lista completa está en «Órdenes de trabajo».
 */
export function PaginaHoy() {
  const usuario = useSesion()
  const { ots, error, recargar } = useOts(RECARGA_MS, LIMITE_MS, 'en_ejecucion')
  const incidentes = useMemo(() => (ots ? incidentesDe(ots) : null), [ots])
  useCampanaDeIncidentes(incidentes)
  const recomendaciones = useRecomendaciones()
  const m = useMetricasDeHoy()
  if (!usuario) return null

  const lista = ots ?? []
  const enCurso = enGrupos(lista).find((g) => g.titulo === 'En ejecución')?.ots ?? []
  const conAlerta = enCurso.filter((o) => avisoDe(o)).length
  const porAsignar = lista.filter((o) => puedeAsignarse(o.estado)).length

  return (
    <>
      <Encabezado usuario={usuario} seccion="Hoy" />
      <FranjaDesactualizada error={ots ? error : null} />
      <Pagina>
        <Stack gap="lg">
          <VisuallyHidden>
            <Title order={2}>Hoy</Title>
          </VisuallyHidden>
          <BarraIncidentes incidentes={incidentes ?? []} />
          <EstadoLista cargando={ots === null} error={error} vacia={false} textoVacia="" onReintentar={() => void recargar()} />
          {ots && (
            <ul className={industrial.celdas}>
              <Dato nombre="En curso" valor={String(enCurso.length)} color={enCurso.length ? 'accion' : undefined} />
              <Dato nombre="Con alerta" valor={String(conAlerta)} color={conAlerta ? 'peligro' : undefined} />
              <Dato nombre="Por asignar" valor={String(porAsignar)} color={porAsignar ? 'precaucion' : undefined} />
              <Dato nombre="Completas hoy" valor={m ? String(m.ots.por_estado.completa ?? 0) : '…'} color="verificado" />
            </ul>
          )}
          <SimpleGrid cols={{ base: 1, md: 2 }} spacing="md">
            <Paper component="section" aria-label="En curso ahora" withBorder radius="md" p="md">
              <Group justify="space-between" mb="xs">
                <Text fw={800}>En curso ahora</Text>
                <Anchor component={Link} to="/supervisor" size="sm">
                  Ver todas las OT
                </Anchor>
              </Group>
              {enCurso.length === 0 ? (
                <Text size="sm" c="dimmed">
                  Ninguna OT corre en este momento.
                </Text>
              ) : (
                <Stack component="ul" gap={0} m={0} p={0} style={{ listStyle: 'none' }}>
                  {enCurso.slice(0, MAX_EN_CURSO).map((o) => (
                    <EnCurso key={o.ot} o={o} />
                  ))}
                </Stack>
              )}
              {enCurso.length > MAX_EN_CURSO && (
                <Text size="xs" c="dimmed" mt="xs">
                  Y {enCurso.length - MAX_EN_CURSO} más en «Órdenes de trabajo».
                </Text>
              )}
            </Paper>
            <Paper component="section" aria-label="El día" withBorder radius="md" p="md">
              <Text fw={800} mb="xs">
                El día
              </Text>
              <ElDia m={m} />
            </Paper>
          </SimpleGrid>
          <Recomendaciones recomendaciones={recomendaciones.recomendaciones} quitar={recomendaciones.quitar} />
        </Stack>
      </Pagina>
    </>
  )
}
