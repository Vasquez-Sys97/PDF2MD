import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import pymupdf

from src.app import main as build_app
from src.pdf_a_md import convertir_archivos_pdf, main, pdf_a_markdown


class PdfToMarkdownTests(unittest.TestCase):
    def test_flet_interface_builds(self) -> None:
        page = MagicMock()
        page.services = []
        page.web = False

        build_app(page)

        self.assertTrue(page.add.called)
        self.assertEqual(len(page.services), 1)

    def test_converts_pdf_text_and_page_heading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            pdf_path = directory / "documento.pdf"
            markdown_path = directory / "documento.md"

            with pymupdf.open() as document:
                page = document.new_page()
                page.insert_text((72, 72), "Texto de prueba")
                document.save(pdf_path)

            pdf_a_markdown(pdf_path, markdown_path)

            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertIn("# documento", markdown)
            self.assertIn("## Página 1", markdown)
            self.assertIn("Texto de prueba", markdown)

    def test_cli_converts_files_from_input_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            input_directory = directory / "input"
            output_directory = directory / "output"
            input_directory.mkdir()
            pdf_path = input_directory / "documento.pdf"

            with pymupdf.open() as document:
                page = document.new_page()
                page.insert_text((72, 72), "Texto de prueba")
                document.save(pdf_path)

            exit_code = main(
                [
                    "--input-dir",
                    str(input_directory),
                    "--output-dir",
                    str(output_directory),
                ]
            )

            self.assertEqual(exit_code, 0)
            markdown = (output_directory / "documento.md").read_text(encoding="utf-8")
            self.assertIn("Texto de prueba", markdown)

    def test_batch_reports_progress_and_does_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            pdf_path = directory / "documento.pdf"
            output_directory = directory / "output"
            existing_markdown = output_directory / "documento.md"
            output_directory.mkdir()
            existing_markdown.write_text("No sobrescribir", encoding="utf-8")
            progress: list[tuple[int, int, bool]] = []

            with pymupdf.open() as document:
                document.new_page().insert_text((72, 72), "Texto de prueba")
                document.save(pdf_path)

            results = convertir_archivos_pdf(
                [pdf_path],
                output_directory,
                on_progress=lambda current, total, result: progress.append(
                    (current, total, result.succeeded)
                ),
            )

            self.assertEqual(len(results), 1)
            self.assertFalse(results[0].succeeded)
            self.assertIn("no se sobrescribió", results[0].error or "")
            self.assertEqual(progress, [(1, 1, False)])
            self.assertEqual(
                existing_markdown.read_text(encoding="utf-8"),
                "No sobrescribir",
            )


if __name__ == "__main__":
    unittest.main()
