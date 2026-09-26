#!/usr/bin/env python3
"""Validate CSV structure and data quality, then write JSON and Markdown reports."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path
import re


SCRIPT_DIR = Path(__file__).resolve().parent
RULES_PATH = SCRIPT_DIR.parent / 'references' / 'rules.json'
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def parse_arguments():
  parser = argparse.ArgumentParser(
    description='Validate a CSV file and generate JSON and Markdown reports.'
  )
  parser.add_argument('--input', required=True, help='Path to the CSV file to validate.')
  parser.add_argument(
    '--output',
    required=True,
    help='Directory where validation_report.json and validation_report.md are created.'
  )
  return parser.parse_args()


def load_rules():
  try:
    with RULES_PATH.open(encoding='utf-8') as rules_file:
      rules = json.load(rules_file)
  except (OSError, json.JSONDecodeError) as error:
    raise RuntimeError(f'No se pudieron cargar las reglas: {error}') from error

  required_keys = {
    'null_values',
    'max_null_percentage_per_column',
    'max_duplicate_rows',
    'max_mixed_type_percentage_per_column',
    'allowed_types'
  }
  missing = required_keys.difference(rules)
  if missing:
    raise RuntimeError(f'Reglas incompletas: faltan {", ".join(sorted(missing))}.')
  return rules


def is_null(value, null_values):
  return value.strip().lower() in null_values


def detect_type(value):
  normalized = value.strip()
  if normalized.lower() in ('true', 'false'):
    return 'boolean'
  if re.fullmatch(r'[+-]?\d+', normalized):
    return 'integer'
  if re.fullmatch(r'[+-]?(?:\d+\.\d*|\d*\.\d+)', normalized):
    return 'decimal'
  if DATE_PATTERN.fullmatch(normalized):
    return 'date'
  return 'string'


def percentage(part, total):
  return round((part / total) * 100, 2) if total else 0.0


def read_csv(input_path):
  try:
    with input_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
      reader = csv.reader(csv_file, strict=True)
      headers = next(reader, None)
      if headers is None:
        raise ValueError('El archivo CSV esta vacio.')
      if not headers or any(not header.strip() for header in headers):
        raise ValueError('El CSV debe tener encabezados no vacios.')

      duplicate_headers = [header for header, count in Counter(headers).items() if count > 1]
      if duplicate_headers:
        raise ValueError(f'Encabezados duplicados: {", ".join(duplicate_headers)}.')

      rows = []
      for line_number, row in enumerate(reader, start=2):
        if len(row) != len(headers):
          raise ValueError(
            f'La fila {line_number} tiene {len(row)} columnas; se esperaban {len(headers)}.'
          )
        rows.append(row)
  except (OSError, UnicodeDecodeError, csv.Error, ValueError) as error:
    raise RuntimeError(f'No se pudo leer el CSV: {error}') from error

  return headers, rows


def analyze(headers, rows, rules):
  null_values = {value.lower() for value in rules['null_values']}
  issues = []
  columns = []
  duplicate_rows = sum(count - 1 for count in Counter(tuple(row) for row in rows).values() if count > 1)

  for index, header in enumerate(headers):
    values = [row[index] for row in rows]
    non_null_values = [value for value in values if not is_null(value, null_values)]
    null_count = len(values) - len(non_null_values)
    types = Counter(detect_type(value) for value in non_null_values)
    inferred_type = types.most_common(1)[0][0] if types else 'unknown'
    mixed_type_count = len(non_null_values) - types.get(inferred_type, 0)
    null_percentage = percentage(null_count, len(rows))
    mixed_type_percentage = percentage(mixed_type_count, len(non_null_values))

    columns.append({
      'name': header,
      'total_values': len(values),
      'null_count': null_count,
      'null_percentage': null_percentage,
      'inferred_type': inferred_type,
      'type_distribution': dict(sorted(types.items())),
      'mixed_type_count': mixed_type_count,
      'mixed_type_percentage': mixed_type_percentage
    })

    if null_percentage > rules['max_null_percentage_per_column']:
      issues.append({
        'rule': 'max_null_percentage_per_column',
        'column': header,
        'message': f'Valores nulos: {null_percentage}% (limite: {rules["max_null_percentage_per_column"]}%).'
      })
    if mixed_type_percentage > rules['max_mixed_type_percentage_per_column']:
      issues.append({
        'rule': 'max_mixed_type_percentage_per_column',
        'column': header,
        'message': f'Tipos mezclados: {mixed_type_percentage}% (limite: {rules["max_mixed_type_percentage_per_column"]}%).'
      })

  if duplicate_rows > rules['max_duplicate_rows']:
    issues.append({
      'rule': 'max_duplicate_rows',
      'column': None,
      'message': f'Filas duplicadas: {duplicate_rows} (limite: {rules["max_duplicate_rows"]}).'
    })

  return {
    'status': 'passed' if not issues else 'failed',
    'summary': {
      'row_count': len(rows),
      'column_count': len(headers),
      'duplicate_rows': duplicate_rows,
      'issue_count': len(issues)
    },
    'columns': columns,
    'issues': issues,
    'rules': rules
  }


def escape_markdown(value):
  return str(value).replace('|', '\\|')


def build_markdown(report, input_path):
  summary = report['summary']
  lines = [
    '# Reporte de validacion CSV',
    '',
    f'- Archivo: `{input_path}`',
    f'- Estado: **{report["status"].upper()}**',
    f'- Filas de datos: {summary["row_count"]}',
    f'- Columnas: {summary["column_count"]}',
    f'- Filas duplicadas: {summary["duplicate_rows"]}',
    '',
    '## Columnas',
    '',
    '| Columna | Nulos | % nulos | Tipo inferido | Distribucion | % tipos mezclados |',
    '| --- | ---: | ---: | --- | --- | ---: |'
  ]
  for column in report['columns']:
    distribution = ', '.join(f'{key}: {value}' for key, value in column['type_distribution'].items()) or 'sin datos'
    lines.append(
      f'| {escape_markdown(column["name"])} | {column["null_count"]} | '
      f'{column["null_percentage"]}% | {column["inferred_type"]} | '
      f'{escape_markdown(distribution)} | {column["mixed_type_percentage"]}% |'
    )

  lines.extend(['', '## Incidencias', ''])
  if report['issues']:
    for issue in report['issues']:
      location = f' ({issue["column"]})' if issue['column'] else ''
      lines.append(f'- `{issue["rule"]}`{location}: {issue["message"]}')
  else:
    lines.append('- No se detectaron incidencias con las reglas configuradas.')
  return '\n'.join(lines) + '\n'


def write_reports(output_path, report, input_path):
  try:
    output_path.mkdir(parents=True, exist_ok=True)
    with (output_path / 'validation_report.json').open('w', encoding='utf-8') as report_file:
      json.dump(report, report_file, ensure_ascii=False, indent=2)
      report_file.write('\n')
    (output_path / 'validation_report.md').write_text(
      build_markdown(report, input_path), encoding='utf-8'
    )
  except OSError as error:
    raise RuntimeError(f'No se pudieron escribir los reportes: {error}') from error


def main():
  args = parse_arguments()
  input_path = Path(args.input)
  output_path = Path(args.output)

  if not input_path.is_file():
    print(f'Error: el archivo de entrada no existe o no es un archivo: {input_path}', file=sys.stderr)
    return 1

  try:
    rules = load_rules()
    headers, rows = read_csv(input_path)
    report = analyze(headers, rows, rules)
    write_reports(output_path, report, input_path)
  except RuntimeError as error:
    print(f'Error: {error}', file=sys.stderr)
    return 1

  print(f'Reporte JSON: {output_path / "validation_report.json"}')
  print(f'Reporte Markdown: {output_path / "validation_report.md"}')
  print(f'Estado de validacion: {report["status"]}')
  return 0


if __name__ == '__main__':
  sys.exit(main())
