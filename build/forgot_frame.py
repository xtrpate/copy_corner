# forgot_frame.py
from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Entry, messagebox, PhotoImage
import mysql.connector
import random
import bcrypt
# --- Import from utils ---
from utils import get_db_connection, round_rectangle, send_verification_email

# --- Asset Paths ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0" # Assuming assets are here

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (ForgotFrame) not found at {asset_file}")
    return asset_file

# --- Placeholder Entry Class (Keep as is) ---
class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", show_char="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder; self.placeholder_color = color
        self.default_fg_color = self["fg"]; self.show_char = show_char
        self.bind("<FocusIn>", self.foc_in); self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()
    def put_placeholder(self):
        # Prevent error if widget destroyed prematurely
        if not self.winfo_exists(): return
        self.delete(0, "end"); self.insert(0, self.placeholder); self["fg"] = self.placeholder_color
        if self.show_char: self.config(show="")
    def foc_in(self, *args):
        # Prevent error if widget destroyed prematurely
        if not self.winfo_exists(): return
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end"); self["fg"] = self.default_fg_color
            if self.show_char: self.config(show=self.show_char)
    def foc_out(self, *args):
        # Prevent error if widget destroyed prematurely
        if not self.winfo_exists(): return
        if not self.get(): self.put_placeholder()

# --- MAIN FORGOT FRAME CLASS ---
class ForgotFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Load Assets ---
        try:
            # Need eye icons from controller
            self.eye_image = controller.eye_image
            self.eye_slash_image = controller.eye_slash_image
        except AttributeError:
             messagebox.showerror("Error", "Eye icons not found in controller. Cannot load Forgot Password Frame.")
             self.destroy()
             return

        # --- Canvas ---
        self.canvas = Canvas(self, bg="#FFFFFF", height=539, width=872, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- UI Elements ---
        self._create_ui()

        # --- Initially hide stage 2 (Password Reset fields) ---
        self.hide_reset_stage()

    def _create_ui(self):
        """Helper method to create the UI elements."""
        # --- Background Elements ---
        self.canvas.create_rectangle(21.0, 17.0, 850.0, 521.0, fill="#FFFFFF", outline="#000000", width=2)
        self.canvas.create_rectangle(21.0, 17.0, 850.0, 102.0, fill="#000000", outline="")
        round_rectangle(self.canvas, 240.0, 43.0, 746.0, 508.0, r=20, fill="#FFFFFF", outline="#000000", width=1.3)
        self.canvas.create_text(361.0, 64.0, anchor="nw", text="Forgot Password", fill="#000000", font=("Inter Bold", -32))

        # --- Stage 1: Email Input ---
        self.email_label = self.canvas.create_text(298.0, 165.0, anchor="nw", text="Email", fill="#000000", font=("Inter", -16))
        self.entry_email, self.email_entry_window, _ = self._create_rounded_entry(400, 155, placeholder="Enter your email")
        self.get_code_btn_id, self.get_code_text_id = self._create_rounded_button(450, 243, "Get Code", self.on_get_code, width=80, height=30)

        # --- Stage 2: Password Reset ---
        self.password_label = self.canvas.create_text(298.0, 165.0, anchor="nw", text="New Password", fill="#000000", font=("Inter", -16))
        self.entry_new_password, self.password_entry_window, self.pw_eye_icon_id = self._create_rounded_entry(400, 155, placeholder="New Password", show_char="*", with_eye=True)

        self.confirm_password_label = self.canvas.create_text(253.0, 218.0, anchor="nw", text="Confirm Password", fill="#000000", font=("Inter", -16))
        self.entry_confirm_password, self.confirm_entry_window, self.confirm_eye_icon_id = self._create_rounded_entry(400, 208, placeholder="Confirm Password", show_char="*", with_eye=True)

        self.reset_btn_id, self.reset_text_id = self._create_rounded_button(445, 300, "Reset Password", self.reset_password, width=180, height=40)

        # --- Back Button (Always Visible) ---
        self._create_rounded_button(270, 450, "Back", self.go_back, width=80, height=30, bg="#000000", fg="white") # Grey back button

    # --- UI Helper Methods ---
    def _create_rounded_entry(self, x_pos, y_pos, placeholder="", show_char="", with_eye=False):
        """Creates the background and the PlaceholderEntry widget."""
        round_rectangle(self.canvas, x_pos + 12, y_pos + 7, x_pos + 232, y_pos + 37, r=10, fill="#DDDDDD", outline="") # Slightly darker shadow
        round_rectangle(self.canvas, x_pos + 10, y_pos + 5, x_pos + 230, y_pos + 35, r=10, fill="white", outline="#CCCCCC", width=1) # Lighter outline
        entry = PlaceholderEntry(self, placeholder=placeholder, bd=0, bg="white", fg="#000000", show_char=show_char, highlightthickness=0, font=("Inter", 12))
        entry_width = 170.0 if with_eye else 190.0
        entry_window_id = self.canvas.create_window(x_pos + 110, y_pos + 20, width=entry_width, height=24, window=entry, anchor="center")

        eye_icon_id = None
        if with_eye:
            eye_icon_id = self.canvas.create_image(x_pos + 205, y_pos + 10, anchor="nw", image=self.eye_slash_image) # Use loaded image
            self.canvas.tag_bind(eye_icon_id, "<Button-1>", lambda e, en=entry, icon=eye_icon_id: self.toggle_password(en, icon))
            self.canvas.tag_bind(eye_icon_id, "<Enter>", lambda e: self.config(cursor="hand2"))
            self.canvas.tag_bind(eye_icon_id, "<Leave>", lambda e: self.config(cursor=""))

        return entry, entry_window_id, eye_icon_id

    def _create_rounded_button(self, x, y, text, command, width=150, height=35, bg="#000000", fg="white"):
        """Creates a rounded button with text and bindings."""
        btn_id = round_rectangle(self.canvas, x, y, x + width, y + height, r=15, fill=bg, outline="")
        text_id = self.canvas.create_text(x + width/2, y + height/2, text=text, fill=fg, font=("Inter Bold", 12), anchor="center")

        hover_bg = "#333333" if bg == "#000000" else "#5a6268" # Darken bg on hover

        def on_click(event):
            if command: command()
        def on_hover(event):
            self.canvas.itemconfig(btn_id, fill=hover_bg)
            self.config(cursor="hand2")
        def on_leave(event):
            self.canvas.itemconfig(btn_id, fill=bg)
            self.config(cursor="")

        if command:
            for item in (btn_id, text_id):
                self.canvas.tag_bind(item, "<Button-1>", on_click)
                self.canvas.tag_bind(item, "<Enter>", on_hover)
                self.canvas.tag_bind(item, "<Leave>", on_leave)
        return btn_id, text_id

    def toggle_password(self, entry, icon_item_id):
        """Toggles password visibility."""
        is_placeholder = (hasattr(entry, 'placeholder') and
                          entry.get() == entry.placeholder and
                          entry["fg"] == entry.placeholder_color)
        if is_placeholder: return

        try:
            if entry.cget("show") == "":
                entry.config(show="*")
                self.canvas.itemconfig(icon_item_id, image=self.eye_slash_image)
            else:
                entry.config(show="")
                self.canvas.itemconfig(icon_item_id, image=self.eye_image)
        except tk.TclError:
            print("Warning: Eye icon could not be updated.")


    # --- Stage Switching ---
    def show_reset_stage(self):
        """Hides email input and shows password reset fields."""
        for item in (self.email_label, self.email_entry_window, self.get_code_btn_id, self.get_code_text_id):
            self.canvas.itemconfig(item, state='hidden')
        for item in (self.password_label, self.password_entry_window, self.confirm_password_label, self.confirm_entry_window, self.reset_btn_id, self.reset_text_id):
            self.canvas.itemconfig(item, state='normal')
        if hasattr(self, 'pw_eye_icon_id') and self.pw_eye_icon_id:
             self.canvas.itemconfig(self.pw_eye_icon_id, state='normal')
        if hasattr(self, 'confirm_eye_icon_id') and self.confirm_eye_icon_id:
             self.canvas.itemconfig(self.confirm_eye_icon_id, state='normal')
        if hasattr(self, 'entry_new_password'): self.entry_new_password.focus()

    def hide_reset_stage(self):
        """Hides password reset fields and shows email input fields."""
        for item in (self.email_label, self.email_entry_window, self.get_code_btn_id, self.get_code_text_id):
            self.canvas.itemconfig(item, state='normal')
        for item in (self.password_label, self.password_entry_window, self.confirm_password_label, self.confirm_entry_window, self.reset_btn_id, self.reset_text_id):
            self.canvas.itemconfig(item, state='hidden')
        if hasattr(self, 'pw_eye_icon_id') and self.pw_eye_icon_id:
            self.canvas.itemconfig(self.pw_eye_icon_id, state='hidden')
        if hasattr(self, 'confirm_eye_icon_id') and self.confirm_eye_icon_id:
            self.canvas.itemconfig(self.confirm_eye_icon_id, state='hidden')
        if hasattr(self, 'entry_email'): self.entry_email.focus()
        # Clear password fields when hiding
        if hasattr(self, 'entry_new_password'): self.entry_new_password.put_placeholder()
        if hasattr(self, 'entry_confirm_password'): self.entry_confirm_password.put_placeholder()


    # --- Logic Methods ---
    def email_exists(self, email):
        """Checks if an email exists in the users table."""
        conn = None; cursor = None
        try:
            conn = get_db_connection()
            if not conn: return False
            cursor = conn.cursor(prepared=True) # Use prepared statement
            cursor.execute("SELECT 1 FROM users WHERE email=%s LIMIT 1", (email,))
            result = cursor.fetchone()
            return result is not None
        except mysql.connector.Error as e: # Catch specific DB errors
            messagebox.showerror("Database Error", f"Error checking email:\n{e}", parent=self)
            return False
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            return False
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def on_get_code(self):
        """Handles the 'Get Code' button click."""
        email = self.entry_email.get().strip()

        is_placeholder = (email == self.entry_email.placeholder and
                          self.entry_email["fg"] == self.entry_email.placeholder_color)
        if not email or is_placeholder:
            messagebox.showerror("Error", "Please enter your email.", parent=self); return
        if not self.email_exists(email):
            messagebox.showerror("Error", "Email not found in registered users.", parent=self); return

        # --- Change button to "Sending" state ---
        self.canvas.itemconfig(self.get_code_text_id, text="Sending...")
        for item in (self.get_code_btn_id, self.get_code_text_id):
            self.canvas.tag_unbind(item, "<Button-1>")
            self.canvas.tag_unbind(item, "<Enter>")
            self.canvas.tag_unbind(item, "<Leave>")
            self.canvas.itemconfig(item, cursor="")
        self.update_idletasks()

        # --- Generate and Send OTP ---
        code = f"{random.randint(0, 999999):06d}"
        email_sent = send_verification_email(
            email, code,
            email_subject="Password Reset Verification Code", context="reset"
        )

        # --- Reset button state regardless of email success ---
        self.canvas.itemconfig(self.get_code_text_id, text="Get Code")
        for item in (self.get_code_btn_id, self.get_code_text_id):
            self.canvas.tag_bind(item, "<Button-1>", lambda e: self.on_get_code())
            self.canvas.tag_bind(item, "<Enter>", lambda e: (self.canvas.itemconfig(self.get_code_btn_id, fill="#333333"), self.config(cursor="hand2"))) # Re-bind hover
            self.canvas.tag_bind(item, "<Leave>", lambda e: (self.canvas.itemconfig(self.get_code_btn_id, fill="#000000"), self.config(cursor=""))) # Re-bind leave

        if email_sent:
            self.controller.temp_otp = code # Store OTP in controller
            self.controller.temp_reset_email = email # Store email in controller
            self.controller.show_otp1_frame() # Navigate using controller
        # else: Error shown by send_verification_email

    def reset_password(self):
        """Handles the 'Reset Password' button click."""
        current_email = self.controller.temp_reset_email
        if not current_email:
             messagebox.showerror("Error", "Verification email missing. Please restart the process.", parent=self)
             self.go_back() # Go back to login if email is lost
             return

        new_pass = self.entry_new_password.get()
        confirm_pass = self.entry_confirm_password.get()

        # Check placeholders
        is_new_pass_placeholder = (new_pass == self.entry_new_password.placeholder and
                                   self.entry_new_password["fg"] == self.entry_new_password.placeholder_color)
        is_confirm_pass_placeholder = (confirm_pass == self.entry_confirm_password.placeholder and
                                       self.entry_confirm_password["fg"] == self.entry_confirm_password.placeholder_color)

        if is_new_pass_placeholder: new_pass = ""
        if is_confirm_pass_placeholder: confirm_pass = ""

        # --- Validation ---
        if not new_pass or not confirm_pass:
            messagebox.showerror("Error", "Both new password fields are required.", parent=self); return
        if len(new_pass) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters.", parent=self); return
        if not any(c.isupper() for c in new_pass):
            messagebox.showerror("Error", "Password needs an uppercase letter.", parent=self); return
        if not any(c.islower() for c in new_pass):
            messagebox.showerror("Error", "Password needs a lowercase letter.", parent=self); return
        if not any(c.isdigit() for c in new_pass):
            messagebox.showerror("Error", "Password needs a digit.", parent=self); return
        # Add special character check if needed
        # if not any(c in "!@#$%^&*()..." for c in new_pass): messagebox.showerror("Error", "Password needs a special character."); return
        if new_pass != confirm_pass:
            messagebox.showerror("Error", "New passwords do not match.", parent=self); return

        # --- Update Password in DB ---
        conn = None; cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()
            hashed_password = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_password, current_email))
            conn.commit()
            messagebox.showinfo("Success", "Password reset successfully! You can now log in.", parent=self)
            self.go_back() # Go back to login screen
        except mysql.connector.Error as e: # Catch specific DB errors
            messagebox.showerror("Database Error", f"Failed to update password:\n{e}", parent=self)
            if conn: conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            if conn: conn.rollback()
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
            # Clear sensitive temp data after attempt
            self.controller.temp_reset_email = None
            self.controller.temp_otp = None


    def go_back(self):
        """Returns to the login screen."""
        self.clear_fields() # Clear fields before leaving
        self.hide_reset_stage() # Reset to email stage for next time
        self.controller.show_login_frame()

    def clear_fields(self):
         """Clears entry fields."""
         if hasattr(self, 'entry_email'): self.entry_email.put_placeholder()
         if hasattr(self, 'entry_new_password'): self.entry_new_password.put_placeholder()
         if hasattr(self, 'entry_confirm_password'): self.entry_confirm_password.put_placeholder()