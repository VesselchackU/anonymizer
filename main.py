import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import configparser
import json
import os
import logging
import threading
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import pyperclip
from datetime import datetime
from docxtpl import DocxTemplate


try:
    import textract
except ImportError:
    textract = None


class AnonymizerApp:
    def __init__(self, root):
        self.anon_entry = None
        self.config_file = None
        self.config = None
        self.root = root
        self.root.title("Анонимизатор текстов")
        self.root.geometry("640x480")

        self.anon_dict: Dict[str, str] = {}
        self.deanon_dict: Dict[str, str] = {}

        self.setup_logging()
        self.load_config()
        self.load_pseudos()
        self.setup_gui()
        self.center_or_restore_window()
        self.bind_events()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('anonymizer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def load_config(self):
        self.config = configparser.ConfigParser()
        self.config_file = self.get_config_path()

        if not self.config_file.exists():
            self.create_default_config()

        self.config.read(self.config_file, encoding='utf-8')

    def get_config_path(self) -> Path:
        from config import settings
        if settings.main_ini_dir:
            return Path(settings.main_ini_dir) / "main.ini"
        return Path(__file__).parent / "main.ini"

    def get_pseudos_path(self) -> Path:
        from config import settings
        if settings.pseudos_list_dir:
            return Path(settings.pseudos_list_dir) / "pseudos.json"
        return Path(__file__).parent / "pseudos.json"

    def create_default_config(self):
        self.config['window'] = {
            'coord_x': '100',
            'coord_y': '100'
        }
        self.config['config'] = {
            'load_dir': str(Path.cwd())
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def load_pseudos(self):
        pseudos_file = self.get_pseudos_path()
        try:
            if pseudos_file.exists():
                with open(pseudos_file, 'r', encoding='utf-8') as f:
                    self.anon_dict = json.load(f)
                self.deanon_dict = {v: k for k, v in self.anon_dict.items()}
                logging.info(f"Загружено {len(self.anon_dict)} псевдонимов")
        except Exception as e:
            logging.error(f"Ошибка загрузки pseudos.json: {e}")
            messagebox.showerror("Ошибка",
                                 f"Не удалось загрузить словарь псевдонимов: {e}")

    def save_pseudos(self):
        pseudos_file = self.get_pseudos_path()
        backup_file = pseudos_file.with_suffix('.json.bak')

        try:
            if pseudos_file.exists():
                shutil.copy2(pseudos_file, backup_file)

            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=pseudos_file.parent,
                                             delete=False) as tmp:
                json.dump(self.anon_dict, tmp, ensure_ascii=False, indent=2)
                tmp_path = tmp.name

            os.replace(tmp_path, pseudos_file)
            logging.info("Словарь псевдонимов сохранён")
        except Exception as e:
            logging.error(f"Ошибка сохранения pseudos.json: {e}")
            messagebox.showerror("Ошибка",
                                 f"Не удалось сохранить словарь псевдонимов: {e}")

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
        frame = ttk.LabelFrame(parent, text="Добавление псевдонима", padding="5")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        ttk.Label(frame, text="Анонимизировать:").grid(row=0, column=0, sticky="w")
        self.anon_entry = ttk.Entry(frame, width=30)
        self.anon_entry.grid(row=1, column=0, sticky="ew", pady=(0, 5))

        ttk.Label(frame, text="Псевдоним:").grid(row=2, column=0, sticky="w")
        self.pseudonym_entry = ttk.Entry(frame, width=30)
        self.pseudonym_entry.grid(row=3, column=0, sticky="ew", pady=(0, 5))

        self.add_button = ttk.Button(frame, text="Добавить", command=self.add_pair,
                                     state="disabled")
        self.add_button.grid(row=4, column=0, sticky="w")

        frame.columnconfigure(0, weight=1)

    def setup_frame2(self, parent):
        frame = ttk.LabelFrame(parent, text="Операции", padding="5")
        frame.grid(row=1, column=0, sticky="nsew")

        self.anon_file_btn = ttk.Button(frame, text="Анонимизировать файл",
                                        command=self.anonymize_file)
        self.anon_file_btn.pack(fill=tk.X, pady=2)

        self.deanon_file_btn = ttk.Button(frame, text="Деанонимизировать в буфер",
                                          command=self.deanonymize_file)
        self.deanon_file_btn.pack(fill=tk.X, pady=2)

        self.deanon_clipboard_btn = ttk.Button(frame, text="Деанонимизировать из буфера",
                                               command=self.deanonymize_clipboard)
        self.deanon_clipboard_btn.pack(fill=tk.X, pady=2)

    def setup_frame3(self, parent):
        frame = ttk.LabelFrame(parent, text="Список псевдонимов", padding="5")
        frame.grid(row=0, column=1, sticky="nsew")

        self.anon_list = tk.Listbox(frame, selectmode=tk.SINGLE)
        self.anon_list.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        ttk.Label(frame, text="Псевдоним:").pack(anchor="w")
        self.deanon_val_entry = ttk.Entry(frame, state="readonly")
        self.deanon_val_entry.pack(fill=tk.X, pady=(0, 5))

        self.del_button = ttk.Button(frame, text="Удалить", command=self.delete_pair)
        self.del_button.pack(anchor="e")

        self.update_anon_list()

    def bind_events(self):
        self.anon_entry.bind('<KeyRelease>', self.on_anon_entry_change)
        self.anon_list.bind('<<ListboxSelect>>', self.on_list_select)
        self.root.bind('<Configure>', self.on_window_move)

    def center_or_restore_window(self):
        try:
            x = self.config.getint('window', 'coord_x')
            y = self.config.getint('window', 'coord_y')
            self.root.geometry(f"+{x}+{y}")
        except (configparser.NoOptionError, ValueError):
            self.root.eval('tk::PlaceWindow . center')

    def on_window_move(self, event):
        if event.widget == self.root:
            self.config.set('window', 'coord_x', str(self.root.winfo_x()))
            self.config.set('window', 'coord_y', str(self.root.winfo_y()))
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)

    def on_anon_entry_change(self, event):
        if self.anon_entry.get().strip():
            self.add_button.config(state="normal")
        else:
            self.add_button.config(state="disabled")

    def on_list_select(self, event):
        selection = self.anon_list.curselection()
        if selection:
            key = self.anon_list.get(selection[0])
            pseudonym = self.anon_dict.get(key, "")
            self.deanon_val_entry.config(state="normal")
            self.deanon_val_entry.delete(0, tk.END)
            self.deanon_val_entry.insert(0, pseudonym)
            self.deanon_val_entry.config(state="readonly")

    def generate_pseudonym(self) -> str:
        max_num = 0
        for pseudo in self.deanon_dict.keys():
            if pseudo.startswith("ЗАМЕНА"):
                try:
                    num_str = pseudo[6:]
                    num = int(num_str)
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        new_num = max_num + 1
        return f"ЗАМЕНА{new_num:03d}"

    def add_pair(self):
        key = self.anon_entry.get().strip()
        value = self.pseudonym_entry.get().strip()

        if not key:
            messagebox.showwarning("Предупреждение", "Введите текст для анонимизации")
            return

        if key in self.anon_dict:
            messagebox.showwarning("Предупреждение", "Такой ключ уже существует")
            return

        if not value:
            value = self.generate_pseudonym()

        if value in self.deanon_dict:
            messagebox.showwarning("Предупреждение", "Такой псевдоним уже используется")
            return

        self.anon_dict[key] = value
        self.deanon_dict[value] = key

        self.save_pseudos()
        self.update_anon_list()

        self.anon_entry.delete(0, tk.END)
        self.pseudonym_entry.delete(0, tk.END)
        self.anon_entry.focus()

        for i, item in enumerate(self.anon_list.get(0, tk.END)):
            if item == key:
                self.anon_list.selection_clear(0, tk.END)
                self.anon_list.selection_set(i)
                self.anon_list.see(i)
                break

    def delete_pair(self):
        selection = self.anon_list.curselection()
        if not selection:
            return

        key = self.anon_list.get(selection[0])

        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить пару '{key}' -> '{self.anon_dict[key]}'?"):
            return

        value = self.anon_dict[key]
        del self.anon_dict[key]
        del self.deanon_dict[value]

        self.save_pseudos()
        self.update_anon_list()
        self.anon_entry.focus()

    def update_anon_list(self):
        self.anon_list.delete(0, tk.END)
        for key in sorted(self.anon_dict.keys()):
            self.anon_list.insert(tk.END, key)

    def get_replacement_order(self) -> List[Tuple[str, str]]:
        items = list(self.anon_dict.items())
        items.sort(key=lambda x: (-len(x[0]), x[0]))
        return items

    def get_deanonymization_order(self) -> List[Tuple[str, str]]:
        items = [(f"[{pseudo}]", original) for pseudo, original in
                 self.deanon_dict.items()]
        items.sort(key=lambda x: (-len(x[0]), x[0]))
        return items

    def anonymize_file(self):
        load_dir = self.config.get('config', 'load_dir', fallback=str(Path.cwd()))
        filename = filedialog.askopenfilename(
            initialdir=load_dir,
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Word документы", "*.docx"),
                ("Word документы (старые)", "*.doc"),
                ("Все файлы", "*.*")
            ]
        )

        if not filename:
            return

        def worker():
            try:
                self.root.config(cursor="watch")
                for btn in [self.anon_file_btn, self.deanon_file_btn,
                            self.deanon_clipboard_btn]:
                    btn.config(state="disabled")

                result = self.process_file_anonymization(filename)
                self.root.after(0, lambda: self.show_anonymization_result(result))
            except Exception as e:
                logging.error(f"Ошибка анонимизации: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "str(e)"))
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def process_file_anonymization(self, filename: str) -> str:
        file_path = Path(filename)
        replacements = self.get_replacement_order()

        if file_path.suffix.lower() == '.txt':
            return self.process_txt_file(file_path, replacements)
        elif file_path.suffix.lower() == '.docx':
            return self.process_docx_file(file_path, replacements, anonymize=True)
        elif file_path.suffix.lower() == '.doc':
            return self.process_doc_file(file_path, replacements, anonymize=True)
        else:
            raise ValueError("Неподдерживаемый формат файла")

    def process_txt_file(self, file_path: Path,
                         replacements: List[Tuple[str, str]]) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
            except UnicodeDecodeError as e:
                raise ValueError(f"Не удалось прочитать файл: {e}")

        for original, pseudo in replacements:
            content = content.replace(original, f"[{pseudo}]")

        output_path = self.get_output_path(file_path, "_аноним")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Файл сохранён как: {output_path.name}"

    def process_docx_file(self, file_path: Path, replacements: List[Tuple[str, str]],
                          anonymize: bool = True) -> str:
        if DocxTemplate is None:
            raise ValueError("Модуль docxtpl не установлен")

        try:
            doc = DocxTemplate(file_path)

            if anonymize:
                context = {}
                for original, pseudo in replacements:
                    context[original] = f"[{pseudo}]"

                doc.render(context)
            else:
                context = {}
                for pseudo_pattern, original in replacements:
                    clean_pseudo = pseudo_pattern[1:-1]  # Remove brackets
                    context[clean_pseudo] = original

                doc.render(context)

            suffix = "_аноним" if anonymize else "_деаном"
            output_path = self.get_output_path(file_path, suffix, ".docx")
            doc.save(output_path)

            return f"Файл сохранён как: {output_path.name}"
        except Exception as e:
            raise ValueError(f"Ошибка обработки .docx файла: {e}")

    def process_doc_file(self, file_path: Path, replacements: List[Tuple[str, str]],
                         anonymize: bool = True) -> str:
        if textract is None:
            raise ValueError(
                "Поддержка .doc требует textract; сконвертируйте в .docx или установите textract")

        try:
            text = textract.process(str(file_path)).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Ошибка чтения .doc файла: {e}")

        if anonymize:
            for original, pseudo in replacements:
                text = text.replace(original, f"[{pseudo}]")
        else:
            for pseudo_pattern, original in replacements:
                text = text.replace(pseudo_pattern, original)

        suffix = "_аноним" if anonymize else "_деаном"
        output_path = self.get_output_path(file_path, suffix, ".txt")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        return f"Файл сохранён как: {output_path.name}"

    def get_output_path(self, original_path: Path, suffix: str,
                        force_ext: str = None) -> Path:
        ext = force_ext if force_ext else original_path.suffix
        base_name = original_path.stem

        counter = 0
        while True:
            if counter == 0:
                new_name = f"{base_name}{suffix}{ext}"
            else:
                new_name = f"{base_name}{suffix}{counter:03d}{ext}"

            output_path = original_path.parent / new_name
            if not output_path.exists():
                return output_path
            counter += 1

    def show_anonymization_result(self, message: str):
        messagebox.showinfo("Успех", message)

    def restore_ui_state(self):
        self.root.config(cursor="")
        for btn in [self.anon_file_btn, self.deanon_file_btn, self.deanon_clipboard_btn]:
            btn.config(state="normal")

    def deanonymize_file(self):
        load_dir = self.config.get('config', 'load_dir', fallback=str(Path.cwd()))
        filename = filedialog.askopenfilename(
            initialdir=load_dir,
            filetypes=[
                ("Текстовые файлы", "*.txt"),
                ("Word документы", "*.docx"),
                ("Word документы (старые)", "*.doc"),
                ("Все файлы", "*.*")
            ]
        )

        if not filename:
            return

        def worker():
            try:
                self.root.config(cursor="watch")
                for btn in [self.anon_file_btn, self.deanon_file_btn,
                            self.deanon_clipboard_btn]:
                    btn.config(state="disabled")

                result = self.process_file_deanonymization(filename)
                self.root.after(0, lambda: self.show_deanonymization_result(result))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            finally:
                self.root.after(0, self.restore_ui_state)

        threading.Thread(target=worker, daemon=True).start()

    def process_file_deanonymization(self, filename: str) -> str:
        file_path = Path(filename)
        replacements = self.get_deanonymization_order()

        if file_path.suffix.lower() == '.txt':
            content = self.process_txt_file_deanonymize(file_path, replacements)
        elif file_path.suffix.lower() == '.docx':
            content = self.process_docx_file_deanonymize(file_path, replacements)
        elif file_path.suffix.lower() == '.doc':
            content = self.process_doc_file_deanonymize(file_path, replacements)
        else:
            raise ValueError("Неподдерживаемый формат файла")

        pyperclip.copy(content)
        return "Деанонимизированный текст скопирован в буфер обмена."

    def process_txt_file_deanonymize(self, file_path: Path,
                                     replacements: List[Tuple[str, str]]) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
            except UnicodeDecodeError as e:
                raise ValueError(f"Не удалось прочитать файл: {e}")

        for pattern, original in replacements:
            content = content.replace(pattern, original)

        return content

    def process_docx_file_deanonymize(self, file_path: Path,
                                      replacements: List[Tuple[str, str]]) -> str:
        if DocxTemplate is None:
            raise ValueError("Модуль docxtpl не установлен")

        try:
            return self.process_docx_file(file_path, replacements, anonymize=False)
        except Exception as e:
            raise ValueError(f"Ошибка деанонимизации .docx файла: {e}")

    def process_doc_file_deanonymize(self, file_path: Path,
                                     replacements: List[Tuple[str, str]]) -> str:
        if textract is None:
            raise ValueError(
                "Поддержка .doc требует textract; сконвертируйте в .docx или установите textract")

        try:
            content = textract.process(str(file_path)).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Ошибка чтения .doc файла: {e}")

        for pattern, original in replacements:
            content = content.replace(pattern, original)

        return content

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
                for btn in [self.anon_file_btn, self.deanon_file_btn,
                            self.deanon_clipboard_btn]:
                    btn.config(state="disabled")

                replacements = self.get_deanonymization_order()
                content = clipboard_content

                for pattern, original in replacements:
                    content = content.replace(pattern, original)

                pyperclip.copy(content)
                self.root.after(0, lambda: messagebox.showinfo("Успех",
                                                               "Деанонимизированный текст скопирован в буфер обмена."))
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
