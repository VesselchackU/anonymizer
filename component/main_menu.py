import tkinter as tk
from tkinter import Misc
from typing import Callable


class MainMenu(tk.Menu):
    """Главное меню приложения.
    @param parent: корневое окно приложения;
    @param on_anonymize_file: обработчик пункта
    «Анонимизировать файл...»;
    @param on_deanon_file_to_file: обработчик пункта
    «Деанонимизировать файл --> файл...»;
    @param on_deanon_file_to_clipboard: обработчик пункта
    «Деанонимизировать файл --> буфер...»;
    @param on_deanon_clipboard: обработчик пункта
    «Деанонимизировать буфер --> буфер»;
    @param on_new_pseudos_file: обработчик пункта
    «Новый файл псевдонимов...»;
    @param on_open_pseudos_file: обработчик пункта
    «Открыть файл псевдонимов...»;
    @param on_save_pseudos_file_as: обработчик пункта
    «Сохранить файл псевдонимов как...»;
    @param on_show_about: обработчик пункта «О программе...»;
    @param on_open_help: обработчик пункта
    «Справка (руководство пользователя)»;
    """

    def __init__(
        self,
        parent: Misc,
        *,
        on_anonymize_file: Callable[[], None],
        on_deanon_file_to_file: Callable[[], None],
        on_deanon_file_to_clipboard: Callable[[], None],
        on_deanon_clipboard: Callable[[], None],
        on_new_pseudos_file: Callable[[], None],
        on_open_pseudos_file: Callable[[], None],
        on_save_pseudos_file_as: Callable[[], None],
        on_show_about: Callable[[], None],
        on_open_help: Callable[[], None],
    ) -> None:
        super().__init__(parent)

        self._create_file_menu(
            on_anonymize_file=on_anonymize_file,
            on_deanon_file_to_file=on_deanon_file_to_file,
            on_deanon_file_to_clipboard=on_deanon_file_to_clipboard,
            on_deanon_clipboard=on_deanon_clipboard,
        )
        self._create_pseudos_menu(
            on_new_pseudos_file=on_new_pseudos_file,
            on_open_pseudos_file=on_open_pseudos_file,
            on_save_pseudos_file_as=on_save_pseudos_file_as,
        )
        self._create_help_menu(
            on_show_about=on_show_about,
            on_open_help=on_open_help,
        )

        parent["menu"] = self

    def _create_file_menu(
        self,
        *,
        on_anonymize_file: Callable[[], None],
        on_deanon_file_to_file: Callable[[], None],
        on_deanon_file_to_clipboard: Callable[[], None],
        on_deanon_clipboard: Callable[[], None],
    ) -> None:
        """Создаёт пункт верхнего меню «Файл»;
        @param on_anonymize_file: обработчик анонимизации файла;
        @param on_deanon_file_to_file: обработчик деанонимизации
        из файла в файл;
        @param on_deanon_file_to_clipboard: обработчик деанонимизации
        файла в буфер;
        @param on_deanon_clipboard: обработчик деанонимизации текста
        из буфера;
        """
        file_menu = tk.Menu(self, tearoff=False)
        file_menu.add_command(
            label="Анонимизировать файл...",
            command=on_anonymize_file,
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Деанонимизировать файл --> файл...",
            command=on_deanon_file_to_file,
        )
        file_menu.add_command(
            label="Деанонимизировать файл --> буфер...",
            command=on_deanon_file_to_clipboard,
        )
        file_menu.add_command(
            label="Деанонимизировать буфер --> буфер",
            command=on_deanon_clipboard,
        )

        self.add_cascade(label="Файл", menu=file_menu)

    def _create_pseudos_menu(
        self,
        *,
        on_new_pseudos_file: Callable[[], None],
        on_open_pseudos_file: Callable[[], None],
        on_save_pseudos_file_as: Callable[[], None],
    ) -> None:
        """Создаёт пункт верхнего меню «Псевдонимы»;
        @param on_new_pseudos_file: обработчик пункта
        «Новый файл псевдонимов...»;
        @param on_open_pseudos_file: обработчик пункта
        «Открыть файл псевдонимов...»;
        @param on_save_pseudos_file_as: обработчик пункта
        «Сохранить файл псевдонимов как...»;
        """
        pseudo_menu = tk.Menu(self, tearoff=False)
        pseudo_menu.add_command(
            label="Новый файл псевдонимов...",
            command=on_new_pseudos_file,
        )
        pseudo_menu.add_command(
            label="Открыть файл псевдонимов...",
            command=on_open_pseudos_file,
        )
        pseudo_menu.add_command(
            label="Сохранить файл псевдонимов как...",
            command=on_save_pseudos_file_as,
        )

        self.add_cascade(label="Псевдонимы", menu=pseudo_menu)

    def _create_help_menu(
        self,
        *,
        on_show_about: Callable[[], None],
        on_open_help: Callable[[], None],
    ) -> None:
        """Создаёт пункт верхнего меню «Помощь»;
        @param on_show_about: обработчик пункта «О программе...»;
        @param on_open_help: обработчик пункта
        «Справка (руководство пользователя)»;
        """
        help_menu = tk.Menu(self, tearoff=False)
        help_menu.add_command(
            label="О программе...",
            command=on_show_about,
        )
        help_menu.add_command(
            label="Справка (руководство пользователя)",
            command=on_open_help,
        )

        self.add_cascade(label="Помощь", menu=help_menu)
