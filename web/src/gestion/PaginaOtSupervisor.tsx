import { ActionIcon, Button, Center, Collapse, Group, Loader, Popover, ScrollArea, SegmentedControl, Stack, Text, Title, UnstyledButton } from '@mantine/core'
import { IconAlertTriangle, IconArrowLeft, IconCheck, IconChevronRight, IconVolume, IconVolumeOff, IconX } from '@tabler/icons-react'
import { useEffect, useMemo, useState, useSyncExternalStore, type CSSProperties, type ReactNode } from 'react'
import { Link, useParams } from 'react-router'
import { senalesDe } from '../api/mejoras'
import type { Calificacion, CalificacionOt, Deteccion, EstadoOt, Evento, Mejora, Pauta, PasoEstado } from '../api/tipos'
import { config } from '../config'
import { queDice, tituloDe } from '../ejecucion/alertas'
import { FranjaSinConexion } from '../ejecucion/Avisos'
import { cerradoPor, type Conexion } from '../ejecucion/estado'
import { voz } from '../ejecucion/voz'
import { useSesion } from '../sesion/sesion'
import { useNombres, type Usuario } from '../sesion/usuarios'
import { estadoDe, VERIFICACION } from './estados'
import estilos from './industrial.module.css'
import { Reporte } from './Reporte'
import { enPalabras, NOMBRE_CLASE, NOMBRE_SENSOR, UNIDAD } from './sensores'
import { Encabezado, EstadoBadge, Pagina } from './ui'
import { useMejoras } from './useMejoras'
import { useOtEnVivo, type Lectura } from './useOtEnVivo'

const hora = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
const horaCorta = (ts: string) => new Date(ts).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit', hour12: false })

/** Los colores de una franja o de un evento, como variables para la hoja de estilos. */
const colores = (prefijo: string, color: string) =>
  ({
    [`--color-${prefijo}`]: `var(--f-${color})`,
    [`--color-${prefijo}-tenue`]: `var(--f-${color}-tenue)`,
    [`--color-${prefijo}-texto`]: `var(--f-${color}-texto)`,
  }) as CSSProperties

/**
 * /supervisor/ot/:id — una OT en vivo para el supervisor, con la forma del monitor: la ficha, el
 * video con su marco, la verificación, los sensores en celdas, los pasos numerados y la bitácora.
 * Solo mira.
 */
export function PaginaOtSupervisor() {
  const { id = '' } = useParams()
  const usuario = useSesion()
  if (!usuario) return null
  return <VistaOt key={id} otId={id} usuario={usuario} />
}

function EnVivo({ conexion }: { conexion: Conexion }) {
  const vivo = conexion === 'en_vivo'
  return (
    <p className={estilos.vivo} data-vivo={vivo || undefined}>
      {vivo ? 'En vivo' : 'Conectando…'}
    </p>
  )
}

/**
 * SOLO PARA EL DEMO (config.VOZ_EN): los avisos en voz suenan en esta vista. El navegador no deja sonar
 * nada hasta que alguien toca la página: «Probar audio» es ese toque, y dice la frase de prueba.
 */
function AudioDeLosAvisos() {
  const audio = useSyncExternalStore(voz.alCambiar, voz.estado)
  const probar = async () => {
    if (voz.estado() !== 'activo') await voz.desbloquear()
    voz.probar()
  }
  return (
    <Group gap="xs" wrap="nowrap">
      {audio === 'activo' ? <IconVolume size={18} /> : <IconVolumeOff size={18} color="var(--f-precaucion-texto)" />}
      <Text size="sm" fw={600} c={audio === 'activo' ? undefined : 'precaucion.7'}>
        {audio === 'activo' ? 'Audio activo' : 'Audio bloqueado'}
      </Text>
      <Button size="compact-sm" variant="subtle" onClick={probar}>
        Probar audio
      </Button>
    </Group>
  )
}

/** Cuánto sigue a la vista una alerta después de resolverse: una lectura que entra y sale no hace parpadear la pantalla. */
const RETENER_MS = 3000

function useRetenidas(alertas: Evento[]): Evento[] {
  const [ultimas, setUltimas] = useState<{ de: Evento[]; vigentes: Evento[] }>({ de: alertas, vigentes: alertas })
  // Mientras hay alertas, son las que se muestran y quedan guardadas (se ajusta durante el render, sin efecto).
  if (alertas.length > 0 && ultimas.de !== alertas) setUltimas({ de: alertas, vigentes: alertas })
  useEffect(() => {
    if (alertas.length > 0) return
    const reloj = setTimeout(() => setUltimas({ de: alertas, vigentes: [] }), RETENER_MS)
    return () => clearTimeout(reloj)
  }, [alertas])
  return alertas.length > 0 ? alertas : ultimas.vigentes
}

/**
 * Las alertas abiertas, en una etiqueta roja chica junto a «En vivo». Al tocarla se abre el detalle en palabras: qué
 * pasa, desde cuándo, qué hacer y «Ver en la bitácora». Lo que se resuelve sigue unos segundos, sin parpadear.
 */
function Incidentes({ alertas, ot, onVer }: { alertas: Evento[]; ot: EstadoOt | null; onVer(id: number): void }) {
  const visibles = useRetenidas(alertas)
  const [abierto, setAbierto] = useState(false)
  if (visibles.length === 0) return null
  const resueltas = alertas.length === 0
  return (
    <div role="alert" aria-label="Alertas abiertas">
      <Popover opened={abierto} onChange={setAbierto} position="bottom-end" width={360} withArrow shadow="md" withinPortal={false}>
        <Popover.Target>
          <Button
            size="compact-sm"
            color={resueltas ? 'roca' : 'peligro'}
            leftSection={<IconAlertTriangle size={14} />}
            onClick={() => setAbierto((a) => !a)}
            aria-expanded={abierto}
          >
            {visibles.length === 1 ? tituloDe(visibles[0]!) : `${visibles.length} alertas`}
          </Button>
        </Popover.Target>
        <Popover.Dropdown>
          <Stack gap="md">
            {visibles.map((a) => {
              const { texto, ayuda } = queDice(a, ot)
              return (
                <Stack key={a.id} gap={4}>
                  <Text fw={700}>
                    {tituloDe(a)}, desde las {hora(a.ts)}
                  </Text>
                  <Text size="sm">{enPalabras(texto)}</Text>
                  {ayuda && (
                    <Text size="sm" c="roca.7">
                      {ayuda}
                    </Text>
                  )}
                  <Button
                    variant="subtle"
                    size="compact-sm"
                    w="fit-content"
                    onClick={() => {
                      setAbierto(false)
                      onVer(a.id)
                    }}
                  >
                    Ver en la bitácora
                  </Button>
                </Stack>
              )
            })}
          </Stack>
        </Popover.Dropdown>
      </Popover>
    </div>
  )
}

const rotuloDe = (v: Deteccion) => `${NOMBRE_CLASE[v.clase] ?? v.clase} ${Math.round(v.conf * 100)} %`
const enPorciento = (x: number) => `${+(x * 100).toFixed(2)}%`
/** Desde esta certeza la cámara está segura; bajo ella, la caja va en ámbar. */
const CERTEZA_SEGURA = 0.8

/** Lo que la cámara reconoce, dibujado sobre el video. Las cajas vienen de 0 a 1 respecto del cuadro. */
function Cajas({ vistas }: { vistas: Deteccion[] }) {
  return (
    <div className={estilos.cajas} aria-hidden>
      {vistas.map((v, i) => {
        if (v.caja?.length !== 4) return null
        const [x1, y1, x2, y2] = v.caja
        return (
          <div
            key={i}
            className={estilos.caja}
            data-seguro={v.conf >= CERTEZA_SEGURA}
            data-arriba={y1 < 0.08 || undefined}
            style={{ left: enPorciento(x1), top: enPorciento(y1), width: enPorciento(x2 - x1), height: enPorciento(y2 - y1) }}
          >
            <span>{rotuloDe(v)}</span>
          </div>
        )
      })}
    </div>
  )
}

/** En qué paso va, sobre el video: quien mira la cámara sabe qué debería estar viendo. */
function PasoSobreElVideo({ ot }: { ot: EstadoOt }) {
  const total = ot.pasos.length
  const actual = ot.pasos.find((p) => p.id === ot.paso_actual)
  return (
    <div className={estilos.hud}>
      <p className={estilos.hudNum}>{actual ? `Paso ${actual.orden} de ${total}` : 'Pauta completa'}</p>
      <p className={estilos.hudTitulo}>{actual ? actual.titulo : `${total} de ${total} pasos verificados`}</p>
    </div>
  )
}

/**
 * El video que la estación manda al servidor (`/edge/{id}/video.mjpg`), si la OT corre en una.
 * Encima van lo que la cámara reconoce y el paso en curso; el marco y sus esquineros toman el
 * color de la verificación.
 */
function Camara({ edgeId, vistas, ot }: { edgeId: string | null; vistas: Deteccion[]; ot: EstadoOt }) {
  const [video, setVideo] = useState<'esperando' | 'viendo' | 'fallo'>('esperando')
  const viendo = video === 'viendo'
  const mensaje = !edgeId
    ? 'Esta OT no está corriendo en una estación ahora. No hay video en vivo.'
    : video === 'fallo'
      ? `No llega el video de ${edgeId}.`
      : `Esperando el video de ${edgeId}…`
  return (
    <div>
      <section aria-label="Cámara de la estación" className={estilos.marco} data-vacio={!viendo || undefined}>
        <span className={estilos.esq} />
        <span className={estilos.esq} />
        <span className={estilos.esq} />
        <span className={estilos.esq} />
        {!viendo && (
          <p className={estilos.marcoMensaje}>
            <span className={estilos.rotulo}>{mensaje}</span>
          </p>
        )}
        {edgeId && video !== 'fallo' && (
          <img
            src={`${config.API_URL}/edge/${encodeURIComponent(edgeId)}/video.mjpg`}
            alt={`Video en vivo de ${edgeId}`}
            onLoad={() => setVideo('viendo')}
            onError={() => setVideo('fallo')}
          />
        )}
        {edgeId && <Cajas vistas={vistas} />}
        {edgeId && viendo && (
          <div className={estilos.arriba}>
            <span className={estilos.rotulo}>{edgeId}</span>
          </div>
        )}
        {edgeId && <PasoSobreElVideo ot={ot} />}
      </section>
      {edgeId && (
        <p className={estilos.rotulo} style={{ marginTop: 10 }}>
          {vistas.length ? `La cámara ve: ${vistas.map(rotuloDe).join(', ')}` : 'La cámara no reconoce nada ahora.'}
        </p>
      )}
    </div>
  )
}

const QUIEN_LO_DICE: Record<number, string> = { 1: 'el sensor', 2: 'la cámara', 3: 'la cámara' }
const certezaDe = (c: Calificacion) => `${Math.round(c.certeza * 100)} % de certeza`

/**
 * Cómo va lo que Factum verifica, en grande y con el color de su nivel, y por qué dice «Atención»
 * o «Detente»: cada aviso activo, quién lo dice y con cuánta certeza.
 */
function Verificacion({ calificacion }: { calificacion: CalificacionOt | null }) {
  return (
    <section aria-label="Verificación">
      <h3 className={estilos.seccion}>Verificación</h3>
      {calificacion && (
        <div className={estilos.veredicto}>
          <p className={estilos.nivel}>{VERIFICACION[calificacion.nivel].etiqueta}</p>
          {/* Con avisos, cada uno trae su certeza; sin ellos, esta es la de «todo bien». */}
          {calificacion.avisos.length === 0 && <p className={estilos.rotulo}>{certezaDe(calificacion)}</p>}
        </div>
      )}
      {!calificacion || calificacion.avisos.length === 0 ? (
        <p className={estilos.sinAvisos}>Sin avisos activos.</p>
      ) : (
        <ul className={estilos.avisos} aria-label="Avisos activos">
          {calificacion.avisos.map((a, i) => {
            const quien = a.capa ? QUIEN_LO_DICE[a.capa] : null
            return (
              <li key={i} data-nivel={a.nivel}>
                <b>{a.nivel === 'error' ? 'Error' : 'Aviso'}</b>
                <span>{a.motivos.map(enPalabras).join(' · ')}</span>
                <small>{quien ? `Lo dice ${quien}, con ${certezaDe(a)}` : `Con ${certezaDe(a)}`}</small>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

/** Hacia dónde va un sensor numérico: sus últimas lecturas, de la más vieja a la más nueva. */
function Tendencia({ serie, nombre }: { serie: number[]; nombre: string }) {
  const min = Math.min(...serie)
  // Con menos de 2 unidades de diferencia la línea se ve plana: el ruido del sensor no parece un cambio.
  const tramo = Math.max(Math.max(...serie) - min, 2)
  const puntos = serie.map((v, i) => `${((100 * i) / (serie.length - 1)).toFixed(1)},${(28 - (26 * (v - min)) / tramo).toFixed(1)}`).join(' ')
  return (
    <svg viewBox="0 0 100 30" preserveAspectRatio="none" role="img" aria-label={`Últimas lecturas de ${nombre}`} className={estilos.tendencia}>
      <polyline points={puntos} />
    </svg>
  )
}

/**
 * Las lecturas de la estación, una celda por sensor: los de la pauta de esta OT y los que están
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
    <Desplegable titulo="Sensores" dato={fichas.length ? String(fichas.length) : undefined}>
      {fichas.length === 0 ? (
        <p className={estilos.sinAvisos}>Todavía no llega ninguna lectura de la estación.</p>
      ) : (
        <ul className={estilos.sensores} aria-label="Lecturas de la estación">
          {fichas.map((id) => {
            const l = sensores[id]
            const esperado = espera?.id === id
            // Solo cuenta una lectura de ahora: la guardada puede ser de otra OT o de hace horas.
            const calza = esperado && !!l?.enVivo && l.valor === espera.espera
            const guardada = l && !l.enVivo
            return (
              <li key={id} className={estilos.sensor} data-espera={esperado ? (calza ? 'calza' : 'falta') : undefined} data-viejo={!l || guardada || undefined}>
                <p className={estilos.rotulo}>{nombreDe(id)}</p>
                <div className={estilos.sensorValor}>
                  {esperado && (calza ? <IconCheck size={24} aria-hidden /> : <IconX size={24} aria-hidden />)}
                  <span>{l ? (UNIDAD[id] ? `${l.valor} ${UNIDAD[id]}` : l.valor) : 'Sin dato'}</span>
                </div>
                {l && l.serie.length > 1 && <Tendencia serie={l.serie} nombre={nombreDe(id)} />}
                {esperado && (
                  <p className={estilos.sensorNota}>
                    El paso {actual!.orden} espera «{espera.espera}»
                  </p>
                )}
                {guardada && <p className={estilos.sensorNota}>Última lectura guardada</p>}
              </li>
            )
          })}
        </ul>
      )}
    </Desplegable>
  )
}

/** Una sección que se pliega: el título es el botón, con el dato a la derecha. Para lo que se consulta, no lo que se vigila. */
function Desplegable({ titulo, dato, children }: { titulo: string; dato?: string; children: ReactNode }) {
  const [abierto, setAbierto] = useState(false)
  return (
    <section aria-label={titulo}>
      <UnstyledButton onClick={() => setAbierto((a) => !a)} aria-expanded={abierto} w="100%">
        <h3 className={estilos.seccion}>
          <IconChevronRight size={16} aria-hidden style={{ transform: abierto ? 'rotate(90deg)' : 'none', transition: 'transform 200ms ease' }} />
          {titulo}
          {dato && <span className={estilos.dato}>{dato}</span>}
        </h3>
      </UnstyledButton>
      <Collapse expanded={abierto} transitionDuration={200} keepMounted keepMountedMode="display-none">
        {children}
      </Collapse>
    </section>
  )
}

const ESTADO_PASO: Record<PasoEstado['estado'], string> = { verificado: 'Verificado', en_conflicto: 'En conflicto', no_verificado: 'Pendiente' }

/** Los pasos de la pauta, numerados: el verificado en lima, el que está en curso en hielo. */
function Pasos({ ot, bitacora }: { ot: EstadoOt; bitacora: Evento[] }) {
  const nombreDe = useNombres()
  const cerrados = ot.pasos.filter((p) => p.estado === 'verificado').length
  return (
    <section>
      <h3 className={estilos.seccion}>
        Pasos
        <span className={estilos.dato}>
          {cerrados} de {ot.pasos.length}
        </span>
      </h3>
      <ol className={estilos.pasos} aria-label="Pasos de la OT">
        {ot.pasos.map((p) => {
          const actual = p.id === ot.paso_actual
          const por = p.estado === 'verificado' ? cerradoPor(bitacora, p.id) : null
          return (
            // Rojo solo si el conflicto lo dice el sensor (capa 1); la duda de la cámara va en ámbar.
            <li key={p.id} data-estado={p.estado} data-capa={p.capa ?? undefined} data-actual={actual || undefined}>
              <span className={estilos.num}>{p.estado === 'verificado' ? <IconCheck size={18} aria-label="Verificado" /> : String(p.orden).padStart(2, '0')}</span>
              <div>
                <b>{p.titulo}</b>
                {por && <small>Confirmado por {nombreDe(por)}</small>}
              </div>
              <span className={estilos.estado}>{actual && p.estado === 'no_verificado' ? 'En curso' : ESTADO_PASO[p.estado]}</span>
            </li>
          )
        })}
      </ol>
    </section>
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

function colorDe(ev: Evento): string | null {
  if (ev.tipo === 'alerta_resuelta' || (ev.tipo === 'veredicto' && ev.estado === 'verificado')) return 'verificado'
  if (ev.calificacion?.nivel === 'error' || ev.tipo === 'alerta') return 'peligro'
  if (ev.calificacion?.nivel === 'warning') return 'precaucion'
  return null
}

/** Todo lo que pasó en la OT, lo último arriba. Una alerta abierta se marca; la elegida, más. */
function Bitacora({ bitacora, ot, abiertas, elegido }: { bitacora: Evento[]; ot: EstadoOt | null; abiertas: Set<number>; elegido: number | null }) {
  const nombreDe = useNombres()
  const eventos = [...bitacora].sort((a, b) => b.id - a.id)
  const orden = (pasoId: string | null) => ot?.pasos.find((p) => p.id === pasoId)?.orden
  return (
    <section>
      <h3 className={estilos.seccion}>
        Bitácora
        <span className={estilos.dato}>{eventos.length} eventos</span>
      </h3>
      <ScrollArea.Autosize mah={560} type="auto" offsetScrollbars>
        <ol className={estilos.bitacora} aria-label="Bitácora de la OT">
          {eventos.map((ev) => {
            const color = colorDe(ev)
            const abierta = abiertas.has(ev.id)
            const n = orden(ev.paso_id)
            return (
              <li
                key={ev.id}
                id={`bitacora-${ev.id}`}
                data-abierta={abierta || undefined}
                data-elegido={elegido === ev.id || undefined}
                style={color ? colores('evento', color) : undefined}
              >
                <time dateTime={ev.ts}>{hora(ev.ts)}</time>
                <b>
                  {etiquetaDe(ev)}
                  {n ? `, paso ${n}` : ''}
                  {abierta ? ' (abierta)' : ''}
                </b>
                <p>{enPalabras(ev.detalle)}</p>
                <small>{ev.actor === 'sistema' ? 'Sistema' : nombreDe(ev.actor)}</small>
              </li>
            )
          })}
        </ol>
      </ScrollArea.Autosize>
    </section>
  )
}

/**
 * Las propuestas de mejora que esta OT alimenta, que se muestran cuando la OT termina: mientras
 * corre, lo que importa es la alerta. Si esta OT fue la segunda en desviarse en el mismo paso,
 * la propuesta nació con ella y aparece sola al completarse, sin recargar. Van en lila.
 */
function PropuestasDeMejora({ propuestas, nuevas }: { propuestas: Mejora[]; nuevas: ReadonlySet<string> }) {
  if (propuestas.length === 0) return null
  return (
    <Stack gap="sm" role="status" aria-label="Propuesta de mejora">
      {propuestas.map((p) => (
        <div key={p.id} className={estilos.franja} style={colores('franja', 'mejora')}>
          <div>
            <strong>{nuevas.has(p.id) ? 'Con esta OT nació una propuesta para mejorar la pauta' : 'Esta OT alimenta una propuesta para mejorar la pauta'}</strong>
            <p>
              «{p.titulo}» se desvió en {p.ots_con_senal} de {p.ejecuciones} OT de la versión {p.version}.
            </p>
            <small>{p.sugerencia}</small>
          </div>
          <Button component={Link} to={`/supervisor/mejoras#${encodeURIComponent(p.id)}`} color="mejora" style={{ flexShrink: 0 }}>
            Revisar la propuesta
          </Button>
        </div>
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
            <Title order={2} className={estilos.titular}>
              Esta OT no está en tu empresa
            </Title>
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
  // La propuesta es parte del cierre: no se muestra hasta que la OT termina, aunque el servidor ya la cuente.
  const propuestas = ot?.completa
    ? (mejoras ?? []).filter((p) => p.estado === 'abierta' && p.pauta === v.detalle?.pauta && p.version === v.detalle.version && conSenal.has(p.paso))
    : []
  // El estado sigue a la OT en vivo: el resumen solo se vuelve a pedir con una asignación o un relevo.
  const estado = !v.detalle ? null : ot?.completa ? 'completa' : enEstacion && estadoDe(v.detalle) === 'asignada' ? 'en_ejecucion' : estadoDe(v.detalle)

  return (
    <>
      <Encabezado usuario={usuario} seccion="Supervisión" />
      {s.conexion === 'reconectando' && <FranjaSinConexion />}
      <Pagina>
        <Stack gap="lg" className={estilos.vista} data-nivel={calificacion?.nivel ?? 'ok'}>
          <Stack gap="md">
            <div className={estilos.cabecera}>
              <div>
                <Group gap={6} wrap="nowrap">
                  <ActionIcon component={Link} to="/supervisor" variant="subtle" color="accion" size="sm" aria-label="Volver a la lista de OT">
                    <IconArrowLeft size={18} />
                  </ActionIcon>
                  <Title order={2} className={estilos.ot} m={0}>
                    {otId.toUpperCase()}
                  </Title>
                </Group>
                <p className={estilos.titular}>{nombre}</p>
              </div>
              <div className={estilos.cabeceraDerecha}>
                <Group gap="sm" wrap="nowrap">
                  <Incidentes
                    alertas={s.alertas}
                    ot={ot}
                    onVer={(id) => {
                      setElegida('vivo')
                      setElegido(id)
                    }}
                  />
                </Group>
                <SegmentedControl
                  aria-label="Qué ver de la OT"
                  value={vista}
                  onChange={(valor) => setElegida(valor as Vista)}
                  data={[
                    { value: 'vivo', label: 'Ejecución' },
                    { value: 'reporte', label: 'Reporte' },
                  ]}
                />
              </div>
            </div>
          </Stack>

          {/* Primero que la OT terminó, después lo que dejó para la pauta. */}
          {ot?.completa && vista === 'vivo' && (
            <div className={estilos.franja} style={colores('franja', 'verificado')}>
              <strong>OT completa: los {ot.pasos.length} pasos quedaron verificados.</strong>
              <Button color="verificado" onClick={() => setElegida('reporte')} style={{ flexShrink: 0 }}>
                Ver el reporte
              </Button>
            </div>
          )}
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
              {/* Como el monitor: a un lado lo que se ve y cómo va; al otro, sensores y pasos; abajo, todo lo que pasó. */}
              <div className={estilos.rejilla}>
                <div className={estilos.col}>
                  <Camara edgeId={enEstacion} vistas={v.vistas} ot={ot} />
                  <Group justify="space-between" gap="sm">
                    <EnVivo conexion={s.conexion} />
                    {config.VOZ_EN === 'supervisor' && <AudioDeLosAvisos />}
                  </Group>
                  <Verificacion calificacion={calificacion} />
                </div>
                <div className={estilos.col}>
                  <Pasos ot={ot} bitacora={s.bitacora} />
                  {/* La ficha: quién la ejecuta, dónde y en qué equipo. Se consulta, no se vigila: va plegada. */}
                  <Desplegable titulo="Detalles" dato={v.detalle?.operador ? nombreDe(v.detalle.operador) : undefined}>
                  <dl className={estilos.celdas}>
                    <div className={estilos.celda} role="group" aria-label="Operador">
                      <dt className={estilos.rotulo}>Operador</dt>
                      <dd>{v.detalle ? (v.detalle.operador ? nombreDe(v.detalle.operador) : 'Sin operador') : '…'}</dd>
                    </div>
                    <div className={estilos.celda}>
                      <dt className={estilos.rotulo}>Estación</dt>
                      <dd>{enEstacion && v.sesion ? `En la estación ${enEstacion} desde las ${horaCorta(v.sesion.desde)}` : 'Sin estación'}</dd>
                    </div>
                    <div className={estilos.celda} data-ancho>
                      <dt className={estilos.rotulo}>Equipo</dt>
                      <dd>{ot ? ot.equipo : '…'}</dd>
                    </div>
                    <div className={estilos.celda}>
                      <dt className={estilos.rotulo}>Estado</dt>
                      <dd>{estado && <EstadoBadge estado={estado} />}</dd>
                    </div>
                  </dl>
                  </Desplegable>
                  {enEstacion && <Sensores sensores={v.sensores} ot={ot} pauta={v.pauta} />}
                </div>
              </div>
              <Bitacora bitacora={s.bitacora} ot={ot} abiertas={abiertas} elegido={elegido} />
            </>
          )}
        </Stack>
      </Pagina>
    </>
  )
}
