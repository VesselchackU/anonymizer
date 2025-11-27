from tkinter import Misc, ttk
from typing import Optional


def add_captioned_entry(
    parent: Misc,
    caption: Optional[str] = None,
    grid_row: Optional[int] = None,
    grid_column: Optional[int] = None,
    label_sticky: str = "w",
    entry_sticky: str = "ew",
) -> ttk.Entry:
    if caption:
        label = ttk.Label(parent, text=caption)
        if grid_row or grid_column:
            label.grid(
                row=grid_row or 0,
                column=grid_column or 0,
                sticky=label_sticky,
            )
    entry = ttk.Entry(parent, width=30)
    if grid_row is not None and grid_column is not None:
        entry.grid(
            row=grid_row,
            column=grid_column,
            sticky=entry_sticky,
            pady=(0, 5),
        )
    return entry
