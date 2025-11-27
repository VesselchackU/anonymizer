import tkinter as tk
from tkinter import ttk


class LabelFrameRight(ttk.LabelFrame):
    def __init__(self, parent, delete_command, *args, **kwargs):
        """
        parent         – родительский контейнер (например, main_frame)
        delete_command – функция/метод, который надо вызвать при нажатии
                         кнопки "Удалить"
        """
        super().__init__(
            parent, text="Список псевдонимов", padding="5", *args, **kwargs
        )

        self.grid(row=0, column=1, sticky="nsew")

        # Настройка растяжения по сетке (на всякий
        # случай, чтобы список нормально расширялся)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Список псевдонимов
        self.listbox_anon = tk.Listbox(self, selectmode=tk.SINGLE)
        self.listbox_anon.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Подпись и поле для отображения выбранного псевдонима
        ttk.Label(self, text="Псевдоним:").pack(anchor="w")

        self.deanon_val_entry = ttk.Entry(self, state="readonly")
        self.deanon_val_entry.pack(fill=tk.X, pady=(0, 5))

        # Кнопка удаления
        self.btn_del_pair = ttk.Button(self, text="Удалить", command=delete_command)
        self.btn_del_pair.pack(anchor="e")
