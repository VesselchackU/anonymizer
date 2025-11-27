import configparser
import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

import pyperclip

from component.label_frame_bottom_left import LabelFrameBottomLeft
from component.label_frame_right import LabelFrameRight
from component.label_frame_top_left import LabelFrameTopLeft
from config import settings
from core import AnonymizationService, FileProcessor, PseudonymStore


class AnonymizerApp:
    def __init__(self, root) -> None:
        self.entry_anon: Optional[ttk.Entry] = None
        self.entry_pseudonym: Optional[ttk.Entry] = None
        self.btn_add_pair: Optional[ttk.Button] = None
        self.frame1: Optional[LabelFrameTopLeft] = None
        self.frame2: Optional[LabelFrameBottomLeft] = None
        self.frame3: Optional[LabelFrameRight] = None
        self.config_file: Path = self.get_config_path()
        self.config = configparser.ConfigParser()
        self.root = root
        self.root.title("Анонимизатор текстов")
        self.root.geometry("640x480")

        self.setup_logging()
        self.load_config()

        self.store = PseudonymStore(self.get_pseudos_path())
        self.store.load()

        self.anon_dict = self.store.anon_dict
        self.deanon_dict = self.store.deanon_dict

        self.file_processor = FileProcessor()
        self.service = AnonymizationService(self.store, self.file_processor)

        self.setup_gui()
        self.center_or_restore_window()
        self.bind_events()

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

    def load_config(self):
        if not self.config_file.exists():
            self.create_default_config()

        self.config.read(self.config_file, encoding="utf-8")

    @staticmethod
    def get_config_path() -> Path:
        if settings.main_ini_dir:
            return Path(settings.main_ini_dir) / "main.ini"
        return Path(__file__).parent / "main.ini"

    @staticmethod
    def get_pseudos_path() -> Path:
        if settings.pseudos_list_dir:
            return Path(settings.pseudos_list_dir) / "pseudos.json"
        return Path(__file__).parent / "pseudos.json"

    def create_default_config(self):
        self.config["window"] = {"coord_x": "100", "coord_y": "100"}
        self.config["config"] = {
            "load_dir": str(Path.cwd()),
            "last_open_dir": str(Path.cwd()),
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)

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

    def setup_frame1(self, parent):
        self.frame1 = LabelFrameTopLeft(parent, add_pair_func=self.add_pair)
        logging.info(self.frame1.__dict__)

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
        try:
            x = self.config.getint("window", "coord_x")
            y = self.config.getint("window", "coord_y")
            self.root.geometry(f"+{x}+{y}")
        except (configparser.NoOptionError, ValueError):
            self.root.eval("tk::PlaceWindow . center")

    def on_window_move(self, event):
        if event.widget == self.root:
            self.config.set("window", "coord_x", str(self.root.winfo_x()))
            self.config.set("window", "coord_y", str(self.root.winfo_y()))
            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)

    def on_anon_entry_change(self, event):
        if self.frame1.entry_anon.get().strip():
            self.frame1.btn_add_pair.config(state="normal")
        else:
            self.frame1.btn_add_pair.config(state="disabled")

    def on_list_select(self, event):
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
        self.frame1.entry_pseudonym.delete(0, tk.END)
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

    def load_filename(self) -> str:
        load_dir = self.config.get("config", "last_open_dir", fallback=str(Path.cwd()))
        filename = filedialog.askopenfilename(
            initialdir=load_dir,
            filetypes=[
                ("Поддерживаемые файлы", ["*.txt", "*.doc", "*.docx"]),
                ("Все файлы", "*.*"),
            ],
        )
        self.config.set("config", "last_open_dir", str(Path(filename).parent))
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)
        return filename

    def anonymize_file(self):
        filename = self.load_filename()

        if not filename:
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

                result = self.service.anonymize_file(filename)
                self.root.after(0, lambda: self.show_anonymization_result(result))
            except Exception as e:
                logging.error(f"Ошибка анонимизации: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "str(e)"))
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def show_anonymization_result(self, message: str):
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

    def deanonymize_file(self):
        filename = self.load_filename()

        if not filename:
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

                result = self.service.deanonymize_file(filename)
                self.root.after(0, lambda: self.show_deanonymization_result(result))
            except Exception as e:
                # self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
                self.root.after(0, messagebox.showerror, "Ошибка", str(e))
                raise e
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def deanonymize_file_to_file(self):
        filename = self.load_filename()

        if not filename:
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

                result = self.service.deanonymize_file(
                    filename,
                    to_clipboard=False,
                    to_file=True,
                )
                self.root.after(0, lambda: self.show_deanonymization_result(result))
            except Exception as e:
                self.root.after(0, messagebox.showerror, "Ошибка", str(e))
                raise e
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def show_deanonymization_result(self, message: str):
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


def main():
    root = tk.Tk()
    app = AnonymizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
