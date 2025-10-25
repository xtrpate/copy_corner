from pathlib import Path
from tkinter import Tk, Canvas, Entry, messagebox, PhotoImage
import mysql.connector
import subprocess
import sys
import random
# Note: smtplib, MIMEText, MIMEMultipart are no longer needed here
import tkinter as tk
import os
import bcrypt
from dotenv import load_dotenv
# --- Import from utils ---
from utils import get_db_connection, round_rectangle, send_verification_email

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
# --- END OF MODIFICATION ---

sent_code = None
current_email = None

# --- Placeholder Entry Class ---
class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", show_char="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder; self.placeholder_color = color
        self.default_fg_color = self["fg"]; self.show_char = show_char
        self.bind("<FocusIn>", self.foc_in); self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()
    def put_placeholder(self):
        self.delete(0, "end"); self.insert(0, self.placeholder); self["fg"] = self.placeholder_color
        if self.show_char: self.config(show="")
    def foc_in(self, *args):
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end"); self["fg"] = self.default_fg_color
            if self.show_char: self.config(show=self.show_char)
    def foc_out(self, *args):
        if not self.get(): self.put_placeholder()

# --- DB Connection is now imported from utils ---

# --- Check if Email Exists ---
def email_exists(email):
    conn = None; cursor = None
    try:
        conn = get_db_connection()
        if not conn: return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        messagebox.showerror("Database Error", str(e)); return False
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- DELETED send_verification_code function ---

# --- BUTTON: Get Code ---
def on_get_code():
    global sent_code, current_email
    email = entry_email.get().strip()
    if not email or email == entry_email.placeholder: messagebox.showerror("Error", "Please enter your email."); return
    if not email_exists(email): messagebox.showerror("Error", "Email not found."); return

    canvas.itemconfig(get_code_text_id, text="Sending...")
    for item in (get_code_btn_id, get_code_text_id):
        canvas.tag_unbind(item, "<Button-1>"); canvas.tag_unbind(item, "<Enter>")
    window.update_idletasks()

    # --- Use imported function with context ---
    code = f"{random.randint(0, 999999):06d}" # Generate code here
    email_sent = send_verification_email(
        email, code,
        email_subject="Password Reset Verification Code", context="reset"
    )

    # --- Reset button state ---
    canvas.itemconfig(get_code_text_id, text="Get Code")
    for item in (get_code_btn_id, get_code_text_id):
        canvas.tag_bind(item, "<Button-1>", lambda e: on_get_code())
        canvas.tag_bind(item, "<Enter>", lambda e: (canvas.itemconfig(get_code_btn_id, fill="#333333"), window.config(cursor="hand2")))
        canvas.tag_bind(item, "<Leave>", lambda e: (canvas.itemconfig(get_code_btn_id, fill="#000000"), window.config(cursor="")))

    if email_sent:
        sent_code = code # Store the generated code
        current_email = email
        otp_process = subprocess.Popen([sys.executable, "OTP1.py", current_email, sent_code])
        window.withdraw()
        check_otp_status(otp_process)
    # else: Error shown by send_verification_email

# --- BUTTON: Reset Password ---
def reset_password():
    if not current_email: messagebox.showerror("Error", "Email missing. Restart process."); return
    new_pass = entry_new_password.get(); confirm_pass = entry_confirm_password.get()
    if new_pass == entry_new_password.placeholder: new_pass = ""
    if confirm_pass == entry_confirm_password.placeholder: confirm_pass = ""
    if not new_pass or not confirm_pass: messagebox.showerror("Error", "Both password fields required."); return
    if len(new_pass) < 8: messagebox.showerror("Error", "Password must be >= 8 chars."); return
    if not any(c.isupper() for c in new_pass): messagebox.showerror("Error", "Password needs uppercase."); return
    if not any(c.islower() for c in new_pass): messagebox.showerror("Error", "Password needs lowercase."); return
    if not any(c.isdigit() for c in new_pass): messagebox.showerror("Error", "Password needs digit."); return
    if new_pass != confirm_pass: messagebox.showerror("Error", "Passwords do not match."); return

    conn = None; cursor = None
    try:
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        hashed_password = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_password, current_email))
        conn.commit()
        messagebox.showinfo("Success", "Password reset successfully!")
        window.destroy()
        subprocess.Popen([sys.executable, "login_frame.py"]) # Or main.py?
    except Exception as e:
        messagebox.showerror("Database Error", str(e))
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- GO BACK ---
def go_back():
    window.destroy()
    subprocess.Popen([sys.executable, "login_frame.py"]) # Or main.py?

# --- Check OTP process ---
def check_otp_status(process):
    flag_file = Path("otp_verified.flag")
    if process.poll() is None:
        window.after(500, check_otp_status, process)
    else:
        if flag_file.exists():
            flag_file.unlink()
            show_reset_stage()
            window.deiconify()
        else:
            window.destroy()

# --- Switch UI to password reset stage ---
def show_reset_stage():
    for item in (email_label, email_entry_window, get_code_btn_id, get_code_text_id): canvas.itemconfig(item, state='hidden')
    for item in (password_label, password_entry_window, confirm_password_label, confirm_entry_window, reset_btn_id, reset_text_id): canvas.itemconfig(item, state='normal')
    if 'pw_eye_icon_id' in globals(): canvas.itemconfig(pw_eye_icon_id, state='normal')
    if 'confirm_eye_icon_id' in globals(): canvas.itemconfig(confirm_eye_icon_id, state='normal')
    entry_new_password.focus()

# --- Asset Paths ---
OUTPUT_PATH = Path(__file__).parent
# Use relative path
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file(): print(f"Warning: Asset not found at {asset_file}")
    return asset_file

# --- Rounded Rectangle is imported from utils ---

# --- Create Rounded Entry ---
def create_rounded_entry(x_pos, y_pos, placeholder="", show_char="", with_eye=False):
    round_rectangle(canvas, x_pos + 12, y_pos + 7, x_pos + 232, y_pos + 37, r=10, fill="#999999", outline="")
    round_rectangle(canvas, x_pos + 10, y_pos + 5, x_pos + 230, y_pos + 35, r=10, fill="white", outline="#000000", width=1)
    entry = PlaceholderEntry(window, placeholder=placeholder, bd=0, bg="white", fg="#000000", show_char=show_char, highlightthickness=0, font=("Inter", 12))
    entry_width = 170.0 if with_eye else 190.0
    entry_window_id = canvas.create_window(x_pos + 110, y_pos + 20, width=entry_width, height=24, window=entry, anchor="center")
    eye_icon_id = None
    if with_eye:
        eye_icon_id = canvas.create_image(x_pos + 205, y_pos + 10, anchor="nw", image=window.eye_slash_image)
        canvas.tag_bind(eye_icon_id, "<Button-1>", lambda e, en=entry, icon=eye_icon_id: toggle_password(en, icon))
        canvas.tag_bind(eye_icon_id, "<Enter>", lambda e: window.config(cursor="hand2"))
        canvas.tag_bind(eye_icon_id, "<Leave>", lambda e: window.config(cursor=""))
    return entry, entry_window_id, eye_icon_id

# --- Toggle Password Visibility ---
def toggle_password(entry, icon_item_id):
    is_placeholder = (entry.get() == entry.placeholder and entry["fg"] == entry.placeholder_color)
    if is_placeholder: return
    if entry.cget("show") == "": entry.config(show="*"); canvas.itemconfig(icon_item_id, image=window.eye_slash_image)
    else: entry.config(show=""); canvas.itemconfig(icon_item_id, image=window.eye_image)

# --- Create Rounded Button ---
def create_rounded_button(x, y, text, command, width=150, height=35, bg="#000000", fg="white"):
    btn_id = round_rectangle(canvas, x, y, x + width, y + height, r=15, fill=bg, outline="")
    text_id = canvas.create_text(x + width/2, y + height/2, text=text, fill=fg, font=("Inter Bold", 12), anchor="center")
    def on_click(event):
        if command: command()
    def on_hover(event): canvas.itemconfig(btn_id, fill="#333333"); canvas.config(cursor="hand2")
    def on_leave(event): canvas.itemconfig(btn_id, fill=bg); canvas.config(cursor="")
    if command:
        for item in (btn_id, text_id):
            canvas.tag_bind(item, "<Button-1>", on_click)
            canvas.tag_bind(item, "<Enter>", on_hover)
            canvas.tag_bind(item, "<Leave>", on_leave)
    return btn_id, text_id

# --- UI ---
window = Tk()
window_width = 859; window_height = 534
screen_width = window.winfo_screenwidth(); screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2)); y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.title("Forgot Password"); window.configure(bg="#FFFFFF")

try: # Load Eye Images
    window.eye_image = PhotoImage(file=relative_to_assets("view.png"))
    window.eye_slash_image = PhotoImage(file=relative_to_assets("hide.png"))
except tk.TclError:
    messagebox.showerror("Asset Error", "Could not find eye icons."); window.destroy(); sys.exit()

canvas = Canvas(window, bg="#FFFFFF", height=539, width=872, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# --- Background Elements ---
canvas.create_rectangle(21.0, 17.0, 850.0, 521.0, fill="#FFFFFF", outline="#000000", width=2)
canvas.create_rectangle(21.0, 17.0, 850.0, 102.0, fill="#000000", outline="")
round_rectangle(canvas, 240.0, 43.0, 746.0, 508.0, r=20, fill="#FFFFFF", outline="#000000", width=1.3)
canvas.create_text(361.0, 64.0, anchor="nw", text="Forgot Password", fill="#000000", font=("Inter Bold", -32))

# --- Stage 1: Email Input ---
email_label = canvas.create_text(298.0, 165.0, anchor="nw", text="Email", fill="#000000", font=("Inter", -16))
entry_email, email_entry_window, _ = create_rounded_entry(400, 155, placeholder="Enter your email")
get_code_btn_id, get_code_text_id = create_rounded_button(450, 243, "Get Code", on_get_code, width=80, height=30)

# --- Stage 2: Password Reset ---
password_label = canvas.create_text(298.0, 165.0, anchor="nw", text="Password", fill="#000000", font=("Inter", -16), state='hidden')
entry_new_password, password_entry_window, pw_eye_icon_id = create_rounded_entry(400, 155, placeholder="New Password", show_char="*", with_eye=True)
confirm_password_label = canvas.create_text(253.0, 218.0, anchor="nw", text="Confirm Password", fill="#000000", font=("Inter", -16), state='hidden')
entry_confirm_password, confirm_entry_window, confirm_eye_icon_id = create_rounded_entry(400, 208, placeholder="Confirm Password", show_char="*", with_eye=True)
reset_btn_id, reset_text_id = create_rounded_button(445, 300, "Reset Password", reset_password, width=180, height=40)

# --- Initially hide stage 2 ---
for item in (password_entry_window, confirm_entry_window, reset_btn_id, reset_text_id, password_label, confirm_password_label): canvas.itemconfig(item, state='hidden')
if pw_eye_icon_id: canvas.itemconfig(pw_eye_icon_id, state='hidden')
if confirm_eye_icon_id: canvas.itemconfig(confirm_eye_icon_id, state='hidden')

# --- Back Button ---
create_rounded_button(270, 450, "Back", go_back, width=80, height=30)

window.resizable(False, False); window.mainloop()