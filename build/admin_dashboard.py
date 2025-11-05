from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Button, PhotoImage, messagebox, ttk, Frame, Label
import mysql.connector
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from utils import get_db_connection, round_rectangle

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (dashboard) not found at {asset_file}")
    return asset_file


class AdminDashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=534, width=905,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        self.canvas.create_rectangle(36.0, 20.0, 873.0, 518.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(48.0, 26.0, 251.0, 514.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(263, 20.0, 264.0, 518.0, fill="#000000", outline="")

        try:
            self.logo_image = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(150.0, 92.0, image=self.logo_image)
        except tk.TclError as e:
            print(f"ERROR loading logo in admin_dashboard: {e}")
            messagebox.showerror("Asset Error",
                                 f"Failed to load logo (image_1.png).\nCheck assets/frame4 folder.\nError: {e}")

        self.canvas.create_text(150, 130, anchor="center", text="ADMIN", fill="#000000", font=("Inter Bold", 15))
        sidebar_y_start = 170
        sidebar_y_offset = 56
        self.create_rounded_menu_button(71, sidebar_y_start, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(71, sidebar_y_start + sidebar_y_offset, 151, 38, "Print Jobs",
                                        self.open_admin_print)
        self.create_rounded_menu_button(71, sidebar_y_start + 2 * sidebar_y_offset, 151, 38, "Reports",
                                        self.open_admin_report)
        self.create_rounded_menu_button(71, sidebar_y_start + 3 * sidebar_y_offset, 151, 38, "Notifications",
                                        self.open_admin_notification)
        self.create_rounded_menu_button(71, sidebar_y_start + 4 * sidebar_y_offset, 151, 38, "Inventory",
                                        self.open_admin_inventory)
        self.create_rounded_menu_button(89, 460, 111, 38, "Logout", self.logout)

        self.canvas.create_text(276.0, 35, anchor="nw", text="DASHBOARD", fill="#000000", font=("Inter Bold", 40))

        # --- Stat Boxes (Restored original layout) ---
        box_y1, box_y2 = 87, 138
        box_y3, box_y4 = 146, 197
        box_y5, box_y6 = 205, 256
        box_x1, box_x2 = 284, 432
        box_x3, box_x4 = 447, 595

        self.canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y1 + 5, anchor="nw", text="Pending approvals", fill="#000000",
                                font=("Inter Bold", 10))
        self.canvas.create_rectangle(box_x3, box_y1, box_x4, box_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y1 + 5, anchor="nw", text="In-progress prints", fill="#000000",
                                font=("Inter Bold", 10))
        self.canvas.create_rectangle(box_x1, box_y3, box_x2, box_y4, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y3 + 5, anchor="nw", text="Completed", fill="#000000",
                                font=("Inter Bold", 10))
        self.canvas.create_rectangle(box_x3, box_y3, box_x4, box_y4, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y3 + 5, anchor="nw", text="Declined", fill="#000000",
                                font=("Inter Bold", 10))
        self.canvas.create_rectangle(box_x1, box_y5, box_x2, box_y6, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y5 + 5, anchor="nw", text="Revenue (₱)", fill="#000000",
                                font=("Inter Bold", 10))
        self.canvas.create_rectangle(box_x3, box_y5, box_x4, box_y6, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y5 + 5, anchor="nw", text="Total Users", fill="#000000",
                                font=("Inter Bold", 10))

        # --- Request List Area (Restored original layout) ---
        req_x1, req_y1 = 276.0, 271.0
        req_x2, req_y2 = 660.0, 507.0
        self.canvas.create_rectangle(req_x1, req_y1, req_x2, req_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(req_x1 + 10, req_y1 + 8, anchor="nw", text="STATUS PRINT REQUESTS", fill="#000000",
                                font=("Inter Bold", 18))
        header_y = req_y1 + 40
        self.canvas.create_line(req_x1, header_y, req_x2, header_y, fill="#000000")
        header_text_y = header_y + 8
        self.canvas.create_text(286, header_text_y, anchor="nw", text="Req ID", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(360, header_text_y, anchor="nw", text="Username", fill="#000000",
                                font=("Inter Bold", 12))
        self.canvas.create_text(484, header_text_y, anchor="nw", text="Pages", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(545, header_text_y, anchor="nw", text="Status", fill="#000000", font=("Inter Bold", 12))

        # --- Scrollable Request List Setup ---
        list_y = header_y + 25
        list_h = req_y2 - list_y - 2
        list_w = req_x2 - req_x1 - 2
        scroll_container = tk.Frame(self, bg="white", bd=0)
        scroll_container.place(x=req_x1 + 1, y=list_y, width=list_w, height=list_h)
        self.request_list_canvas = Canvas(scroll_container, bg="white", bd=0, highlightthickness=0)
        req_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.request_list_canvas.yview)
        self.request_list_canvas.configure(yscrollcommand=req_scrollbar.set)
        req_scrollbar.pack(side="right", fill="y")
        self.request_list_canvas.pack(side="left", fill="both", expand=True)
        self.request_content_frame = tk.Frame(self.request_list_canvas, bg="white")
        self.request_content_frame_window = self.request_list_canvas.create_window(
            (0, 0), window=self.request_content_frame, anchor="nw"
        )
        self.request_content_frame.bind("<Configure>", lambda event: self.on_frame_configure(self.request_list_canvas))
        self.request_list_canvas.bind("<Configure>",
                                      lambda e: self.request_list_canvas.itemconfig(self.request_content_frame_window,
                                                                                    width=e.width))
        self.request_list_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.request_list_canvas))
        self.request_list_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))
        self.request_content_frame.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.request_list_canvas))
        self.request_content_frame.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        # --- MODIFIED: Alerts Area (Restored, Scrollable, and Clickable) ---
        alert_x1, alert_y1 = 670.0, 81.0
        alert_x2, alert_y2 = 865.0, 257.0

        # Create a tag for all alert components
        alert_tag = "alert_inventory_button"

        self.canvas.create_rectangle(alert_x1, alert_y1, alert_x2, alert_y2,
                                     fill="#FFFFFF", outline="#000000", tags=alert_tag)
        self.canvas.create_text((alert_x1 + alert_x2) / 2, alert_y1 + 18, anchor="center", text="ALERTS",
                                fill="#000000", font=("Inter Bold", 18), tags=alert_tag)

        alert_header_y = alert_y1 + 40
        self.canvas.create_line(alert_x1, alert_header_y, alert_x2, alert_header_y, fill="#000000", tags=alert_tag)

        # --- Scrollable Alert List Setup ---
        alert_list_y = alert_header_y + 1
        alert_list_h = alert_y2 - alert_list_y - 2
        alert_list_w = alert_x2 - alert_x1 - 2

        alert_scroll_container = tk.Frame(self, bg="white", bd=0)
        alert_scroll_container.place(x=alert_x1 + 1, y=alert_list_y, width=alert_list_w, height=alert_list_h)

        self.alert_list_canvas = Canvas(alert_scroll_container, bg="white", bd=0, highlightthickness=0)
        alert_scrollbar = ttk.Scrollbar(alert_scroll_container, orient="vertical", command=self.alert_list_canvas.yview)
        self.alert_list_canvas.configure(yscrollcommand=alert_scrollbar.set)

        alert_scrollbar.pack(side="right", fill="y")
        self.alert_list_canvas.pack(side="left", fill="both", expand=True)

        self.alert_content_frame = tk.Frame(self.alert_list_canvas, bg="white")
        self.alert_content_frame_window = self.alert_list_canvas.create_window(
            (0, 0), window=self.alert_content_frame, anchor="nw"
        )

        # Bind events for scrolling
        self.alert_content_frame.bind("<Configure>", lambda event: self.on_frame_configure(self.alert_list_canvas))
        self.alert_list_canvas.bind("<Configure>",
                                    lambda e: self.alert_list_canvas.itemconfig(self.alert_content_frame_window,
                                                                                width=e.width))
        self.alert_list_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.alert_list_canvas))
        self.alert_list_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))
        self.alert_content_frame.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.alert_list_canvas))
        self.alert_content_frame.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        # --- Bind Click and Hover for the entire alert area ---
        # Bind canvas tags
        self.canvas.tag_bind(alert_tag, "<Button-1>", lambda e: self.open_admin_inventory())
        self.canvas.tag_bind(alert_tag, "<Enter>", lambda e: self.config(cursor="hand2"))
        self.canvas.tag_bind(alert_tag, "<Leave>", lambda e: self.config(cursor=""))

        # Bind the frame/canvas widgets inside
        for widget in (alert_scroll_container, self.alert_list_canvas, self.alert_content_frame, alert_scrollbar):
            widget.bind("<Button-1>", lambda e: self.open_admin_inventory())
            widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
            widget.bind("<Leave>", lambda e: self.config(cursor=""))
        # --- END MODIFICATION ---

        # --- Date Filter Dropdown and Apply Button ---
        self.canvas.create_rectangle(677.0, 40.0, 763.0, 75.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(720, 30, anchor="center", text="Group By", fill="#000000", font=("Inter Bold", 11))

        self.date_filter_var = tk.StringVar(value="Today")
        filter_options = ["Today", "This Week", "This Month", "This Year", "All Time"]
        self.filter_dropdown = ttk.Combobox(self, textvariable=self.date_filter_var, values=filter_options,
                                            state="readonly", font=("Inter", 10), width=10)
        self.filter_dropdown.place(x=680.0, y=48.0, height=25.0, width=80.0)

        self.apply_button = Button(self, text="Apply", font=("Inter Bold", 10), command=self.apply_date_filter,
                                   relief="raised", bd=1, bg="#000000", fg="#FFFFFF",
                                   activebackground="#333333", activeforeground="white", cursor="hand2")
        self.apply_button.place(x=774.0, y=48.0, width=86.0, height=25.0)

        self.load_dashboard_data()

    def load_dashboard_data(self):
        """Public method to refresh all dynamic data on the dashboard."""
        self.date_filter_var.set("Today")
        self.apply_date_filter()

    def apply_date_filter(self):
        """Calculates date range and calls update functions for stats, requests, and alerts."""
        filter_period = self.date_filter_var.get()
        today = date.today()

        start_date = None
        end_date = None

        if filter_period == "Today":
            start_date = today
            end_date = today
        elif filter_period == "This Week":
            start_date = today - timedelta(days=(today.weekday() + 1) % 7)
            end_date = start_date + timedelta(days=6)
        elif filter_period == "This Month":
            start_date = today.replace(day=1)
            next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = next_month - timedelta(days=1)
        elif filter_period == "This Year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)

        self.update_stat_boxes(start_date, end_date)
        self.fetch_and_display_requests(start_date, end_date)
        self.fetch_and_display_alerts()

    def update_stat_boxes(self, start_date, end_date):
        """Fetches and displays all dashboard statistics, honoring the date filter."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database for stats.", parent=self)
                return

            cursor = conn.cursor()

            # --- 1. Get Non-Filtered Stats ---
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users_result = cursor.fetchone()
            total_users = total_users_result[0] if total_users_result else 0

            query_jobs_static = """
                SELECT
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_total,
                    SUM(CASE WHEN status IN ('Paid', 'Cash') THEN 1 ELSE 0 END) as paid_total
                FROM print_jobs
            """
            cursor.execute(query_jobs_static)
            job_stats_static = cursor.fetchone()
            pending_count = int(job_stats_static[0] or 0)
            in_progress_count = int(job_stats_static[1] or 0)

            # --- 2. Prepare Date-Filtered Parts ---
            jobs_where_clause = ""
            revenue_where_clause = ""
            params_jobs = []
            params_revenue = []

            if start_date and end_date:
                jobs_where_clause = " AND DATE(updated_at) BETWEEN %s AND %s"
                revenue_where_clause = " WHERE DATE(payment_timestamp) BETWEEN %s AND %s"
                params_jobs = [start_date, end_date, start_date, end_date]
                params_revenue = [start_date, end_date]

            # --- 3. Get Date-Filtered Stats ---
            query_jobs_date = f"""
                SELECT
                    SUM(CASE WHEN status = 'Completed' {jobs_where_clause} THEN 1 ELSE 0 END) as completed_filtered,
                    SUM(CASE WHEN status = 'Declined' {jobs_where_clause} THEN 1 ELSE 0 END) as declined_filtered
                FROM print_jobs
            """
            cursor.execute(query_jobs_date, tuple(params_jobs))
            job_stats_date = cursor.fetchone()
            completed_filtered = int(job_stats_date[0] or 0)
            declined_filtered = int(job_stats_date[1] or 0)

            query_revenue = f"""
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM payments
                {revenue_where_clause}
            """
            cursor.execute(query_revenue, tuple(params_revenue))
            revenue_result = cursor.fetchone()
            revenue_filtered = Decimal(revenue_result[0] or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # --- 4. Display All Stats ---
            self.canvas.delete("pending_count")
            self.canvas.delete("in_progress_count")
            self.canvas.delete("completed_today_count")
            self.canvas.delete("declined_today_count")
            self.canvas.delete("revenue_today_count")
            self.canvas.delete("users_count")

            val_x1, val_y1 = 358, 122.5  # (284+432)/2
            val_x2, val_y2 = 521, 122.5  # (447+595)/2
            val_y3 = 176.5
            val_y4 = 235.5

            self.canvas.create_text(val_x1, val_y1, text=str(pending_count), fill="#000000",
                                    font=("Inter Bold", 20), tags="pending_count", anchor="center")
            self.canvas.create_text(val_x2, val_y1, text=str(in_progress_count), fill="#000000",
                                    font=("Inter Bold", 20), tags="in_progress_count", anchor="center")
            self.canvas.create_text(val_x1, val_y3, text=str(completed_filtered), fill="#000000",
                                    font=("Inter Bold", 20), tags="completed_today_count", anchor="center")
            self.canvas.create_text(val_x2, val_y3, text=str(declined_filtered), fill="#000000",
                                    font=("Inter Bold", 20), tags="declined_today_count", anchor="center")
            revenue_text = f"₱{revenue_filtered:,.2f}"
            self.canvas.create_text(val_x1, val_y4, text=revenue_text, fill="#000000",
                                    font=("Inter Bold", 18), tags="revenue_today_count", anchor="center")
            self.canvas.create_text(val_x2, val_y4, text=str(total_users), fill="#000000",
                                    font=("Inter Bold", 20), tags="users_count", anchor="center")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch dashboard stats: {err}", parent=self)
        except Exception as e:
            print(f"Error in update_stat_boxes: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred fetching stats:\n{e}", parent=self)
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def fetch_and_display_requests(self, start_date, end_date):
        for widget in self.request_content_frame.winfo_children():
            widget.destroy()

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                return
            cursor = conn.cursor(dictionary=True)

            params = []
            where_clause = ""
            if start_date and end_date:
                where_clause = """
                    WHERE (pj.status NOT IN ('Completed', 'Declined'))
                    OR (pj.status IN ('Completed', 'Declined') AND DATE(pj.updated_at) BETWEEN %s AND %s)
                """
                params = [start_date, end_date]

            sql_query = f"""
                SELECT pj.job_id, u.username, pj.pages, pj.status, pj.payment_method
                FROM print_jobs pj LEFT JOIN users u ON pj.user_id = u.user_id
                {where_clause}
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
                    pj.updated_at DESC, pj.created_at DESC
            """
            cursor.execute(sql_query, tuple(params))
            requests = cursor.fetchall()

            # --- Columns for original layout ---
            self.request_content_frame.columnconfigure(0, minsize=74)
            self.request_content_frame.columnconfigure(1, minsize=124)
            self.request_content_frame.columnconfigure(2, minsize=61)
            self.request_content_frame.columnconfigure(3, minsize=115)

            color_map = {
                "Approved": "#2E7D32", "Paid": "#388E3C", "Declined": "#D32F2F",
                "Pending": "#F9A825", "Completed": "#1976D2", "In Progress": "#7B1FA2",
                "Cash": "#388E3C"
            }

            if not requests:
                no_req_label = Label(self.request_content_frame, text="No print requests found.",
                                     font=("Inter Italic", 11), bg="white", fg="#888888")
                no_req_label.grid(row=0, column=0, columnspan=4, pady=20, padx=10, sticky="ew")

            for i, request in enumerate(requests):
                job_id = request.get('job_id', 'N/A')
                username = request.get('username', 'N/A')
                pages = request.get('pages', 'N/A')
                status = str(request.get('status', 'N/A'))
                status_color = color_map.get(status, "#333333")
                bg_color = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"

                lbl_id = Label(self.request_content_frame, text=job_id, anchor="w", bg=bg_color, fg="#333333",
                               font=("Inter", 11))
                lbl_user = Label(self.request_content_frame, text=username, anchor="w", bg=bg_color, fg="#333333",
                                 font=("Inter", 11))
                lbl_pages = Label(self.request_content_frame, text=pages, anchor="w", bg=bg_color, fg="#333333",
                                  font=("Inter", 11))
                lbl_status = Label(self.request_content_frame, text=status, anchor="w", bg=bg_color, fg=status_color,
                                   font=("Inter Bold", 11))

                lbl_id.grid(row=i, column=0, sticky="ew", padx=(10, 0))
                lbl_user.grid(row=i, column=1, sticky="ew")
                lbl_pages.grid(row=i, column=2, sticky="ew")
                lbl_status.grid(row=i, column=3, sticky="ew")

                for widget in (lbl_id, lbl_user, lbl_pages, lbl_status):
                    widget.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.request_list_canvas))
                    widget.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch requests: {err}", parent=self)
        except Exception as e:
            print(f"Error in fetch_and_display_requests: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred fetching requests:\n{e}", parent=self)
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        self.request_content_frame.update_idletasks()
        self.on_frame_configure(self.request_list_canvas)

    # --- ADDED: New function to fetch and display alerts ---
    def fetch_and_display_alerts(self):
        """Fetches bond paper stock and printer status and displays them in the alerts box."""
        for widget in self.alert_content_frame.winfo_children():
            widget.destroy()

        self.alert_content_frame.columnconfigure(0, weight=1)
        row_index = 0

        # --- 1. Placeholder for Printer Status ---
        printer_status = "Printer Status: N/A"
        lbl_printer = Label(self.alert_content_frame, text=printer_status, font=("Inter Bold", 10),
                            bg="white", fg="#555555", anchor="w")
        lbl_printer.grid(row=row_index, column=0, sticky="ew", padx=10, pady=(5, 5))
        row_index += 1

        # --- 2. Fetch and Display Bond Paper Stock ---
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                lbl_error = Label(self.alert_content_frame, text="DB Connection Failed.",
                                  font=("Inter", 10), bg="white", fg="red", anchor="w")
                lbl_error.grid(row=row_index, column=0, sticky="ew", padx=10, pady=5)
                return

            cursor = conn.cursor(dictionary=True)
            # Fetch bond paper products
            cursor.execute(
                "SELECT product_name, quantity FROM products WHERE product_name LIKE %s ORDER BY product_name ASC",
                ('%Bond Paper%',))
            bond_paper_items = cursor.fetchall()

            if not bond_paper_items:
                lbl_no_alerts = Label(self.alert_content_frame, text="No bond paper products found.",
                                      font=("Inter", 10), bg="white", fg="#555555", anchor="w")
                lbl_no_alerts.grid(row=row_index, column=0, sticky="ew", padx=10, pady=5)

            # --- Bind click/hover for the "No alerts" label ---
            if 'lbl_no_alerts' in locals():
                lbl_no_alerts.bind("<Button-1>", lambda e: self.open_admin_inventory())
                lbl_no_alerts.bind("<Enter>", lambda e: self.config(cursor="hand2"))
                lbl_no_alerts.bind("<Leave>", lambda e: self.config(cursor=""))

            for item in bond_paper_items:
                name = item.get('product_name')
                qty = item.get('quantity')

                display_name = name[:18] + "..." if len(name) > 18 else name
                alert_text = f"{display_name}: {qty}"
                alert_color = "#000000"

                lbl_alert = Label(self.alert_content_frame, text=alert_text,
                                  font=("Inter Bold", 10), bg="white", fg=alert_color, anchor="w")
                lbl_alert.grid(row=row_index, column=0, sticky="ew", padx=10, pady=2)
                row_index += 1

            # --- MODIFIED: Bind mousewheel AND click/hover for all labels ---
            all_labels_in_alert_frame = self.alert_content_frame.winfo_children()
            for widget in all_labels_in_alert_frame:
                widget.bind("<Enter>", lambda e, w=widget: (self._bind_mousewheel(e, self.alert_list_canvas),
                                                            w.config(cursor="hand2")))
                widget.bind("<Leave>", lambda e, w=widget: (self._unbind_mousewheel(e), w.config(cursor="")))
                widget.bind("<Button-1>", lambda e: self.open_admin_inventory())
            # --- END MODIFICATION ---

        except mysql.connector.Error as err:
            lbl_db_error = Label(self.alert_content_frame, text=f"DB Error: {err.errno}",
                                 font=("Inter", 9), bg="white", fg="red", anchor="w")
            lbl_db_error.grid(row=row_index, column=0, sticky="ew", padx=10, pady=5)
        except Exception as e:
            print(f"Error fetching alerts: {e}")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        # Update the canvas scrollregion
        self.alert_content_frame.update_idletasks()
        self.on_frame_configure(self.alert_list_canvas)

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

    def open_admin_user(self):
        self.controller.show_admin_user()

    def open_admin_print(self):
        self.controller.show_admin_print()

    def open_admin_report(self):
        self.controller.show_admin_report()

    def open_admin_notification(self):
        self.controller.show_admin_notification()

    def open_admin_inventory(self):
        self.controller.show_admin_inventory()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure you want to log out?", parent=self):
            self.controller.show_login_frame()