from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, ttk, Frame, Label
import mysql.connector
import os
import shutil
from tkinter import filedialog
from decimal import Decimal, InvalidOperation
from utils import get_db_connection, round_rectangle
from datetime import datetime

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_print) not found at {asset_file}")
    return asset_file


class AdminPrintFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_job_ref = [None]

        self.job_row_widgets = []
        self.selected_job_row = None
        self.selected_row_index = -1

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=570, width=1294,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        self.canvas.create_rectangle(33.0, 31.0, 1063.0, 535.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(41.0, 39.0, 244.0, 527.0, fill="#FFFFFF", outline="#000000")
        try:
            self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(143.0, 79.0, image=self.image_image_1)
        except tk.TclError:
            self.canvas.create_text(143.0, 79.0, text="Logo Missing", fill="#000000")
        self.canvas.create_text(117.0, 130.0, anchor="nw", text="ADMIN", fill="#000000", font=("Inter Bold", 15 * -1))
        self.canvas.create_text(272.0, 40.0, anchor="nw", text="Print Jobs Management", fill="#000000",
                                font=("Inter Bold", 32 * -1))
        self.canvas.create_rectangle(258.0, 32.0, 258.0, 536.0, fill="#000000", outline="")

        self.canvas.create_rectangle(865.0, 79.0, 1051.0, 527.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(882.0, 84.0, anchor="nw", text="Selected User Details", fill="#000000",
                                font=("Inter Bold", 15 * -1))
        self.canvas.create_text(876.0, 246.0, anchor="nw", text="Admin Notes/Reason if Declined", fill="#000000",
                                font=("Inter Bold", 11 * -1))
        self.canvas.create_rectangle(871.0, 262.0, 1046.0, 318.0, fill="#FFFFFF", outline="#000000")

        self.canvas.create_rectangle(260.0, 86.0, 863.0, 138.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(269.0, 86.0, anchor="nw", text="Search Username:", fill="#000000",
                                font=("Inter Bold", 12 * -1))
        self.canvas.create_rectangle(482.0, 101.0, 579.0, 132.0, fill="#FFFFFF",
                                     outline="#000000")
        self.canvas.create_text(462.0, 86.0, anchor="nw", text="Status:", fill="#000000", font=("Inter Bold", 12 * -1))

        self.canvas.create_rectangle(257.0, 183.0, 863.0, 185.0, fill="#000000", outline="#000000")

        headers = [
            (271.0, "ID"), (321.0, "Username"), (421.0, "File"), (541.0, "Pages"),
            (591.0, "Size"), (641.0, "Color"), (701.0, "Status"), (771.0, "Submitted")
        ]

        for x_pos, text in headers:
            self.canvas.create_text(x_pos, 167.0, anchor="nw", text=text, fill="#000000", font=("Inter Bold", 12 * -1))

        self.search_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, highlightcolor="#000000",
                                  highlightbackground="#CCCCCC", font=("Inter", 11), relief="solid")
        self.search_entry.place(x=303, y=105, width=150, height=22)
        self.search_entry.bind("<Enter>", self.on_search_hover)
        self.search_entry.bind("<Leave>", self.on_search_leave)

        self.status_var = tk.StringVar(value="All")
        self.status_dropdown = ttk.Combobox(self, textvariable=self.status_var,
                                            values=["All", "Pending", "Approved", "Paid", "Cash", "Declined",
                                                    "Completed", "In Progress"], state="readonly", font=("Inter", 11))
        self.status_dropdown.place(x=485, y=105, width=85, height=22)

        x1, y1, width, height = 590, 103, 55, 25
        x2, y2 = x1 + width, y1 + height
        round_rectangle(self.canvas, x1, y1, x2, y2, r=5, fill="#FFFFFF", outline="#000000", width=1,
                        tags=("filter_btn_rect", "filter_btn_all"))
        self.canvas.create_text(x1 + (width / 2), y1 + (height / 2), text="Filter", fill="#000000",
                                font=("Inter Bold", 11), tags=("filter_btn_txt", "filter_btn_all"))
        self.canvas.tag_bind("filter_btn_all", "<Button-1>", lambda e: self.on_filter_click())
        self.canvas.tag_bind("filter_btn_all", "<Enter>", self.on_filter_hover)
        self.canvas.tag_bind("filter_btn_all", "<Leave>", self.on_filter_leave)

        self.create_rounded_menu_button(74, 170, 151, 38, "Dashboard", self.open_admin_dashboard)
        self.create_rounded_menu_button(74, 226, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(74, 283, 151, 38, "Reports", self.open_admin_report)
        self.create_rounded_menu_button(74, 340, 151, 38, "Notifications", self.open_admin_notification)
        self.create_rounded_menu_button(74, 397, 151, 38, "Inventory", self.open_admin_inventory)
        self.create_rounded_menu_button(97, 473, 111, 38, "Logout", self.logout)

        self.notes_text = Text(self, bd=0, relief="flat", wrap="word", highlightthickness=1,
                               highlightbackground="#000000")
        self.notes_text.place(x=875, y=265, width=165, height=50)
        self.notes_text.insert("1.0", "")

        list_x = 259
        list_y = 185
        list_w = 863 - list_x
        list_h = 527 - list_y

        scroll_container = tk.Frame(self, bg="white", bd=0)
        scroll_container.place(x=list_x, y=list_y, width=list_w, height=list_h)

        self.job_list_canvas = Canvas(scroll_container, bg="white", bd=0, highlightthickness=0, takefocus=1)
        job_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.job_list_canvas.yview)
        self.job_list_canvas.configure(yscrollcommand=job_scrollbar.set)

        job_scrollbar.pack(side="right", fill="y")
        self.job_list_canvas.pack(side="left", fill="both", expand=True)

        self.job_content_frame = tk.Frame(self.job_list_canvas, bg="white")
        self.job_content_frame_window = self.job_list_canvas.create_window(
            (0, 0), window=self.job_content_frame, anchor="nw"
        )

        self.job_content_frame.bind("<Configure>", lambda event: self.on_frame_configure(self.job_list_canvas))
        self.job_list_canvas.bind("<Configure>",
                                  lambda e: self.job_list_canvas.itemconfig(self.job_content_frame_window,
                                                                            width=e.width))
        self.job_list_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.job_list_canvas))
        self.job_list_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))
        self.job_content_frame.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.job_list_canvas))
        self.job_content_frame.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        self.job_list_canvas.bind("<Up>", lambda e: self.navigate_jobs("up"))
        self.job_list_canvas.bind("<Down>", lambda e: self.navigate_jobs("down"))

        self.add_print_job_buttons()
        self.load_print_jobs()

    def load_print_jobs(self):
        self.job_row_widgets.clear()
        self.selected_job_row = None
        self.selected_row_index = -1

        self.display_print_jobs()
        self.update_job_details(None)
        self.notes_text.delete("1.0", tk.END)
        self.selected_job_ref[0] = None

    def fetch_print_jobs(self):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                return []
            cursor = conn.cursor(dictionary=True)
            query = """ SELECT pj.job_id, u.username, u.user_id, f.file_id, f.file_name, f.file_type,
                                   pj.pages, pj.paper_size, pj.color_option, pj.copies, pj.payment_method,
                                   pj.total_amount, pj.status, pj.notes, pj.created_at, pj.updated_at
                                FROM print_jobs pj LEFT JOIN users u ON pj.user_id = u.user_id
                                LEFT JOIN files f ON pj.file_id = f.file_id
                                ORDER BY
                                    CASE
                                        WHEN pj.status = 'Paid' THEN 1
                                        WHEN pj.status = 'Cash' THEN 2
                                        WHEN pj.status = 'Pending' THEN 3
                                        WHEN pj.status = 'Approved' THEN 4
                                        WHEN pj.status = 'In Progress' THEN 5
                                        WHEN pj.status = 'Declined' THEN 6
                                        WHEN pj.status = 'Completed' THEN 7
                                        ELSE 8
                                    END,
                                    pj.updated_at DESC, pj.created_at DESC """
            cursor.execute(query)
            rows = cursor.fetchall()
            return rows if rows else []
        except mysql.connector.Error as err:
            print(f"DB Error: {err}")
            return []
        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def display_print_jobs(self, jobs_to_display=None):
        for widget in self.job_content_frame.winfo_children():
            widget.destroy()

        self.job_row_widgets.clear()
        self.selected_job_row = None
        self.selected_row_index = -1

        jobs = jobs_to_display if jobs_to_display is not None else self.fetch_print_jobs()

        status_map = {
            "Pending": "P", "Approved": "A", "Completed": "C",
            "Declined": "D", "In Progress": "IP", "Paid": "Paid",
            "Cash": "Cash"
        }

        self.job_content_frame.columnconfigure(0, minsize=50)
        self.job_content_frame.columnconfigure(1, minsize=100)
        self.job_content_frame.columnconfigure(2, minsize=120)
        self.job_content_frame.columnconfigure(3, minsize=50)
        self.job_content_frame.columnconfigure(4, minsize=50)
        self.job_content_frame.columnconfigure(5, minsize=60)
        self.job_content_frame.columnconfigure(6, minsize=70)
        self.job_content_frame.columnconfigure(7, minsize=95)

        if not jobs:
            no_req_label = Label(self.job_content_frame, text="No print jobs found.",
                                 font=("Inter Italic", 11), bg="white", fg="#888888")
            no_req_label.grid(row=0, column=0, columnspan=8, pady=20, padx=10, sticky="ew")

        for index, job in enumerate(jobs):
            job_id_val = job.get("job_id", "N/A")
            username_full = job.get("username", "-")
            username_val = username_full[:12] + "..." if len(username_full) > 12 else username_full
            file_id_val = job.get("file_id", "-")
            pages_val = job.get("pages", "-")
            size_val = job.get("paper_size", "-")
            color_option_val = job.get("color_option", "-")

            if color_option_val == "Black & White":
                color_val = "B&W"
            elif color_option_val == "Color":
                color_val = "C"
            elif color_option_val == "Partially Colored":
                color_val = "PC"
            else:
                color_val = color_option_val

            status_text_val = job.get("status", "-")
            status_val = status_map.get(status_text_val, status_text_val)
            file_name_full = job.get("file_name", f"File {file_id_val}")
            file_name_val = file_name_full[:15] + "..." if len(file_name_full) > 15 else file_name_full
            submitted_dt = job.get("created_at")
            submitted_val = submitted_dt.strftime("%m/%d %H:%M") if submitted_dt else "-"

            bg_color = "#FFFFFF" if index % 2 == 0 else "#F8F9FA"

            row_frame = Frame(self.job_content_frame, bg=bg_color)
            row_frame.grid(row=index, column=0, columnspan=8, sticky="ew", pady=(1, 0))

            row_frame.columnconfigure(0, minsize=50)
            row_frame.columnconfigure(1, minsize=100)
            row_frame.columnconfigure(2, minsize=120)
            row_frame.columnconfigure(3, minsize=50)
            row_frame.columnconfigure(4, minsize=50)
            row_frame.columnconfigure(5, minsize=60)
            row_frame.columnconfigure(6, minsize=70)
            row_frame.columnconfigure(7, minsize=95)

            labels_data = [
                (f"#{job_id_val}", "w", 13), (username_val, "w", 0), (file_name_val, "w", 0),
                (pages_val, "w", 0), (size_val, "w", 0), (color_val, "w", 0),
                (status_val, "w", 0), (submitted_val, "w", 0)
            ]

            widget_list_for_binding = [row_frame]

            for col, (text, anchor, padx_left) in enumerate(labels_data):
                lbl = Label(row_frame, text=text, font=("Inter", 10), bg=bg_color, fg="#333333", anchor=anchor)
                lbl.grid(row=0, column=col, sticky="nsew", padx=(padx_left, 0))
                widget_list_for_binding.append(lbl)

            for widget in widget_list_for_binding:
                widget.bind("<Enter>", lambda e, rf=row_frame, idx=index: self.on_row_enter(e, rf, idx))
                widget.bind("<Leave>", lambda e, rf=row_frame, idx=index: self.on_row_leave(e, rf, idx))
                widget.bind("<Button-1>", lambda e, rf=row_frame, idx=index, j=job: self.on_row_click(e, rf, idx, j))
                widget.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.job_list_canvas), add="+")
                widget.bind("<Leave>", lambda e: self._unbind_mousewheel(e), add="+")
                widget.bind("<Button-1>", lambda e: self.job_list_canvas.focus_set(), add="+")

            self.job_row_widgets.append(row_frame)

        self.job_content_frame.update_idletasks()
        self.on_frame_configure(self.job_list_canvas)
        self.job_list_canvas.yview_moveto(0)

    def set_row_color(self, row_frame, index, state):
        """Helper function to set the background color of a row and its children."""
        if not row_frame or not row_frame.winfo_exists():
            return

        if state == "selected":
            color = "#CCE5FF"
        elif state == "hover":
            color = "#E0F0FF"
        else:
            color = "#FFFFFF" if index % 2 == 0 else "#F8F9FA"

        row_frame.config(bg=color)
        for widget in row_frame.winfo_children():
            widget.config(bg=color)

    def on_row_click(self, event, row_frame, index, job_data):
        """Handles clicking on a request row."""
        if self.selected_job_row and self.selected_job_row.winfo_exists():
            self.set_row_color(self.selected_job_row, self.selected_row_index, "default")

        self.set_row_color(row_frame, index, "selected")
        self.selected_job_row = row_frame
        self.selected_row_index = index

        self.selected_job_ref[0] = job_data
        self.update_job_details(job_data)

        self.job_list_canvas.yview_moveto(row_frame.winfo_y() / self.job_content_frame.winfo_height())

    def on_row_enter(self, event, row_frame, index):
        """Handles mouse hovering over a request row."""
        if row_frame != self.selected_job_row:
            self.set_row_color(row_frame, index, "hover")
        self.config(cursor="hand2")

    def on_row_leave(self, event, row_frame, index):
        """Handles mouse leaving a request row."""
        if row_frame != self.selected_job_row:
            self.set_row_color(row_frame, index, "default")
        self.config(cursor="")

    def navigate_jobs(self, direction):
        """Handles Up/Down arrow key navigation."""
        if not self.job_row_widgets:
            return

        if self.selected_row_index == -1:
            new_index = 0
        elif direction == "down":
            new_index = min(self.selected_row_index + 1, len(self.job_row_widgets) - 1)
        elif direction == "up":
            new_index = max(self.selected_row_index - 1, 0)
        else:
            return

        if new_index == self.selected_row_index and self.selected_row_index != -1:
            return

        row_to_select = self.job_row_widgets[new_index]

        jobs = []
        username_filter = self.search_entry.get().strip()
        status_filter = self.status_var.get().strip()

        if not username_filter and status_filter == "All":
            jobs = self.fetch_print_jobs()
        else:
            jobs = self.filter_print_jobs(username_filter, status_filter, return_jobs=True)

        if not jobs or new_index >= len(jobs):
            return

        job_data = jobs[new_index]

        self.on_row_click(None, row_to_select, new_index, job_data)

    def filter_print_jobs(self, username_filter, status_filter, return_jobs=False):
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                return [] if return_jobs else None
            cursor = conn.cursor(dictionary=True)
            query = """ SELECT pj.job_id, u.username, u.user_id, f.file_id, f.file_name, f.file_type, 
                           pj.pages, pj.paper_size, pj.color_option, pj.copies, pj.payment_method, 
                           pj.total_amount, pj.status, pj.notes, pj.created_at, pj.updated_at 
                        FROM print_jobs pj 
                        LEFT JOIN users u ON pj.user_id = u.user_id 
                        LEFT JOIN files f ON pj.file_id = f.file_id 
                        WHERE 1=1 """
            params = []
            if username_filter:
                query += " AND u.username LIKE %s"
                params.append(f"%{username_filter}%")
            if status_filter and status_filter != "All":
                query += " AND pj.status = %s"
                params.append(status_filter)
            query += """ ORDER BY
                            CASE
                                WHEN pj.status = 'Paid' THEN 1
                                WHEN pj.status = 'Cash' THEN 2
                                WHEN pj.status = 'Pending' THEN 3
                                WHEN pj.status = 'Approved' THEN 4
                                WHEN pj.status = 'In Progress' THEN 5
                                WHEN pj.status = 'Declined' THEN 6
                                WHEN pj.status = 'Completed' THEN 7
                                ELSE 8
                            END,
                            pj.updated_at DESC, pj.created_at DESC """

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

            if return_jobs:
                return rows if rows else []

            self.display_print_jobs(jobs_to_display=rows)
            self.update_job_details(None)
            self.selected_job_ref[0] = None

        except mysql.connector.Error as err:
            messagebox.showerror("DB Error", f"Error filtering: {err}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Error filtering: {e}", parent=self)
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        return [] if return_jobs else None

    def update_job_details(self, job):
        self.canvas.delete("job_details")
        self.notes_text.delete("1.0", tk.END)

        if not job:
            return

        job_id = job.get('job_id', 'N/A')
        username = job.get('username', '-')
        file_id = job.get('file_id', 'N/A')
        file_name_full = job.get("file_name", f"File {file_id}")
        file_name_display = file_name_full[:27] + "..." if len(file_name_full) > 30 else file_name_full
        pages = str(job.get('pages', '-'))
        status = job.get('status', '-')
        created_at = job.get('created_at')
        submitted_text = created_at.strftime('%Y-%m-%d %H:%M') if created_at else '-'
        notes = job.get('notes', '')

        color_opt = job.get('color_option', '-')
        details = [
            ("Req ID:", f"#{job_id}"), ("User:", username), ("File:", file_name_display),
            ("Pages:", pages), ("Color:", color_opt), ("Status:", status)
        ]
        y = 112
        for label, value in details:
            self.canvas.create_text(871.0, y, anchor="nw", text=f"{label} {value}", fill="#000000",
                                    font=("Inter Bold", 12 * -1), tags="job_details")
            y += 20

        self.canvas.create_text(871.0, y, anchor="nw", text=f"Submitted: {submitted_text}", fill="#000000",
                                font=("Inter Bold", 12 * -1), tags="job_details")
        if notes:
            self.notes_text.insert("1.0", notes)

    def add_print_job_buttons(self):

        def change_status(new_status, deduct_inventory=False):
            job = self.selected_job_ref[0]
            if not job:
                messagebox.showwarning("No Selection", "Please select a job first.", parent=self)
                return False

            # CORRECTED: Inventory check is now *after* the 'if not job' block
            if new_status == "Approved":
                try:
                    pages = int(job.get('pages', 0))
                    copies = int(job.get('copies', 0))
                    paper_size = job.get('paper_size', 'A4')

                    if pages <= 0 or copies <= 0:
                        messagebox.showwarning("Invalid Job", "Job has 0 pages or 0 copies. Cannot approve.",
                                               parent=self)
                        return False

                    total_paper_needed = pages * copies

                    if paper_size == 'Short':
                        product_to_check = "Short Bond Paper"
                    elif paper_size == 'Long':
                        product_to_check = "Long Bond Paper"
                    else:
                        product_to_check = "A4 Bond Paper"

                    check_conn = None
                    check_cursor = None
                    try:
                        check_conn = get_db_connection()
                        if not check_conn:
                            messagebox.showerror("DB Error", "Failed to connect to check inventory.", parent=self)
                            return False

                        check_cursor = check_conn.cursor()
                        check_cursor.execute("SELECT quantity FROM products WHERE product_name = %s",
                                             (product_to_check,))
                        stock_result = check_cursor.fetchone()

                        if not stock_result:
                            messagebox.showwarning("Inventory Error",
                                                   f"'{product_to_check}' not found in inventory.\nCannot approve this job.",
                                                   parent=self)
                            return False

                        current_stock = int(stock_result[0])
                        if current_stock < total_paper_needed:
                            messagebox.showwarning("Insufficient Stock",
                                                   f"Cannot approve. Not enough stock for '{product_to_check}'.\n"
                                                   f"Required: {total_paper_needed}, Available: {current_stock}",
                                                   parent=self)
                            return False

                    except mysql.connector.Error as db_err:
                        messagebox.showerror("Inventory Check Error", f"Failed to check stock:\n{db_err}",
                                             parent=self)
                        return False
                    finally:
                        if check_cursor: check_cursor.close()
                        if check_conn and check_conn.is_connected(): check_conn.close()

                except (ValueError, TypeError) as e:
                    messagebox.showerror("Job Data Error", f"Could not validate job data for inventory check: {e}",
                                         parent=self)
                    return False

            current_status = job.get('status')

            if new_status == "Completed" and not deduct_inventory:
                messagebox.showerror("Logic Error",
                                     "Do not call change_status('Completed') directly. Use start_print() instead.",
                                     parent=self)
                return False

            if current_status in ["Paid", "Cash", "Completed"]:
                if new_status != "Completed":
                    messagebox.showwarning("Action Not Allowed",
                                           f"Cannot {new_status.lower()} a job that is already '{current_status}'.",
                                           parent=self)
                    return False

            if new_status == "Approved":
                if current_status not in ["Pending", "Declined"]:
                    messagebox.showwarning("Action Not Allowed",
                                           f"This is already approved.\nThis request is '{current_status}'.",
                                           parent=self)
                    return False
                if current_status == "Approved":
                    messagebox.showinfo("Already Approved", "This request is already 'Approved'.", parent=self)
                    return False

            if new_status == "Declined":
                if current_status == "Declined":
                    messagebox.showinfo("Already Declined", "This request is already  'Declined'.", parent=self)
                    return False

            note_content = self.notes_text.get("1.0", "end-1c").strip()
            conn = None
            cursor = None
            success = False

            try:
                conn = get_db_connection()
                if not conn:
                    messagebox.showerror("DB Error", "Connection failed.", parent=self)
                    return False

                conn.start_transaction()
                cursor = conn.cursor()

                if deduct_inventory:
                    try:
                        pages = int(job.get('pages', 0))
                        copies = int(job.get('copies', 0))
                        paper_size = job.get('paper_size', 'A4')

                        if pages <= 0 or copies <= 0:
                            raise ValueError("Invalid pages or copies count for inventory deduction.")

                        total_paper_needed = pages * copies

                        if paper_size == 'Short':
                            product_to_deduct = "Short Bond Paper"
                        elif paper_size == 'Long':
                            product_to_deduct = "Long Bond Paper"
                        else:
                            product_to_deduct = "A4 Bond Paper"

                        cursor.execute("SELECT quantity FROM products WHERE product_name = %s FOR UPDATE",
                                       (product_to_deduct,))
                        stock_result = cursor.fetchone()

                        if not stock_result:
                            raise ValueError(f"'{product_to_deduct}' not found in inventory. Cannot complete job.")

                        current_stock = int(stock_result[0])
                        if current_stock < total_paper_needed:
                            raise ValueError(
                                f"Insufficient stock for '{product_to_deduct}'.\nRequired: {total_paper_needed}, Available: {current_stock}")

                        cursor.execute(
                            "UPDATE products SET quantity = quantity - %s WHERE product_name = %s",
                            (total_paper_needed, product_to_deduct)
                        )
                        print(
                            f"Deducted {total_paper_needed} sheets of {product_to_deduct}. New stock: {current_stock - total_paper_needed}")

                    except (ValueError, TypeError, InvalidOperation) as e:
                        conn.rollback()
                        messagebox.showerror("Inventory Error", f"{e}", parent=self)
                        return False
                    except mysql.connector.Error as db_err:
                        conn.rollback()
                        messagebox.showerror("Database Error", f"Failed to update inventory:\n{db_err}", parent=self)
                        return False

                if new_status == "Declined":
                    if not note_content:
                        messagebox.showwarning("Note Required", "Reason needed.", parent=self)
                        conn.rollback()
                        return False
                    cursor.execute(
                        "UPDATE print_jobs SET status = %s, notes = %s, updated_at = NOW() WHERE job_id = %s",
                        (new_status, note_content, job.get("job_id")))
                else:
                    cursor.execute(
                        "UPDATE print_jobs SET status = %s, notes = NULL, updated_at = NOW() WHERE job_id = %s",
                        (new_status, job.get("job_id")))
                    note_content = None

                conn.commit()
                success = True

                job["status"] = new_status
                job["notes"] = note_content
                job["updated_at"] = datetime.now()

                self.update_job_details(job)
                self.on_filter_click()

                if new_status == "Completed":
                    messagebox.showinfo("Success", "Printing successful. Inventory updated.", parent=self)
                else:
                    messagebox.showinfo("Success", f"Request marked as {new_status}.", parent=self)

            except mysql.connector.Error as err:
                messagebox.showerror("Database Error", f"Error updating status:\n{err}", parent=self)
                if conn: conn.rollback()
            except Exception as e:
                messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
                if conn: conn.rollback()
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
            return success

        def start_print():
            job = self.selected_job_ref[0]
            if not job:
                messagebox.showwarning("No Selection", "Select job.", parent=self)
                return

            current_status = job.get('status')
            if current_status not in ['Approved', 'Paid', 'Cash']:
                messagebox.showwarning("Cannot Start",
                                       f"Job must be 'Approved' or 'Paid' to start printing.\nStatus is '{current_status}'.",
                                       parent=self)
                return

            messagebox.showinfo("Printing", "The file is now printing.", parent=self)
            if change_status("Completed", deduct_inventory=True):


                user_id_to_notify = job.get('user_id')
                job_id_to_notify = job.get('job_id')
                file_name_to_notify = job.get('file_name', f"File {job.get('file_id', 'N/A')}")

                if user_id_to_notify and job_id_to_notify:
                    conn_notify = None
                    cursor_notify = None
                    try:
                        conn_notify = get_db_connection()
                        if conn_notify:
                            cursor_notify = conn_notify.cursor()
                            subject = "Print Job Completed"
                            message = f"Your file ('{file_name_to_notify}') is now printed and is ready for pickup."
                            insert_query = "INSERT INTO notifications (user_id, subject, message, created_at, status) VALUES (%s, %s, %s, NOW(), 'Unread')"
                            cursor_notify.execute(insert_query, (user_id_to_notify, subject, message))
                            conn_notify.commit()
                            print(f"Notification sent for job {job_id_to_notify}.")
                        else:
                            print(f"Could not connect to send notification for job {job_id_to_notify}.")
                    except mysql.connector.Error as err:
                        print(f"DB Error sending notification: {err}")
                        if conn_notify: conn_notify.rollback()
                    except Exception as e:
                        print(f"Error sending notification: {e}")
                        if conn_notify: conn_notify.rollback()
                    finally:
                        if cursor_notify: cursor_notify.close()
                        if conn_notify and conn_notify.is_connected(): conn_notify.close()
                else:
                    print(f"Could not send notification for job {job_id_to_notify}: Missing ID.")

        def message_user():
            job = self.selected_job_ref[0]
            if not job:
                messagebox.showwarning("No Selection", "Select job.")
                return

            note_content = self.notes_text.get("1.0", "end-1c").strip()
            if job.get("status") != "Declined":
                messagebox.showwarning("Not Declined", "Only message Declined.")
                return
            if not note_content:
                messagebox.showwarning("Empty Note", "Type message.")
                return

            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO notifications (user_id, subject, message, created_at, status) VALUES (%s, %s, %s, NOW(), 'Unread')",
                    (job.get("user_id"), "Declined Request Notice", note_content))
                conn.commit()
                messagebox.showinfo("Message Sent", f"Sent to {job.get('username', 'N/A')}.")
            except mysql.connector.Error as err:
                messagebox.showerror("DB Error", f"Error: {err}")
                if conn: conn.rollback()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
                if conn: conn.rollback()
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()

        def download_file():
            job = self.selected_job_ref[0]
            if not job:
                messagebox.showwarning("No Selection", "Select job.")
                return

            file_id_to_download = job.get("file_id")
            if not file_id_to_download:
                messagebox.showerror("Error", "No file ID.")
                return

            conn = None
            cursor = None
            try:
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT file_name, file_path FROM files WHERE file_id = %s", (file_id_to_download,))
                file_record = cursor.fetchone()

                if not file_record:
                    messagebox.showerror("Error", "File record not found.")
                    return

                file_name = file_record.get("file_name")
                file_path = file_record.get("file_path")

                if not file_name or not file_path:
                    messagebox.showerror("Error", "Record incomplete.")
                    return
                if not os.path.exists(file_path):
                    messagebox.showerror("Error", f"File not found:\n{file_path}")
                    return

                save_path = filedialog.asksaveasfilename(initialfile=file_name, title="Save As",
                                                         defaultextension=os.path.splitext(file_name)[1],
                                                         filetypes=[("All Files", "*.*")])

                if save_path:
                    shutil.copy2(file_path, save_path)
                    messagebox.showinfo("Download Complete", f"Saved to:\n{save_path}")
            except mysql.connector.Error as err:
                messagebox.showerror("DB Error", f"Error: {err}")
            except IOError as e:
                messagebox.showerror("File Error", f"Error: {e}")
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
            finally:
                if cursor:
                    cursor.close()
                if conn and conn.is_connected():
                    conn.close()

        def create_action_button(x1, y1, x2, y2, text, command):
            rect_tag = f"btn_rect_{text.replace(' ', '_').lower()}"
            text_tag = f"btn_text_{text.replace(' ', '_').lower()}"
            full_tag = f"btn_full_{text.replace(' ', '_').lower()}"

            rect = round_rectangle(self.canvas, x1, y1, x2, y2, r=5, fill="#FFFFFF", outline="#000000", width=1,
                                   tags=(rect_tag, full_tag))
            txt = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="#000000",
                                          font=("Inter Bold", 11), tags=(text_tag, full_tag))

            self.canvas.tag_bind(full_tag, "<Enter>",
                                 lambda e: (self.canvas.itemconfig(rect, fill="#E0E0E0"), self.config(cursor="hand2")))
            self.canvas.tag_bind(full_tag, "<Leave>",
                                 lambda e: (self.canvas.itemconfig(rect, fill="#FFFFFF"), self.config(cursor="")))

            self.canvas.tag_bind(full_tag, "<Button-1>", lambda e: command())

        create_action_button(876, 335, 1039, 366, "Approve", lambda: change_status("Approved"))
        create_action_button(876, 372, 1039, 403, "Start Print", start_print)
        create_action_button(877, 409, 1040, 440, "Decline", lambda: change_status("Declined"))
        create_action_button(876, 446, 1039, 477, "Download File", download_file)
        create_action_button(877, 483, 1040, 514, "Message User", message_user)

    def on_filter_click(self, event=None):
        username = self.search_entry.get().strip()
        status = self.status_var.get().strip()
        self.filter_print_jobs(username, status)

    def on_filter_hover(self, event):
        self.canvas.itemconfig("filter_btn_rect", fill="#E8E8E8")
        self.config(cursor="hand2")

    def on_filter_leave(self, event):
        self.canvas.itemconfig("filter_btn_rect", fill="#FFFFFF")
        self.config(cursor="")

    def on_search_hover(self, event):
        self.search_entry.config(highlightbackground="#000000", highlightcolor="#000000")

    def on_search_leave(self, event):
        self.search_entry.config(highlightbackground="#CCCCCC", highlightcolor="#CCCCCC")

    def open_admin_user(self):
        self.controller.show_admin_user()

    def open_admin_dashboard(self):
        self.controller.show_admin_dashboard()

    def open_admin_report(self):
        self.controller.show_admin_report()

    def open_admin_notification(self):
        self.controller.show_admin_notification()

    def open_admin_inventory(self):
        self.controller.show_admin_inventory()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?", parent=self):
            self.controller.show_login_frame()

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

    def on_frame_configure(self, canvas):
        """Reset the scroll region to encompass the inner frame"""
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_mousewheel(self, event, canvas):
        """Scroll the canvas on mousewheel event"""
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
        """Bind mousewheel scrolling when mouse enters canvas"""
        self.bind_all("<MouseWheel>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-4>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-5>", lambda ev: self._on_mousewheel(ev, canvas))

    def _unbind_mousewheel(self, event):
        """Unbind mousewheel scrolling when mouse leaves canvas"""
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")