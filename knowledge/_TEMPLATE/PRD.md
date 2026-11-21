# Plantilla — PRD

> **Qué es.** El razonamiento de un frente del producto: quién lo usa, qué le duele hoy, qué debe poder hacer después y cómo se prueba. **No dicta el código**: nada de código final, esquemas ni pantallas terminadas. Vive en `knowledge/projects/<slug>/PRD.md`.
>
> **Cómo se escribe.**
> - No se inventan usuarios, datos ni reglas. Lo que no está confirmado se declara como decisión abierta, con su estado (`Confirmada`, `Candidata a validar` o `Brecha`, ver [CONTRIBUTING](../CONTRIBUTING.md)).
> - **Describe el producto, no el avance.** Nada de casillas ni porcentajes: el estado vive solo en [SEGUIMIENTO](../roadmap/SEGUIMIENTO.md).
> - Una decisión estructural que aparece al escribirlo va a un ADR ([plantilla](./ADR.md)); el PRD la enlaza.
> - Cada capacidad tiene un solo hogar. Si dos PRD la describen, uno la tiene y el otro enlaza.
> - Las reglas de negocio viven en [LOGICA](../architecture/LOGICA.md). El PRD las cita, no las repite.

Todo lo que va entre `---` se copia tal cual.

---

# PRD — <Frente>

> **Dueño de la decisión:** <una persona> · **Se consulta a:** <quién y de qué materia> · **Alcance:** <una frase>
>
> **Estado →** [SEGUIMIENTO](../../roadmap/SEGUIMIENTO.md). Este documento no lleva avance.

## 1. Resumen

**Hoy:** <qué pasa hoy y qué cuesta>.

**Después:** <qué podrá lograr el usuario y por qué es mejor>.

## 2. Historia

**Antes.** <Actor>, en <momento concreto>, intenta <objetivo>. Hoy <fricción o riesgo>.

**Después.** <Mismo actor>, en ese momento, puede <resultado observable> sin <lo que se elimina>.

## 3. Objetivos y no-objetivos

- **O1 —** <resultado verificable>
- **NO1 —** <límite explícito que frena el «ya que estamos»>

## 4. Flujo: hoy → después

```text
HOY
<actor> → <paso actual> → <fricción>

DESPUÉS
<actor> → <disparador> → <paso nuevo> → <resultado observable>
```

## 5. Datos y reglas

| Entidad o dato | Cambio | Regla o fuente |
| --- | --- | --- |
| `<entidad>` | <qué se crea, lee o cambia> | <LOGICA, ADR o fuente> |

## 6. Contrato de comportamiento

```text
CUANDO <disparador>
  SI <guarda que lo detiene>
    NO <resultado>
  ENTONCES <resultado observable>
```

## 7. Alcance

**Entra:** <capacidades>.

**No entra:** <exclusiones explícitas>.

## 8. Criterios de aceptación

Dado / cuando / entonces, desde el actor, para que un test los copie. Sin casillas.

- **CA1 —** **Dado** <estado>, **cuando** <acción>, **entonces** <resultado>.

## 9. Riesgos y decisiones abiertas

| Tema | Impacto | Qué falta decidir | Se consulta a | Decide |
| --- | --- | --- | --- | --- |
| `<tema>` | alto · medio · bajo | <pregunta que se responde con una frase> | <quién> | <dueño> |

## Fuentes

- <ADR, reunión o documento de origen>
