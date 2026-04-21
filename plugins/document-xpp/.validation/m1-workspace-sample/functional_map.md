# Mapa funcional — Axxon365LicenseManagement

> Generado: 2026-04-21T00:45:00Z
> Plugin: document-xpp@0.1.0
> Modo de sesión: nuevo
> **Este mapa se generó como validación end-to-end de M1** contra el módulo real bajo `XppSource/Axxon365LicenseManagement/`. Es un golden output para auditar la calidad del flujo antes de liberar Fases 3–5.

---

## Gestión de Suscripciones y Licencias

**Descripción:** Núcleo del producto: alta, consulta, sincronización y verificación del estado de suscripciones de licencia por compañía y por usuario.
**Status:** nueva
**Slug:** `subscription-lifecycle`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicCompanySubscriptionExtension` *(controller)* | — | `DialogButton` |
| `AxnLicSubscriptionApply` *(controller)* | `AxnLicParameters`, `AxnLicSubscriptionApplyService`, `AxnLicSubscriptionRequestContract`, `AxnLicSubscriptionService` | — |
| `AxnLicSubscriptionApplyService` *(service)* | `AxnLicSubscriptionSync` | `AxnLicExtensionLicenseStatus`, `DialogButton` |
| `AxnLicSubscriptionChecker` *(service)* | `AxnLicSubscription`, `AxnLicSubscriptionState`, `AxnLicUser` | `AxnLicState`, `AxnLicSubscriptionStatus` |
| `AxnLicSubscriptionRequestContract` *(dto)* | — | `ClrInterop`, `xSysConfig` |
| `AxnLicSubscriptionResponseContract` *(dto)* | — | — |
| `AxnLicSubscriptionResponseDetailContract` *(dto)* | — | — |
| `AxnLicSubscriptionResponseTokenContract` *(dto)* | — | — |
| `AxnLicSubscriptionService` *(service)* | `AxnLicHttpAuthProviderApiKey`, `AxnLicHttpCallContract`, `AxnLicHttpCallService` | `AxnLicHttpAuthApiKeyAddTo`, `AxnLicSubscriptionStatus`, `FormJsonSerializer` |
| `AxnLicSubscriptionSync` *(service)* | — | `AxnLicState` |
| `AxnLicSubscription` *(entity)* | — | — |
| `AxnLicSubscriptionState` *(entity)* | — | — |
| `AxnLicSubscriptionTmp` *(entity)* | — | — |
| `AxnLicUser` *(controller, AxForm)* | — | — |
| `AxnLicUser` *(entity, AxTable)* | — | — |

---

## Gestión de Extensiones y Features de Producto

**Descripción:** Activación y verificación de extensiones y features adicionales contratadas por la compañía sobre la licencia base.
**Status:** nueva
**Slug:** `extension-feature`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicCompanyExtensionFeature` *(controller)* | — | `Box`, `DialogButton`, `SysQuery` |
| `AxnLicExtensionChecker` *(service)* | `AxnLicSubscriptionChecker`, `AxnLicSubscriptionExtension`, `AxnLicSubscriptionExtensionState` | `AxnLicExtensionInstallationStatus`, `AxnLicExtensionLicenseStatus`, `AxnLicState` |
| `AxnLicExtensionFeatureDiscoveryService` *(service)* | `AxnLicConfigurationKeyDiscoveryService`, `AxnLicSubscriptionSync` | `AxnLicExtensionInstallationStatus` |
| `AxnLicFeatureChecker` *(service)* | `AxnLicExtensionChecker`, `AxnLicSubscriptionExtensionFeature`, `AxnLicSubscriptionExtensionFeatureState` | `AxnLicState` |
| `AxnLicSubscriptionExtension` *(entity)* | — | — |
| `AxnLicSubscriptionExtensionFeature` *(entity)* | — | — |
| `AxnLicSubscriptionExtensionFeatureState` *(entity)* | — | — |
| `AxnLicSubscriptionExtensionState` *(entity)* | — | — |
| `AxnLicSubscriptionExtensionTmp` *(entity)* | — | — |

---

## Descubrimiento y Caché de Configuration Keys

**Descripción:** Resolución en tiempo de ejecución de qué configuration keys están activas para una compañía según su suscripción, con caché en memoria.
**Status:** nueva
**Slug:** `configuration-discovery`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicConfigurationKey` *(other)* | — | — |
| `AxnLicConfigurationKeyCache` *(other)* | — | — |
| `AxnLicConfigurationKeyDiscoveryService` *(service)* | `AxnLicConfigurationKey`, `AxnLicConfigurationKeyHelper` | `AxnLicExtensionFeature`, `DictConfigurationKey` |
| `AxnLicConfigurationKeyHelper` *(helper)* | — | `AxnLicExtensionFeature`, `DictConfigurationKey` |

---

## Integración HTTP con Plataforma de Licenciamiento

**Descripción:** Cliente HTTP, autenticación (API key / Bearer) y contrato de llamada remota hacia la plataforma externa que emite y valida las licencias.
**Status:** nueva
**Slug:** `http-integration`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicHttpAuthProviderApiKey` *(service)* | `IAxnLicHttpAuthProvider` | `AxnLicHttpAuthApiKeyAddTo` |
| `AxnLicHttpAuthProviderBearer` *(service)* | `IAxnLicHttpAuthProvider` | — |
| `AxnLicHttpCallContract` *(dto)* | — | — |
| `AxnLicHttpCallService` *(service)* | `AxnLicHttpClient` | — |
| `AxnLicHttpClient` *(service)* | `IAxnLicHttpClient` | `CLRInterop` |
| `AxnLicTimerService` *(helper)* | — | — |
| `IAxnLicHttpAuthProvider` *(other, interface)* | — | — |
| `IAxnLicHttpClient` *(other, interface)* | — | — |

---

## Integridad Criptográfica de Datos de Licencia

**Descripción:** Cálculo y verificación de hashes (MD5) sobre los registros de suscripción y extensión para detectar manipulación no autorizada de los datos de licencia.
**Status:** nueva
**Slug:** `data-integrity`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicDataIntegrityHandler` *(service)* | `AxnLicDataIntegrityServiceExtension`, `AxnLicDataIntegrityServiceSubscription` | — |
| `AxnLicDataIntegrityServiceBase` *(service)* | `AxnLicDataIntegrityTable` | — |
| `AxnLicDataIntegrityServiceExtension` *(service)* | `AxnLicDataIntegrityServiceBase` | — |
| `AxnLicDataIntegrityServiceSubscription` *(service)* | `AxnLicDataIntegrityServiceBase` | `DateDay`, `DateMonth`, `DateSeparator`, `DateYear` |
| `AxnLicDataIntegrityTable` *(entity)* | — | — |

---

## Notificaciones al Usuario sobre Estado de Licencia

**Descripción:** Emisión de mensajes y alertas en la UI ante eventos de integridad y de estado de suscripción (expiración, inconsistencias, acciones requeridas).
**Status:** nueva
**Slug:** `notifications`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicNotificationHandler` *(service)* | `AxnLicDataIntegrityServiceExtension`, `AxnLicDataIntegrityServiceSubscription`, `AxnLicNotificationService`, `AxnLicSubscriptionChecker` | `AxnLicSubscriptionStatus`, `MessageSeverity` |
| `AxnLicNotificationService` *(service)* | — | `FormJsonSerializer`, `Message`, `MessageActionType`, `MenuItemMessageAction` |

---

## Bootstrap y Parametrización de la Aplicación

**Descripción:** Arranque del módulo, parámetros globales del sistema y extensiones de FormRun/Global que conectan los componentes en tiempo de ejecución.
**Status:** nueva
**Slug:** `app-bootstrap`

| Clase | Referencias internas | Referencias externas |
| :--- | :--- | :--- |
| `AxnLicApplicationStartupEventManager` *(service)* | `AxnLicExtensionFeatureDiscoveryService`, `AxnLicParameters` | — |
| `FormRun_Axxon365LicenseManagement_Extension` *(other)* | `AxnLicNotificationHandler` | — |
| `Global_Axxon365LicenseManagement_Extension` *(other)* | `AxnLicConfigurationKeyCache`, `AxnLicConfigurationKeyHelper`, `AxnLicExtensionChecker`, `AxnLicFeatureChecker` | `AxnLicExtensionFeature`, `DictConfigurationKey` |
| `AxnLicParameters` *(controller, AxForm)* | — | — |
| `AxnLicParameters` *(entity, AxTable)* | — | `Company` |

---

## Resumen

- **Módulo:** `Axxon365LicenseManagement`
- **Clases parseadas:** 48
- **Grupos identificados:** 7
- **Clases sin clasificar:** 0
- **Dependencias procesadas:** 135

## Warnings del run

- Duplicado de nombre `AxnLicUser` y `AxnLicParameters` (AxForm + AxTable) — no puede desambiguarse automáticamente porque `dependencies.csv` no trae la columna `file`.
- Roles ausentes en el contrato actual: `form` (5 clases), `interface` (2 clases) — mapeadas a `controller` / `other`.
- `external_refs` contaminadas por enums/EDTs del propio módulo (`AxnLicState`, `AxnLicSubscriptionStatus`, `AxnLicExtensionFeature`, `AxnLicHttpAuthApiKeyAddTo`, …) — el parser no procesa `AxEnum` ni `AxEdt`.
- Gaps en `exclusion-list.md`: `DictConfigurationKey`, `SysQuery`, `Company`, `xSysConfig`, `ClrInterop`, `CLRInterop`, `DialogButton`, `Box`, `MessageSeverity`, `MessageActionType`, `MenuItemMessageAction`, `Message`, `FormJsonSerializer`, `DateDay`, `DateMonth`, `DateSeparator`, `DateYear`.
- Criterio `Contract → dto` rígido — `AxnLicSubscriptionRequestContract` tiene 9 métodos y valida, más cerca de un service.
- Path separator inconsistente: `hashes.csv` usa `/` pero `inventory.csv`/`dependencies.csv` usan `\` — romper con el schema documentado (schema dice `/`).
