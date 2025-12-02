import logging
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Iterable, List, Optional, Tuple, reveal_type

import pyperclip

from component.label import LinkLabel
from component.label_frame_bottom_left import LabelFrameBottomLeft
from component.label_frame_right import LabelFrameRight
from component.label_frame_top_left import LabelFrameTopLeft
from component.main_menu import MainMenu
from config import AppConfig, settings
from core import AnonymizationService, FileProcessor, PseudonymStore


class AnonymizerApp:
    frame1: LabelFrameTopLeft
    frame2: LabelFrameBottomLeft
    frame3: LabelFrameRight
    main_menu: MainMenu
    _about_icon_ref: tk.PhotoImage

    def __init__(self, root) -> None:
        self.root = root
        self.root.title("Анонимизатор текстов")
        self.root.geometry("640x480")

        self.setup_logging()
        self._window_icon_ref: tk.PhotoImage | None = self.set_window_icon()
        self.app_config: AppConfig = AppConfig(AppConfig.default_path())

        self.store = PseudonymStore(self.get_pseudos_path())
        self.store.load()

        self.anon_dict = self.store.anon_dict
        self.deanon_dict = self.store.deanon_dict

        self.file_processor = FileProcessor()
        self.service = AnonymizationService(self.store, self.file_processor)

        self.set_window_icon()

        self.setup_gui()
        self.setup_menu()
        self.center_or_restore_window()
        self.bind_events()

    def set_window_icon(self) -> tk.PhotoImage | None:
        """Устанавливает иконку окна приложения, если файл найден."""
        icons_dir = Path(__file__).parent / "icons"
        icon_path = icons_dir / "icon_app_64.png"

        if not icon_path.exists():
            return None

        try:
            icon_image = tk.PhotoImage(file=str(icon_path))
        except Exception as e:  # noqa: BLE001
            logging.warning("Не удалось загрузить иконку окна %s: %s", icon_path, e)
            return None

        # iconphoto работает кроссплатформенно
        self.root.iconphoto(True, icon_image)

        return icon_image

    @staticmethod
    def setup_logging():
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("anonymizer.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )

    def get_pseudos_path(self) -> Path:
        """Возвращает путь к текущему файлу псевдонимов;
        @return: объект Path с путём к файлу pseudos.json;
        @note: приоритет имеет путь из AppConfig, затем из настроек
        окружения, затем каталог модуля;
        """
        reveal_type(self.app_config)
        cfg_path = self.app_config.pseudos_file
        if cfg_path is not None:
            return cfg_path

        if settings.pseudos_list_dir:
            return Path(settings.pseudos_list_dir) / "pseudos.json"
        return Path(__file__).parent / "pseudos.json"

    def load_pseudos(self):
        self.store.load()

    def save_pseudos(self):
        self.store.save()

    def setup_gui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)

        self.setup_frame1(left_frame)
        self.setup_frame2(left_frame)
        self.setup_frame3(main_frame)

    def setup_menu(self) -> None:
        """Создаёт и привязывает главное меню приложения;
        Пункты меню «Файл» дублируют функциональность
        соответствующих кнопок;
        """
        self.main_menu = MainMenu(
            self.root,
            on_anonymize_file=self.anonymize_file,
            on_deanon_file_to_file=self.deanonymize_file_to_file,
            on_deanon_file_to_clipboard=self.deanonymize_file,
            on_deanon_clipboard=self.deanonymize_clipboard,
            on_new_pseudos_file=self.new_pseudos_file,
            on_open_pseudos_file=self.open_pseudos_file,
            on_save_pseudos_file_as=self.save_pseudos_file_as,
            on_show_about=self.show_about_dialog,
            on_open_help=self.open_user_guide,
        )

    def setup_frame1(self, parent):
        self.frame1 = LabelFrameTopLeft(parent, add_pair_func=self.add_pair)

    def setup_frame2(self, parent):
        self.frame2 = LabelFrameBottomLeft(
            parent,
            anonymize_func=self.anonymize_file,
            deanonymize_func=self.deanonymize_file,
            deanonymize_to_file_func=self.deanonymize_file_to_file,
            deanonymize_from_clipboard_func=self.deanonymize_clipboard,
        )

    def setup_frame3(self, parent):
        self.frame3 = LabelFrameRight(parent, self.delete_pair)
        self.update_anon_list()

    def bind_events(self):
        self.frame1.entry_anon.bind("<KeyRelease>", self.on_anon_entry_change)
        self.frame3.listbox_anon.bind("<<ListboxSelect>>", self.on_list_select)
        self.root.bind("<Configure>", self.on_window_move)

    def center_or_restore_window(self):
        pos = self.app_config.window_position
        if pos:
            x, y = pos
            self.root.geometry(f"+{x}+{y}")
        else:
            self.root.eval("tk::PlaceWindow . center")

    def on_window_move(self, event):
        if event.widget == self.root:
            self.app_config.window_position = (
                self.root.winfo_x(),
                self.root.winfo_y(),
            )

    def on_anon_entry_change(self, event):  # noqa: F841
        if self.frame1.entry_anon.get().strip():
            self.frame1.btn_add_pair.config(state="normal")
        else:
            self.frame1.btn_add_pair.config(state="disabled")

    def on_list_select(
        self,
        event,  # noqa: F841
    ):
        selection = self.frame3.listbox_anon.curselection()
        if selection:
            key = self.frame3.listbox_anon.get(selection[0])
            pseudonym = self.anon_dict.get(key, "")
            self.frame3.deanon_val_entry.config(state="normal")
            self.frame3.deanon_val_entry.delete(0, tk.END)
            self.frame3.deanon_val_entry.insert(0, pseudonym)
            self.frame3.deanon_val_entry.config(state="readonly")

    def generate_pseudonym(self, initial_pseudo: Optional[str] = None) -> str:
        return self.store.generate_pseudonym(initial_pseudo)

    def add_pair(self):
        key = self.frame1.entry_anon.get().strip()
        value = self.frame1.entry_pseudonym.get().strip()

        if not key:
            messagebox.showwarning("Предупреждение", "Введите текст для анонимизации")
            return

        if key in self.anon_dict:
            messagebox.showwarning("Предупреждение", "Такой ключ уже существует")
            return

        if not value:
            value = self.generate_pseudonym()

        if value in self.deanon_dict:
            value = self.generate_pseudonym(value)

        self.anon_dict[key] = value
        self.deanon_dict[value] = key

        self.save_pseudos()
        self.update_anon_list()

        self.frame1.entry_anon.delete(0, tk.END)
        self.frame1.entry_anon.focus()

        for i, item in enumerate(self.frame3.listbox_anon.get(0, tk.END)):
            if item == key:
                self.frame3.listbox_anon.selection_clear(0, tk.END)
                self.frame3.listbox_anon.selection_set(i)
                self.frame3.listbox_anon.see(i)
                break

    def delete_pair(self):
        selection = self.frame3.listbox_anon.curselection()
        if not selection:
            return

        key = self.frame3.listbox_anon.get(selection[0])

        if not messagebox.askyesno(
            "Подтверждение", f"Удалить пару '{key}' -> '{self.anon_dict[key]}'?"
        ):
            return

        value = self.anon_dict[key]
        del self.anon_dict[key]
        del self.deanon_dict[value]

        self.save_pseudos()
        self.update_anon_list()
        self.frame1.entry_anon.focus()

    def update_anon_list(self):
        self.frame3.listbox_anon.delete(0, tk.END)
        for key in sorted(self.anon_dict.keys()):
            self.frame3.listbox_anon.insert(tk.END, key)

    def get_replacement_order(self) -> List[Tuple[str, str]]:
        return self.store.get_replacement_order()

    def get_deanonymization_order(self) -> List[Tuple[str, str]]:
        return self.store.get_deanonymization_order()

    def get_pseudos_initial_dir(self) -> Path:
        """Возвращает каталог по умолчанию для диалогов файлов псевдонимов;
        @return: объект Path с директорией по умолчанию;
        """
        cfg_path = self.app_config.pseudos_file
        if cfg_path is not None and cfg_path.parent.exists():
            return cfg_path.parent

        if settings.pseudos_list_dir:
            env_dir = Path(settings.pseudos_list_dir)
            if env_dir.exists():
                return env_dir

        return Path(__file__).parent

    def _activate_pseudos_file(self, path: Path) -> None:
        """Переключает приложение на указанный файл псевдонимов;
        @param path: путь к JSON-файлу псевдонимов;
        """
        self.store.path = path
        # синхронизируем ссылки на словари
        self.anon_dict = self.store.anon_dict
        self.deanon_dict = self.store.deanon_dict
        self.app_config.pseudos_file = path
        self.update_anon_list()
        self.frame1.entry_anon.focus()

    def new_pseudos_file(self) -> None:
        """Создаёт новый файл псевдонимов;
        Показывает диалог сохранения *.json без варианта *.*;
        При существующем файле спрашивает подтверждение на замену;
        После создания переключает приложение на новый файл;
        """
        initial_dir = self.get_pseudos_initial_dir()
        filename = filedialog.asksaveasfilename(
            title="Новый файл псевдонимов",
            defaultextension=".json",
            filetypes=[("Файлы псевдонимов (*.json)", "*.json")],
            initialdir=str(initial_dir),
        )
        if not filename:
            return

        path = Path(filename)

        if path.exists():
            if not messagebox.askyesno(
                "Подтверждение",
                f"Файл '{path.name}' уже существует.\nЗаменить его?",
            ):
                return

        self.store.anon_dict.clear()
        self.store.deanon_dict.clear()
        self._activate_pseudos_file(path)
        self.save_pseudos()

    def open_pseudos_file(self) -> None:
        """Открывает существующий файл псевдонимов *.json;
        После открытия переключает приложение на этот файл;
        """
        initial_dir = self.get_pseudos_initial_dir()
        filename = filedialog.askopenfilename(
            title="Открыть файл псевдонимов",
            filetypes=[("Файлы псевдонимов (*.json)", "*.json")],
            initialdir=str(initial_dir),
        )
        if not filename:
            return

        path = Path(filename)
        self.store.path = path
        self.load_pseudos()
        self._activate_pseudos_file(path)

    def save_pseudos_file_as(self) -> None:
        """Сохраняет текущий словарь псевдонимов в новый файл *.json;
        При существующем файле спрашивает подтверждение на замену;
        После сохранения переключает приложение на новый файл;
        """
        initial_dir = self.get_pseudos_initial_dir()
        filename = filedialog.asksaveasfilename(
            title="Сохранить файл псевдонимов как...",
            defaultextension=".json",
            filetypes=[("Файлы псевдонимов (*.json)", "*.json")],
            initialdir=str(initial_dir),
        )
        if not filename:
            return

        path = Path(filename)

        if path.exists():
            if not messagebox.askyesno(
                "Подтверждение",
                f"Файл '{path.name}' уже существует.\nЗаменить его?",
            ):
                return

        self._activate_pseudos_file(path)
        self.save_pseudos()

    def show_about_dialog(self) -> None:
        """Открывает модальное окно «О программе...»;
        Окно ~300x300, неизменяемое, с логотипом 64x64 и заглушкой текста;
        """
        about = tk.Toplevel(self.root)
        about.title("О программе")
        about.resizable(False, False)
        about.transient(self.root)
        about.grab_set()
        about.geometry("300x350")

        container = ttk.Frame(about, padding=10, borderwidth=2)
        container.pack(fill=tk.BOTH, expand=True)

        icon_path = Path(__file__).parent / "icons" / "icon_app_64.png"
        if icon_path.exists():
            try:
                img = tk.PhotoImage(file=str(icon_path))
                icon_label = ttk.Label(container, image=img)
                self._about_icon_ref = img  # не даём GC всё сломать
                icon_label.pack(pady=(0, 10))
            except Exception as e:  # noqa: BLE001
                logging.warning(
                    "Не удалось загрузить иконку для окна 'О программе': %s",
                    e,
                )

        about_text = (
            "Анонимизатор текстов\n"
            "версия: <1.0.001>\n\n"
            "Программа для анонимизации и деанонимизации текстовых "
            "документов и содержимого буфера обмена.\n\n"
            "© Автор - Виктор Ушакевич\n\n"
            "Код приложения можно посмотреть здесь:"
        )

        label = ttk.Label(
            container,
            text=about_text,
            justify="center",
            anchor="center",
            wraplength=260,
        )
        label.pack(pady=(0, 10), anchor="center")

        code_link_text = "https://github.com/VesselchackU/anonymizer"
        code_link_label = LinkLabel(
            container,
            url=code_link_text,
            justify="center",
            anchor="center",
            wraplength=260,
        )
        code_link_label.pack(fill=tk.BOTH, expand=True)

        close_btn = ttk.Button(container, text="Закрыть", command=about.destroy)
        close_btn.pack(pady=(10, 0))

        self._center_child_window(about)

    def _center_child_window(self, window: tk.Toplevel) -> None:
        """Центрирует дочернее окно относительно основного окна;
        @param window: окно Toplevel, которое нужно центрировать;
        """
        window.update_idletasks()
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        win_w = window.winfo_width()
        win_h = window.winfo_height()

        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        window.geometry(f"+{x}+{y}")

    @staticmethod
    def open_user_guide() -> None:
        """Открывает руководство пользователя в браузере;
        Использует файл index.html из каталога users_guideline;
        """
        guide_path = Path(__file__).parent / "users_guideline" / "index.html"
        if not guide_path.exists():
            messagebox.showerror(
                "Ошибка",
                f"Файл справки не найден:\n{guide_path}",
            )
            return

        try:
            webbrowser.open(guide_path.as_uri())
        except Exception as e:  # noqa: BLE001
            logging.exception("Ошибка открытия руководства пользователя")
            messagebox.showerror(
                "Ошибка",
                f"Не удалось открыть руководство пользователя: {e}",
            )

    def load_filename(
        self,
        filetypes: Iterable[tuple[str, str | list[str] | tuple[str, ...]]]
        | None = None,
    ) -> str:
        """
        Открывает диалог выбора файла для загрузки и возвращает путь к выбранному файлу.

        При успешном выборе обновляет сохранённую директорию последнего открытия
        в конфигурации приложения (app_config.last_open_dir);

        @param filetypes: список кортежей, описывающих допустимые типы файлов
            в формате (описание, шаблон), где шаблон может быть строкой, списком
            или кортежем расширений (например: '*.txt' или ['*.doc', '*.docx']);
            если None или не задан, используется список по умолчанию:
            - ('Поддерживаемые файлы', ['*.txt', '*.doc', '*.docx']),
            - ('Все файлы', '*.*');
        @return: полный путь к выбранному файлу в виде строки; пустая строка,
            если диалог был отменён;
        @note: при выборе файла автоматически обновляется
            self.app_config.last_open_dir;
        """
        load_dir = self.app_config.last_open_dir

        filename = filedialog.askopenfilename(
            initialdir=str(load_dir),
            filetypes=filetypes
            or [
                ("Поддерживаемые файлы", ["*.txt", "*.doc", "*.docx"]),
                ("Все файлы", "*.*"),
            ],
        )

        if filename:
            self.app_config.last_open_dir = Path(filename).parent

        return filename

    def anonymize_file(self) -> None:
        filename = self.load_filename()
        if not filename:
            return

        def task() -> str:
            return self.service.anonymize_file(filename)

        def on_success(msg: str) -> None:
            self.show_anonymization_result(msg)

        self.run_in_thread(task, on_success, error_title="Ошибка анонимизации")

    @staticmethod
    def show_anonymization_result(message: str):
        messagebox.showinfo("Успех", message)

    def restore_ui_state(self):
        self.root.config(cursor="")
        for btn in [
            self.frame2.btn_anon,
            self.frame2.btn_deanon_file,
            self.frame2.btn_deanon_to_file,
            self.frame2.btn_deanon_clipboard,
        ]:
            btn.config(state="normal")

    def deanonymize_file(self) -> None:
        filename = self.load_filename()
        if not filename:
            return

        def task() -> str:
            return self.service.deanonymize_file(filename)

        def on_success(msg: str) -> None:
            self.show_deanonymization_result(msg)

        self.run_in_thread(task, on_success, error_title="Ошибка деанонимизации")

    def deanonymize_file_to_file(self) -> None:
        filename = self.load_filename()
        if not filename:
            return

        def task() -> str:
            return self.service.deanonymize_file(
                filename,
                to_clipboard=False,
                to_file=True,
            )

        def on_success(msg: str) -> None:
            self.show_deanonymization_result(msg)

        self.run_in_thread(task, on_success, error_title="Ошибка деанонимизации")

    @staticmethod
    def show_deanonymization_result(message: str):
        messagebox.showinfo("Успех", message)

    def deanonymize_clipboard(self):
        try:
            clipboard_content = pyperclip.paste()
            if not clipboard_content.strip():
                messagebox.showwarning("Предупреждение", "Буфер обмена пуст")
                return
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать буфер обмена: {e}")
            return

        def worker():
            try:
                self.root.config(cursor="watch")
                for btn in [
                    self.frame2.btn_anon,
                    self.frame2.btn_deanon_file,
                    self.frame2.btn_deanon_to_file,
                    self.frame2.btn_deanon_clipboard,
                ]:
                    btn.config(state="disabled")

                replacements = self.get_deanonymization_order()
                content = clipboard_content

                for pattern, original in replacements:
                    content = content.replace(pattern, original)

                pyperclip.copy(content)
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "Успех", "Деанонимизированный текст скопирован в буфер обмена."
                    ),
                )
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def set_busy(self, busy: bool) -> None:
        """
        Переключает состояние интерфейса между «занят» и «свободен».
        Меняет курсор и активность основных кнопок.
        """
        self.root.config(cursor="watch" if busy else "")

        buttons = [
            self.frame2.btn_anon,
            self.frame2.btn_deanon_file,
            self.frame2.btn_deanon_to_file,
            self.frame2.btn_deanon_clipboard,
            self.frame1.btn_add_pair,
        ]

        state = "disabled" if busy else "normal"
        for btn in buttons:
            btn.config(state=state)

    def run_in_thread(
        self,
        task: Callable[[], str],
        on_success: Callable[[str], None],
        error_title: str = "Ошибка",
    ) -> None:
        """
        Запускает задачу в фоновом потоке с автоматическим управлением
        состоянием интерфейса (индикатор загрузки) и обработкой результата

        @param task: функция без аргументов, выполняет фоновую работу
            и возвращает строку-результат;
        @param on_success: обработчик результата, вызывается
            в главном потоке через root.after() после успешного завершения;
        @param error_title: заголовок окна ошибки, отображается при исключении;
        """

        def worker():
            try:
                result = task()
                self.root.after(0, lambda: on_success(result))
            except Exception as e:
                logging.exception("Ошибка фоновой операции")
                err = str(e)
                self.root.after(
                    0,
                    lambda: messagebox.showerror(error_title, err),
                )
            finally:
                self.root.after(0, lambda: self.set_busy(False))

        self.set_busy(True)
        threading.Thread(target=worker, daemon=True).start()


def main():
    root = tk.Tk()
    app = AnonymizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
