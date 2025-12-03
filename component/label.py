import webbrowser
from tkinter import ttk
from typing import Any, Callable


class LinkLabel(ttk.Label):
    def __init__(
        self,
        parent,
        *,
        url: str,
        text: str | None = None,
        command: Callable[[], Any] | None = None,
        **kwargs,
    ):
        kwargs.setdefault("foreground", "blue")
        kwargs.setdefault("cursor", "hand2")
        super().__init__(parent, text=text or url, **kwargs)

        self._command = command
        self.url = url

        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", lambda e: self.configure(foreground="red"))
        self.bind("<Leave>", lambda e: self.configure(foreground="blue"))

    def _on_click(self, event=None):
        if self._command is None:
            webbrowser.open(self.url)
            return
        self._command()
