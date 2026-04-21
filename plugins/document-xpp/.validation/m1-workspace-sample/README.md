# M1 validation workspace sample

Golden output de la validación end-to-end del milestone **M1** del plugin `document-xpp` contra el módulo real `Axxon365LicenseManagement` bajo `XppSource/`.

## Propósito

- Baseline auditable del contrato de persistencia (`_tracking/*`) y del entregable visual (`functional_map.md`).
- Evidencia para regresión: cualquier cambio en parser, agent o prompts debe poder reproducir este workspace (salvo `hashes.csv`, volátil por `mtime`).
- Referencia de shape para los workflows de M2+ (diagramas) que van a leer estos YAMLs.

## Qué se commitea

| Archivo | Motivo |
|---------|--------|
| `_tracking/manifest.yaml` | Metadata del workspace sample |
| `_tracking/inventory.csv` | Snapshot de 48 clases parseadas |
| `_tracking/dependencies.csv` | 135 dependencias inferidas |
| `_tracking/funcionalidades/*.yaml` | 7 grupos funcionales (uno por archivo) |
| `_tracking/classifier-output.json` | Salida cruda del agent functional-classifier (JSON) |
| `functional_map.md` | Entregable human-readable con warnings de la run |
| `README.md` | Este archivo |

## Qué NO se commitea (por diseño)

- `_tracking/hashes.csv` — depende de `LastWriteTimeUtc` del filesystem; no es determinista.
- `_tracking/hashes.previous.csv` — idem, sólo existe en sesiones `actualizar`.
- `adicionales/` — inputs opcionales registrados por sesión (scope docs, manuales, diagramas previos); esta validación se corrió sin inputs adicionales.

## Cómo regenerar

Desde el root del repo, con el plugin instalado:

```bash
# Hashing (PowerShell 7+)
pwsh -NoProfile -File plugins/document-xpp/skills/document-xpp/scripts/Compute-XppHashes.ps1 `
  -SourcePath "C:/Repos/AxxonPractica/AxxonPracticaDev/AiCodeDocumenter/XppSource" `
  -OutputPath "plugins/document-xpp/.validation/m1-workspace-sample/_tracking"

# Inventario + dependencias (Python ≥ 3.10, solo stdlib)
python plugins/document-xpp/skills/document-xpp/scripts/build_xpp_inventory.py \
  --source-path "XppSource" \
  --output-path "plugins/document-xpp/.validation/m1-workspace-sample/_tracking"
```

Luego disparar el skill `document-xpp` en modo `nuevo` sobre este workspace y comparar contra los artefactos commiteados.

## Findings de la run (resumen)

48 clases parseadas, 135 dependencias, 7 grupos de negocio, 0 sin clasificar, 9 warnings accionables — ver sección final de `functional_map.md` y `classifier-output.json` para detalle. Los gaps identificados están tracked como follow-ups (roles `form`/`interface`, path separator en CSVs, exclusion-list incompleta, criterio `Contract → dto` rígido, parsing de `AxEnum`/`AxEdt`, columna `file` en `dependencies.csv`).
