import type { MensajeStream, Snapshot } from '../api/tipos'
import type { Conexion } from './estado'
import { conectarStream } from './stream'

class FakeWebSocket {
  static instancias: FakeWebSocket[] = []
  url: string
  onopen: ((e: Event) => void) | null = null
  onmessage: ((e: { data: string }) => void) | null = null
  onclose: ((e: { code: number }) => void) | null = null
  cerradoPorCliente = false

  constructor(url: string) {
    this.url = url
    FakeWebSocket.instancias.push(this)
  }
  open() {
    this.onopen?.(new Event('open'))
  }
  recibir(obj: unknown) {
    this.onmessage?.({ data: JSON.stringify(obj) })
  }
  cerrar(code: number) {
    this.onclose?.({ code })
  }
  close() {
    this.cerradoPorCliente = true
    this.onclose?.({ code: 1005 })
  }
}

const snapshot = { tipo: 'snapshot', bitacora: [] } as unknown as Snapshot
const ultima = () => FakeWebSocket.instancias.at(-1)!

function conectar(desde: () => number = () => 0) {
  const mensajes: Array<[MensajeStream, boolean]> = []
  const conexiones: Conexion[] = []
  const cerrar = conectarStream((d) => `wss://x/ot/ot-12/stream?desde=${d}`, desde, {
    mensaje: (m, inicial) => mensajes.push([m, inicial]),
    conexion: (c) => conexiones.push(c),
  }, { WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket })
  return { mensajes, conexiones, cerrar }
}

beforeEach(() => {
  FakeWebSocket.instancias = []
  vi.useFakeTimers()
})
afterEach(() => vi.useRealTimers())

it('reconnects with the latest desde and marks the second snapshot as not inicial', () => {
  let desde = 0
  const { mensajes, conexiones } = conectar(() => desde)
  ultima().open()
  ultima().recibir(snapshot)
  desde = 12
  ultima().cerrar(1006)
  expect(conexiones.at(-1)).toBe('reconectando')
  vi.advanceTimersByTime(1000)
  expect(FakeWebSocket.instancias).toHaveLength(2)
  expect(ultima().url).toBe('wss://x/ot/ot-12/stream?desde=12')
  ultima().open()
  ultima().recibir(snapshot)
  expect(mensajes.map(([, inicial]) => inicial)).toEqual([true, false])
})

it('passes every later message through as not inicial', () => {
  const { mensajes } = conectar()
  ultima().open()
  ultima().recibir(snapshot)
  ultima().recibir({ tipo: 'evento', evento: { id: 1 } })
  expect(mensajes.map(([m, inicial]) => [m.tipo, inicial])).toEqual([['snapshot', true], ['evento', false]])
})

it('backs off 1s, 2s, 4s, 8s, 8s', () => {
  conectar()
  const esperas: number[] = []
  for (let i = 0; i < 5; i++) {
    const antes = FakeWebSocket.instancias.length
    ultima().cerrar(1006)
    let ms = 0
    while (FakeWebSocket.instancias.length === antes) {
      vi.advanceTimersByTime(500)
      ms += 500
    }
    esperas.push(ms)
  }
  expect(esperas).toEqual([1000, 2000, 4000, 8000, 8000])
})

it('a successful connection resets the backoff', () => {
  conectar()
  ultima().cerrar(1006)
  vi.advanceTimersByTime(1000)
  ultima().cerrar(1006)
  vi.advanceTimersByTime(2000)
  ultima().open()
  ultima().cerrar(1006)
  vi.advanceTimersByTime(1000)
  expect(FakeWebSocket.instancias).toHaveLength(4)
})

it('stops on 4404', () => {
  const { conexiones } = conectar()
  ultima().cerrar(4404)
  expect(conexiones.at(-1)).toBe('no_existe')
  vi.advanceTimersByTime(60_000)
  expect(FakeWebSocket.instancias).toHaveLength(1)
})

it('stops after cerrar()', () => {
  const { cerrar } = conectar()
  ultima().open()
  cerrar()
  expect(FakeWebSocket.instancias[0].cerradoPorCliente).toBe(true)
  vi.advanceTimersByTime(60_000)
  expect(FakeWebSocket.instancias).toHaveLength(1)
})

it('cerrar() during a backoff wait cancels the retry', () => {
  const { cerrar } = conectar()
  ultima().cerrar(1006)
  cerrar()
  vi.advanceTimersByTime(60_000)
  expect(FakeWebSocket.instancias).toHaveLength(1)
})
