import tkinter as tk
from tkinter import ttk

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi-Page Tkinter App")
        self.geometry("400x300")

        self.frames = {}
        for F in (Page1, Page2):
            page_name = F.__name__
            frame = F(parent=self, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("Page1")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

class Page1(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = ttk.Label(self, text="This is Page 1")
        label.pack(pady=20)
        button = ttk.Button(self, text="Go to Page 2",
                            command=lambda: controller.show_frame("Page2"))
        button.pack()

class Page2(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        label = ttk.Label(self, text="This is Page 2")
        label.pack(pady=20)
        button = ttk.Button(self, text="Go to Page 1",
                            command=lambda: controller.show_frame("Page1"))
        button.pack()

if __name__ == "__main__":
    app = App()
    app.mainloop()
