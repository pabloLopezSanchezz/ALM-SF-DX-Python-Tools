# Retrofit Report Generator

Script para generar reportes HTML de Retrofit de LQA usando Jinja2.

## Estructura

```
utils/
├── generate_retrofit_report.py    # Script principal
└── resources/
    └── retrofit_report_template.html  # Template Jinja2
```

## Uso

```bash
python3 generate_retrofit_report.py <config_json>
```

## Configuración JSON

El script requiere un archivo JSON con la siguiente estructura:

```json
{
  "retrofit_date": "20260129",
  "source_branch": "LQA",
  "build_number": "123",
  "build_url": "https://dev.azure.com/...",
  "dry_run": "False",
  "output_file": "/path/to/output.html",
  "streams": {
    "TpmEU": {
      "result": "Succeeded",
      "enabled": "True"
    },
    "B2BEU": {
      "result": "Failed",
      "enabled": "True"
    }
  }
}
```

## Dependencias

- Python 3.x
- Jinja2 (`pip install jinja2`)

## Output

El script genera un archivo HTML con el reporte de Retrofit que incluye:
- Estadísticas generales (streams procesados, exitosos, fallidos, tasa de éxito)
- Detalles por stream (estado, source branch, target branch)
- Información del build y dry run
