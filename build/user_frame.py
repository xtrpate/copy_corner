from pathlib import Path
from tkinter import Tk, Canvas, messagebox, PhotoImage, Label, Entry, Button
import tkinter as tk
import subprocess
import sys
import mysql.connector
import bcrypt
from utils import get_db_connection, round_rectangle


# --- DB Connection ---
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="copy_corner_db"
    )


# --- Asset Path ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(
    r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame0"
)


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# --- Rounded Rectangle ---
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2, y2 - radius,
              x2, y2, x2 - radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- Rounded Button Helper ---
def create_rounded_button(canvas, x, y, w, h, text, command=None, fill="#000000", text_color="#FFFFFF"):
    rect = create_rounded_rect(canvas, x, y, x + w, y + h, radius=15, fill=fill, outline="")
    txt = canvas.create_text(x + w / 2, y + h / 2, text=text, fill=text_color, font=("Inter Bold", 14), anchor="center")

    def on_click(event):
        if command: command()

    for tag in (rect, txt):
        canvas.tag_bind(tag, "<Button-1>", on_click)
        canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor=""))
    return rect, txt


# --- MAIN USER FRAME CLASS ---
class UserFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Get user data FROM THE CONTROLLER ---
        self.user_id = controller.user_id
        self.fullname = controller.fullname

        # --- Load Assets ---
        try:
            self.icon_edit = PhotoImage(file=relative_to_assets("image_13.png"))
            self.icon_bell = PhotoImage(file=relative_to_assets("image_14.png"))
            self.icon_sheet = PhotoImage(file=relative_to_assets("image_15.png"))
            self.icon_help = PhotoImage(file=relative_to_assets("image_16.png"))
            # Use the eye icons from the main controller
            self.eye_open_icon = controller.eye_image
            self.eye_closed_icon = controller.eye_slash_image
        except Exception as e:
            messagebox.showerror("Asset Error", f"Error loading assets for UserFrame: {e}")
            return

        self.password_visible = False
        self.eye_button = None
        self.entries = {}

        canvas = Canvas(self, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
        canvas.place(x=0, y=0)
        self.canvas = canvas

        # --- Borders and Header ---
        create_rounded_rect(canvas, 21, 16, 850, 520, radius=0, fill="#FFFFFF", outline="#000000", width=2)
        create_rounded_rect(canvas, 21, 15, 850, 103, radius=0, fill="#000000", outline="")
        canvas.create_text(120, 60, anchor="center", text="Profile", fill="#FFFFFF", font=("Inter Bold", 34))
        canvas.create_rectangle(233.0, 17.0, 234.0, 522.0, fill="#000000", outline="", width=3)

        # --- Left Menu ---
        self.create_rounded_menu_button(46, 129, 171, 38, "Print Request", self.open_printer)
        self.create_rounded_menu_button(46, 178, 171, 38, "Notifications", self.open_notification_py)
        self.create_rounded_menu_button(46, 227, 171, 38, "Pricelist", self.open_prices_py)
        self.create_rounded_menu_button(46, 276, 171, 38, "Help", self.open_help_py)
        create_rounded_button(canvas, 50, 450, 160, 45, "Log Out", self.logout)

        # --- Left Menu Icons ---
        lbl_edit = Label(self, image=self.icon_edit, bg="#FFFFFF", bd=0)
        lbl_bell = Label(self, image=self.icon_bell, bg="#FFFFFF", bd=0)
        lbl_sheet = Label(self, image=self.icon_sheet, bg="#FFFFFF", bd=0)
        lbl_help = Label(self, image=self.icon_help, bg="#FFFFFF", bd=0)
        lbl_edit.place(x=63.0, y=148.0, anchor="center")
        lbl_bell.place(x=63.0, y=198.0, anchor="center")
        lbl_sheet.place(x=63.0, y=248.0, anchor="center")
        lbl_help.place(x=63.0, y=298.0, anchor="center")
        self.make_icon_clickable(lbl_edit, self.open_printer)
        self.make_icon_clickable(lbl_bell, self.open_notification_py)
        self.make_icon_clickable(lbl_sheet, self.open_prices_py)
        self.make_icon_clickable(lbl_help, self.open_help_py)

        # --- Profile Picture ---
        create_rounded_rect(canvas, 609, 51, 810, 214, radius=20, fill="#FFFFFF", outline="#000000", width=2)
        canvas.create_text(682.0, 123.0, anchor="nw", text="Picture", fill="#000000", font=("Inter Bold", 16))

        # --- Form Fields ---
        self.field_positions = {
            "fullname": (271, 146, 500, 174), "username": (271, 212, 500, 240),
            "password": (271, 278, 500, 306), "email": (269, 341, 500, 369),
            "contact": (269, 407, 500, 435)
        }
        labels = {"fullname": "Full Name", "username": "Username", "password": "Password",
                  "email": "Email", "contact": "Contact"}

        for key, label in labels.items():
            lx, ly, x1, y1, x2, y2 = (
                271, {"fullname": 121, "username": 187, "password": 250, "email": 316, "contact": 382}[key],
                *self.field_positions[key]
            )
            canvas.create_text(lx, ly, anchor="nw", text=label, fill="#000000", font=("Inter Bold", 15))
            create_rounded_rect(canvas, x1, y1, x2, y2, radius=10, fill="#FFFAFA", outline="#000000")

            if key == "password":
                entry = Entry(self, bd=0, bg="#FFFAFA", font=("Inter", 13), show="*")
                entry.place(x=x1 + 8, y=y1 + 3, width=x2 - x1 - 40, height=22)
                self.eye_button = Button(
                    self, image=self.eye_closed_icon, bg="#FFFAFA", bd=1, relief="solid",
                    command=self.toggle_password_visibility
                )
                self.eye_button.place(x=x2 - 30, y=y1 + 2, width=24, height=24)
                self.eye_button.place_forget()  # Hide initially
            else:
                entry = Entry(self, bd=0, bg="#FFFAFA", font=("Inter", 13))
                entry.place(x=x1 + 8, y=y1 + 3, width=x2 - x1 - 16, height=22)

            entry.config(state="readonly")
            self.entries[key] = entry

        # --- Buttons ---
        self.edit_btn_rect = create_rounded_rect(canvas, 271, 468, 351, 496, radius=15, fill="#000000", outline="")
        self.edit_btn_text = canvas.create_text(311, 482, text="Edit", fill="#FFFFFF", font=("Inter Bold", 14))
        canvas.tag_bind(self.edit_btn_rect, "<Button-1>", lambda e: self.enter_edit_mode())
        canvas.tag_bind(self.edit_btn_text, "<Button-1>", lambda e: self.enter_edit_mode())

        self.cancel_btn_rect = create_rounded_rect(canvas, 271, 468, 371, 496, radius=15, fill="#FFFFFF",
                                                   outline="#000000")
        self.cancel_btn_text = canvas.create_text(321, 482, text="Cancel", fill="#000000", font=("Inter Bold", 14))
        canvas.tag_bind(self.cancel_btn_rect, "<Button-1>", lambda e: self.cancel_edit())
        canvas.tag_bind(self.cancel_btn_text, "<Button-1>", lambda e: self.cancel_edit())
        canvas.itemconfigure(self.cancel_btn_rect, state="hidden")
        canvas.itemconfigure(self.cancel_btn_text, state="hidden")

        self.save_btn_rect = create_rounded_rect(canvas, 385, 468, 465, 496, radius=15, fill="#000000", outline="")
        self.save_btn_text = canvas.create_text(425, 482, text="Save", fill="#FFFFFF", font=("Inter Bold", 14))
        canvas.tag_bind(self.save_btn_rect, "<Button-1>", lambda e: self.save_changes())
        canvas.tag_bind(self.save_btn_text, "<Button-1>", lambda e: self.save_changes())
        canvas.itemconfigure(self.save_btn_rect, state="hidden")
        canvas.itemconfigure(self.save_btn_text, state="hidden")

        # Load user data when frame is created
        self.load_user_data()

    def load_user_data(self):
        """Fetches data and populates the fields."""
        self.user_data = self.get_user_data(self.user_id)  # Store data
        if self.user_data:
            for key, entry in self.entries.items():
                entry.config(state="normal")
                entry.delete(0, "end")
                entry.insert(0, self.user_data[key])
                entry.config(state="readonly")
                if key == "password":
                    entry.config(show="*")

    def get_user_data(self, user_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT fullname, username, email, password, contact FROM users WHERE user_id = %s",
                           (user_id,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            return user
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return None

    def update_user_data(self, user_id, new_data):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Hash the password (from Step 1)
            new_password_plain = new_data["password"]
            hashed_password = bcrypt.hashpw(new_password_plain.encode('utf-8'), bcrypt.gensalt())

            cursor.execute("""
                UPDATE users SET fullname=%s, username=%s, email=%s, password=%s, contact=%s
                WHERE user_id=%s
            """, (
                new_data["fullname"], new_data["username"], new_data["email"],
                hashed_password, new_data["contact"], user_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Success", "Profile updated successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return False

    # --- Navigation ---
    def open_printer(self):
        self.controller.show_printer_frame()

    def open_notification_py(self):
        self.controller.show_notification_frame()

    def open_prices_py(self):
        self.controller.show_prices_frame()

    def open_help_py(self):
        self.controller.show_help_frame()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure you want to log out?"):
            self.controller.show_login_frame()  # Go back to login screen

    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = create_rounded_rect(self.canvas, x, y, x + w, y + h, radius=12, fill="#FFFFFF", outline="#000000",
                                   width=1)
        txt = self.canvas.create_text(x + 40, y + 10, text=text, anchor="nw", fill="#000000", font=("Inter Bold", 16))

        def on_click(event): command() if command else None

        for tag in (rect, txt):
            self.canvas.tag_bind(tag, "<Button-1>", on_click)
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.itemconfig(rect, fill="#E8E8E8"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.itemconfig(rect, fill="#FFFFFF"))
        return rect, txt

    def toggle_password_visibility(self):
        if self.password_visible:
            self.entries["password"].config(show="*")
            self.eye_button.config(image=self.eye_closed_icon)
            self.password_visible = False
        else:
            self.entries["password"].config(show="")
            self.eye_button.config(image=self.eye_open_icon)
            self.password_visible = True

    # --- Edit / Save / Cancel Logic ---
    def enter_edit_mode(self):
        for key, entry in self.entries.items():
            entry.config(state="normal")
            if key == "password":
                entry.delete(0, "end")  # Clear the hash
                entry.config(show="*")

        if self.eye_button:
            self.eye_button.place(x=self.field_positions["password"][2] - 30, y=self.field_positions["password"][1] + 2,
                                  width=24, height=24)

        self.canvas.itemconfigure(self.edit_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.edit_btn_text, state="hidden")
        self.canvas.itemconfigure(self.save_btn_rect, state="normal")
        self.canvas.itemconfigure(self.save_btn_text, state="normal")
        self.canvas.itemconfigure(self.cancel_btn_rect, state="normal")
        self.canvas.itemconfigure(self.cancel_btn_text, state="normal")

    def save_changes(self):
        updated_data = {k: v.get().strip() for k, v in self.entries.items()}
        for field, value in updated_data.items():
            if not value:
                messagebox.showerror("Error", f"{field.capitalize()} cannot be empty.")
                return
        password = updated_data["password"]
        email = updated_data["email"]
        if len(password) < 8: messagebox.showerror("Error", "Password must be at least 8 chars."); return
        if not any(c.isupper() for c in password): messagebox.showerror("Error", "Password needs uppercase."); return
        if not any(c.islower() for c in password): messagebox.showerror("Error", "Password needs lowercase."); return
        if not any(c.isdigit() for c in password): messagebox.showerror("Error", "Password needs digit."); return
        if not email.lower().endswith("@gmail.com"): messagebox.showerror("Error", "Email must be @gmail.com"); return

        if self.update_user_data(self.user_id, updated_data):
            self.load_user_data()  # Reload data
            self.cancel_edit()  # Revert to view mode

    def cancel_edit(self):
        self.load_user_data()  # Just reload the original data
        for entry in self.entries.values():
            entry.config(state="readonly")
        if self.eye_button:
            self.eye_button.place_forget()
        if self.password_visible:
            self.toggle_password_visibility()

        self.canvas.itemconfigure(self.save_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.save_btn_text, state="hidden")
        self.canvas.itemconfigure(self.cancel_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.cancel_btn_text, state="hidden")
        self.canvas.itemconfigure(self.edit_btn_rect, state="normal")
        self.canvas.itemconfigure(self.edit_btn_text, state="normal")