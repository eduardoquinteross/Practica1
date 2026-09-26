# CSV & Data Validator Skill

Skill autocontenida para validar calidad y estructura de archivos CSV con Python 3 y librerias estandar. Revisa valores nulos, filas duplicadas, tipos de datos y estructura de filas, y produce un reporte JSON y otro Markdown.

## Requisitos

- Python 3.8 o superior.
- No requiere instalar paquetes ni ejecutar `pip install`.

## Estructura

```text
csv-data-validator/
├── SKILL.md
├── scripts/validate_csv.py
├── references/rules.json
└── assets/
    ├── sample_valid.csv
    └── sample_invalid.csv
```

## Uso

Desde la raiz del repositorio, ejecuta el script indicando un archivo CSV y un directorio para los reportes:

```bash
python .codex/skills/csv-data-validator/scripts/validate_csv.py --input RUTA/archivo.csv --output RUTA/reportes
```

`--output` es un directorio. El script lo crea cuando no existe y genera estos archivos:

- `validation_report.json`: resultado estructurado para integraciones.
- `validation_report.md`: resumen legible para personas.

El codigo de salida `0` confirma que el CSV se pudo analizar; consulta `status` para conocer si cumple las reglas. El codigo `1` indica que el archivo no existe, esta corrupto, tiene encabezados invalidos, filas con diferente numero de columnas o no se pudieron generar los reportes.

## Caso exitoso

```bash
python .codex/skills/csv-data-validator/scripts/validate_csv.py --input .codex/skills/csv-data-validator/assets/sample_valid.csv --output .codex/skills/csv-data-validator/output/valid
```

El resultado esperado incluye `Estado de validacion: passed` y los dos reportes dentro de `output/valid`.

## Caso de error

`sample_invalid.csv` tiene una comilla sin cerrar, por lo que simula un CSV corrupto:

```bash
python .codex/skills/csv-data-validator/scripts/validate_csv.py --input .codex/skills/csv-data-validator/assets/sample_invalid.csv --output .codex/skills/csv-data-validator/output/invalid
```

El resultado esperado es un mensaje `Error: No se pudo leer el CSV: ...` en stderr y codigo de salida `1`.

Para probar tambien el archivo inexistente:

```bash
python .codex/skills/csv-data-validator/scripts/validate_csv.py --input no-existe.csv --output .codex/skills/csv-data-validator/output/missing
```

## Reglas configurables

`references/rules.json` contiene las tolerancias. Por defecto permite hasta 10% de nulos por columna y no permite filas duplicadas ni tipos mezclados. Los valores `""`, `null`, `none`, `n/a` y `na` se consideran nulos sin distinguir mayusculas.

Los tipos inferidos son `integer`, `decimal`, `boolean`, `date` con formato `YYYY-MM-DD` y `string`. Cada reporte incluye la distribucion de tipos por columna y las reglas efectivamente aplicadas.

## Puntos clave para la presentacion

- La skill sigue la arquitectura `.codex/skills/` y esta documentada para que un agente pueda ejecutarla sin contexto adicional.
- Solo usa `csv`, `json`, `sys`, `pathlib`, `argparse` y otros modulos de la biblioteca estandar.
- Separa los errores operativos y de sintaxis (codigo 1) de las incidencias de calidad, que quedan registradas en los reportes.
- Los limites estan desacoplados del codigo en `references/rules.json`, facilitando adaptar la validacion a cada fuente de datos.
