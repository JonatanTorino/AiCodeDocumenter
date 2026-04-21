# Prompt 01 — Identificar grupos funcionales

**Rol:** arquitecto de soluciones D365 F&O con experiencia en ingeniería inversa y nomenclatura de código X++ (Best Practices de Microsoft).

**Objetivo:** analizar los nombres de clase del inventario y proponer **candidatos a grupo funcional** basados en patrones de nomenclatura y clustering estructural.

---

## Input

- `inventory.csv` ya cargado en contexto. Columnas relevantes: `file, class, prefix`.
- `exclusion-list.md` del plugin para filtrar ruido antes del análisis.
- `product_name` — el nombre del módulo (ej: "License", "Subscription").
- Opcionalmente: documentos de alcance o manuales que reforzarán nombres.

---

## Procedimiento

### 1. Filtrar ruido

Descartá las filas del inventario cuya `class` aparezca en `exclusion-list.md`. Estas NO participan del análisis.

### 2. Detectar prefijo(s) dominante(s)

La columna `prefix` trae los primeros caracteres del nombre de clase (típicamente 3 — ej: `Axn`, `Axx`, `Cus`).

- Si hay **un prefijo dominante** (>80% de las clases): lo fijás como prefijo del proyecto.
- Si hay **varios prefijos**: listalos. Probablemente hay un proyecto principal + integraciones externas o extensiones.

### 3. Detectar infijos funcionales

El infijo es lo que viene **después** del prefijo y **antes** del nombre específico. Ejemplos:

| Clase | Prefijo | Infijo | Nombre específico |
|-------|---------|--------|-------------------|
| `AxnLicSubscriptionService` | `Axn` | `Lic` | `SubscriptionService` |
| `AxnLicInvoiceLine` | `Axn` | `Lic` | `InvoiceLine` |
| `AxnLicSubscription` | `Axn` | `Lic` | `Subscription` |

Acá `Lic` es un infijo de producto (Licencias). Si todas las clases comparten un único infijo (como en un plugin monolítico), el infijo no sirve para discriminar — en ese caso usá el **nombre específico** como base del agrupamiento.

### 4. Clustering semántico

Agrupá las clases por **similitud del nombre específico** y por **dominio de negocio**. Ejemplos de grupos válidos:

- **Gestión de Suscripciones** — `Subscription`, `SubscriptionService`, `SubscriptionRenewal`, `SubscriptionPlan`
- **Facturación** — `Invoice`, `InvoiceLine`, `InvoiceJournal`, `InvoicePosting`
- **Integración con pasarelas de pago** — `PaymentGatewayAdapter`, `StripeClient`, `MercadoPagoClient`

Heurísticas:
- Un **verbo + entidad** compartido (`Create`, `Post`, `Cancel`) suele indicar un proceso dentro del mismo dominio.
- `*Service`, `*Manager`, `*Handler` son usualmente la fachada de un grupo.
- `*Table`, `*Entity` son datos del mismo grupo que su servicio.
- `*Helper`, `*Util` sin dominio claro → candidatos a `other` o a quedar `unclassified`.

### 5. Nombrar cada grupo

Reglas duras:

- **Prohibido** usar nombres técnicos genéricos: "Tablas", "Clases", "Utilidades", "Varios", "Otros", "Helpers".
- **Obligatorio** usar un nombre que refleje **qué hace** el grupo para el negocio, no qué es técnicamente.
- Si el `product_name` aporta contexto, usalo. Ej: en producto "License", un grupo puede llamarse "Gestión de Licencias" si cubre el ciclo de vida central.

### 6. Slug

Generá `slug` en kebab-case ASCII derivado del nombre. Ej:

- "Gestión de Suscripciones" → `subscription`
- "Integración con pasarelas de pago" → `payment-gateway`
- "Facturación y notas de crédito" → `billing`

---

## Output

Un JSON con el array `groups[]`. Cada elemento tiene:

- `slug`
- `name`
- `description` (una línea)
- `patterns` — lista de prefijos + infijos que identifican a este grupo
- `candidate_classes` — lista tentativa de clases que caen acá (será refinada por el Prompt 02)

Si hay ambigüedades críticas (siglas que no podés desambiguar, un dominio que parece pero no es), emití un `warnings[]` con las preguntas que el humano debería responder.

**No escribas prosa fuera del JSON. El Prompt 02 consume esto directamente.**
