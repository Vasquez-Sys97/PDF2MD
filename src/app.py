"""Flet desktop interface for converting selected PDF files to Markdown."""

from __future__ import annotations

import asyncio
from pathlib import Path
from time import perf_counter

import flet as ft

from src.pdf_a_md import ConversionResult, convertir_archivos_pdf


BACKGROUND = "#F3F6FB"
CARD = "#FFFFFF"
INK = "#17243A"
MUTED = "#718096"
ACCENT = "#4169E1"
ACCENT_LIGHT = "#EAF0FF"
SUCCESS = "#188567"
ERROR = "#C44545"


def _controls(*items: ft.Control) -> list[ft.Control]:
    return list(items)


def main(page: ft.Page) -> None:
    page.title = "PDF a Markdown"
    page.theme = ft.Theme(color_scheme_seed=ACCENT)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BACKGROUND
    page.padding = 28
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 940
    page.window.height = 880
    page.window.min_width = 880
    page.window.min_height = 680

    selector = ft.FilePicker()
    page.services.append(selector)

    selected_files: dict[str, Path] = {}
    output_directory: Path | None = None
    is_running = False

    selected_count = ft.Text("0 archivos seleccionados", color=MUTED, size=13)
    selected_list = ft.Column(spacing=6)
    output_path_text = ft.Text(
        "Selecciona dónde guardar los archivos Markdown",
        color=MUTED,
        size=13,
        expand=True,
    )
    status_text = ft.Text(
        "Selecciona uno o varios PDF para comenzar.",
        color=MUTED,
        size=14,
    )
    current_file_text = ft.Text("", color=MUTED, size=12)
    progress_label = ft.Text(
        "Progreso",
        color=INK,
        size=13,
        weight=ft.FontWeight.BOLD,
    )
    progress_count = ft.Text("0 / 0", color=MUTED, size=13)
    progress_bar = ft.ProgressBar(value=0, color=ACCENT, bgcolor=ACCENT_LIGHT)
    elapsed_text = ft.Text(
        "00:00.0",
        color=INK,
        size=24,
        weight=ft.FontWeight.BOLD,
    )
    result_list = ft.Column(spacing=8)

    def refresh_files() -> None:
        selected_count.value = (
            f"{len(selected_files)} archivo"
            f"{'s' if len(selected_files) != 1 else ''} seleccionado"
            f"{'s' if len(selected_files) != 1 else ''}"
        )
        selected_list.controls.clear()
        for path_key, pdf_path in selected_files.items():
            selected_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        _controls(
                            ft.Icon(ft.Icons.PICTURE_AS_PDF, color=ERROR, size=20),
                            ft.Text(pdf_path.name, color=INK, size=13, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=MUTED,
                                tooltip="Quitar archivo",
                                on_click=create_remove_handler(path_key),
                            ),
                        ),
                        spacing=10,
                    ),
                    padding=ft.Padding(left=12, top=3, right=5, bottom=3),
                    bgcolor="#F8FAFD",
                    border_radius=10,
                )
            )
        page.update()

    def remove_file(path_key: str) -> None:
        selected_files.pop(path_key, None)
        refresh_files()

    def create_remove_handler(
        path_key: str,
    ) -> ft.ControlEventHandler[ft.IconButton]:
        def handle_remove(event: ft.Event[ft.IconButton]) -> None:
            del event
            remove_file(path_key)

        return handle_remove

    async def select_pdfs() -> None:
        if page.web:
            status_text.value = (
                "La selección de carpetas está disponible al ejecutar la "
                "aplicación de escritorio."
            )
            status_text.color = ERROR
            page.update()
            return

        try:
            files = await selector.pick_files(
                dialog_title="Selecciona los archivos PDF",
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["pdf"],
                allow_multiple=True,
            )
        except Exception as error:
            status_text.value = f"No se pudieron seleccionar los PDF: {error}"
            status_text.color = ERROR
            page.update()
            return

        for file in files:
            if file.path:
                path = Path(file.path)
                selected_files[str(path.resolve())] = path

        status_text.value = (
            "PDF listos para convertir."
            if selected_files
            else "No se seleccionaron archivos."
        )
        status_text.color = MUTED
        refresh_files()

    def handle_select_pdfs() -> None:
        page.run_task(select_pdfs)

    async def select_output_directory() -> None:
        nonlocal output_directory
        if page.web:
            status_text.value = (
                "Elige una carpeta local ejecutando la aplicación de escritorio."
            )
            status_text.color = ERROR
            page.update()
            return

        try:
            directory = await selector.get_directory_path(
                dialog_title="Selecciona la carpeta de destino",
                initial_directory=(
                    str(output_directory) if output_directory is not None else None
                ),
            )
        except Exception as error:
            status_text.value = f"No se pudo seleccionar la carpeta: {error}"
            status_text.color = ERROR
            page.update()
            return

        if directory:
            output_directory = Path(directory)
            output_path_text.value = str(output_directory)
            output_path_text.color = INK
            status_text.value = "Carpeta de destino seleccionada."
            status_text.color = MUTED
            page.update()

    def handle_select_output_directory() -> None:
        page.run_task(select_output_directory)

    async def update_clock(started_at: float) -> None:
        while is_running:
            elapsed_tenths = int((perf_counter() - started_at) * 10)
            minutes, remainder = divmod(elapsed_tenths, 600)
            seconds, tenths = divmod(remainder, 10)
            elapsed_text.value = f"{minutes:02d}:{seconds:02d}.{tenths}"
            page.update()
            await asyncio.sleep(0.1)

    def render_result(result: ConversionResult) -> None:
        succeeded = result.succeeded
        result_list.controls.append(
            ft.Row(
                _controls(
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE_OUTLINE
                        if succeeded
                        else ft.Icons.ERROR_OUTLINE,
                        color=SUCCESS if succeeded else ERROR,
                        size=18,
                    ),
                    ft.Column(
                        _controls(
                            ft.Text(
                                result.source.name,
                                color=INK,
                                size=13,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"Guardado como {result.destination.name}"
                                if succeeded
                                else result.error or "No se pudo convertir.",
                                color=SUCCESS if succeeded else ERROR,
                                size=12,
                            ),
                        ),
                        spacing=2,
                        expand=True,
                    ),
                ),
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

    async def start_conversion() -> None:
        nonlocal is_running
        if is_running:
            return
        if not selected_files:
            status_text.value = "Primero selecciona al menos un archivo PDF."
            status_text.color = ERROR
            page.update()
            return
        if output_directory is None:
            status_text.value = "Primero selecciona una carpeta de destino."
            status_text.color = ERROR
            page.update()
            return

        pdf_paths = list(selected_files.values())
        total = len(pdf_paths)
        started_at = perf_counter()
        is_running = True
        progress_bar.value = 0
        progress_count.value = f"0 / {total}"
        current_file_text.value = ""
        result_list.controls.clear()
        status_text.value = "Convirtiendo archivos en este equipo…"
        status_text.color = ACCENT
        select_button.disabled = True
        output_button.disabled = True
        convert_button.disabled = True
        clock_task = asyncio.create_task(update_clock(started_at))
        page.update()

        converted = 0
        failed = 0
        try:
            for index, pdf_path in enumerate(pdf_paths, start=1):
                current_file_text.value = f"Procesando {pdf_path.name}"
                page.update()
                try:
                    result = await asyncio.to_thread(
                        convertir_archivos_pdf,
                        [pdf_path],
                        output_directory,
                    )
                    item_result = result[0]
                except Exception as error:
                    item_result = ConversionResult(
                        source=pdf_path,
                        destination=output_directory / f"{pdf_path.stem}.md",
                        error=str(error),
                    )
                render_result(item_result)
                if item_result.succeeded:
                    converted += 1
                else:
                    failed += 1
                progress_bar.value = index / total
                progress_count.value = f"{index} / {total}"
                page.update()
        finally:
            is_running = False
            clock_task.cancel()
            await asyncio.gather(clock_task, return_exceptions=True)
            elapsed_tenths = int((perf_counter() - started_at) * 10)
            minutes, remainder = divmod(elapsed_tenths, 600)
            seconds, tenths = divmod(remainder, 10)
            elapsed_text.value = f"{minutes:02d}:{seconds:02d}.{tenths}"
            current_file_text.value = ""
            select_button.disabled = False
            output_button.disabled = False
            convert_button.disabled = False
            status_text.value = (
                f"Proceso finalizado: {converted} convertido(s), "
                f"{failed} con error."
            )
            status_text.color = SUCCESS if failed == 0 else ERROR
            page.update()

    def handle_start_conversion() -> None:
        page.run_task(start_conversion)

    select_button = ft.OutlinedButton(
        "Seleccionar PDF",
        icon=ft.Icons.ADD,
        on_click=handle_select_pdfs,
    )
    output_button = ft.OutlinedButton(
        "Elegir carpeta",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=handle_select_output_directory,
    )
    convert_button = ft.FilledButton(
        "Convertir a Markdown",
        icon=ft.Icons.AUTO_AWESOME,
        on_click=handle_start_conversion,
        bgcolor=ACCENT,
        color=CARD,
        height=48,
    )

    card_padding = ft.Padding(left=22, top=20, right=22, bottom=20)
    file_card = ft.Container(
        content=ft.Column(
            _controls(
                ft.Row(
                    _controls(
                        ft.Column(
                            _controls(
                                ft.Text(
                                    "Archivos PDF",
                                    size=17,
                                    color=INK,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                selected_count,
                            ),
                            spacing=3,
                            expand=True,
                        ),
                        select_button,
                    ),
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=selected_list,
                    padding=ft.Padding(left=0, top=8, right=0, bottom=0),
                ),
            ),
            spacing=12,
        ),
        padding=card_padding,
        bgcolor=CARD,
        border_radius=18,
    )

    output_card = ft.Container(
        content=ft.Column(
            _controls(
                ft.Text(
                    "Carpeta de destino",
                    size=17,
                    color=INK,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Row(
                    _controls(
                        ft.Icon(ft.Icons.FOLDER_OPEN, color=ACCENT, size=22),
                        output_path_text,
                        output_button,
                    ),
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ),
            spacing=14,
        ),
        padding=card_padding,
        bgcolor=CARD,
        border_radius=18,
    )

    progress_card = ft.Container(
        content=ft.Column(
            _controls(
                ft.Row(
                    _controls(
                        ft.Column(
                            _controls(
                                ft.Text(
                                    "Progreso de conversión",
                                    size=17,
                                    color=INK,
                                    weight=ft.FontWeight.BOLD,
                                ),
                                status_text,
                            ),
                            spacing=5,
                            expand=True,
                        ),
                        ft.Container(
                            content=ft.Row(
                                _controls(
                                    ft.Icon(
                                        ft.Icons.TIMER_OUTLINED,
                                        color=ACCENT,
                                        size=21,
                                    ),
                                    elapsed_text,
                                ),
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            padding=ft.Padding(left=12, top=8, right=12, bottom=8),
                            bgcolor=ACCENT_LIGHT,
                            border_radius=12,
                        ),
                    ),
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    _controls(progress_label, progress_count),
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                progress_bar,
                current_file_text,
                convert_button,
                result_list,
            ),
            spacing=14,
        ),
        padding=card_padding,
        bgcolor=CARD,
        border_radius=18,
    )

    page.add(
        ft.Container(
            content=ft.Column(
                _controls(
                    ft.Row(
                        _controls(
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.AUTO_AWESOME,
                                    color=CARD,
                                    size=27,
                                ),
                                width=54,
                                height=54,
                                alignment=ft.Alignment.CENTER,
                                bgcolor=ACCENT,
                                border_radius=16,
                            ),
                            ft.Column(
                                _controls(
                                    ft.Text(
                                        "PDF a Markdown",
                                        size=29,
                                        color=INK,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Text(
                                        "Convierte documentos localmente, "
                                        "con control de cada archivo.",
                                        size=14,
                                        color=MUTED,
                                    ),
                                ),
                                spacing=4,
                            ),
                        ),
                        spacing=16,
                    ),
                    file_card,
                    output_card,
                    progress_card,
                    ft.Text(
                        "Tus archivos se procesan en este equipo; no se suben a Internet.",
                        size=12,
                        color=MUTED,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ),
                spacing=16,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=820,
        )
    )


if __name__ == "__main__":
    ft.run(main)
