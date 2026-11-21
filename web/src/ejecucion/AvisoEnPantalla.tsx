import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { IconAlertTriangle, IconVolume } from '@tabler/icons-react'
import type { EstadoOt, Evento } from '../api/tipos'
import { queDice, tituloDe } from './alertas'
import { textoParaVoz, tipoDeAlerta } from './estado'

/** El paso del que habla el aviso, para llevar al operario hasta él al cerrarlo. */
function pasoDe(ev: Evento): string | null {
  const id = tipoDeAlerta(ev) === 'orden' ? ev.evidencia?.pendiente : tipoDeAlerta(ev) === 'control' ? ev.evidencia?.paso : ev.paso_id
  return typeof id === 'string' ? id : null
}

type Props = {
  evento: Evento | null
  ot: EstadoOt | null
  /** Vuelve a decir el aviso; el toque también desbloquea el audio si el navegador lo frenó. */
  onEscuchar(texto: string): void
  onEntendido(id: number): void
}

/**
 * Lo que suena, también en grande: el operario con guantes y ruido de planta puede no oírlo, y
 * en el celular el banner queda fuera de la vista si bajó por la lista. Dice la misma frase que la
 * voz; al cerrarlo, la pantalla va al paso afectado, donde está lo que hay que hacer.
 */
export function AvisoEnPantalla({ evento, ot, onEscuchar, onEntendido }: Props) {
  const texto = evento ? textoParaVoz(evento, ot) : ''
  const ayuda = evento?.tipo === 'alerta' ? queDice(evento, ot).ayuda : null

  const entendido = () => {
    if (!evento) return
    onEntendido(evento.id)
    const paso = pasoDe(evento)
    if (paso) document.getElementById(`paso-${paso}`)?.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  }

  return (
    <Modal
      opened={evento !== null}
      onClose={entendido}
      centered
      withCloseButton={false}
      closeOnClickOutside={false}
      radius="md"
      padding="lg"
      title={
        evento && (
          <Group gap={8} wrap="nowrap">
            <IconAlertTriangle size={28} color="white" aria-hidden />
            <span>{tituloDe(evento)}</span>
          </Group>
        )
      }
      styles={{
        header: { background: 'var(--mantine-color-peligro-6)', color: 'white' },
        title: { fontWeight: 900, fontSize: 'var(--mantine-font-size-xl)' },
      }}
    >
      <Stack gap="md" pt="md">
        <Text fw={700} size="xl" lh={1.3}>
          {texto}
        </Text>
        {ayuda && <Text c="roca.7">{ayuda}</Text>}
        <Button size="xl" color="accion" fullWidth onClick={entendido} data-autofocus>
          Entendido
        </Button>
        <Button size="lg" variant="default" fullWidth leftSection={<IconVolume size={20} />} onClick={() => onEscuchar(texto)}>
          Escuchar de nuevo
        </Button>
      </Stack>
    </Modal>
  )
}
