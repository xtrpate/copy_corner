from pathlib import Path
import tkinter as tk
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, font
# Note: mysql.connector might not be needed if not logging attempts
import subprocess
import sys
import random  # For generating OTP
# Note: smtplib, MIMEText, MIMEMultipart are no longer needed here
import os
from dotenv import load_dotenv
# --- Import from utils ---
from utils import get_db_connection, round_rectangle, send_verification_email

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()
# --- END OF MODIFICATION ---

# --- Get Arguments Passed from forgot.py ---
try:
    user_email = sys.argv[1]
    correct_otp = sys.argv[2]
except IndexError:
    messagebox.showerror("Error", "Could not load verification data.")
    # Exit cleanly if arguments are missing
    sys.exit()

# --- Asset Path ---
OUTPUT_PATH = Path(__file__).parent
# Use relative path
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file(): print(f"Warning: Asset not found at {asset_file}")
    return asset_file

# --- DB Connection is now imported from utils ---
# --- Rounded Rectangle is now imported from utils ---

# --- Verify the OTP Code ---
def verify_otp():
    entered_otp = "".join(entry.get() for entry in otp_entries)
    if entered_otp == correct_otp:
        try:
            Path("otp_verified.flag").touch() # Signal success
            window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not signal verification success: {e}")
    else:
        messagebox.showerror("Verification Failed", "Incorrect code. Please try again.")
        for entry in otp_entries: entry.delete(0, 'end')
        otp_entries[0].focus()

# --- DELETED send_verification_email function ---

# --- Resend OTP ---
def resend_otp():
    new_otp = f"{random.randint(0, 999999):06d}"
    # --- Use imported function with context ---
    email_sent = send_verification_email(
        user_email, new_otp,
        email_subject="Password Reset Verification Code", context="reset"
    )
    if email_sent:
        messagebox.showinfo("Code Resent", f"A new 6-digit code sent to {user_email}.")
        window.destroy()
        subprocess.Popen([sys.executable, "OTP1.py", user_email, new_otp])
    # else: Error shown by send_verification_email

# --- Setup Window ---
window = Tk()
window_width = 400; window_height = 500
screen_width = window.winfo_screenwidth(); screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2)); y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")
window.configure(bg="#FFFFFF"); window.title("Password Reset Verification")

canvas = Canvas(window, bg="#FFFFFF", height=500, width=400, bd=0, highlightthickness=0, relief="ridge")
canvas.place(x=0, y=0)

# --- UI Elements ---
canvas.create_text(window_width / 2, 60, anchor="center", text="Password Reset", fill="#000000", font=("Inter Bold", 24))
canvas.create_text(window_width / 2, 110, anchor="center", text="We sent a code to your email:", fill="#333333", font=("Inter", 12))
canvas.create_text(window_width / 2, 135, anchor="center", text=f"{user_email}", fill="#000000", font=("Inter Bold", 12))
canvas.create_text(window_width / 2, 175, anchor="center", text="Please enter the 6-digit code below.", fill="#333333", font=("Inter", 12))

# --- OTP Entry Boxes ---
otp_entries = []
entry_font = font.Font(family="Inter Bold", size=24); entry_width = 40; entry_padding = 10
total_width = (entry_width * 6) + (entry_padding * 5); start_x = (window_width - total_width) / 2
def validate_digit(P): return (P.isdigit() and len(P) <= 1) or P == ""
vcmd = (window.register(validate_digit), '%P')
def on_key_press(event, index):
    key = event.keysym; widget = event.widget
    if key == "BackSpace":
        if index > 0: widget.delete(0, 'end'); otp_entries[index - 1].focus(); otp_entries[index - 1].delete(0, 'end')
        else: widget.delete(0, 'end')
    elif key == "Left" and index > 0: otp_entries[index - 1].focus()
    elif key == "Right" and index < 5: otp_entries[index + 1].focus()
    elif len(key) == 1 and key.isdigit():
        widget.delete(0, 'end'); widget.insert(0, key)
        if index < 5: otp_entries[index + 1].focus()
        return "break"
    elif len(key) > 1 and key not in ("Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Tab", "Caps_Lock"): return "break"
def on_paste(event, index):
    try: clipboard_data = window.clipboard_get()
    except tk.TclError: clipboard_data = ""
    pasted_digits = [c for c in clipboard_data if c.isdigit()]; current_index = index
    for digit in pasted_digits:
        if current_index < 6: otp_entries[current_index].delete(0, 'end'); otp_entries[current_index].insert(0, digit); current_index += 1
        else: break
    otp_entries[min(current_index, 5)].focus(); return "break"

for i in range(6):
    x_pos = start_x + (i * (entry_width + entry_padding))
    round_rectangle(canvas, x_pos, 220, x_pos + entry_width, 220 + 50, r=10, fill="#F0F0F0", outline="#CCCCCC")
    entry = Entry(window, bd=0, bg="#F0F0F0", fg="#000000", font=entry_font, justify="center", width=2, highlightthickness=0, insertbackground="#000000")
    entry.config(validate="key", validatecommand=vcmd)
    entry.bind("<Key>", lambda e, idx=i: on_key_press(e, idx))
    entry.bind("<Control-v>", lambda e, idx=i: on_paste(e, idx))
    entry.bind("<Command-v>", lambda e, idx=i: on_paste(e, idx)) # Mac
    canvas.create_window(x_pos + (entry_width / 2), 245, window=entry)
    otp_entries.append(entry)

# --- Buttons ---
verify_btn_bg = round_rectangle(canvas, 50, 320, window_width - 50, 370, r=15, fill="#000000", outline="")
verify_btn_text = canvas.create_text(window_width / 2, 345, anchor="center", text="Verify Code", fill="#FFFFFF", font=("Inter Bold", 14))
canvas.tag_bind(verify_btn_bg, "<Button-1>", lambda e: verify_otp()); canvas.tag_bind(verify_btn_text, "<Button-1>", lambda e: verify_otp())
canvas.create_text(window_width / 2 - 30, 420, anchor="e", text="Didn't receive a code?", fill="#555555", font=("Inter", 11))
resend_label = canvas.create_text(window_width / 2 - 25, 420, anchor="w", text="Resend", fill="#000000", font=("Inter Bold", 11))
canvas.tag_bind(resend_label, "<Button-1>", lambda e: resend_otp())
canvas.tag_bind(resend_label, "<Enter>", lambda e: canvas.config(cursor="hand2"))
canvas.tag_bind(resend_label, "<Leave>", lambda e: canvas.config(cursor=""))

otp_entries[0].focus(); window.resizable(False, False); window.mainloop()