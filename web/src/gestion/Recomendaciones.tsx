import {
  Accordion,
  ActionIcon,
  Alert,
  Anchor,
  Button,
  Group,
  List,
  Paper,
  Stack,
  Text,
  Tooltip,
} from "@mantine/core";
import { IconBulb, IconCheck, IconInfoCircle } from "@tabler/icons-react";
import { useState } from "react";
import { Link } from "react-router";
import { api } from "../api/cliente";
import type { ResumenMejoras } from "../api/tipos";
import { mensajeDe } from "./useOts";

/** Un cambio en una línea; el porqué, en el ícono de información, al pasar el cursor. */
function Linea({
  que,
  porque,
  tenue = false,
}: {
  que: string;
  porque: string | null;
  tenue?: boolean;
}) {
  return (
    <List.Item>
      <Group gap={6} wrap="nowrap" align="center">
        <Text size="sm" fw={tenue ? 400 : 600} c={tenue ? "dimmed" : undefined}>
          {que}
        </Text>
        {porque && (
          <Tooltip label={porque} multiline w={320} withArrow openDelay={100}>
            <ActionIcon
              variant="subtle"
              color="roca"
              size="sm"
              aria-label={porque}
            >
              <IconInfoCircle size={16} />
            </ActionIcon>
          </Tooltip>
        )}
      </Group>
    </List.Item>
  );
}

/** Una pauta, desplegable: qué cambia (y qué no), con el porqué a mano, y un solo botón. */
function Propuesta({
  r,
  onAplicada,
  onPosponer,
}: {
  r: ResumenMejoras;
  onAplicada: (texto: string) => void;
  onPosponer: () => void;
}) {
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const n = r.cambios.length;

  const aplicar = async () => {
    setEnviando(true);
    setError(null);
    try {
      const a = await api.aplicarMejoras(r.pauta);
      onAplicada(
        a.version
          ? `Listo. Factum armó la versión ${a.version.version} de «${r.nombre}»; el equipo la revisa y la aprueba antes de que llegue a las OT.`
          : `Quedó en manos de Factum. ${a.aviso ?? ""}`.trim(),
      );
    } catch (e) {
      setError(mensajeDe(e));
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Accordion.Item value={r.pauta} aria-label={`Mejoras para ${r.nombre}`}>
      <Accordion.Control>
        <Group gap="sm" wrap="nowrap" justify="space-between" pr="sm">
          <Text fw={700} truncate>
            {r.nombre}
          </Text>
          <Text size="sm" c="dimmed" style={{ flexShrink: 0 }}>
            {n
              ? `versión ${r.version} · ${n === 1 ? "1 cambio" : `${n} cambios`}`
              : "sin cambios a la pauta"}
          </Text>
        </Group>
      </Accordion.Control>
      <Accordion.Panel>
        <Stack gap="sm">
          {n > 0 && (
            <List spacing={6}>
              {r.cambios.map((c) => (
                <Linea
                  key={`${c.propuesta}:${c.que}`}
                  que={c.que}
                  porque={c.porque}
                />
              ))}
            </List>
          )}
          {r.sin_cambio.length > 0 && (
            <List spacing={6}>
              {r.sin_cambio.map((c) => (
                <Linea
                  key={c.propuesta}
                  que={`No cambia: ${c.que}`}
                  porque={c.por_que_no}
                  tenue
                />
              ))}
            </List>
          )}
          {error && (
            <Text size="sm" c="peligro" role="alert">
              {error}
            </Text>
          )}
          <Group gap="sm">
            <Button
              loading={enviando}
              leftSection={<IconCheck size={18} />}
              onClick={() => void aplicar()}
            >
              {n === 0
                ? "Entendido"
                : n === 1
                  ? "Aplicar el cambio"
                  : `Aplicar los ${n} cambios`}
            </Button>
            <Button variant="subtle" onClick={onPosponer}>
              Ahora no
            </Button>
            <Anchor
              component={Link}
              to="/supervisor/mejoras"
              size="sm"
              ml="auto"
            >
              Ver el detalle
            </Anchor>
          </Group>
        </Stack>
      </Accordion.Panel>
    </Accordion.Item>
  );
}

/** Lo que Factum propone cambiar en las pautas, resumido: una tarjeta por pauta, con un solo toque para aplicarlo. */
export function Recomendaciones({
  recomendaciones,
  quitar,
}: {
  recomendaciones: ResumenMejoras[];
  quitar: (pauta: string) => void;
}) {
  const [pospuestas, setPospuestas] = useState<Set<string>>(new Set());
  const [hechos, setHechos] = useState<{ pauta: string; texto: string }[]>([]);
  const visibles = recomendaciones.filter((r) => !pospuestas.has(r.pauta));
  if (visibles.length === 0 && hechos.length === 0) return null;
  return (
    <Stack gap="sm" role="region" aria-label="Recomendaciones de Factum">
      {hechos.map((h) => (
        <Alert
          key={h.pauta}
          color="verificado"
          variant="light"
          icon={<IconCheck size={18} />}
          withCloseButton
          onClose={() =>
            setHechos((hs) => hs.filter((x) => x.pauta !== h.pauta))
          }
          closeButtonLabel="Cerrar aviso"
        >
          {h.texto}
        </Alert>
      ))}
      {visibles.length > 0 && (
        <Paper
          withBorder
          radius="md"
          p="md"
          style={{ borderLeft: "4px solid var(--mantine-color-precaucion-6)" }}
        >
          <Group gap="sm" wrap="nowrap" mb="xs">
            <IconBulb
              size={22}
              color="var(--mantine-color-precaucion-5)"
              style={{ flexShrink: 0 }}
            />
            <Text fw={800}>
              {visibles.length === 1
                ? "Factum propone mejorar una pauta"
                : `Factum propone mejorar ${visibles.length} pautas`}
            </Text>
          </Group>
          <Accordion
            variant="contained"
            radius="sm"
           
            chevronPosition="left"
          >
            {visibles.map((r) => (
              <Propuesta
                key={r.pauta}
                r={r}
                onAplicada={(texto) => {
                  quitar(r.pauta);
                  setHechos((hs) => [
                    ...hs.filter((x) => x.pauta !== r.pauta),
                    { pauta: r.pauta, texto },
                  ]);
                }}
                onPosponer={() => setPospuestas((s) => new Set(s).add(r.pauta))}
              />
            ))}
          </Accordion>
        </Paper>
      )}
    </Stack>
  );
}
