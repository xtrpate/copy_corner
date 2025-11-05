import tkinter as tk
from tkinter import PhotoImage, messagebox
from pathlib import Path

# --- Import all standard frames ---
from login_frame import LoginFrame
from printer_frame import PrinterFrame
from user_frame import UserFrame
from history_frame import HistoryFrame
from prices_frame import PricesFrame
from help_frame import HelpFrame
from notification_frame import NotificationFrame

# --- Import all ADMIN frames ---
from admin_dashboard import AdminDashboardFrame
from admin_user import AdminUserFrame
from admin_print import AdminPrintFrame
from admin_report import AdminReportFrame
from admin_notification import AdminNotificationFrame
from admin_inventory import AdminInventoryFrame  # <-- ADDED

# --- Import NEW frames ---
from register_frame import RegisterFrame
from otp_frame import OTPFrame
from forgot_frame import ForgotFrame
from otp1_frame import OTP1Frame


class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id = None
        self.fullname = None
        self.admin_name = None
        self.temp_user_data = None
        self.temp_otp = None
        self.temp_reset_email = None

        self.default_width = 859
        self.default_height = 534

        OUTPUT_PATH = Path(__file__).parent
        ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"
        try:
            self.eye_image = PhotoImage(file=ASSETS_PATH / "view.png")
            self.eye_slash_image = PhotoImage(file=ASSETS_PATH / "hide.png")
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not find eye icons (view.png, hide.png).\n{e}")
            self.destroy()
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred loading assets: {e}")
            self.destroy()
            return

        self.title("Copy Corner Printing System")
        self.resizable(False, False)

        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        try:
            self.show_frame(LoginFrame)
        except Exception as e:
            print(f"Error during initial LoginFrame display: {e}")
            messagebox.showerror("Initialization Error",
                                 f"Failed to load the login screen:\n{e}\nCheck console for details.")
            self.destroy()

    def center_window(self, width, height):
        self.update_idletasks()
        try:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            x = int((screen_width / 2) - (width / 2))
            y = int((screen_height / 2) - (height / 2))
            if width > 0 and height > 0 and x >= 0 and y >= 0:
                self.geometry(f"{width}x{height}+{x}+{y}")
            else:
                print(f"Warning: Invalid window dimensions or position: {width}x{height}+{x}+{y}")
                self.geometry(f"{self.default_width}x{self.default_height}")  # Fallback
        except tk.TclError as e:
            print(f"Error centering window: {e}")
            self.geometry(f"{self.default_width}x{self.default_height}")

    def show_frame(self, frame_class):
        name = frame_class.__name__
        frame = self.frames.get(name)

        if not frame or not frame.winfo_exists():
            print(f"Creating instance of {name}")
            try:
                frame = frame_class(parent=self.container, controller=self)
                self.frames[name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
            except Exception as e:
                messagebox.showerror("Frame Error", f"Could not create frame: {name}\nError: {e}")
                return

        # --- Resize Window Based on Frame ---
        target_width, target_height = self.default_width, self.default_height

        frame_sizes = {
            "AdminDashboardFrame": (905, 534),
            "AdminUserFrame": (905, 570),
            "AdminPrintFrame": (1305, 570),
            "AdminReportFrame": (905, 575),
            "AdminNotificationFrame": (905, 567),
            "AdminInventoryFrame": (880, 550),
            "HistoryFrame": (900, 504),
            "PricesFrame": (829, 504),
            "RegisterFrame": (851, 604),
            "OTPFrame": (400, 500),
            "OTP1Frame": (400, 500),
            "ForgotFrame": (859, 534),
            "PrinterFrame": (871, 540),
            "UserFrame": (871, 540),
            "HelpFrame": (871, 540),
            "NotificationFrame": (871, 540),
            "LoginFrame": (self.default_width, self.default_height)
        }

        target_width, target_height = frame_sizes.get(name, (self.default_width, self.default_height))

        try:
            current_geo_parts = self.geometry().split('+')
            current_size = current_geo_parts[0]
            current_w_str, current_h_str = current_size.split('x')
            if int(current_w_str) != target_width or int(current_h_str) != target_height:
                self.center_window(target_width, target_height)
        except Exception as e:
            self.center_window(target_width, target_height)
        # --- END RESIZE ---

        # --- Refresh data logic ---
        if frame and frame.winfo_exists():
            try:
                if hasattr(frame, "load_user_data") and callable(frame.load_user_data):
                    frame.load_user_data()
            except Exception as e:
                print(f"Error calling load_user_data for {name}: {e}")
            try:
                if hasattr(frame, "load_user_requests") and callable(frame.load_user_requests):
                    frame.load_user_requests()
            except Exception as e:
                print(f"Error calling load_user_requests for {name}: {e}")
            try:
                if hasattr(frame, "load_history") and callable(frame.load_history):
                    frame.load_history()
            except Exception as e:
                print(f"Error calling load_history for {name}: {e}")
            try:
                if hasattr(frame, "load_notifications") and callable(frame.load_notifications):
                    frame.load_notifications()
            except Exception as e:
                print(f"Error calling load_notifications for {name}: {e}")

            # Admin frames
            try:
                if hasattr(frame, "load_dashboard_data") and callable(frame.load_dashboard_data):
                    frame.load_dashboard_data()
            except Exception as e:
                print(f"Error calling load_dashboard_data for {name}: {e}")
            try:
                if hasattr(frame, "load_print_jobs") and callable(frame.load_print_jobs):
                    frame.load_print_jobs()
            except Exception as e:
                print(f"Error calling load_print_jobs for {name}: {e}")
            try:
                if hasattr(frame, "load_users") and callable(frame.load_users):
                    frame.load_users()
            except Exception as e:
                print(f"Error calling load_users for {name}: {e}")
            try:
                if hasattr(frame, "load_notifications_admin") and callable(frame.load_notifications_admin):
                    frame.load_notifications_admin()
            except Exception as e:
                print(f"Error calling load_notifications_admin for {name}: {e}")
            try:
                if hasattr(frame, "load_products") and callable(frame.load_products):  # <-- ADDED
                    frame.load_products()
            except Exception as e:
                print(f"Error calling load_products for {name}: {e}")

            # OTP/Forgot Frames
            try:
                if hasattr(frame, "prepare_otp_entry") and callable(frame.prepare_otp_entry):
                    frame.prepare_otp_entry()
            except Exception as e:
                print(f"Error calling prepare_otp_entry for {name}: {e}")
            try:
                if name == "ForgotFrame" and hasattr(frame, "hide_reset_stage") and not self.temp_reset_email:
                    frame.hide_reset_stage()
            except Exception as e:
                print(f"Error resetting ForgotFrame stage: {e}")

            frame.tkraise()

    def on_login_success(self, user_id, fullname):
        self.user_id = user_id
        self.fullname = fullname
        self.admin_name = None
        self.show_printer_frame()

    def on_admin_login(self, admin_name):
        self.admin_name = admin_name
        self.user_id = None
        self.fullname = None
        self.show_admin_dashboard()

    def show_login_frame(self):
        """Logs out user/admin, clears login fields, and returns to login screen."""
        self.user_id = None
        self.fullname = None
        self.admin_name = None
        self.temp_user_data = None
        self.temp_otp = None
        self.temp_reset_email = None

        login_frame_instance = self.frames.get(LoginFrame.__name__)
        if login_frame_instance and login_frame_instance.winfo_exists():
            if hasattr(login_frame_instance, 'clear_fields') and callable(login_frame_instance.clear_fields):
                login_frame_instance.clear_fields()
        else:
            print("Error: LoginFrame instance missing during logout.")
            messagebox.showerror("Critical Error", "Login screen cannot be displayed.")
            self.destroy()
            return

        self.show_frame(LoginFrame)

        if login_frame_instance and login_frame_instance.winfo_exists():
            if hasattr(login_frame_instance, 'entry_email'):
                login_frame_instance.after(10, login_frame_instance.entry_email.focus_set)

    # --- USER NAVIGATION METHODS ---
    def show_printer_frame(self):
        self.show_frame(PrinterFrame)

    def show_user_frame(self):
        self.show_frame(UserFrame)

    def show_history_frame(self):
        self.show_frame(HistoryFrame)

    def show_prices_frame(self):
        self.show_frame(PricesFrame)

    def show_help_frame(self):
        self.show_frame(HelpFrame)

    def show_notification_frame(self):
        self.show_frame(NotificationFrame)

    # --- ADMIN NAVIGATION METHODS ---
    def show_admin_dashboard(self):
        self.show_frame(AdminDashboardFrame)

    def show_admin_user(self):
        self.show_frame(AdminUserFrame)

    def show_admin_print(self):
        self.show_frame(AdminPrintFrame)

    def show_admin_report(self):
        self.show_frame(AdminReportFrame)

    def show_admin_notification(self):
        self.show_frame(AdminNotificationFrame)

    # --- ADDED: show_admin_inventory ---
    def show_admin_inventory(self):
        self.show_frame(AdminInventoryFrame)

    # --- END ADDITION ---

    # --- NEW NAVIGATION METHODS for Register/OTP/Forgot ---
    def show_register_frame(self):
        register_frame = self.frames.get(RegisterFrame.__name__)
        if register_frame and hasattr(register_frame, 'clear_fields') and callable(register_frame.clear_fields):
            try:
                register_frame.clear_fields()
            except Exception as e:
                print(f"Error clearing RegisterFrame fields: {e}")
        self.show_frame(RegisterFrame)

    def show_otp_frame(self):
        self.show_frame(OTPFrame)

    def show_forgot_frame(self):
        forgot_frame = self.frames.get(ForgotFrame.__name__)
        if forgot_frame and hasattr(forgot_frame, 'hide_reset_stage') and not self.temp_reset_email:
            try:
                forgot_frame.hide_reset_stage()
            except Exception as e:
                print(f"Error resetting ForgotFrame stage: {e}")
        self.show_frame(ForgotFrame)

    def show_otp1_frame(self):
        self.show_frame(OTP1Frame)


if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()