# admin_report.py
from pathlib import Path
import tkinter as tk
from tkinter import Canvas, messagebox, PhotoImage, Frame, Label, ttk
from utils import get_db_connection, round_rectangle
from datetime import datetime, timedelta, date # Import date
from decimal import Decimal, ROUND_HALF_UP
import mysql.connector

# --- NEW IMPORTS ---
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror("Missing Library", "Please install tkcalendar: pip install tkcalendar")
try:
    import pandas as pd
except ImportError:
     messagebox.showerror("Missing Library", "Please install pandas: pip install pandas")
try:
    # import matplotlib # Keep commented
    # matplotlib.use('TkAgg') # Keep commented
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.dates import DateFormatter
except ImportError:
     messagebox.showerror("Missing Library", "Please install matplotlib: pip install matplotlib")
# --- END NEW IMPORTS ---


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

        # --- UI Elements (Keep layout as is) ---
        # Backgrounds, Logo, Sidebar, Main Content, Filter Bar, Stat Box Frames, Chart Frame, Table Frame...
        self.canvas.create_rectangle(15.0, 24.0, 886.0, 564.0, fill="#FFF6F6", outline="#000000"); self.canvas.create_rectangle(37.0, 42.0, 866.0, 546.0, fill="#FFFFFF", outline="#000000"); self.canvas.create_rectangle(53.0, 50.0, 256.0, 539.0, fill="#FFFFFF", outline="#000000")
        try: self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png")); self.canvas.create_image(154.0, 88.0, image=self.image_image_1)
        except tk.TclError as e: print(f"ERROR loading logo: {e}")
        self.canvas.create_text(154, 149, anchor="center", text="ADMIN", fill="#000000", font=("Inter Bold", 18)); sidebar_y_start = 171; sidebar_y_offset = 56
        self.create_rounded_menu_button(75, sidebar_y_start, 151, 38, "Dashboard", self.open_admin_dashboard); self.create_rounded_menu_button(75, sidebar_y_start + sidebar_y_offset, 151, 38, "User", self.open_admin_user); self.create_rounded_menu_button(75, sidebar_y_start + 2 * sidebar_y_offset, 151, 38, "Print Jobs", self.open_admin_print); self.create_rounded_menu_button(75, sidebar_y_start + 3 * sidebar_y_offset, 151, 38, "Notifications", self.open_admin_notification); self.create_rounded_menu_button(75, sidebar_y_start + 4 * sidebar_y_offset, 151, 38, "Settings"); self.create_rounded_menu_button(89, 490, 111, 38, "Logout", self.logout)
        self.canvas.create_text(279.0, 48.0, anchor="nw", text="Reports", fill="#000000", font=("Inter Bold", 36)); self.canvas.create_rectangle(265.0, 41.0, 266.0, 546.0, fill="#000000", outline="#000000")
        self.canvas.create_rectangle(281.0, 93.0, 844.0, 142.0, fill="#F0F0F0", outline="#CCCCCC"); self.canvas.create_text(291.0, 110.0, anchor="w", text="Date Range:", fill="#000000", font=("Inter Bold", 12))
        default_end_date = datetime.now().date(); default_start_date = default_end_date - timedelta(days=29)
        self.start_date_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', year=default_start_date.year, month=default_start_date.month, day=default_start_date.day); self.start_date_entry.place(x=380, y=108)
        Label(self, text="-", bg="#F0F0F0", font=("Inter Bold", 12)).place(x=485, y=108)
        self.end_date_entry = DateEntry(self, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd', year=default_end_date.year, month=default_end_date.month, day=default_end_date.day); self.end_date_entry.place(x=500, y=108)
        self.canvas.create_text(610.0, 110.0, anchor="w", text="Group by:", fill="#000000", font=("Inter Bold", 12)); self.group_by_var = tk.StringVar(value="Daily"); self.group_by_combo = ttk.Combobox(self, textvariable=self.group_by_var, values=["Daily", "Weekly", "Monthly"], state="readonly", width=8, font=("Inter", 11)); self.group_by_combo.place(x=685, y=108)
        apply_btn = tk.Button(self, text="Apply", font=("Inter Bold", 11), relief="raised", bd=1, command=self.update_reports); apply_btn.place(x=775, y=106, height=28, width=60)
        stat_frame = Frame(self, bg="#FFFFFF"); stat_frame.place(x=280, y=152, width=560, height=140); self.stat_labels = {}
        box_width = 180; box_height = 60; pad_x = 5; pad_y = 5
        stats_info = [("Revenue (₱)", "revenue"), ("Total Jobs", "total_jobs"), ("Pages Printed", "pages_printed"), ("Avg. Payment (₱)", "avg_value")] # Changed label
        for i, (text, key) in enumerate(stats_info): # ... create stat box frames/labels ...
            row = i // 2; col = i % 2; x_pos = pad_x + col * (box_width + 10 + pad_x*2); y_pos = pad_y + row * (box_height + pad_y)
            box_frame = Frame(stat_frame, width=box_width, height=box_height, bd=1, relief="solid", bg="#FFFFFF"); box_frame.place(x=x_pos, y=y_pos); box_frame.pack_propagate(False)
            lbl_title = Label(box_frame, text=text, font=("Inter Bold", 11), bg="#FFFFFF", anchor="nw"); lbl_title.pack(side="top", anchor="nw", padx=5, pady=(3, 0))
            lbl_value = Label(box_frame, text="--", font=("Inter Bold", 16), bg="#FFFFFF", anchor="center"); lbl_value.pack(side="bottom", fill="x", pady=(0, 5)); self.stat_labels[key] = lbl_value
        chart_frame = Frame(self, bd=1, relief="solid", bg="#FFFFFF"); chart_frame.place(x=274, y=303, width=316, height=234); chart_frame.pack_propagate(False)
        Label(chart_frame, text="Revenue Over Time", font=("Inter Bold", 14), bg="#FFFFFF").pack(side="top", pady=5)
        self.fig = Figure(figsize=(3.5, 2), dpi=100); self.ax = self.fig.add_subplot(111); self.chart_canvas = FigureCanvasTkAgg(self.fig, master=chart_frame); self.chart_canvas_widget = self.chart_canvas.get_tk_widget(); self.chart_canvas_widget.pack(side="top", fill="both", expand=True, padx=5, pady=(0,5))
        table_frame = Frame(self, bd=1, relief="solid", bg="#FFFFFF"); table_frame.place(x=597, y=303, width=254, height=234); table_frame.grid_propagate(False)
        Label(table_frame, text="Top Users by Spend", font=("Inter Bold", 14), bg="#FFFFFF").pack(side="top", pady=5, anchor="w", padx=10)
        tree_columns = ("user", "jobs", "pages", "spend"); self.tree = ttk.Treeview(table_frame, columns=tree_columns, show="headings", height=8)
        self.tree.heading("user", text="User"); self.tree.heading("jobs", text="Jobs"); self.tree.heading("pages", text="Pages"); self.tree.heading("spend", text="Spend (₱)")
        self.tree.column("user", anchor="w", width=80); self.tree.column("jobs", anchor="center", width=40); self.tree.column("pages", anchor="center", width=50); self.tree.column("spend", anchor="e", width=70)
        tree_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview); self.tree.configure(yscrollcommand=tree_scrollbar.set)
        table_frame.grid_rowconfigure(1, weight=1); table_frame.grid_columnconfigure(0, weight=1); self.tree.grid(row=1, column=0, sticky="nsew", padx=(5,0), pady=(0,5)); tree_scrollbar.grid(row=1, column=1, sticky="ns", pady=(0,5))

        # --- Initial Data Load ---
        self.update_reports()

    # --- Update All Reports Method (Keep as is) ---
    def update_reports(self):
        try:
            start_date = self.start_date_entry.get_date()
            end_date = self.end_date_entry.get_date()
            group_by = self.group_by_var.get()
            if start_date > end_date: messagebox.showerror("Date Error", "Start date cannot be after end date.", parent=self); return
            print(f"Updating reports from {start_date} to {end_date}, grouped {group_by}")
            self.update_stat_boxes(start_date, end_date)
            self.update_revenue_chart(start_date, end_date, group_by)
            self.update_top_users_table(start_date, end_date)
        except Exception as e: messagebox.showerror("Update Error", f"Failed to update reports:\n{e}", parent=self); print(f"Error updating reports: {e}")


    # --- **** MODIFIED: Update Stat Boxes **** ---
    def update_stat_boxes(self, start_date, end_date):
        """Fetches and updates the four main statistic boxes, using payments table for revenue."""
        conn = None
        cursor = None
        revenue = Decimal("0.00")
        total_jobs = 0
        pages_printed = 0 # Based on COMPLETED/PAID jobs
        avg_payment_value = Decimal("0.00") # Changed from avg_value

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()

            # 1. Get Revenue and Paid Job Count from payments table
            query_payments = """
                SELECT COALESCE(SUM(payment_amount), 0), COUNT(DISTINCT job_id)
                FROM payments
                WHERE DATE(payment_timestamp) BETWEEN %s AND %s
            """
            cursor.execute(query_payments, (start_date, end_date))
            payment_result = cursor.fetchone()
            revenue = Decimal(payment_result[0] or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            paid_job_count = payment_result[1] or 0

            # 2. Get Total Jobs Created and Pages Printed (for Completed/Paid jobs) in the period
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
            # Pages printed calculation remains based on print_jobs status
            pages_printed = job_page_result[1] if job_page_result else 0

            # 3. Calculate Average Payment Value (Revenue / Number of Payments)
            # Use paid_job_count from the payments query
            if paid_job_count > 0:
                avg_payment_value = (revenue / Decimal(paid_job_count)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        except mysql.connector.Error as err:
            print(f"DB Error updating stats: {err}")
            messagebox.showerror("Database Error", f"Failed to fetch statistics:\n{err}", parent=self)
        except Exception as e:
            print(f"Error updating stats: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        # Update labels
        self.stat_labels["revenue"].config(text=f"₱{revenue:,.2f}")
        self.stat_labels["total_jobs"].config(text=f"{total_jobs:,}") # Total jobs created
        self.stat_labels["pages_printed"].config(text=f"{pages_printed:,}") # Pages from completed/paid jobs
        self.stat_labels["avg_value"].config(text=f"₱{avg_payment_value:,.2f}") # Changed key name
    # --- **** END MODIFICATION **** ---


    # --- **** MODIFIED: Update Revenue Chart **** ---
    def update_revenue_chart(self, start_date, end_date, group_by):
        """Fetches revenue data from payments table and updates the matplotlib chart."""
        conn = None
        cursor = None
        df = pd.DataFrame()

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)

            # Adjust query for grouping on payments table
            if group_by == "Daily":
                group_expr = "DATE(payment_timestamp)"
                plot_date_format = "%b %d"
            elif group_by == "Weekly":
                group_expr = "STR_TO_DATE(CONCAT(YEAR(payment_timestamp), ' ', WEEK(payment_timestamp, 1), ' 1'), '%Y %u %w')"
                plot_date_format = "W%W %y"
            elif group_by == "Monthly":
                group_expr = "DATE_FORMAT(payment_timestamp, '%Y-%m-01')"
                plot_date_format = "%b %Y"
            else: # Default daily
                 group_expr = "DATE(payment_timestamp)"
                 plot_date_format = "%b %d"

            # Query the payments table
            query = f"""
                SELECT {group_expr} as date_group, SUM(payment_amount) as revenue_total
                FROM payments
                WHERE DATE(payment_timestamp) BETWEEN %s AND %s
                GROUP BY date_group
                ORDER BY date_group ASC
            """
            cursor.execute(query, (start_date, end_date))
            results = cursor.fetchall()

            if results:
                df = pd.DataFrame(results)
                df['date_group'] = pd.to_datetime(df['date_group'], errors='coerce')
                # Convert revenue_total to Decimal then float
                df['revenue_total'] = df['revenue_total'].apply(lambda x: float(Decimal(x or 0)))
                df = df.dropna(subset=['date_group'])
                df = df.set_index('date_group')

        except mysql.connector.Error as err:
            print(f"DB Error fetching chart data: {err}")
            messagebox.showerror("Database Error", f"Failed to get chart data:\n{err}", parent=self)
        except Exception as e:
            print(f"Error processing chart data: {e}")
            messagebox.showerror("Error", f"Error processing chart data:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        # Update the plot (same plotting logic)
        self.ax.clear()
        if not df.empty:
            df['revenue_total'].plot(kind='line', ax=self.ax, marker='o', linestyle='-')
            self.ax.set_ylabel("Revenue (₱)")
            self.ax.set_xlabel("Date Group") # Changed label slightly
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.xaxis.set_major_formatter(DateFormatter(plot_date_format))
            self.fig.autofmt_xdate()
        else:
            self.ax.text(0.5, 0.5, "No revenue data for selected period", ha='center', va='center', transform=self.ax.transAxes, color='grey')
            self.ax.set_yticks([]); self.ax.set_xticks([])

        self.ax.set_title("")
        try:
             self.fig.tight_layout() # Can sometimes raise errors with certain data
        except ValueError:
             print("Warning: tight_layout failed for chart.")
        self.chart_canvas.draw()
    # --- **** END MODIFICATION **** ---


    # --- **** MODIFIED: Update Top Users Table **** ---
    def update_top_users_table(self, start_date, end_date):
        """Fetches top user data based on payments and populates the ttk.Treeview table."""
        conn = None
        cursor = None
        top_users_data = []

        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)

            # Join payments -> print_jobs -> users to get user info and aggregate payment amount
            # Also get job count and page count from print_jobs for the same user in the period
            query = """
                SELECT
                    u.username,
                    COALESCE(job_counts.job_count, 0) AS job_count,
                    COALESCE(page_counts.total_pages, 0) AS total_pages,
                    COALESCE(SUM(p.payment_amount), 0) AS total_spend
                FROM payments p
                JOIN print_jobs pj ON p.job_id = pj.job_id
                JOIN users u ON pj.user_id = u.user_id
                LEFT JOIN ( -- Subquery for job counts in the period
                    SELECT user_id, COUNT(*) as job_count
                    FROM print_jobs
                    WHERE DATE(created_at) BETWEEN %s AND %s
                    GROUP BY user_id
                ) AS job_counts ON u.user_id = job_counts.user_id
                LEFT JOIN ( -- Subquery for page counts (completed/paid) in the period
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
            # Pass dates multiple times for subqueries and main query
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

        # Clear existing table data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        if top_users_data:
            for user_data in top_users_data:
                username = user_data.get('username', 'N/A')
                jobs = user_data.get('job_count', 0)
                pages = user_data.get('total_pages', 0)
                spend = Decimal(user_data.get('total_spend', 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                self.tree.insert("", tk.END, values=(username, jobs, pages, f"₱{spend:,.2f}"))
        else:
            self.tree.insert("", tk.END, values=("No users found", "", "", ""))
    # --- **** END MODIFICATION **** ---


    # --- Reusable Button Creation (Keep as is) ---
    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        # ... (same code) ...
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1); txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center", fill="#000000", font=("Inter Bold", 15)); button_tag = f"button_{text.replace(' ', '_').lower()}"
        def on_click(event):
            if command: command()
        def on_hover(event): self.canvas.itemconfig(rect, fill="#E8E8E8"); self.config(cursor="hand2")
        def on_leave(event): self.canvas.itemconfig(rect, fill="#FFFFFF"); self.config(cursor="")
        self.canvas.addtag_withtag(button_tag, rect); self.canvas.addtag_withtag(button_tag, txt); self.canvas.tag_bind(button_tag, "<Button-1>", on_click); self.canvas.tag_bind(button_tag, "<Enter>", on_hover); self.canvas.tag_bind(button_tag, "<Leave>", on_leave)

    # --- Sidebar Navigation (Keep as is) ---
    def open_admin_user(self): self.controller.show_admin_user()
    def open_admin_print(self): self.controller.show_admin_print()
    def open_admin_dashboard(self): self.controller.show_admin_dashboard()
    def open_admin_notification(self): self.controller.show_admin_notification()
    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?", parent=self):
            self.controller.show_login_frame()


# --- Optional: If you want to test this frame directly (Keep as is) ---
# if __name__ == "__main__":
#     root = tk.Tk()
#     class MockController: #... (mock methods)
#     controller_mock = MockController(); root.geometry("905x575")
#     frame = AdminReportFrame(root, controller_mock); frame.pack(fill="both", expand=True)
#     root.mainloop()