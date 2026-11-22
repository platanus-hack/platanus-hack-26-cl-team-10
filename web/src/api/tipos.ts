// La forma de la API desplegada (https://34-176-44-192.sslip.io/agente).
// Verificado contra app/servicios.py (snapshot, evento_dict) y app/cerebro.py (estado_de_ot).
// La gestión (operador, estado_general, asignar) ya está en el back desplegado.

export type EstadoPasoApi = 'no_verificado' | 'verificado' | 'en_conflicto'
export type Nivel = 'ok' | 'warning' | 'error'

export type Calificacion = { nivel: Nivel; certeza: number; capa: number | null; motivos: string[] }
export type CalificacionOt = Calificacion & { avisos: Calificacion[] }

export type TipoEvento =
  | 'ot_abierta'
  | 'ot_asignada'
  | 'paso_iniciado'
  | 'declaracion'
  | 'veredicto'
  | 'alerta'
  | 'alerta_resuelta'
  | 'relevo_entregado'
  | 'relevo_recibido'
  | 'propuesta_pauta'

export type Evento = {
  id: number
  ot_id: string
  tipo: TipoEvento
  ts: string
  actor: string
  detalle: string
  paso_id: string | null
  estado: EstadoPasoApi | null
  capa: number | null
  declarado: string | null
  evidencia: Record<string, unknown> | null
  calificacion: Calificacion | null
}

export type PasoEstado = {
  id: string
  orden: number
  titulo: string
  estado: EstadoPasoApi
  control_critico: boolean
  capa: number | null
  evidencia: Record<string, unknown> | null
  detalle: string | null
}

export type EstadoOt = {
  pauta: string
  equipo: string
  paso_actual: string | null
  completa: boolean
  pasos: PasoEstado[]
  verificados: string[]
  en_conflicto: string[]
  pendientes: string[]
}

export type TipoEvidencia = 'sensor' | 'camara' | 'confirmacion'

export type PasoPauta = {
  id: string
  orden: number
  titulo: string
  instruccion: string
  tipo_evidencia: TipoEvidencia
  capa_minima: number
  control_critico: boolean
  pregunta_visual: string | null
  sensor: { id: string; espera: string } | null
  /** La cámara del edge lo cierra sola cuando su modelo ve (o deja de ver) esta clase. */
  deteccion?: { clase: string; presente: boolean } | null
}

export type Pauta = { id: string; nombre: string; version: number; equipo: string; pasos: PasoPauta[] }

/** Un ítem de `GET /cliente/pautas`, lo que la empresa puede pedir: `pasos` es cuántos tiene. */
export type PautaResumen = {
  id: string
  nombre: string
  version: number
  equipo: string
  pasos: number
  protocolos: { id: string; nombre: string }[]
}

export type Rol = 'supervisor' | 'operador'

/** Quién entró (`GET /yo`): su `id` es el actor que queda en la bitácora. */
export type Persona = {
  id: string
  nombre: string
  usuario: string
  rol: Rol
  cliente: { id: string; nombre: string; industria: string }
}

/** `GET /cliente/personas`: lo que cualquier persona de la empresa sabe de las demás. */
export type Companero = { id: string; nombre: string; rol: Rol }

/** `POST /auth/entrar`: el token dura 12 horas y se manda como `Authorization: Bearer`. */
export type Entrada = { token: string; expira: string; persona: Persona }

/** `POST /cliente/ots`: la OT nueva, de la última versión aprobada de la pauta. */
export type OtPedida = { ot: string; pauta: string; version: number; nombre: string; cliente: string }

export type EstadoGeneral = 'sin_asignar' | 'asignada' | 'en_ejecucion' | 'entregada' | 'completa'

export type OtResumen = {
  ot: string
  pauta: string
  version: number
  equipo: string
  abierta_en: string
  paso_actual: string | null
  completa: boolean
  operador?: string | null
  estado_general?: EstadoGeneral
  /** Quién entregó el turno, mientras la OT sigue `entregada`. */
  entregada_por?: string | null
  /** Pasos verificados (por su evidencia o confirmados por una persona) de `total`. */
  cerrados?: number
  total?: number
  /** Todo bien, atención o detente: `GET /cliente/ots` la trae en cada OT. */
  calificacion?: CalificacionOt
}

/** `GET /cliente/ots/{id}`: el resumen con su calificación (todo bien, atención o detente). */
export type OtDetalle = OtResumen & { calificacion: CalificacionOt }

/** Qué OT ejecuta una estación (edge), con qué operario y desde cuándo. */
export type Sesion = { edge_id: string; ot_id: string; operario: string; desde: string }

export type Snapshot = {
  tipo: 'snapshot'
  ot: string
  estado: EstadoOt
  calificacion: CalificacionOt
  alertas_activas: Evento[]
  sesion: Sesion | null
  video: unknown
  sensores: Record<string, string>
  bitacora: Evento[]
}

export type MensajeStream =
  | Snapshot
  | { tipo: 'lectura'; edge_id: string; sensor_id: string; valor: string; ts: string }
  | { tipo: 'evento'; evento: Evento }
  | { tipo: 'calificacion_ot'; calificacion: CalificacionOt }
  | { tipo: 'sesion'; sesion: Sesion; video: unknown }
  | { tipo: 'detecciones'; edge_id: string; modelo?: string; ts: number; objetos: Deteccion[] }

export type Deteccion = { clase: string; conf: number; caja?: number[] }

export type RespuestaDeclarar = {
  paso: string
  estado: EstadoPasoApi
  capa: number | null
  detalle: string
  interrumpe: boolean
  evidencia?: Record<string, unknown> | null
  calificacion?: Calificacion | null
  calificacion_ot?: CalificacionOt
}

/** POST /ot/{id}/pasos/{paso}/confirmar: una persona cierra el paso en curso aunque la evidencia no lo muestre. */
export type RespuestaConfirmar = RespuestaDeclarar

/** Si un paso se desvía más que el resto de su pauta (app/recurrencia.py). */
export type Recurrencia = {
  ots_con_senal: number
  ots: number
  tasa: number | null
  tasa_del_resto: number
  p_valor: number
  recurrente: boolean
}

export type EstadoMejora = 'abierta' | 'aceptada' | 'descartada' | 'aplicada' | 'superada'

/**
 * Una propuesta para mejorar un paso de una pauta (`GET /cliente/mejoras`, app/mejora.py). `detectada` dice cuándo
 * y en qué OT Factum la avisó: solo las recurrentes se avisan. Cuenta OT y operarios distintos, nunca nombra a nadie.
 */
export type Mejora = {
  id: string
  pauta: string
  nombre: string
  version: number
  paso: string
  titulo: string
  control_critico: boolean
  ejecuciones: number
  ots_con_senal: number
  operarios_distintos: number
  senales: Record<string, number>
  motivo: string
  sugerencia: string
  recurrencia: Recurrencia | null
  detectada: { ot: string; evento: number | null; ts: string } | null
  estado: EstadoMejora
}
