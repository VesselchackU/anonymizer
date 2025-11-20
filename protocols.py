def set_close_protocol(window):
    def close():
        window.destroy()
        print("Window closed")

    window.protocol("WM_DELETE_WINDOW", close)
