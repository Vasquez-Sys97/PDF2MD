# Conversor de PDF a Markdown

Aplicación de escritorio para extraer el texto de archivos PDF y guardarlo en Markdown, con una sección por página. Incluye una interfaz gráfica hecha con Flet y una alternativa de línea de comandos.

## Requisitos

- Python 3.10 o posterior
- Las dependencias listadas en `requirements.txt`

## Instalación

Desde la carpeta del proyecto, crea y activa un entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

En macOS o Linux, activa el entorno con `source .venv/bin/activate`.

## Uso

### Interfaz gráfica

Inicia la aplicación de escritorio:

```powershell
python -m src.app
```

Usa **Seleccionar PDF** para elegir uno o varios documentos y **Elegir carpeta** para escoger dónde guardar los resultados. La interfaz muestra el progreso por archivo, el tiempo transcurrido y los errores individuales. No sobrescribe archivos Markdown existentes: informa el conflicto y continúa con los demás.

### Línea de comandos

Por defecto, el programa lee los PDF de `data/input/` y guarda los resultados en `data/output/`:

```powershell
python src/pdf_a_md.py
```

También puedes indicar otras carpetas:

```powershell
python src/pdf_a_md.py --input-dir "ruta/a/pdfs" --output-dir "ruta/a/resultados"
```

Los archivos PDF deben contener texto seleccionable. Los documentos escaneados requieren OCR, que esta herramienta no realiza.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

## Privacidad y publicación

- La interfaz trabaja con los archivos y carpetas locales; no los carga a Internet.
- Los PDF, hojas de cálculo, documentos, carpetas `data/` y archivos de entorno están excluidos de Git por defecto.
- Coloca los documentos de trabajo en `data/input/`. Tanto los originales como los Markdown generados permanecen fuera del repositorio.
- Revisa siempre `git status` y los archivos que vas a subir antes de publicar. No agregues documentos, datos personales, credenciales ni resultados extraídos de documentos privados.
- El `.gitignore` reduce el riesgo de incluir esos archivos por accidente, pero no sustituye la revisión manual.
- Para publicar este proyecto, abre una terminal en esta carpeta y usa Git desde aquí; no inicialices ni ejecutes `git add` desde el Escritorio.
