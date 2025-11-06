from tkinter import *
from tkinter import ttk

from protocols import set_close_protocol

root = Tk()
root.title("Анонимайзер")
root.geometry("640x480+400+300")

frame = ttk.Frame(borderwidth=1, relief="solid", padding=[8, 10])
label = ttk.Label(frame, text="Hello, world!")
label.pack(anchor=NW)
entry = ttk.Entry(frame)
entry.pack(anchor=NW)
button = ttk.Button(frame, text="Закрыть")
button.pack(anchor=NW)
frame.pack(anchor=NW, fill=X, padx=5, pady=5)

set_close_protocol(root)


root.mainloop()
