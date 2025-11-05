from pathlib import Path
import tkinter as tk
from tkinter import Canvas, messagebox, PhotoImage, Frame, Label, ttk
from utils import get_db_connection, round_rectangle
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
import mysql.connector

try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Missing Library", "Please install tkcalendar: pip install tkcalendar")
try:
    import pandas as pd
except ImportError:
    messagebox.showerror("Missing Library", "Please install pandas: pip install pandas")
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.dates import DateFormatter
except ImportError:
    messagebox.showerror("Missing Library", "Please install matplotlib: pip install matplotlib")

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_report) not found at {asset_file}")
    return asset_file


class AdminReportFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        window_width = 905
        window_height = 575

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=window_height, width=window_width,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- UI Elements ---
        self.canvas.create_rectangle(15.0, 24.0, 886.0, 564.0, fill="#FFF6F6", outline="#000000")
        self.canvas.create_rectangle(37.0, 42.0, 866.0, 546.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(53.0, 50.0, 256.0, 539.0, fill="#FFFFFF", outline="#000000")
        try:
            self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(154.0, 88.0, image=self.image_image_1)
        except tk.TclError as e:
            print(f"ERROR loading logo: {e}")
        self.canvas.create_text(154, 149, anchor="center", text="ADMIN", fill="#000000", font=("Inter Bold", 18))
        sidebar_y_start = 171
        sidebar_y_offset = 56
        self.create_rounded_menu_button(75, sidebar_y_start, 151, 38, "Dashboard", self.open_admin_dashboard)
        self.create_rounded_menu_button(75, sidebar_y_start + sidebar_y_offset, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(75, sidebar_y_start + 2 * sidebar_y_offset, 151, 38, "Print Jobs",
                                        self.open_admin_print)
        self.create_rounded_menu_button(75, sidebar_y_start + 3 * sidebar_y_offset, 151, 38, "Notifications",
                                        self.open_admin_notification)
        self.create_rounded_menu_button(75, sidebar_y_start + 4 * sidebar_y_offset, 151, 38, "Inventory",
                                        self.open_admin_inventory)
        self.create_rounded_menu_button(89, 490, 111, 38, "Logout", self.logout)

        self.canvas.create_text(279.0, 48.0, anchor="nw", text="Reports", fill="#000000", font=("Inter Bold", 36))
        self.canvas.create_rectangle(265.0, 41.0, 266.0, 546.0, fill="#000000", outline="#000000")

        # --- MODIFIED: Taller Filter Box ---
        self.canvas.create_rectangle(281.0, 93.0, 844.0, 150.0, fill="#F0F0F0", outline="#CCCCCC")

        # --- NEW: Date Preset Dropdown ---
        self.canvas.create_text(291.0, 110.0, anchor="w", text="Date Preset:", fill="#000000", font=("Inter Bold", 12))
        self.date_preset_var = tk.StringVar(value="This Month")
        self.date_preset_combo = ttk.Combobox(
            self, textvariable=self.date_preset_var,
            values=["Today", "This Week", "This Month", "This Year", "All Time", "Custom"],
            state="readonly", width=11, font=("Inter", 11)
        )
        self.date_preset_combo.place(x=400, y=98)
        self.date_preset_combo.bind("<<ComboboxSelected>>", self.on_preset_selected)

        # --- MODIFIED: Custom Date Range (now in row 2) ---
        self.canvas.create_text(291.0, 130.0, anchor="w", text="Custom Date:", fill="#000000", font=("Inter Bold", 12))
        default_end_date = datetime.now().date()
        default_start_date = default_end_date - timedelta(days=29)
        self.start_date_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                                          date_pattern='yyyy-mm-dd', year=default_start_date.year,
                                          month=default_start_date.month, day=default_start_date.day,
                                          state="disabled")  # Disabled by default
        self.start_date_entry.place(x=400, y=125)

        self.date_dash_label = Label(self, text="-", bg="#F0F0F0", font=("Inter Bold", 12))
        self.date_dash_label.place(x=500, y=125)
        self.end_date_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2,
                                        date_pattern='yyyy-mm-dd', year=default_end_date.year,
                                        month=default_end_date.month, day=default_end_date.day,
                                        state="disabled")  # Disabled by default
        self.end_date_entry.place(x=520, y=125)

        # --- MODIFIED: Group By (moved right) ---
        self.canvas.create_text(560.0, 110.0, anchor="w", text="Group by:", fill="#000000", font=("Inter Bold", 12))
        self.group_by_var = tk.StringVar(value="Daily")
        self.group_by_combo = ttk.Combobox(self, textvariable=self.group_by_var,
                                           values=["Daily", "Weekly", "Monthly"], state="readonly", width=8,
                                           font=("Inter", 11))
        self.group_by_combo.place(x=635, y=100)

        # --- MODIFIED: Replaced old button with new styled, rounded button ---
        self.create_rounded_button_widget(
            x=770, y=112, w=60, h=28,
            text="Apply",
            command=self.update_reports
        )

        # --- MODIFIED: Stats frame moved down ---
        stat_frame = Frame(self, bg="#FFFFFF")
        stat_frame.place(x=280, y=162, width=560, height=140)  # y was 152

        self.stat_labels = {}
        box_width = 180
        box_height = 60
        pad_x = 5
        pad_y = 5
        stats_info = [("Revenue (₱)", "revenue"), ("Total Jobs", "total_jobs"), ("Pages Printed", "pages_printed"),
                      ("Avg. Payment (₱)", "avg_value")]
        for i, (text, key) in enumerate(stats_info):
            row = i // 2
            col = i % 2
            x_pos = pad_x + col * (box_width + 10 + pad_x * 2)
            y_pos = pad_y + row * (box_height + pad_y)
            box_frame = Frame(stat_frame, width=box_width, height=box_height, bd=1, relief="solid", bg="#FFFFFF")
            box_frame.place(x=x_pos, y=y_pos)
            box_frame.pack_propagate(False)
            lbl_title = Label(box_frame, text=text, font=("Inter Bold", 11), bg="#FFFFFF", anchor="nw")
            lbl_title.pack(side="top", anchor="nw", padx=5, pady=(3, 0))
            lbl_value = Label(box_frame, text="--", font=("Inter Bold", 16), bg="#FFFFFF", anchor="center")
            lbl_value.pack(side="bottom", fill="x", pady=(0, 5))
            self.stat_labels[key] = lbl_value

        # --- MODIFIED: Chart frame moved down ---
        chart_frame = Frame(self, bd=1, relief="solid", bg="#FFFFFF")
        chart_frame.place(x=274, y=313, width=316, height=234)  # y was 303
        chart_frame.pack_propagate(False)
        Label(chart_frame, text="Revenue Over Time", font=("Inter Bold", 14), bg="#FFFFFF").pack(side="top", pady=5)
        self.fig = Figure(figsize=(3.5, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.chart_canvas_widget = self.chart_canvas.get_tk_widget()
        self.chart_canvas_widget.pack(side="top", fill="both", expand=True, padx=5, pady=(0, 5))

        # --- MODIFIED: Table frame moved down ---
        table_frame = Frame(self, bd=1, relief="solid", bg="#FFFFFF")
        table_frame.place(x=597, y=313, width=254, height=234)  # y was 303
        table_frame.grid_propagate(False)
        Label(table_frame, text="Top Users by Spend", font=("Inter Bold", 14), bg="#FFFFFF").pack(side="top", pady=5,
                                                                                                  anchor="w", padx=10)
        tree_columns = ("user", "jobs", "pages", "spend")
        self.tree = ttk.Treeview(table_frame, columns=tree_columns, show="headings", height=8)
        self.tree.heading("user", text="User")
        self.tree.heading("jobs", text="Jobs")
        self.tree.heading("pages", text="Pages")
        self.tree.heading("spend", text="Spend (₱)")
        self.tree.column("user", anchor="w", width=80)
        self.tree.column("jobs", anchor="center", width=40)
        self.tree.column("pages", anchor="center", width=50)
        self.tree.column("spend", anchor="e", width=70)
        tree_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=(5, 0), pady=(0, 5))
        tree_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 5))

        self.on_preset_selected()  # Call this to set initial state
        self.update_reports()

    # --- NEW: Function to handle preset selection ---
    def on_preset_selected(self, event=None):
        preset = self.date_preset_var.get()
        if preset == "Custom":
            self.start_date_entry.config(state="normal")
            self.end_date_entry.config(state="normal")
            # We can't disable a label, but we can change its color
            self.date_dash_label.config(fg="black")
        else:
            self.start_date_entry.config(state="disabled")
            self.end_date_entry.config(state="disabled")
            self.date_dash_label.config(fg="grey")  # Grey out the dash

    # --- MODIFIED: update_reports now reads from the new preset combo ---
    def update_reports(self):
        try:
            preset = self.date_preset_var.get()
            group_by = self.group_by_var.get()

            # 1. Determine Date Range
            if preset == "Custom":
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                if start_date > end_date:
                    messagebox.showerror("Date Error", "Start date cannot be after end date.", parent=self)
                    return
            else:
                today = datetime.now().date()
                if preset == "Today":
                    start_date = today
                    end_date = today
                elif preset == "This Week":
                    start_date = today - timedelta(days=today.weekday())
                    end_date = start_date + timedelta(days=6)
                elif preset == "This Month":
                    start_date = today.replace(day=1)
                    # Find first day of next month, then subtract 1 day
                    next_month = (start_date + timedelta(days=32)).replace(day=1)
                    end_date = next_month - timedelta(days=1)
                elif preset == "This Year":
                    start_date = today.replace(month=1, day=1)
                    end_date = today.replace(month=12, day=31)
                elif preset == "All Time":
                    start_date = date(1970, 1, 1)  # A long time ago
                    end_date = date(2999, 12, 31)  # Far in the future

                # Update the disabled DateEntry widgets to show the range
                self.start_date_entry.set_date(start_date)
                self.end_date_entry.set_date(end_date)

            print(f"Updating reports from {start_date} to {end_date}, grouped {group_by}")

            # 2. Run all updates
            self.update_stat_boxes(start_date, end_date)
            self.update_revenue_chart(start_date, end_date, group_by)
            self.update_top_users_table(start_date, end_date)

        except Exception as e:
            messagebox.showerror("Update Error", f"Failed to update reports:\n{e}", parent=self)
            print(f"Error updating reports: {e}")

    def update_stat_boxes(self, start_date, end_date):
        conn = None
        cursor = None
        revenue = Decimal("0.00")
        total_jobs = 0
        pages_printed = 0
        avg_payment_value = Decimal("0.00")

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()

            query_payments = """
                SELECT COALESCE(SUM(payment_amount), 0), COUNT(DISTINCT job_id)
                FROM payments
                WHERE DATE(payment_timestamp) BETWEEN %s AND %s
            """
            cursor.execute(query_payments, (start_date, end_date))
            payment_result = cursor.fetchone()
            revenue = Decimal(payment_result[0] or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            paid_job_count = payment_result[1] or 0

            query_jobs_pages = """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(CASE WHEN status IN ('Completed', 'Paid') THEN pages ELSE 0 END), 0)
                FROM print_jobs
                WHERE DATE(created_at) BETWEEN %s AND %s
            """
            cursor.execute(query_jobs_pages, (start_date, end_date))
            job_page_result = cursor.fetchone()
            total_jobs = job_page_result[0] if job_page_result else 0
            pages_printed = job_page_result[1] if job_page_result else 0

            if paid_job_count > 0:
                avg_payment_value = (revenue / Decimal(paid_job_count)).quantize(Decimal("0.01"),
                                                                                 rounding=ROUND_HALF_UP)

        except mysql.connector.Error as err:
            print(f"DB Error updating stats: {err}")
            messagebox.showerror("Database Error", f"Failed to fetch statistics:\n{err}", parent=self)
        except Exception as e:
            print(f"Error updating stats: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        self.stat_labels["revenue"].config(text=f"₱{revenue:,.2f}")
        self.stat_labels["total_jobs"].config(text=f"{total_jobs:,}")
        self.stat_labels["pages_printed"].config(text=f"{pages_printed:,}")
        self.stat_labels["avg_value"].config(text=f"₱{avg_payment_value:,.2f}")

    # --- **** MODIFIED: Update Revenue Chart **** ---
    def update_revenue_chart(self, start_date, end_date, group_by):
        conn = None
        cursor = None
        df = pd.DataFrame()
        plot_type = 'line'
        x_label = "Date"
        rotate_labels = False  # Flag to control label rotation

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)

            query_base = "FROM payments WHERE DATE(payment_timestamp) BETWEEN %s AND %s"
            params = (start_date, end_date)

            if group_by == "Daily":
                query = f"""
                    SELECT 
                        DAYNAME(payment_timestamp) as date_group, 
                        SUM(payment_amount) as revenue_total
                    {query_base}
                    GROUP BY date_group, WEEKDAY(payment_timestamp)
                    ORDER BY WEEKDAY(payment_timestamp) ASC
                """
                plot_type = 'bar'
                x_label = "Day of the Week"
                rotate_labels = True  # Rotate "Wednesday", etc.


            elif group_by == "Weekly":
                query = f"""
                        SELECT 
                            -- This is the new, simpler logic:
                            -- It groups days 1-7 as '1', 8-14 as '2', 15-21 as '3', etc.
                            FLOOR((DAY(payment_timestamp) - 1) / 7) + 1 as week_num,
                            SUM(payment_amount) as revenue_total
                        {query_base}
                        GROUP BY week_num
                        ORDER BY week_num ASC
                    """
                plot_type = 'bar'
                x_label = "Week of the Month"
                rotate_labels = False

            elif group_by == "Monthly":
                query = f"""
                    SELECT 
                        DATE_FORMAT(payment_timestamp, '%Y-%m-01') as date_sort,
                        DATE_FORMAT(payment_timestamp, '%b %Y') as date_group, 
                        SUM(payment_amount) as revenue_total
                    {query_base}
                    GROUP BY date_sort, date_group
                    ORDER BY date_sort ASC
                """
                plot_type = 'bar'
                x_label = "Month"
                rotate_labels = True  # Rotate "November 2025", etc.

            cursor.execute(query, params)
            results = cursor.fetchall()

            if results:
                df = pd.DataFrame(results)
                df['revenue_total'] = df['revenue_total'].apply(lambda x: float(Decimal(x or 0)))

                if group_by == "Weekly":
                    df['date_group'] = 'Week ' + df['week_num'].astype(str)
                elif group_by == "Daily":
                    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    # Convert results to a dictionary for easy lookup
                    data_dict = {item['date_group']: item['revenue_total'] for item in results}
                    # Build the DataFrame in the correct order
                    df = pd.DataFrame({'date_group': days})
                    df['revenue_total'] = df['date_group'].map(data_dict).fillna(0.0)

                # --- FIX: Convert 'Monthly' date_group to string to prevent auto-formatting ---
                elif group_by == "Monthly":
                    df['date_group'] = df['date_group'].astype(str)
                # --- END FIX ---

        except mysql.connector.Error as err:
            print(f"DB Error fetching chart data: {err}")
            messagebox.showerror("Database Error", f"Failed to get chart data:\n{err}", parent=self)
        except Exception as e:
            print(f"Error processing chart data: {e}")
            messagebox.showerror("Error", f"Error processing chart data:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        # --- Plotting ---
        self.ax.clear()
        if not df.empty:
            x_data = df['date_group']
            y_data = df['revenue_total']

            if plot_type == 'bar':
                self.ax.bar(x_data, y_data)
            else:
                self.ax.plot(x_data, y_data, marker='o', linestyle='-')

            if rotate_labels:
                self.ax.tick_params(axis='x', rotation=45, labelsize=8)
            else:
                self.ax.tick_params(axis='x', labelsize=8)

            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel("Revenue (₱)")
            self.ax.grid(True, linestyle='--', alpha=0.6)

        else:
            self.ax.text(0.5, 0.5, "No revenue data for selected period", ha='center', va='center',
                         transform=self.ax.transAxes, color='grey')
            self.ax.set_yticks([])
            self.ax.set_xticks([])

        self.ax.set_title("")
        try:
            self.fig.tight_layout()
        except ValueError:
            print("Warning: tight_layout failed for chart.")
        self.chart_canvas.draw()

    # --- **** END MODIFICATION **** ---

    def update_top_users_table(self, start_date, end_date):
        conn = None
        cursor = None
        top_users_data = []

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    u.username,
                    COALESCE(job_counts.job_count, 0) AS job_count,
                    COALESCE(page_counts.total_pages, 0) AS total_pages,
                    COALESCE(SUM(p.payment_amount), 0) AS total_spend
                FROM payments p
                JOIN print_jobs pj ON p.job_id = pj.job_id
                JOIN users u ON pj.user_id = u.user_id
                LEFT JOIN (
                    SELECT user_id, COUNT(*) as job_count
                    FROM print_jobs
                    WHERE DATE(created_at) BETWEEN %s AND %s
                    GROUP BY user_id
                ) AS job_counts ON u.user_id = job_counts.user_id
                LEFT JOIN (
                    SELECT user_id, SUM(pages) as total_pages
                    FROM print_jobs
                    WHERE DATE(created_at) BETWEEN %s AND %s AND status IN ('Completed', 'Paid')
                    GROUP BY user_id
                ) AS page_counts ON u.user_id = page_counts.user_id
                WHERE DATE(p.payment_timestamp) BETWEEN %s AND %s
                GROUP BY u.user_id, u.username, job_counts.job_count, page_counts.total_pages
                ORDER BY total_spend DESC
                LIMIT 10
            """
            cursor.execute(query, (start_date, end_date, start_date, end_date, start_date, end_date))
            top_users_data = cursor.fetchall()

        except mysql.connector.Error as err:
            print(f"DB Error fetching top users: {err}")
            messagebox.showerror("Database Error", f"Failed to fetch top users:\n{err}", parent=self)
        except Exception as e:
            print(f"Error processing top users: {e}")
            messagebox.showerror("Error", f"Error processing top users:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        for item in self.tree.get_children():
            self.tree.delete(item)

        if top_users_data:
            for user_data in top_users_data:
                username = user_data.get('username', 'N/A')
                jobs = user_data.get('job_count', 0)
                pages = user_data.get('total_pages', 0)
                spend = Decimal(user_data.get('total_spend', 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.tree.insert("", tk.END, values=(username, jobs, pages, f"₱{spend:,.2f}"))
        else:
            self.tree.insert("", tk.END, values=("No users found", "", "", ""))

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center", fill="#000000",
                                      font=("Inter Bold", 15))
        button_tag = f"button_{text.replace(' ', '_').lower()}"

        def on_click(event):
            if command: command()

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

    # --- NEW: Function to create a styled, rounded button on the canvas ---
    def create_rounded_button_widget(self, x, y, w, h, text, command=None):
        """Creates a black, rounded button on the canvas."""
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10,
                               fill="#000000",  # Black background
                               outline="#000000", width=1)
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center",
                                      fill="#FFFFFF",  # White text
                                      font=("Inter Bold", 11))

        button_tag = f"canvas_btn_{text.replace(' ', '_').lower()}"

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#333333")  # Dark grey hover
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#000000")  # Black normal
            self.config(cursor="")

        self.canvas.addtag_withtag(button_tag, rect)
        self.canvas.addtag_withtag(button_tag, txt)
        self.canvas.tag_bind(button_tag, "<Button-1>", on_click)
        self.canvas.tag_bind(button_tag, "<Enter>", on_hover)
        self.canvas.tag_bind(button_tag, "<Leave>", on_leave)

    def open_admin_user(self):
        self.controller.show_admin_user()

    def open_admin_print(self):
        self.controller.show_admin_print()

    def open_admin_dashboard(self):
        self.controller.show_admin_dashboard()

    def open_admin_notification(self):
        self.controller.show_admin_notification()

    def open_admin_inventory(self):
        self.controller.show_admin_inventory()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?", parent=self):
            self.controller.show_login_frame()