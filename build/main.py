import tkinter as tk
from tkinter import font, PhotoImage, messagebox
import sys

# --- Import all our new frames ---
from login_frame import LoginFrame
from printer_frame import PrinterFrame
from user_frame import UserFrame
from history_frame import HistoryFrame
from prices_frame import PricesFrame
from help_frame import HelpFrame
from notification_frame import NotificationFrame # <--- IMPORT NotificationFrame

class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id = None
        self.fullname = None
        self.default_width = 859
        self.default_height = 534

        try:
            self.eye_image = PhotoImage(file=r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame0\view.png")
            self.eye_slash_image = PhotoImage(file=r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame0\hide.png")
        except tk.TclError:
            messagebox.showerror("Asset Error", "Could not find eye icons (view.png, hide.png).")
            self.destroy(); return

        self.title("Copy Corner Printing System")
        self.center_window(self.default_width, self.default_height)
        self.resizable(False, False)

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        login_frame = LoginFrame(parent=self.container, controller=self)
        self.frames[LoginFrame.__name__] = login_frame
        login_frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame(LoginFrame)

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_frame(self, frame_class):
        name = frame_class.__name__
        if name not in self.frames:
            frame = frame_class(parent=self.container, controller=self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        frame = self.frames[name]
        # --- Refresh data if the frame has a load method ---
        if hasattr(frame, "load_user_data"): frame.load_user_data()
        if hasattr(frame, "load_user_requests"): frame.load_user_requests()
        if hasattr(frame, "load_history"): frame.load_history()
        if hasattr(frame, "load_notifications"): frame.load_notifications() # <--- ADD THIS
        # Add load methods for Prices and Help if needed later
        frame.tkraise()

    def on_login_success(self, user_id, fullname):
        self.user_id = user_id
        self.fullname = fullname
        self.show_frame(PrinterFrame)

    def show_login_frame(self):
        self.center_window(self.default_width, self.default_height)
        self.user_id = None; self.fullname = None
        for name, frame in self.frames.items():
            if name != LoginFrame.__name__: frame.destroy()
        self.frames = { LoginFrame.__name__: self.frames[LoginFrame.__name__] }
        self.show_frame(LoginFrame)

    # --- NAVIGATION METHODS ---
    def show_printer_frame(self):
        self.center_window(self.default_width, self.default_height)
        self.show_frame(PrinterFrame)
    def show_user_frame(self):
        self.center_window(self.default_width, self.default_height)
        self.show_frame(UserFrame)
    def show_history_frame(self):
        self.show_frame(HistoryFrame)
    def show_prices_frame(self):
        self.show_frame(PricesFrame)
    def show_help_frame(self):
        self.center_window(self.default_width, self.default_height)
        self.show_frame(HelpFrame)
    def show_notification_frame(self):
         # NotificationFrame handles its own size
        self.show_frame(NotificationFrame) # <--- UPDATED

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()