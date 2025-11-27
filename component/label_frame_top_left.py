from tkinter import Misc, ttk

from component.entry import add_captioned_entry


class LabelFrameTopLeft(ttk.Labelframe):
    def __init__(self, parent: Misc | None = None, *, add_pair_func):
        super().__init__(parent, text="Добавление псевдонима", padding="10")
        self.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.entry_anon = add_captioned_entry(self, "Анонимизировать", 0, 0)
        self.entry_pseudonym = add_captioned_entry(self, "Псевдоним", 1, 0)
        self.btn_add_pair = ttk.Button(
            self, text="Добавить", state="disabled", command=add_pair_func
        )
        self.btn_add_pair.grid(row=4, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)
