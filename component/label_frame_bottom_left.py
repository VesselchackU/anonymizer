import tkinter as tk
from tkinter import ttk

from component.button import (
    AnonFileButton,
    DeanonClipboardButton,
    DeanonFileButton,
    DeanonToFileButton,
)


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
        self.btn_anon = AnonFileButton(self, command=anonymize_func)
        # self.btn_anon.pack(fill=tk.X, pady=2)
        self.btn_anon.grid(row=0, column=0, sticky="nsew")

        # Кнопка Деанонимизировать файл
        self.btn_deanon_file = DeanonFileButton(
            self,
            command=deanonymize_func,
        )
        # self.btn_deanon_file.pack(fill=tk.X, pady=2)
        self.btn_deanon_file.grid(row=0, column=1, sticky="nsew")

        # Кнопка Деанонимизировать в файл
        self.btn_deanon_to_file = DeanonToFileButton(
            self,
            command=deanonymize_to_file_func,
        )
        # self.btn_deanon_to_file.pack(fill=tk.X, pady=2)
        self.btn_deanon_to_file.grid(row=1, column=0, sticky="nsew")

        # Кнопка Деанонимизировать из буфера
        self.btn_deanon_clipboard = DeanonClipboardButton(
            self,
            command=deanonymize_from_clipboard_func,
        )
        # self.btn_deanon_clipboard.pack(fill=tk.X, pady=2)
        self.btn_deanon_clipboard.grid(row=1, column=1, sticky="nsew")
