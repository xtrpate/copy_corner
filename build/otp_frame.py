from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, font
import mysql.connector
import random
import bcrypt
# --- Import from utils ---
from utils import get_db_connection, round_rectangle, send_verification_email

# --- Asset Path ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0" # Assuming assets are here

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (OTPFrame) not found at {asset_file}")
    return asset_file

# --- MAIN OTP FRAME CLASS (for Registration) ---
class OTPFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Canvas Setup ---
        self.canvas = Canvas(self, bg="#FFFFFF", height=500, width=400, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- UI Elements ---
        self.canvas.create_text(200, 60, anchor="center", text="Email Verification", fill="#000000", font=("Inter Bold", 24))
        self.canvas.create_text(200, 110, anchor="center", text="We sent a code to your email:", fill="#333333", font=("Inter", 12))
        # Email Label (will be updated)
        self.email_label = self.canvas.create_text(200, 135, anchor="center", text="", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(200, 175, anchor="center", text="Please enter the 6-digit code below.", fill="#333333", font=("Inter", 12))

        # --- OTP Entry Boxes ---
        self.otp_entries = []
        entry_font = font.Font(family="Inter Bold", size=24); entry_width = 40; entry_padding = 10
        total_width = (entry_width * 6) + (entry_padding * 5); start_x = (400 - total_width) / 2
        vcmd = (self.register(self._validate_digit), '%P') # Register validation command

        for i in range(6):
            x_pos = start_x + (i * (entry_width + entry_padding))
            round_rectangle(self.canvas, x_pos, 220, x_pos + entry_width, 220 + 50, r=10, fill="#F0F0F0", outline="#CCCCCC")
            entry = Entry(self, bd=0, bg="#F0F0F0", fg="#000000", font=entry_font, justify="center", width=2, highlightthickness=0, insertbackground="#000000")
            entry.config(validate="key", validatecommand=vcmd)
            entry.bind("<Key>", lambda e, idx=i: self._on_key_press(e, idx))
            entry.bind("<Control-v>", lambda e, idx=i: self._on_paste(e, idx)) # Windows/Linux Paste
            entry.bind("<Command-v>", lambda e, idx=i: self._on_paste(e, idx)) # Mac Paste
            self.canvas.create_window(x_pos + (entry_width / 2), 245, window=entry)
            self.otp_entries.append(entry)

        # --- Buttons ---
        verify_btn_bg = round_rectangle(self.canvas, 50, 320, 400 - 50, 370, r=15, fill="#000000", outline="")
        verify_btn_text = self.canvas.create_text(200, 345, anchor="center", text="Verify Account", fill="#FFFFFF", font=("Inter Bold", 14))
        self.canvas.tag_bind(verify_btn_bg, "<Button-1>", lambda e: self.verify_otp())
        self.canvas.tag_bind(verify_btn_text, "<Button-1>", lambda e: self.verify_otp())
        for tag in (verify_btn_bg, verify_btn_text):
             self.canvas.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
             self.canvas.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))

        self.canvas.create_text(200 - 30, 420, anchor="e", text="Didn't receive a code?", fill="#555555", font=("Inter", 11))
        resend_label = self.canvas.create_text(200 - 25, 420, anchor="w", text="Resend", fill="#000000", font=("Inter Bold", 11))
        self.canvas.tag_bind(resend_label, "<Button-1>", lambda e: self.resend_otp())
        self.canvas.tag_bind(resend_label, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(resend_label, "<Leave>", lambda e: self.config(cursor=""))

    # --- Methods ---

    def prepare_otp_entry(self):
        """Called by controller's show_frame to update email label and clear entries."""
        # Update email label
        user_email = self.controller.temp_user_data.get("email", "N/A") if self.controller.temp_user_data else "N/A"
        self.canvas.itemconfig(self.email_label, text=user_email)

        # Clear existing OTP entries
        for entry in self.otp_entries:
            if entry.winfo_exists(): # Check if widget exists
                 entry.delete(0, 'end')

        # Set focus to the first OTP entry
        if self.otp_entries and self.otp_entries[0].winfo_exists():
            self.otp_entries[0].focus_set()

    def _validate_digit(self, P):
        """Validation command for OTP entry."""
        return (P.isdigit() and len(P) <= 1) or P == ""

    def _on_key_press(self, event, index):
        """Handles key presses within OTP entries for navigation and input."""
        key = event.keysym
        widget = event.widget

        if key == "BackSpace":
            if index > 0:
                widget.delete(0, 'end') # Clear current
                if self.otp_entries[index - 1].winfo_exists():
                    self.otp_entries[index - 1].focus()
                    self.otp_entries[index - 1].delete(0, 'end') # Clear previous too
            else:
                widget.delete(0, 'end') # Clear first entry
            return "break" # Prevent default backspace behavior

        elif key == "Left" and index > 0:
            if self.otp_entries[index - 1].winfo_exists():
                self.otp_entries[index - 1].focus()
            return "break"

        elif key == "Right" and index < 5:
            if self.otp_entries[index + 1].winfo_exists():
                self.otp_entries[index + 1].focus()
            return "break"

        elif len(key) == 1 and key.isdigit():
            # Allow replacing existing digit
            widget.delete(0, 'end')
            widget.insert(0, key)
            # Move focus to the next entry if not the last one
            if index < 5 and self.otp_entries[index + 1].winfo_exists():
                self.otp_entries[index + 1].focus()
            return "break" # Prevent default insertion if we handled it

        # Allow navigation keys like Tab, Shift, Ctrl, Alt etc.
        elif len(key) > 1 and key not in ("Shift_L", "Shift_R", "Control_L", "Control_R",
                                          "Alt_L", "Alt_R", "Tab", "Caps_Lock",
                                          "Meta_L", "Meta_R"): # Added Meta for Mac Command key
             return "break" # Block other non-digit keys like letters, symbols

        return None # Allow default behavior otherwise


    def _on_paste(self, event, index):
        """Handles pasting into OTP fields."""
        try:
            clipboard_data = self.clipboard_get()
        except tk.TclError:
            clipboard_data = ""

        pasted_digits = [c for c in clipboard_data if c.isdigit()]
        current_index = index

        for digit in pasted_digits:
            if current_index < 6:
                if self.otp_entries[current_index].winfo_exists():
                    self.otp_entries[current_index].delete(0, 'end')
                    self.otp_entries[current_index].insert(0, digit)
                    current_index += 1
            else:
                break # Stop if we exceed 6 digits

        # Focus on the next available empty slot or the last filled slot
        focus_index = min(current_index, 5)
        if self.otp_entries[focus_index].winfo_exists():
            self.otp_entries[focus_index].focus()
        return "break" # Prevent default paste behavior


    def create_user_account(self):
        """Creates the user account in the database using data from controller."""
        if not self.controller.temp_user_data:
             messagebox.showerror("Error", "User registration data missing.", parent=self)
             return False

        conn = get_db_connection()
        if not conn: return False
        cursor = None
        try:
            cursor = conn.cursor()
            insert_query = """
            INSERT INTO users (fullname, username, email, password, contact, status)
            VALUES (%s, %s, %s, %s, %s, 'active')
            """ # Added status='active'
            user_data = self.controller.temp_user_data
            password_bytes = user_data['password'].encode('utf-8')
            hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
            user_values = (
                user_data['fullname'], user_data['username'], user_data['email'],
                hashed_password, user_data['contact']
            )
            cursor.execute(insert_query, user_values)
            conn.commit()
            return True
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Could not create account:\n{err}", parent=self)
            if conn: conn.rollback() # Rollback on error
            return False
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            if conn: conn.rollback()
            return False
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
            # Clear temp data after attempt
            self.controller.temp_user_data = None
            self.controller.temp_otp = None


    def verify_otp(self):
        entered_otp = "".join(entry.get() for entry in self.otp_entries if entry.winfo_exists())
        correct_otp = self.controller.temp_otp

        if not correct_otp:
             messagebox.showerror("Error", "Verification code expired or missing. Please go back and register again.", parent=self)
             # Go back to register or login? Login might be safer.
             self.controller.show_login_frame()
             return

        if entered_otp == correct_otp:
            if self.create_user_account():
                messagebox.showinfo("Success", "Email verified and account created!\nYou can now log in.", parent=self)
                self.controller.show_login_frame()
            # else: DB error already shown by create_user_account, data cleared
        else:
            messagebox.showerror("Verification Failed", "Incorrect code. Please try again.", parent=self)
            for entry in self.otp_entries:
                 if entry.winfo_exists(): entry.delete(0, 'end')
            if self.otp_entries and self.otp_entries[0].winfo_exists():
                 self.otp_entries[0].focus()

    def resend_otp(self):
        if not self.controller.temp_user_data or not self.controller.temp_user_data.get("email"):
             messagebox.showerror("Error", "Cannot resend OTP. User data missing. Please register again.", parent=self)
             self.controller.show_login_frame()
             return

        user_email = self.controller.temp_user_data["email"]
        new_otp = f"{random.randint(0, 999999):06d}"

        # Show loading/disabling state? (Optional, less critical than signup)
        if send_verification_email(user_email, new_otp): # Default subject/context
            self.controller.temp_otp = new_otp # Update OTP in controller
            messagebox.showinfo("Code Resent", f"A new 6-digit code has been sent to {user_email}.", parent=self)
            self.prepare_otp_entry() # Clear fields and focus
        # else: Error message already shown by send_verification_email