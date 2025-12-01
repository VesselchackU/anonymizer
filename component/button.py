from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import Misc, ttk
from typing import Any, Callable, Optional

from config import settings


class AutoIconButton(ttk.Button):
    """Базовый класс для кнопок с автоматической загрузкой иконки;
    @param parent: родительский виджет;
    @param text: текст на кнопке;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог, в котором искать иконку. Если не указан,
    используется путь из config.settings.icons_dir или текущий каталог;
    @param icon_file: имя файла иконки. Если не указано, берётся имя
    класса в нижнем регистре с расширением .png;
    @param kwargs: дополнительные параметры, передаваемые в ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        text: str,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        icon_file: Optional[str] = None,
        **kwargs,
    ) -> None:
        if self.__class__ is AutoIconButton:
            raise TypeError(
                "Нельзя создавать экземпляры AutoIconButton напрямую; "
                "наследуйтесь и используйте конкретный подкласс."
            )

        resolved_dir = self._resolve_icon_dir(icon_dir)
        resolved_file = self._resolve_icon_file(icon_file)

        icon = self._load_icon(resolved_dir, resolved_file)

        if icon is not None:
            kwargs.setdefault("image", icon)
            kwargs.setdefault("compound", "left")

        super().__init__(parent, text=text, command=command, **kwargs)

        # Храним ссылку, чтобы GC не выкинул картинку.
        self._icon_ref = icon

    @staticmethod
    def _resolve_icon_dir(icon_dir: Optional[str | Path]) -> Path:
        """Определяет каталог с иконками;
        @param icon_dir: путь, переданный при создании кнопки;
        @return: объект Path с каталогом иконок.
        """
        if icon_dir is not None:
            return Path(icon_dir)

        settings_dir = getattr(settings, "icons_dir", None)
        if settings_dir:
            return Path(settings_dir)

        # Фоллбек: текущий каталог процесса, чтобы хоть куда-то смотреть.
        return Path.cwd()

    def _resolve_icon_file(self, icon_file: Optional[str]) -> str:
        """Определяет имя файла иконки;
        @param icon_file: имя файла иконки, если указано явно;
        @return: строка с именем файла иконки.
        """
        if icon_file:
            filename = icon_file
        else:
            # По ТЗ: lower(имя_класса) + .png
            filename = f"{self.__class__.__name__.lower()}.png"

        if not filename.lower().endswith(".png"):
            filename = f"{filename}.png"

        return filename

    @staticmethod
    def _load_icon(icon_dir: Path, icon_file: str) -> Optional[tk.PhotoImage]:
        """Пытается загрузить иконку из файловой системы;
        @param icon_dir: каталог, в котором ищем иконку;
        @param icon_file: имя файла иконки;
        @return: объект tk.PhotoImage или None, если не удалось загрузить.
        """
        icon_path = icon_dir / icon_file
        if not icon_path.exists():
            logging.info("Иконка не найдена: %s", icon_path)
            return None

        try:
            return tk.PhotoImage(file=str(icon_path))
        except Exception as e:  # noqa: BLE001
            logging.warning("Ошибка загрузки иконки %s: %s", icon_path, e)
            return None


class AddPairButton(AutoIconButton):
    """Кнопка добавления пары «оригинал–псевдоним»;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Добавить",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_add_pair_dark_32.png",
            **kwargs,
        )
        # Как и раньше, стартуем в disabled-состоянии.
        self.config(state="disabled")


class DeletePairButton(AutoIconButton):
    """Кнопка удаления пары «оригинал–псевдоним»;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Удалить",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_delete_pair_dark_32.png",
            **kwargs,
        )


class AnonFileButton(AutoIconButton):
    """Кнопка анонимизации файла;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Анонимизировать файл",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_anon_file_dark_32.png",
            **kwargs,
        )


class DeanonFileButton(AutoIconButton):
    """Кнопка деанонимизации файла на месте;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Деанон файл --> буфер",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_deanon_file_to_clipboard_dark_32.png",
            **kwargs,
        )


class DeanonToFileButton(AutoIconButton):
    """Кнопка деанонимизации в новый файл;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Деанон файл --> файл",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_deanon_to_file_dark_32.png",
            **kwargs,
        )


class DeanonClipboardButton(AutoIconButton):
    """Кнопка деанонимизации текста из буфера;
    @param parent: родительский виджет;
    @param command: функция, вызываемая при нажатии кнопки;
    @param icon_dir: каталог с иконками (опционально);
    @param kwargs: дополнительные параметры для ttk.Button.
    """

    def __init__(
        self,
        parent: Misc,
        *,
        command: str | Callable[[], Any],
        icon_dir: Optional[str | Path] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            text="Деанон буфер --> буфер",
            command=command,
            icon_dir=icon_dir,
            icon_file="icon_deanon_clipboard_to_clipboard_dark_32.png",
            **kwargs,
        )
