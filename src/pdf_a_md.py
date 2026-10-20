"""Convert PDF files to Markdown."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable, Sequence

import pymupdf


DEFAULT_INPUT_DIR = Path("data") / "input"
DEFAULT_OUTPUT_DIR = Path("data") / "output"


@dataclass(frozen=True)
class ConversionResult:
    """Outcome of converting one selected PDF."""

    source: Path
    destination: Path
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error is None


def pdf_a_markdown(pdf_path: Path, md_path: Path) -> None:
    """Convert a PDF to Markdown, keeping a heading for each page."""
    contenido = [f"# {pdf_path.stem}\n"]

    with pymupdf.open(pdf_path) as documento:
        for numero_pagina in range(documento.page_count):
            pagina = documento.load_page(numero_pagina)
            contenido.append(f"\n\n---\n\n## Página {numero_pagina + 1}\n\n")
            texto = pagina.get_text("text")
            if not isinstance(texto, str):
                raise TypeError(f"Se esperaba texto para la página {numero_pagina + 1}")
            contenido.append(texto)

    md_path.write_text("".join(contenido), encoding="utf-8")


def convertir_archivos_pdf(
    archivos_pdf: Sequence[Path],
    carpeta_salida: Path,
    on_progress: Callable[[int, int, ConversionResult], None] | None = None,
) -> list[ConversionResult]:
    """Convert PDFs individually without overwriting existing Markdown files."""
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    resultados: list[ConversionResult] = []
    total = len(archivos_pdf)

    for indice, pdf_path in enumerate(archivos_pdf, start=1):
        md_path = carpeta_salida / f"{pdf_path.stem}.md"
        try:
            if pdf_path.suffix.lower() != ".pdf":
                raise ValueError("El archivo seleccionado no tiene extensión PDF.")
            if md_path.exists():
                raise FileExistsError(
                    f"Ya existe {md_path.name}; no se sobrescribió."
                )
            pdf_a_markdown(pdf_path, md_path)
        except Exception as error:
            resultado = ConversionResult(
                source=pdf_path,
                destination=md_path,
                error=str(error),
            )
        else:
            resultado = ConversionResult(source=pdf_path, destination=md_path)

        resultados.append(resultado)
        if on_progress is not None:
            on_progress(indice, total, resultado)

    return resultados


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convierte todos los PDF de una carpeta a archivos Markdown."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Carpeta con los PDF (predeterminada: {DEFAULT_INPUT_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Carpeta de salida (predeterminada: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args(argv)

    if not args.input_dir.is_dir():
        print(
            f"Error: no existe la carpeta de entrada: {args.input_dir}",
            file=sys.stderr,
        )
        return 2

    archivos_pdf = sorted(
        archivo
        for archivo in args.input_dir.iterdir()
        if archivo.is_file() and archivo.suffix.lower() == ".pdf"
    )
    if not archivos_pdf:
        print(f"No se encontraron archivos PDF en: {args.input_dir}")
        return 0

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"Error al crear la carpeta de salida: {error}", file=sys.stderr)
        return 1

    def mostrar_resultado(
        indice: int,
        total: int,
        resultado: ConversionResult,
    ) -> None:
        if resultado.succeeded:
            print(
                f"[{indice}/{total}] Convertido: "
                f"{resultado.source.name} -> {resultado.destination}"
            )
        else:
            print(
                f"[{indice}/{total}] Error en "
                f"{resultado.source.name}: {resultado.error}",
                file=sys.stderr,
            )

    resultados = convertir_archivos_pdf(
        archivos_pdf,
        args.output_dir,
        on_progress=mostrar_resultado,
    )
    return 1 if any(not resultado.succeeded for resultado in resultados) else 0


if __name__ == "__main__":
    raise SystemExit(main())
