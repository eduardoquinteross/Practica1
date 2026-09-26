---
name: csv-data-validator
description: Analiza archivos CSV para detectar valores nulos, filas duplicadas, inconsistencias de tipo y errores de estructura; genera reportes JSON y Markdown.
version: 1.0.0
author: Practica1
---

# CSV & Data Validator Skill

Usa esta skill cuando se necesite revisar la calidad de un CSV antes de importarlo, procesarlo o compartirlo. Detecta archivos inexistentes o corruptos, encabezados duplicados, filas con un numero incorrecto de columnas, valores nulos, filas duplicadas y tipos de datos mezclados.

No la uses para modificar datos de origen: el script solo los lee y crea reportes separados.

## Procedimiento para el agente

1. Identifica el CSV que se va a analizar y crea o selecciona un directorio de salida vacio o dedicado.
2. Desde la raiz del repositorio, ejecuta:

   ```bash
   python .codex/skills/csv-data-validator/scripts/validate_csv.py --input RUTA/archivo.csv --output RUTA/reportes
   ```

3. Comprueba el codigo de salida. `0` significa que se pudo analizar el archivo; las observaciones se consultan en el reporte. `1` indica un problema operativo o de sintaxis CSV y se muestra un error limpio en stderr.
4. Lee `validation_report.md` para el resumen humano y `validation_report.json` para automatizaciones.
5. Si el campo `status` del JSON es `failed`, corrige los problemas enumerados en `issues` y vuelve a ejecutar la validacion.

## Reglas

Las tolerancias se definen en `references/rules.json`. El script las carga automaticamente y las incluye en el reporte para que los resultados sean reproducibles.

## Archivos de demostracion

El caso correcto se ejecuta con:

```bash
python .codex/skills/csv-data-validator/scripts/validate_csv.py --input .codex/skills/csv-data-validator/assets/sample_valid.csv --output .codex/skills/csv-data-validator/output/valid
```

El archivo `assets/sample_invalid.csv` contiene una comilla sin cerrar para demostrar el manejo de un CSV corrupto. Su ejecucion debe finalizar con codigo `1` y no genera un reporte valido.
