from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, ttk, Listbox
import mysql.connector
import re
import bcrypt
from datetime import datetime
from utils import get_db_connection, round_rectangle
import random
import string
import os
import io  # <-- 1. ADDED THIS IMPORT
from PIL import Image, ImageTk

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame6"


# --- 2. REMOVED THE PROFILE_PIC_PATH VARIABLE ---


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_user) not found at {asset_file}")
    return asset_file


class AdminUserFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.all_users = []
        self.selected_user_row_bg = None

        self.canvas = Canvas(
            self,
            bg="#FFFFFF",
            height=570,
            width=905,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- Background Elements ---
        self.canvas.create_rectangle(15, 15, 905 - 15, 570 - 15, fill="#FFF6F6", outline="#CCCCCC")
        self.canvas.create_rectangle(35, 37, 864, 541, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(44, 46, 247, 535, fill="#FFFFFF", outline="#000000")

        try:
            self.logo_image = PhotoImage(file=relative_to_assets("image_2.png"))
            self.canvas.create_image(145.0, 84.0, image=self.logo_image)
        except tk.TclError:
            self.canvas.create_text(145, 85, text="Logo Missing", fill="#555555", font=("Inter", 10))

        self.canvas.create_text(119.0, 135.0, anchor="nw", text="ADMIN", fill="#000000", font=("Inter Bold", 15 * -1))

        self.canvas.create_text(260.0, 46.0, anchor="nw", text="User Details", fill="#000000",
                                font=("Inter Bold", 32 * -1))
        self.canvas.create_rectangle(253.0, 37.0, 254.0, 542.0, fill="#000000", outline="#000000")

        self.canvas.create_rectangle(266.0, 87.0, 630.0, 162.0, fill="#FFFFFF", outline="#000000")

        # --- Picture Area (Modified) ---
        self.current_user_photo = None  # Holds the photo to prevent garbage collection
        self.PIC_BOX = (273.0, 92.0, 349.0, 158.0)  # (x1, y1, x2, y2)

        self.pic_area_rect = self.canvas.create_rectangle(
            self.PIC_BOX[0], self.PIC_BOX[1], self.PIC_BOX[2], self.PIC_BOX[3],
            fill="#F0F0F0", outline="#CCCCCC"
        )
        self.pic_area_text = self.canvas.create_text(
            (self.PIC_BOX[0] + self.PIC_BOX[2]) / 2,
            (self.PIC_BOX[1] + self.PIC_BOX[3]) / 2,
            anchor="center",
            text="Picture\nArea",
            fill="#999999",
            font=("Inter", 10),
            justify="center"
        )
        # --- End Picture Area ---

        self.canvas.create_rectangle(265.0, 171.0, 441.0, 225.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(455.0, 171.0, 631.0, 225.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(266.0, 230.0, 442.0, 284.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(455.0, 230.0, 631.0, 284.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(266.0, 288.0, 630.0, 439.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(266.0, 443.0, 630.0, 535.0, fill="#FFFFFF", outline="#000000")

        # --- Labels for Details ---
        self.canvas.create_text(366.0, 98.0, anchor="nw", text="Name:", fill="#000000", font=("Inter Bold", 13 * -1))
        self.canvas.create_text(366.0, 118.0, anchor="nw", text="Role:", fill="#000000", font=("Inter Bold", 12 * -1))
        self.canvas.create_text(366.0, 138.0, anchor="nw", text="Member since:", fill="#000000",
                                font=("Inter Bold", 12 * -1))
        self.canvas.create_text(273.0, 178.0, anchor="nw", text="Total Jobs", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        self.canvas.create_text(464.0, 178.0, anchor="nw", text="Completed", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        self.canvas.create_text(273.0, 236.0, anchor="nw", text="Declined", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        self.canvas.create_text(464.0, 236.0, anchor="nw", text="Pages Printed", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        self.canvas.create_text(277.0, 296.0, anchor="nw", text="Profile", fill="#000000", font=("Inter Bold", 20 * -1))
        self.canvas.create_text(276.0, 327.0, anchor="nw", text="Full name:", fill="#000000", font=("Inter", 12 * -1))
        self.canvas.create_text(276.0, 347.0, anchor="nw", text="Username:", fill="#000000", font=("Inter", 12 * -1))
        self.canvas.create_text(276.0, 367.0, anchor="nw", text="Email:", fill="#000000", font=("Inter", 12 * -1))
        self.canvas.create_text(276.0, 387.0, anchor="nw", text="Contact:", fill="#000000", font=("Inter", 12 * -1))
        self.canvas.create_text(276.0, 407.0, anchor="nw", text="Password:", fill="#000000", font=("Inter", 12 * -1))

        # --- Action Buttons ---
        self.create_rounded_button(421.0, 451.0, 102.0, 25.0, "Reset Password", self.reset_password,
                                   fill="#000000", text_color="#FFFFFF", outline_color="#000000", outline_width=1)
        self.create_rounded_button(533.0, 451.0, 88.0, 25.0, "Disable User", self.disable_selected_user,
                                   fill="#DC3545", text_color="#FFFFFF", outline_color="#A72A36", outline_width=1)
        self.create_rounded_button(533.0, 491.0, 88.0, 25.0, "Activate User", self.activate_selected_user,
                                   fill="#28A745", text_color="#FFFFFF", outline_color="#1D7A32", outline_width=1)

        # --- Recent Activity Area ---
        self.canvas.create_text(286.0, 451.0, anchor="nw", text="Recent Activity", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        round_rectangle(self.canvas, 276.0, 475.0, 420.0, 525.0, r=5, fill="#F8F9FA", outline="#E0E0E0")

        # --- User List Area ---
        self.canvas.create_rectangle(635.0, 37.0, 638.0, 542.0, fill="#000000", outline="#000000")
        self.canvas.create_text(646.0, 55.0, anchor="nw", text="Search", fill="#000000", font=("Inter Bold", 14 * -1))

        self.search_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, highlightcolor="#000000",
                                  highlightbackground="#CCCCCC", font=("Inter", 12))
        self.search_entry.place(x=704.0, y=50.0, width=134.0, height=25.0)
        self.search_entry.bind("<KeyRelease>", self.on_user_search)

        # --- Scrollable User List ---
        main_list_container = tk.Frame(self, bg="white", bd=1, relief="solid")
        main_list_container.place(x=646.0, y=83.0, width=212.0, height=448.0)
        header_frame = tk.Frame(main_list_container, bg="white", height=35)
        header_frame.pack(side="top", fill="x")
        header_frame.pack_propagate(False)
        scroll_container = tk.Frame(main_list_container, bg="white")
        scroll_container.pack(side="top", fill="both", expand=True)
        header_frame.columnconfigure(0, weight=1)
        header_frame.columnconfigure(1, weight=3)
        tk.Label(header_frame, text="User ID", font=("Inter Bold", 11), bg="white", anchor="w").grid(row=0, column=0,
                                                                                                     sticky="nsew",
                                                                                                     padx=(15, 5),
                                                                                                     pady=5)
        tk.Label(header_frame, text="Username", font=("Inter Bold", 11), bg="white", anchor="w").grid(row=0, column=1,
                                                                                                      sticky="nsew",
                                                                                                      padx=(5, 15),
                                                                                                      pady=5)
        ttk.Separator(header_frame, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew")

        self.user_list_canvas = Canvas(scroll_container, bg="white", bd=0, highlightthickness=0)
        user_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.user_list_canvas.yview)
        self.user_list_canvas.configure(yscrollcommand=user_scrollbar.set)
        user_scrollbar.pack(side="right", fill="y")
        self.user_list_canvas.pack(side="left", fill="both", expand=True)
        self.user_content_frame = tk.Frame(self.user_list_canvas, bg="white")
        self.user_content_frame_window = self.user_list_canvas.create_window((0, 0), window=self.user_content_frame,
                                                                             anchor="nw")

        self.user_content_frame.bind("<Configure>", lambda event: self.on_frame_configure(self.user_list_canvas))
        self.user_list_canvas.bind("<Configure>",
                                   lambda e: self.user_list_canvas.itemconfig(self.user_content_frame_window,
                                                                              width=e.width))
        self.user_list_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.user_list_canvas))
        self.user_list_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))
        self.user_content_frame.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.user_list_canvas))
        self.user_content_frame.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        # --- Sidebar Buttons ---
        sidebar_y_start = 150
        sidebar_y_offset = 56
        self.create_rounded_menu_button(71, sidebar_y_start, 151, 38, "Dashboard", self.open_admin_dashboard)
        self.create_rounded_menu_button(71, sidebar_y_start + sidebar_y_offset, 151, 38, "Print Jobs",
                                        self.open_admin_print)
        self.create_rounded_menu_button(71, sidebar_y_start + 2 * sidebar_y_offset, 151, 38, "Reports",
                                        self.open_admin_report)
        self.create_rounded_menu_button(71, sidebar_y_start + 3 * sidebar_y_offset, 151, 38, "Notifications",
                                        self.open_admin_notification)
        self.create_rounded_menu_button(71, sidebar_y_start + 4 * sidebar_y_offset, 151, 38, "Inventory",
                                        self.open_admin_inventory)
        self.create_rounded_menu_button(89, 490, 111, 38, "Logout", self.logout)

        self.load_users()

    def create_rounded_button(self, x, y, w, h, text, command, fill, text_color, outline_color="#000000",
                              outline_width=1):
        """Creates a generic rounded action button."""
        btn_font = ("Inter Bold", 9)

        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill=fill,
                               outline=outline_color, width=outline_width)
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, font=btn_font, fill=text_color)

        try:
            r_hex, g_hex, b_hex = fill[1:3], fill[3:5], fill[5:7]
            r, g, b = int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)
            hover_r, hover_g, hover_b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
            hover_fill = f'#{hover_r:02x}{hover_g:02x}{hover_b:02x}'
        except Exception:
            hover_fill = "#333333"

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill=hover_fill)
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill=fill)
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="")

        self.canvas.tag_bind(rect, "<Button-1>", on_click)
        self.canvas.tag_bind(txt, "<Button-1>", on_click)
        self.canvas.tag_bind(rect, "<Enter>", on_hover)
        self.canvas.tag_bind(txt, "<Enter>", on_hover)
        self.canvas.tag_bind(rect, "<Leave>", on_leave)
        self.canvas.tag_bind(txt, "<Leave>", on_leave)

    def load_users(self):
        self.update_user_details(None)
        self.all_users = self.fetch_users()
        self.display_users_list(self.user_content_frame, self.all_users)
        self.search_entry.delete(0, tk.END)

    def fetch_users(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT user_id, username FROM users ORDER BY user_id ASC"
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            return rows
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching users:\n{err}")
            return []

    def fetch_user_details(self, user_id):
        details = {}
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                return None
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user_info = cursor.fetchone()
            if not user_info:
                return None
            details.update(user_info)

            cursor.execute("""
                SELECT
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN status = 'Declined' THEN 1 ELSE 0 END) as declined_jobs,
                    SUM(CASE WHEN status = 'Completed' THEN pages ELSE 0 END) as total_pages
                FROM print_jobs
                WHERE user_id = %s
            """, (user_id,))
            stats = cursor.fetchone()
            if stats:
                details.update(stats)

            if 'created_at' in details and details['created_at']:
                if isinstance(details['created_at'], datetime):
                    details['member_since'] = details['created_at'].strftime('%Y-%m-%d')
                else:
                    details['member_since'] = str(details['created_at'])
            else:
                details['member_since'] = '-'

            details['total_jobs'] = details.get('total_jobs', 0)
            details['completed_jobs'] = details.get('completed_jobs', 0)
            details['declined_jobs'] = details.get('declined_jobs', 0)
            details['total_pages'] = details.get('total_pages', 0) or 0
            details['role'] = details.get('role', 'User')

            return details

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching user details:\n{err}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def disable_selected_user(self):
        if not self.selected_user_row_bg or not hasattr(self.selected_user_row_bg, "user_data"):
            messagebox.showwarning("No Selection", "Please select a user to disable.")
            return
        user_data = self.selected_user_row_bg.user_data
        user_id = user_data["user_id"]
        if not messagebox.askyesno("Confirm Disable", f"Disable user ID {user_id}?"):
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = 'disabled' WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Account Disabled", f"User ID {user_id} disabled.")
            self.load_users()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error disabling user:\n{err}")

    def reset_password(self):
        if not self.selected_user_row_bg or not hasattr(self.selected_user_row_bg, "user_data"):
            messagebox.showwarning("No Selection", "Select user to reset password.")
            return
        user_data = self.selected_user_row_bg.user_data
        user_id = user_data["user_id"]
        username = user_data["username"]

        reset_window = tk.Toplevel(self.controller)
        reset_window.title(f"Reset Password - {username}")
        reset_window.geometry("400x320")
        reset_window.resizable(False, False)
        reset_window.configure(bg="#FFFFFF")
        reset_window.transient(self.controller)
        reset_window.grab_set()

        reset_window.update_idletasks()
        main_win_x = self.controller.winfo_rootx()
        main_win_y = self.controller.winfo_rooty()
        main_win_w = self.controller.winfo_width()
        main_win_h = self.controller.winfo_height()
        reset_win_w = reset_window.winfo_width()
        reset_win_h = reset_window.winfo_height()
        x = main_win_x + (main_win_w // 2) - (reset_win_w // 2)
        y = main_win_y + (main_win_h // 2) - (reset_win_h // 2)
        reset_window.geometry(f"+{x}+{y}")

        tk.Label(reset_window, text=f"Reset Password for {username}", font=("Inter Bold", 14), bg="#FFFFFF").pack(
            pady=10)
        tk.Label(reset_window, text="New Password:", font=("Inter", 10), bg="#FFFFFF", anchor="w").pack(fill="x",
                                                                                                        padx=20,
                                                                                                        pady=(5, 0))
        new_password_entry = tk.Entry(reset_window, show="", font=("Inter", 10), highlightthickness=1,
                                      highlightcolor="#000000", highlightbackground="#CCCCCC")
        new_password_entry.pack(fill="x", padx=20, pady=5)
        tk.Label(reset_window, text="Confirm New Password:", font=("Inter", 10), bg="#FFFFFF", anchor="w").pack(
            fill="x", padx=20, pady=(5, 0))
        confirm_password_entry = tk.Entry(reset_window, show="", font=("Inter", 10), highlightthickness=1,
                                          highlightcolor="#000000", highlightbackground="#CCCCCC")
        confirm_password_entry.pack(fill="x", padx=20, pady=5)

        req_frame = tk.Frame(reset_window, bg="#FFFFFF")
        req_frame.pack(fill="x", padx=20, pady=5)
        tk.Label(req_frame, text="Password must include:", font=("Inter", 9, "bold"), bg="#FFFFFF",
                 justify="left").pack(anchor="w")
        req_details = "• 8+ characters\n• Uppercase letter\n• Lowercase letter\n• Number\n• Special character (!@#$%^&*...)"
        tk.Label(req_frame, text=req_details, font=("Inter", 8), bg="#FFFFFF", justify="left", fg="#666666").pack(
            anchor="w")

        def generate_random_password():
            chars = string.ascii_letters + string.digits + string.punctuation
            pwd = (
                    random.choice(string.ascii_lowercase) +
                    random.choice(string.ascii_uppercase) +
                    random.choice(string.digits) +
                    random.choice(string.punctuation)
            )
            pwd += ''.join(random.choice(chars) for _ in range(8))
            pwd_list = list(pwd)
            random.shuffle(pwd_list)
            final_pwd = ''.join(pwd_list)

            new_password_entry.config(show="")
            confirm_password_entry.config(show="")
            new_password_entry.delete(0, tk.END)
            new_password_entry.insert(0, final_pwd)
            confirm_password_entry.delete(0, tk.END)
            confirm_password_entry.insert(0, final_pwd)

        def validate_and_reset():
            new_password = new_password_entry.get()
            confirm_password = confirm_password_entry.get()

            if not new_password or not confirm_password:
                messagebox.showerror("Error", "Fill both fields.", parent=reset_window)
                return
            if new_password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match.", parent=reset_window)
                return
            if len(new_password) < 8:
                messagebox.showerror("Error", "Min 8 chars.", parent=reset_window)
                return
            if not re.search(r"[A-Z]", new_password):
                messagebox.showerror("Error", "Needs uppercase.", parent=reset_window)
                return
            if not re.search(r"[a-z]", new_password):
                messagebox.showerror("Error", "Needs lowercase.", parent=reset_window)
                return
            if not re.search(r"\d", new_password):
                messagebox.showerror("Error", "Needs digit.", parent=reset_window)
                return
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>_+=~`\[\]\\';/-]", new_password):
                messagebox.showerror("Error", "Needs special char.", parent=reset_window)
                return
            if re.search(r"\s", new_password):
                messagebox.showerror("Error", "No spaces allowed.", parent=reset_window)
                return

            try:
                hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
                conn.commit()
                cursor.close()
                conn.close()
                messagebox.showinfo("Success", f"Password for {username} reset.")
                reset_window.destroy()
            except mysql.connector.Error as err:
                messagebox.showerror("DB Error", f"Error resetting:\n{err}", parent=reset_window)

        button_frame = tk.Frame(reset_window, bg="#FFFFFF")
        button_frame.pack(fill="x", padx=20, pady=(10, 5))

        # --- "Generate" BUTTON ---
        gen_btn = tk.Button(
            button_frame,
            text="Generate",
            command=generate_random_password,
            bg="#007BFF",  # Blue
            fg="#FFFFFF",
            font=("Inter Bold", 10),
            padx=10, pady=2, relief="raised", bd=1,
            activebackground="#0056B3", activeforeground="#FFFFFF",
            width=8
        )
        gen_btn.pack(side="left", padx=5)

        # --- "Reset" AND "Cancel" BUTTONS ---
        reset_btn = tk.Button(
            button_frame,
            text="Reset Password",
            command=validate_and_reset,
            bg="#000000",
            fg="#FFFFFF",
            font=("Inter Bold", 10),
            padx=10, pady=2, relief="raised", bd=1,
            activebackground="#333333", activeforeground="#FFFFFF",
            width=13
        )
        reset_btn.pack(side="right", padx=(5, 0))

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            command=reset_window.destroy,
            bg="#DC3545",
            fg="#FFFFFF",
            font=("Inter Bold", 10),
            padx=10, pady=2, relief="raised", bd=1,
            activebackground="#A72A36", activeforeground="#FFFFFF",
            width=8
        )
        cancel_btn.pack(side="right", padx=(0, 5))

        new_password_entry.focus_set()

    def activate_selected_user(self):
        if not self.selected_user_row_bg or not hasattr(self.selected_user_row_bg, "user_data"):
            messagebox.showwarning("No Selection", "Please select a user to activate.")
            return
        user_data = self.selected_user_row_bg.user_data
        user_id = user_data["user_id"]
        if not messagebox.askyesno("Confirm Activate", f"Activate user ID {user_id}?"):
            return
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET status = 'active' WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            messagebox.showinfo("Account Activated", f"User ID {user_id} activated.")
            self.load_users()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error activating user:\n{err}")

    def fetch_recent_activity(self, user_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT action, details, created_at FROM activity_logs WHERE user_id = %s ORDER BY created_at DESC LIMIT 3",
                (user_id,))
            activities = cursor.fetchall()
            cursor.close()
            conn.close()
            return activities
        except mysql.connector.Error as err:
            print("DB error fetching activity:", err)
            if err.errno == 1146:
                print("Creating 'activity_logs' table...")
                self.create_activity_logs_table()
            return []

    def create_activity_logs_table(self):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS activity_logs (
                                log_id INT AUTO_INCREMENT PRIMARY KEY, 
                                user_id INT, 
                                action VARCHAR(100), 
                                details VARCHAR(255), 
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, 
                                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                           )""")
            conn.commit()
            cursor.close()
            conn.close()
            print("'activity_logs' table OK.")
            return True
        except mysql.connector.Error as err:
            print(f"Failed to create 'activity_logs': {err}")
            return False

    def update_user_details(self, details):
        # Reset photo area to default placeholder
        self.canvas.delete("user_profile_pic")  # Delete old photo
        self.current_user_photo = None  # Clear reference
        if hasattr(self, 'pic_area_rect'):  # Ensure rects exist
            self.canvas.itemconfigure(self.pic_area_rect, state="normal")  # Show placeholder rect
            self.canvas.itemconfigure(self.pic_area_text, state="normal")  # Show placeholder text

        self.canvas.delete("user_detail")

        activity_y_start = 485

        if not details:
            self.canvas.create_text(366, 98, anchor="nw", text="Name: -", font=("Inter Bold", 13 * -1),
                                    tags="user_detail")
            self.canvas.create_text(366, 118, anchor="nw", text="Role: -", font=("Inter Bold", 12 * -1),
                                    tags="user_detail")
            self.canvas.create_text(366, 138, anchor="nw", text="Member since: -", font=("Inter Bold", 12 * -1),
                                    tags="user_detail")
            self.canvas.create_text(273, 196, anchor="nw", text="-", font=("Inter Bold", 20 * -1), tags="user_detail")
            self.canvas.create_text(464, 196, anchor="nw", text="-", font=("Inter Bold", 20 * -1), tags="user_detail")
            self.canvas.create_text(273, 255, anchor="nw", text="-", font=("Inter Bold", 20 * -1),
                                    tags="user_detail")
            self.canvas.create_text(464, 255, anchor="nw", text="-", font=("Inter Bold", 20 * -1), tags="user_detail")
            self.canvas.create_text(350, 327, anchor="nw", text="-", font=("Inter", 12 * -1), tags="user_detail")
            self.canvas.create_text(350, 347, anchor="nw", text="-", font=("Inter", 12 * -1), tags="user_detail")
            self.canvas.create_text(350, 367, anchor="nw", text="-", font=("Inter", 12 * -1), tags="user_detail")
            self.canvas.create_text(350, 387, anchor="nw", text="-", font=("Inter", 12 * -1), tags="user_detail")
            self.canvas.create_text(350, 407, anchor="nw", text="********", fill="#999999", font=("Inter", 12 * -1),
                                    tags="user_detail")
            self.canvas.create_text(286, activity_y_start, anchor="nw", text="Select a user to see details.",
                                    fill="#999999",
                                    font=("Inter Italic", 10 * -1), tags="user_detail")
            return

        self.canvas.create_text(366, 98, anchor="nw", text=f"Name: {details.get('fullname', '-')}",
                                font=("Inter Bold", 13 * -1), tags="user_detail")
        self.canvas.create_text(366, 118, anchor="nw", text=f"Role: {details.get('role', 'User')}",
                                font=("Inter Bold", 12 * -1), tags="user_detail")
        self.canvas.create_text(366, 138, anchor="nw", text=f"Member since: {details.get('member_since', '-')}",
                                font=("Inter Bold", 12 * -1), tags="user_detail")
        status = details.get('status', 'active')
        status_text, status_color = ("DISABLED", "#D32F2F") if status == 'disabled' else ("ACTIVE", "#2E7D32")
        self.canvas.create_text(550, 98, anchor="nw", text=status_text, fill=status_color, font=("Inter Bold", 12 * -1),
                                tags="user_detail")
        self.canvas.create_text(273, 196, anchor="nw", text=f"{details.get('total_jobs', 0)}",
                                font=("Inter Bold", 20 * -1), tags="user_detail")
        self.canvas.create_text(464, 196, anchor="nw", text=f"{details.get('completed_jobs', 0)}",
                                font=("Inter Bold", 20 * -1), tags="user_detail")
        self.canvas.create_text(273, 255, anchor="nw", text=f"{details.get('declined_jobs', 0)}",
                                font=("Inter Bold", 20 * -1), tags="user_detail")
        self.canvas.create_text(464, 255, anchor="nw", text=f"{details.get('total_pages', 0)}",
                                font=("Inter Bold", 20 * -1), tags="user_detail")
        self.canvas.create_text(350, 327, anchor="nw", text=f"{details.get('fullname', '-')}", font=("Inter", 12 * -1),
                                tags="user_detail")
        self.canvas.create_text(350, 347, anchor="nw", text=f"{details.get('username', '-')}", font=("Inter", 12 * -1),
                                tags="user_detail")
        self.canvas.create_text(350, 367, anchor="nw", text=f"{details.get('email', '-')}", font=("Inter", 12 * -1),
                                tags="user_detail")
        self.canvas.create_text(350, 387, anchor="nw", text=f"{details.get('contact', '-')}", font=("Inter", 12 * -1),
                                tags="user_detail")
        self.canvas.create_text(350, 407, anchor="nw", text="********", font=("Inter", 12 * -1), tags="user_detail")

        recent_activities = self.fetch_recent_activity(details.get('user_id'))
        y_position = activity_y_start
        if recent_activities:
            for activity in recent_activities:
                created_at_dt = activity.get('created_at')
                created_at_str = created_at_dt.strftime('%m/%d %H:%M') if created_at_dt else "--/-- --:--"
                action_desc = activity.get('action', 'Unknown')
                details_text = activity.get('details', '') or ''
                full_activity = f"{action_desc}" + (f": {details_text}" if details_text else "")
                full_activity = full_activity[:25] + "..." if len(full_activity) > 25 else full_activity
                self.canvas.create_text(286, y_position, anchor="nw", text=f"{created_at_str} - {full_activity}",
                                        fill="#333333", font=("Inter", 9 * -1), tags="user_detail")
                y_position += 16
        else:
            self.canvas.create_text(286, y_position, anchor="nw", text="No recent activity.", fill="#999999",
                                    font=("Inter Italic", 10 * -1), tags="user_detail")

        # --- 3. REPLACED THIS ENTIRE BLOCK ---
        # --- Load Profile Picture (MODIFIED TO READ BLOB) ---
        image_data = details.get('profile_picture')  # Get the BLOB data

        if image_data and isinstance(image_data, bytes):  # Check if it's bytes
            try:
                # Use io.BytesIO to treat the byte data as a file
                image_stream = io.BytesIO(image_data)

                # Define box size
                box_w = self.PIC_BOX[2] - self.PIC_BOX[0]
                box_h = self.PIC_BOX[3] - self.PIC_BOX[1]

                # Open the in-memory file
                image = Image.open(image_stream)
                image.thumbnail((box_w, box_h), Image.Resampling.LANCZOS)

                # Must store on self to prevent garbage collection!
                self.current_user_photo = ImageTk.PhotoImage(image)

                # Calculate center for placing the image
                center_x = (self.PIC_BOX[0] + self.PIC_BOX[2]) / 2
                center_y = (self.PIC_BOX[1] + self.PIC_BOX[3]) / 2

                # Hide placeholder
                self.canvas.itemconfigure(self.pic_area_rect, state="hidden")
                self.canvas.itemconfigure(self.pic_area_text, state="hidden")

                # Create the image on the canvas
                self.canvas.create_image(
                    center_x, center_y,
                    image=self.current_user_photo,
                    tags=("user_detail", "user_profile_pic")
                )

            except Exception as e:
                # This might happen if the BLOB data is corrupt or not an image
                print(f"Error loading profile picture from BLOB data: {e}")
                # If error, placeholder will just remain visible
        # --- End Profile Picture ---

        self.canvas.tag_raise("user_detail")

    def display_users_list(self, frame, users_to_display):
        for widget in frame.winfo_children():
            widget.destroy()
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)

        def on_row_enter(event, bg_widget):
            if bg_widget != self.selected_user_row_bg:
                bg_widget.config(bg="#E8F0FE")
                [child.config(bg="#E8F0FE") for child in bg_widget.winfo_children() if isinstance(child, tk.Label)]
            self.config(cursor="hand2")

        def on_row_leave(event, bg_widget):
            if bg_widget != self.selected_user_row_bg:
                bg_widget.config(bg="white")
                [child.config(bg="white") for child in bg_widget.winfo_children() if isinstance(child, tk.Label)]
            self.config(cursor="")

        def on_row_click(event, user_data, bg_widget):
            if self.selected_user_row_bg and self.selected_user_row_bg.winfo_exists():
                self.selected_user_row_bg.config(bg="white")
                [child.config(bg="white") for child in self.selected_user_row_bg.winfo_children() if
                 isinstance(child, tk.Label)]
            bg_widget.config(bg="#BBDEFB")
            [child.config(bg="#BBDEFB") for child in bg_widget.winfo_children() if isinstance(child, tk.Label)]
            self.selected_user_row_bg = bg_widget
            bg_widget.user_data = user_data
            details = self.fetch_user_details(user_data['user_id'])
            self.update_user_details(details)

        row_index = 0
        if not users_to_display:
            tk.Label(frame, text="No users found.", font=("Inter", 12), fg="grey", bg="white").grid(row=0, column=0,
                                                                                                    columnspan=2,
                                                                                                    pady=20)

        for user in users_to_display:
            row_bg_frame = tk.Frame(frame, bg="white", height=30)
            row_bg_frame.grid(row=row_index, column=0, columnspan=2, sticky="ew", pady=(0, 1))
            row_bg_frame.grid_propagate(False)
            row_bg_frame.columnconfigure(0, weight=1)
            row_bg_frame.columnconfigure(1, weight=3)

            id_label = tk.Label(row_bg_frame, text=user["user_id"], font=("Inter", 11), bg="white", anchor="w")
            id_label.place(relx=0.05, rely=0.5, anchor='w')
            username_label = tk.Label(row_bg_frame, text=user["username"], font=("Inter", 11), bg="white", anchor="w")
            username_label.place(relx=0.3, rely=0.5, anchor='w')

            for widget in [row_bg_frame, id_label, username_label]:
                widget.bind("<Enter>", lambda e, bg=row_bg_frame: on_row_enter(e, bg))
                widget.bind("<Leave>", lambda e, bg=row_bg_frame: on_row_leave(e, bg))
                widget.bind("<Button-1>", lambda e, u=user, bg=row_bg_frame: on_row_click(e, u, bg))
            row_index += 1

    def on_user_search(self, event):
        search_term = self.search_entry.get().lower().strip()
        if not self.all_users:
            self.all_users = self.fetch_users()

        filtered_users = self.all_users if not search_term else [
            user for user in self.all_users
            if search_term in str(user.get("user_id", "")) or search_term in str(user.get("username", "")).lower()
        ]

        self.display_users_list(self.user_content_frame, filtered_users)
        self.user_list_canvas.after(50, lambda: self.on_frame_configure(self.user_list_canvas))

    def on_frame_configure(self, canvas):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_mousewheel(self, event, canvas):
        scroll_info = canvas.yview()
        if scroll_info[0] == 0.0 and scroll_info[1] == 1.0:
            return
        if event.delta > 0 or event.num == 4:
            if scroll_info[0] > 0.0:
                canvas.yview_scroll(-1, "units")
        elif event.delta < 0 or event.num == 5:
            if scroll_info[1] < 1.0:
                canvas.yview_scroll(1, "units")

    def _bind_mousewheel(self, event, canvas):
        self.bind_all("<MouseWheel>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-4>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-5>", lambda ev: self._on_mousewheel(ev, canvas))

    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center", fill="#000000",
                                      font=("Inter Bold", 15))
        button_tag = f"button_{text.replace(' ', '_').lower()}"

        def on_click(event):
            if command:
                command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#E8E8E8")
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#FFFFFF")
            self.config(cursor="")

        self.canvas.addtag_withtag(button_tag, rect)
        self.canvas.addtag_withtag(button_tag, txt)
        self.canvas.tag_bind(button_tag, "<Button-1>", on_click)
        self.canvas.tag_bind(button_tag, "<Enter>", on_hover)
        self.canvas.tag_bind(button_tag, "<Leave>", on_leave)

    def open_admin_dashboard(self):
        self.controller.show_admin_dashboard()

    def open_admin_print(self):
        self.controller.show_admin_print()

    def open_admin_report(self):
        self.controller.show_admin_report()

    def open_admin_notification(self):
        self.controller.show_admin_notification()

    def open_admin_inventory(self):
        self.controller.show_admin_inventory()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?"):
            self.controller.show_login_frame()