from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, font
import mysql.connector
import subprocess
import sys
import bcrypt
from utils import get_db_connection, round_rectangle

# --- Placeholder Entry Class ---
class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", show_char="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]
        self.show_char = show_char
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    def put_placeholder(self):
        self.delete(0, "end")
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color
        if self.show_char: self.config(show="")

    def foc_in(self, *args):
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color
            if self.show_char: self.config(show=self.show_char)

    def foc_out(self, *args):
        if not self.get(): self.put_placeholder()


# --- RadioTile Class ---
class RadioTile(tk.Canvas):
    def __init__(self, master, text, variable, value, width=270, height=30, radius=12, **kwargs):
        super().__init__(master, width=width, height=height, bg="#F2F6F5", highlightthickness=0, **kwargs)
        self.variable = variable
        self.value = value
        self.text = text
        self.radius = radius
        self.width = width
        self.height = height
        self.draw_tile()
        self.bind("<Button-1>", self.select_tile)
        self.tag_bind("text", "<Button-1>", self.select_tile)
        self.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        self.bind("<Leave>", lambda e: self.config(cursor=""))

    def draw_rounded_rect(self, x1, y1, x2, y2, r, fill):
        points = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                  x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(points, smooth=True, fill=fill, outline="black", width=1)

    def draw_tile(self):
        self.delete("all")
        if self.variable.get() == self.value:
            fill, text_color = "black", "white"
        else:
            fill, text_color = "#F0F0F0", "black"
        self.draw_rounded_rect(1, 1, self.width - 2, self.height - 2, self.radius, fill=fill)
        self.create_text(self.width / 2, self.height / 2,
                         text=self.text, fill=text_color, font=("Inter", 12, "bold"), tags="text")

    def select_tile(self, event=None):
        self.variable.set(self.value)
        for sibling in self.master.winfo_children():
            if isinstance(sibling, RadioTile): sibling.draw_tile()

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"D:\downloadss\New folder\Tkinter\Tkinter-Designer-master\build\assets\frame0")


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# --- MAIN LOGIN FRAME CLASS ---
class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Load Assets ---
        try:
            self.eye_image = PhotoImage(file=relative_to_assets("view.png"))
            self.eye_slash_image = PhotoImage(file=relative_to_assets("hide.png"))
            self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
            self.image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
            self.image_image_4 = PhotoImage(file=relative_to_assets("image_4.png"))
            self.image_image_5 = PhotoImage(file=relative_to_assets("image_5.png"))
        except tk.TclError:
            messagebox.showerror("Asset Error", "Could not find assets in the 'frame0' folder.")
            self.controller.destroy()
            return

        canvas = Canvas(
            self, bg="#FFFFFF", height=534, width=859, bd=0, highlightthickness=0, relief="ridge"
        )
        canvas.place(x=0, y=0)
        self.canvas = canvas  # Store canvas as instance variable

        canvas.create_rectangle(15.0, 14.0, 844.0, 518.0, fill="#FFFFFF", outline="#000000", width=1.5)
        canvas.create_text(84.0, 208.0, anchor="nw", text="Your Documents, Our Priority", fill="#000000",
                           font=("Inter", -20))
        canvas.create_rectangle(427.0, 14.0, 844.0, 518.0, fill="#F2F6F5", outline="#000000", width=1.5)
        register_text = canvas.create_text(700.0, 468.0, anchor="nw", text="Register Now", fill="#000000",
                                           font=("Inter", 11, "bold"))
        text = "WELCOME!"
        font_style = font.Font(family="Inter Black", size=42, weight="bold")
        shadow_offset_x, shadow_offset_y, shadow_color = 1, 3, "#999999"
        canvas.create_text(506.0 + shadow_offset_x, 58.0 + shadow_offset_y, anchor="nw", text=text, fill=shadow_color,
                           font=font_style)
        canvas.create_text(506.0, 58.0, anchor="nw", text=text, fill="#000000", font=font_style)
        text1 = "Login with Email / Username"
        font_style1 = font.Font(family="Inter Black", size=12, weight="bold")
        shadow_offset_x1, shadow_offset_y1, shadow_color1 = 1, 1, "#999999"
        canvas.create_text(553.0 + shadow_offset_x1, 131.0 + shadow_offset_y1, anchor="nw", text=text1,
                           fill=shadow_color1,
                           font=font_style1)
        canvas.create_text(553.0, 131.0, anchor="nw", text=text1, fill="#000000", font=font_style1)

        role_frame = tk.Frame(self, bg="#F2F6F5")
        role_frame.place(x=500, y=155)
        self.selected_role = tk.StringVar(value="User")
        admin_tile = RadioTile(role_frame, "Admin", self.selected_role, "Admin", width=153, height=32)
        admin_tile.grid(row=0, column=0)
        user_tile = RadioTile(role_frame, "User", self.selected_role, "User", width=153, height=32)
        user_tile.grid(row=0, column=1)

        self.entry_email, _ = self.create_rounded_entry(500, 221, placeholder="Email or Username")
        self.entry_password, self.eye_icon = self.create_rounded_entry(500, 293, placeholder="Password", show_char="*",
                                                                       with_eye=True)

        canvas.create_text(500.0, 195.0, anchor="nw", text="Email or Username", fill="#000000",
                           font=("Inter Bold", -20))
        canvas.create_text(500.0, 267.0, anchor="nw", text="Password", fill="#000000", font=("Inter Bold", -20))
        btn_login = round_rectangle(canvas, 553, 385, 731, 427, r=10, fill="#000000", outline="")
        btn_login_text = canvas.create_text(615.0, 395.0, anchor="nw", text="Login", fill="#FFFFFF",
                                            font=("Inter", -20))
        self.forgot_pw_label = canvas.create_text(671.0, 349.0, anchor="nw", text="Forgot Password?", fill="#000000",
                                                  font=("Inter", 11, "bold"), state="hidden")
        canvas.create_text(506.0, 468.0, anchor="nw", text="Don’t have an account?", fill="#000000",
                           font=("Inter", -16))

        image_1 = canvas.create_image(220.0, 90.0, image=self.image_image_1)
        canvas.create_rectangle(169.0, 390.0, 427.0, 391.0, fill="#000000", outline="#000000")
        image_2 = canvas.create_image(475.0, 65.0, image=self.image_image_2)
        canvas.create_rectangle(14.0, 390.0, 24.0, 391.0, fill="#000000", outline="")
        image_3 = canvas.create_image(97.0, 417.0, image=self.image_image_3)
        image_4 = canvas.create_image(360.0, 464.0, image=self.image_image_4)
        image_5 = canvas.create_image(249.0, 426.0, image=self.image_image_5)

        canvas.tag_bind(btn_login, "<Button-1>", lambda e: self.login_user())
        canvas.tag_bind(btn_login_text, "<Button-1>", lambda e: self.login_user())
        for tag in (btn_login, btn_login_text, self.forgot_pw_label, register_text):
            canvas.tag_bind(tag, "<Enter>", lambda e: self.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda e: self.config(cursor=""))
        canvas.tag_bind(self.forgot_pw_label, "<Button-1>", lambda e: self.open_forgot())
        canvas.tag_bind(register_text, "<Button-1>", lambda e: self.open_register())

    # --- Open Register Window ---
    def open_register(self):
        # We still use subprocess for modal windows (register/forgot)
        # We just hide the main controller window
        self.controller.withdraw()
        process = subprocess.Popen([sys.executable, "register.py"])
        process.wait()  # Wait for register.py to close
        self.controller.deiconify()  # Show main window again

    def open_forgot(self):
        self.controller.withdraw()
        process = subprocess.Popen([sys.executable, "forgot.py"])
        process.wait()  # Wait for forgot.py to close
        self.controller.deiconify()  # Show main window again

    # --- Login Function (MODIFIED) ---
    def login_user(self):
        username_or_email = self.entry_email.get()
        password = self.entry_password.get()
        role = self.selected_role.get()

        if username_or_email == "Email or Username": username_or_email = ""
        if password == "Password": password = ""

        if not username_or_email or not password:
            messagebox.showerror("Error", "Please enter both username/email and password.")
            return

        password_bytes = password.encode('utf-8')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            if role == "User":
                cursor.execute("""
                    SELECT user_id, fullname, status, password 
                    FROM users
                    WHERE (username = %s OR email = %s)
                """, (username_or_email, username_or_email))
                user = cursor.fetchone()

                # Use .encode() on the password from the DB (which is bytes)
                if user and bcrypt.checkpw(password_bytes, user['password'].encode('utf-8')):
                    if user['status'] == 'disabled':
                        messagebox.showerror("Account Disabled", "Sorry, your account was disabled.")
                        return
                    elif user['status'] == 'active':
                        user_id = user['user_id']
                        fullname = user['fullname']
                        messagebox.showinfo("Success", f"Welcome {fullname}!")

                        # --- KEY CHANGE ---
                        # Instead of subprocess, call the controller
                        self.controller.on_login_success(user_id, fullname)
                        # --- END KEY CHANGE ---

                    else:
                        messagebox.showerror("Error", "Your account status is invalid.")
                else:
                    messagebox.showerror("Error", "Invalid username/email or password.")
                    self.canvas.itemconfigure(self.forgot_pw_label, state="normal")

            elif role == "Admin":
                cursor.execute("""
                    SELECT * FROM admin_login
                    WHERE admin_username = %s AND admin_password = %s
                """, (username_or_email, password))
                admin = cursor.fetchone()

                if admin:
                    admin_name = admin['admin_username']
                    messagebox.showinfo("Success", f"Welcome {admin_name} (Admin)!")
                    # We can't transition to admin frame yet, so just close for now
                    self.controller.destroy()
                    # subprocess.Popen([sys.executable, "admin_dashboard.py", admin_name]) # This still works
                else:
                    messagebox.showerror("Error", "Invalid admin username or password.")
                    self.canvas.itemconfigure(self.forgot_pw_label, state="normal")
            cursor.close()
            conn.close()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

    # --- Helper for Rounded Entry ---
    def create_rounded_entry(self, x_pos, y_pos, placeholder="", show_char="", with_eye=False):
        round_rectangle(self.canvas, x_pos, y_pos + 7, 802, y_pos + 37, r=10, fill="#999999", outline="")
        round_rectangle(self.canvas, x_pos, y_pos + 5, 800, y_pos + 35, r=10, fill="white", outline="#000000", width=1)
        entry = PlaceholderEntry(
            self, placeholder=placeholder, bd=0, bg="white", fg="#000000",
            show_char=show_char, highlightthickness=0, font=("Inter", 12)
        )
        if with_eye:
            self.canvas.create_window(635, y_pos + 20, width=260, height=20, window=entry)
        else:
            self.canvas.create_window(650, y_pos + 20, width=290, height=20, window=entry)
        icon_item = None
        if with_eye:
            icon_item = self.canvas.create_image(775, y_pos + 10, anchor="nw", image=self.eye_image)
            self.canvas.tag_bind(icon_item, "<Button-1>", lambda e: self.toggle_password(entry, icon_item))
            self.canvas.tag_bind(icon_item, "<Enter>", lambda e: self.config(cursor="hand2"))
            self.canvas.tag_bind(icon_item, "<Leave>", lambda e: self.config(cursor=""))
        return entry, icon_item

    # --- Toggle Password ---
    def toggle_password(self, entry, icon_item):
        if entry.get() == entry.placeholder and entry["fg"] == entry.placeholder_color: return
        if entry.cget("show") == "":
            entry.config(show="*")
            self.canvas.itemconfig(icon_item, image=self.eye_slash_image)
        else:
            entry.config(show="")
            self.canvas.itemconfig(icon_item, image=self.eye_image)