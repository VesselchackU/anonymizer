import tkinter as tk
from tkinter import ttk


class LabelFrameBottomLeft(ttk.LabelFrame):
    def __init__(
        self,
        parent,
        *,
        anonymize_func,
        deanonymize_func,
        deanonymize_to_file_func,
        deanonymize_from_clipboard_func,
    ):
        super().__init__(parent, text="Операции", padding=5)
        self.grid(row=1, column=0, sticky="nsew")

        # Кнопка Анонимизировать файл
        self.btn_anon = ttk.Button(
            self, text="Анонимизировать файл", command=anonymize_func
        )
        self.btn_anon.pack(fill=tk.X, pady=2)

        # Кнопка Деанонимизировать из файла
        self.btn_deanon_file = ttk.Button(
            self,
            text="Деанонимизировать из файла",
            command=deanonymize_func,
        )
        self.btn_deanon_file.pack(fill=tk.X, pady=2)

        # Кнопка: деанонимизировать в файл
        self.btn_deanon_to_file = ttk.Button(
            self,
            text="Деанонимизировать в файл",
            command=deanonymize_to_file_func,
        )
        self.btn_deanon_to_file.pack(fill=tk.X, pady=2)

        # Кнопка Деанонимизировать из буфера
        self.btn_deanon_clipboard = ttk.Button(
            self,
            text="Деанонимизировать из буфера",
            command=deanonymize_from_clipboard_func,
        )
        self.btn_deanon_clipboard.pack(fill=tk.X, pady=2)
