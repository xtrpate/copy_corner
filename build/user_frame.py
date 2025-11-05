from pathlib import Path
from tkinter import Canvas, messagebox, PhotoImage, Label, Entry, Button
import tkinter as tk
import mysql.connector
import bcrypt
import re
from utils import get_db_connection, round_rectangle

from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import io

# --- Asset Path --- (No changes needed)
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset file not found at {asset_file}")
    return asset_file


# --- Rounded Rectangle --- (No changes needed)
def create_rounded_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    points = [x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius, x2, y2 - radius,
              x2, y2, x2 - radius, y2, x1 + radius, y2, x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# --- Rounded Button Helper --- (No changes needed)
def create_rounded_button(canvas, x, y, w, h, text, command=None, fill="#000000", text_color="#FFFFFF"):
    rect = create_rounded_rect(canvas, x, y, x + w, y + h, radius=15, fill=fill, outline="")
    txt = canvas.create_text(x + w / 2 + 3, y + h / 2, text=text, fill=text_color, font=("Inter Bold", 14),
                             anchor="center")

    def on_click(event):
        if command: command()

    for tag in (rect, txt):
        canvas.tag_bind(tag, "<Button-1>", on_click)
        canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
        canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor=""))
    return rect, txt


# --- Helper function to crop and mask image to a circle --- (No changes needed)
def crop_and_mask_circle(image, size):
    """Crops the image to a square, resizes it, and applies a circular mask."""
    # Ensure square aspect ratio for circular crop
    width, height = image.size
    if width > height:
        left = (width - height) / 2
        top = 0
        right = (width + height) / 2
        bottom = height
    else:
        left = 0
        top = (height - width) / 2
        right = width
        bottom = (height + width) / 2

    image = image.crop((left, top, right, bottom))
    image = image.resize((size, size), Image.Resampling.LANCZOS)

    # Create a circular mask
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)  # Draw a white ellipse on black background

    # Apply mask to image
    rounded_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # Create transparent image
    rounded_img.paste(image, (0, 0), mask)  # Paste with mask
    return rounded_img


# --- MAIN USER FRAME CLASS ---
class UserFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_id = controller.user_id

        try:
            self.icon_edit = PhotoImage(file=relative_to_assets("image_13.png"))
            self.icon_bell = PhotoImage(file=relative_to_assets("image_14.png"))
            self.icon_sheet = PhotoImage(file=relative_to_assets("image_15.png"))
            self.icon_help = PhotoImage(file=relative_to_assets("image_16.png"))
            self.eye_open_icon = controller.eye_image
            self.eye_closed_icon = controller.eye_slash_image
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Error loading image asset for UserFrame:\n{e}")
            return
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred loading assets for UserFrame: {e}")
            return

        self.password_visible = False
        self.eye_button = None
        self.entries = {}
        self.user_data = {}

        self.pfp_image = None
        self.new_pfp_path = None

        canvas = Canvas(self, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
        canvas.place(x=0, y=0)
        self.canvas = canvas

        create_rounded_rect(canvas, 21, 16, 850, 520, radius=0, fill="#FFFFFF", outline="#000000", width=2)
        create_rounded_rect(canvas, 21, 15, 850, 103, radius=0, fill="#000000", outline="")
        canvas.create_text(120, 60, anchor="center", text="Profile", fill="#FFFFFF", font=("Inter Bold", 34))
        canvas.create_rectangle(233.0, 17.0, 234.0, 522.0, fill="#000000", outline="", width=3)

        self.create_rounded_menu_button(46, 129, 171, 38, "Print Request", self.open_printer)
        self.create_rounded_menu_button(46, 178, 171, 38, "Notifications", self.open_notification_py)
        self.create_rounded_menu_button(46, 227, 171, 38, "Pricelist", self.open_prices_py)
        self.create_rounded_menu_button(46, 276, 171, 38, "Help", self.open_help_py)
        create_rounded_button(canvas, 50, 450, 160, 45, "Log Out", self.logout)

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

        # --- Profile Picture area --- (No changes needed)
        pfp_diameter = 150
        pfp_center_x = 710
        pfp_center_y = 132
        pfp_x1 = pfp_center_x - pfp_diameter // 2
        pfp_y1 = pfp_center_y - pfp_diameter // 2
        pfp_x2 = pfp_center_x + pfp_diameter // 2
        pfp_y2 = pfp_center_y + pfp_diameter // 2

        self.pfp_bg = canvas.create_oval(pfp_x1, pfp_y1, pfp_x2, pfp_y2,
                                         fill="#FFFFFF", outline="#000000", width=2)

        self.pfp_text = canvas.create_text(pfp_center_x, pfp_center_y, anchor="center", text="Picture",
                                           fill="#000000", font=("Inter Bold", 16))
        self.pfp_image_id = self.canvas.create_image(pfp_center_x, pfp_center_y, anchor="center")
        self.pfp_display_size = pfp_diameter - 4

        # --- Form Fields --- (No changes needed)
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
                entry.place(x=x1 + 8, y=y1 + 4, width=(x2 - x1 - 16 - 24), height=20)
                self.eye_button = Button(
                    self, image=self.eye_closed_icon, bg="#FFFAFA", bd=0, relief="flat",
                    activebackground="#FFFAFA",
                    command=self.toggle_password_visibility
                )
                self.eye_button.place(x=x2 - 30, y=y1 + 2, width=24, height=24)
                self.eye_button.place_forget()
            else:
                entry = Entry(self, bd=0, bg="#FFFAFA", font=("Inter", 13))
                entry.place(x=x1 + 8, y=y1 + 4, width=x2 - x1 - 16, height=20)

            entry.config(state="readonly", readonlybackground="#FFFAFA", fg="#555555")
            self.entries[key] = entry

        # --- Buttons --- (No changes needed)
        self.edit_btn_rect = create_rounded_rect(canvas, 271, 468, 351, 496, radius=15, fill="#000000", outline="")
        self.edit_btn_text = canvas.create_text(311 + 3, 479 + 3, anchor="center", text="Edit", fill="#FFFFFF",
                                                font=("Inter Bold", 14))
        canvas.tag_bind(self.edit_btn_rect, "<Button-1>", lambda e: self.enter_edit_mode())
        canvas.tag_bind(self.edit_btn_text, "<Button-1>", lambda e: self.enter_edit_mode())

        self.cancel_btn_rect = create_rounded_rect(canvas, 271, 468, 371, 496, radius=15, fill="#FFFFFF",
                                                   outline="#000000")
        self.cancel_btn_text = canvas.create_text(321 + 3, 479 + 3, anchor="center", text="Cancel", fill="#000000",
                                                  font=("Inter Bold", 14))
        canvas.tag_bind(self.cancel_btn_rect, "<Button-1>", lambda e: self.cancel_edit())
        canvas.tag_bind(self.cancel_btn_text, "<Button-1>", lambda e: self.cancel_edit())
        canvas.itemconfigure(self.cancel_btn_rect, state="hidden")
        canvas.itemconfigure(self.cancel_btn_text, state="hidden")

        self.save_btn_rect = create_rounded_rect(canvas, 385, 468, 465, 496, radius=15, fill="#000000", outline="")
        self.save_btn_text = canvas.create_text(425 + 3, 479 + 3, anchor="center", text="Save", fill="#FFFFFF",
                                                font=("Inter Bold", 14))
        canvas.tag_bind(self.save_btn_rect, "<Button-1>", lambda e: self.save_changes())
        canvas.tag_bind(self.save_btn_text, "<Button-1>", lambda e: self.save_changes())
        canvas.itemconfigure(self.save_btn_rect, state="hidden")
        canvas.itemconfigure(self.save_btn_text, state="hidden")

        self.load_user_data()

    # --- load_user_data --- (No changes needed)
    def load_user_data(self):
        if not self.controller.user_id:
            messagebox.showerror("Error", "No user logged in.")
            self.controller.show_login_frame()
            return
        self.user_data = self.get_user_data(self.controller.user_id)
        if self.user_data:
            self.controller.fullname = self.user_data.get('fullname', '')
            for key, entry in self.entries.items():
                entry.config(state="normal")
                entry.delete(0, "end")
                if key == "password":
                    entry.insert(0, "********")
                    entry.config(show="*")
                else:
                    entry.insert(0, self.user_data.get(key, ""))
                entry.config(state="readonly", readonlybackground="#FFFAFA", fg="#555555")

            pfp_data = self.user_data.get('profile_picture')
            if pfp_data:
                self.display_profile_picture_from_blob(pfp_data)
            else:
                self.canvas.itemconfigure(self.pfp_image_id, image="")
                self.canvas.itemconfigure(self.pfp_text, text="Picture", state="normal")
                self.pfp_image = None # This is key: set to None if no picture
        else:
            messagebox.showerror("Error", "Could not load user profile data.")
            self.controller.show_login_frame()

    # --- get_user_data --- (No changes needed)
    def get_user_data(self, user_id):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return None
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT user_id, fullname, username, email, contact, created_at, status, profile_picture "
                "FROM users WHERE user_id = %s", (user_id,)
            )
            user = cursor.fetchone()
            return user
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to get user data: {e}")
            return None
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    # --- update_user_data --- (No changes needed)
    def update_user_data(self, user_id, data_to_update):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return False
            cursor = conn.cursor()
            set_clauses = []
            params = []
            if "fullname" in data_to_update: set_clauses.append("fullname = %s"); params.append(
                data_to_update["fullname"])
            if "username" in data_to_update: set_clauses.append("username = %s"); params.append(
                data_to_update["username"])
            if "email" in data_to_update: set_clauses.append("email = %s"); params.append(data_to_update["email"])
            if "contact" in data_to_update: set_clauses.append("contact = %s"); params.append(data_to_update["contact"])

            if "profile_picture" in data_to_update:
                set_clauses.append("profile_picture = %s")
                params.append(data_to_update["profile_picture"])

            if "password" in data_to_update:
                hashed_password = bcrypt.hashpw(data_to_update["password"].encode('utf-8'), bcrypt.gensalt())
                set_clauses.append("password = %s");
                params.append(hashed_password)

            if not set_clauses: messagebox.showinfo("No Changes", "No fields were modified."); return True

            sql = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = %s"
            params.append(user_id)
            cursor.execute(sql, tuple(params))
            conn.commit()

            if "fullname" in data_to_update: self.controller.fullname = data_to_update["fullname"]
            messagebox.showinfo("Success", "Profile updated successfully!")
            return True
        except mysql.connector.Error as err:
            if conn: conn.rollback()
            if err.errno == 1062:
                if 'username' in err.msg:
                    messagebox.showerror("Update Error", "Username already exists.")
                elif 'email' in err.msg:
                    messagebox.showerror("Update Error", "Email address already registered.")
                else:
                    messagebox.showerror("Database Error", f"Duplicate data error:\n{err}")
            else:
                messagebox.showerror("Database Error", f"Failed to update profile:\n{err}")
            return False
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Error", f"Unexpected error during update: {e}")
            return False
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    # --- Navigation & Helpers --- (No changes needed)
    def open_printer(self):
        self.controller.show_printer_frame()

    def open_notification_py(self):
        self.controller.show_notification_frame()

    def open_prices_py(self):
        self.controller.show_prices_frame()

    def open_help_py(self):
        self.controller.show_help_frame()

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.controller.show_login_frame()

    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = create_rounded_rect(self.canvas, x, y, x + w, y + h, radius=12, fill="#FFFFFF", outline="#000000",
                                   width=1)
        icon_space = 45
        text_start_x = x + icon_space
        txt = self.canvas.create_text(
            text_start_x - 4, y + h / 2, text=text, anchor="w",
            fill="#000000", font=("Inter Bold", 16)
        )

        def on_click(event): command() if command else None

        for tag in (rect, txt):
            self.canvas.tag_bind(tag, "<Button-1>", on_click)
            self.canvas.tag_bind(tag, "<Enter>",
                                 lambda e: (self.canvas.itemconfig(rect, fill="#E8E8E8"), self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>",
                                 lambda e: (self.canvas.itemconfig(rect, fill="#FFFFFF"), self.config(cursor="")))
        return rect, txt

    def toggle_password_visibility(self):
        if self.entries["password"]["state"] == "readonly": return
        if self.password_visible:
            self.entries["password"].config(show="*")
            self.eye_button.config(image=self.eye_closed_icon)
            self.password_visible = False
        else:
            self.entries["password"].config(show="")
            self.eye_button.config(image=self.eye_open_icon)
            self.password_visible = True

    # --- UPDATED: enter_edit_mode ---
    def enter_edit_mode(self):
        for key, entry in self.entries.items():
            entry.config(state="normal", fg="black")
            if key == "password":
                entry.delete(0, "end")
                entry.config(show="*")
                if self.eye_button:
                    x1, y1, x2, y2 = self.field_positions["password"]
                    self.eye_button.place(x=x2 - 30, y=y1 + 2, width=24, height=24)

        # --- UPDATED: Only show text if no image exists ---
        if self.pfp_image:
            self.canvas.itemconfigure(self.pfp_text, state="hidden")
        else:
            self.canvas.itemconfigure(self.pfp_text, text="Add a Picture", state="normal",
                                      fill="#000000")
            self.canvas.tag_raise(self.pfp_text)
        # --- END OF UPDATE ---

        for tag in (self.pfp_bg, self.pfp_text, self.pfp_image_id):
            self.canvas.tag_bind(tag, "<Button-1>", self.on_pfp_click)
            self.canvas.tag_bind(tag, "<Enter>", lambda e: self.canvas.config(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: self.canvas.config(cursor=""))

        self.canvas.itemconfigure(self.edit_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.edit_btn_text, state="hidden")
        self.canvas.itemconfigure(self.save_btn_rect, state="normal")
        self.canvas.itemconfigure(self.save_btn_text, state="normal")
        self.canvas.itemconfigure(self.cancel_btn_rect, state="normal")
        self.canvas.itemconfigure(self.cancel_btn_text, state="normal")

    # --- save_changes --- (No changes needed)
    def save_changes(self):
        data_to_update = {}
        original_data = self.get_user_data(self.controller.user_id)
        if not original_data: messagebox.showerror("Error", "Could not verify original user data."); return

        if self.new_pfp_path:
            try:
                with open(self.new_pfp_path, 'rb') as f:
                    image_blob = f.read()
                data_to_update['profile_picture'] = image_blob
            except Exception as e:
                messagebox.showerror("Image Error", f"Could not read image file for saving: {e}")
                return

        for key, entry in self.entries.items():
            new_value = entry.get().strip()
            if key == "password":
                if new_value:
                    if len(new_value) < 8: messagebox.showerror("Error",
                                                                "Password must be at least 8 characters."); return
                    if not re.search(r"[A-Z]", new_value): messagebox.showerror("Error",
                                                                                "Password needs uppercase."); return
                    if not re.search(r"[a-z]", new_value): messagebox.showerror("Error",
                                                                                "Password needs lowercase."); return
                    if not re.search(r"\d", new_value): messagebox.showerror("Error", "Password needs digit."); return
                    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_+=~`\[\]\\';/-]", new_value): messagebox.showerror(
                        "Error", "Password needs special char."); return
                    if re.search(r"\s", new_value): messagebox.showerror("Error",
                                                                         "Password cannot contain spaces."); return
                    data_to_update[key] = new_value
            elif key == "email":
                if new_value != original_data.get(key, ""):
                    if not new_value: messagebox.showerror("Error", "Email cannot be empty."); return
                    if not new_value.lower().endswith(("@gmail.com", "@yahoo.com")): messagebox.showerror("Error",
                                                                                                          "Email must end with @gmail.com or @yahoo.com"); return
                    data_to_update[key] = new_value
            elif key == "username":
                if new_value != original_data.get(key, ""):
                    if not new_value: messagebox.showerror("Error", "Username cannot be empty."); return
                    data_to_update[key] = new_value
            elif key == "contact":
                if new_value != original_data.get(key, ""):
                    if not new_value: messagebox.showerror("Error", "Contact cannot be empty."); return
                    if not new_value.isdigit() or len(new_value) < 10: messagebox.showerror("Error",
                                                                                            "Invalid contact number format."); return
                    data_to_update[key] = new_value
            else:  # fullname
                if new_value != original_data.get(key, ""):
                    if not new_value: messagebox.showerror("Error", f"{key.capitalize()} cannot be empty."); return
                    data_to_update[key] = new_value

        if not data_to_update:
            messagebox.showinfo("No Changes", "No profile information was modified.")
            self.cancel_edit()
            return

        if self.update_user_data(self.controller.user_id, data_to_update):
            self.new_pfp_path = None
            self.load_user_data()
            self.cancel_edit()

    # --- cancel_edit --- (No changes needed)
    def cancel_edit(self):
        self.new_pfp_path = None
        for tag in (self.pfp_bg, self.pfp_text, self.pfp_image_id):
            self.canvas.tag_unbind(tag, "<Button-1>")
            self.canvas.tag_unbind(tag, "<Enter>")
            self.canvas.tag_unbind(tag, "<Leave>")
        self.canvas.config(cursor="")

        self.load_user_data() # This will reload the original PFP and hide/show text correctly

        for key, entry in self.entries.items():
            entry.config(state="readonly", readonlybackground="#FFFAFA", fg="#555555")
            if key == "password": entry.config(show="*")

        if self.eye_button: self.eye_button.place_forget()
        self.password_visible = False

        self.canvas.itemconfigure(self.save_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.save_btn_text, state="hidden")
        self.canvas.itemconfigure(self.cancel_btn_rect, state="hidden")
        self.canvas.itemconfigure(self.cancel_btn_text, state="hidden")
        self.canvas.itemconfigure(self.edit_btn_rect, state="normal")
        self.canvas.itemconfigure(self.edit_btn_text, state="normal")

    # --- on_pfp_click --- (No changes needed)
    def on_pfp_click(self, event=None):
        """Opens a file dialog to select a profile picture."""
        file_types = [
            ('Image Files', '*.png *.jpg *.jpeg'),
            ('PNG files', '*.png'),
            ('JPEG files', '*.jpg *.jpeg')
        ]
        filepath = filedialog.askopenfilename(
            title="Select a Profile Picture",
            filetypes=file_types
        )
        if not filepath:
            return

        self.new_pfp_path = filepath
        self.display_profile_picture_from_file(filepath)

    # --- UPDATED: display_profile_picture_from_file ---
    def display_profile_picture_from_file(self, filepath):
        """Loads, rounds, resizes, and displays an image from a file."""
        try:
            img = Image.open(filepath)
            img = crop_and_mask_circle(img, self.pfp_display_size)

            self.pfp_image = ImageTk.PhotoImage(img) # Set the image reference
            self.canvas.itemconfigure(self.pfp_image_id, image=self.pfp_image)

            # --- UPDATED: Always hide text when an image is displayed ---
            self.canvas.itemconfigure(self.pfp_text, state="hidden")
            # --- END OF UPDATE ---

        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.new_pfp_path = None
            self.pfp_image = None # Ensure reference is cleared on error

    # --- UPDATED: display_profile_picture_from_blob ---
    def display_profile_picture_from_blob(self, blob_data):
        """Loads, rounds, resizes, and displays an image from BLOB data."""
        try:
            img_data = io.BytesIO(blob_data)
            img = Image.open(img_data)
            img = crop_and_mask_circle(img, self.pfp_display_size)

            self.pfp_image = ImageTk.PhotoImage(img) # Set the image reference
            self.canvas.itemconfigure(self.pfp_image_id, image=self.pfp_image)

            # --- UPDATED: Always hide text when an image is displayed ---
            self.canvas.itemconfigure(self.pfp_text, state="hidden")
            # --- END OF UPDATE ---

        except Exception as e:
            print(f"Error loading PFP from BLOB: {e}")
            self.canvas.itemconfigure(self.pfp_image_id, image="")
            self.canvas.itemconfigure(self.pfp_text, text="Picture", state="normal")
            self.pfp_image = None # Ensure reference is cleared on error