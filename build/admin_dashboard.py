# admin_dashboard.py
from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Button, PhotoImage, messagebox
import mysql.connector
from datetime import datetime, date # Import date
from decimal import Decimal, ROUND_HALF_UP # Import Decimal parts
from utils import get_db_connection, round_rectangle # Import round_rectangle

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4" # Ensure this path is correct

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (dashboard) not found at {asset_file}")
    return asset_file

class AdminDashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        # self.admin_name = controller.admin_name # Get admin name if needed

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=534, width=905,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- Layout / UI (Keep as is) ---
        self.canvas.create_rectangle(36.0, 20.0, 873.0, 518.0, fill="#FFFFFF", outline="#000000") # Main content area
        self.canvas.create_rectangle(48.0, 26.0, 251.0, 514.0, fill="#FFFFFF", outline="#000000") # Sidebar area
        self.canvas.create_rectangle(263, 20.0, 264.0, 518.0, fill="#000000", outline="") # Vertical divider

        # --- Logo ---
        try:
            self.logo_image = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(150.0, 92.0, image=self.logo_image)
        except tk.TclError as e:
            print(f"ERROR loading logo in admin_dashboard: {e}")
            messagebox.showerror("Asset Error", f"Failed to load logo (image_1.png).\nCheck assets/frame4 folder.\nError: {e}")

        # --- Sidebar Content (Keep as is) ---
        self.canvas.create_text(150, 130, anchor="center", text="ADMIN", fill="#000000", font=("Inter Bold", 15))
        sidebar_y_start = 170; sidebar_y_offset = 56
        self.create_rounded_menu_button(71, sidebar_y_start, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(71, sidebar_y_start + sidebar_y_offset, 151, 38, "Print Jobs", self.open_admin_print)
        self.create_rounded_menu_button(71, sidebar_y_start + 2*sidebar_y_offset, 151, 38, "Reports", self.open_admin_report)
        self.create_rounded_menu_button(71, sidebar_y_start + 3*sidebar_y_offset, 151, 38, "Notifications", self.open_admin_notification)
        self.create_rounded_menu_button(71, sidebar_y_start + 4*sidebar_y_offset, 151, 38, "Settings")
        self.create_rounded_menu_button(89, 460, 111, 38, "Logout", self.logout)

        # --- Main Content Area (Keep as is) ---
        self.canvas.create_text(276.0, 35, anchor="nw", text="DASHBOARD", fill="#000000", font=("Inter Bold", 40))

        # --- Stat Boxes (Keep definitions as is) ---
        box_y1, box_y2 = 87, 138; box_y3, box_y4 = 146, 197; box_y5, box_y6 = 205, 256
        box_x1, box_x2 = 284, 432; box_x3, box_x4 = 447, 595
        # Pending
        self.canvas.create_rectangle(box_x1, box_y1, box_x2, box_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y1 + 5, anchor="nw", text="Pending approvals", fill="#000000", font=("Inter Bold", 10))
        # In-progress
        self.canvas.create_rectangle(box_x3, box_y1, box_x4, box_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y1 + 5, anchor="nw", text="In-progress prints", fill="#000000", font=("Inter Bold", 10))
        # Completed Today
        self.canvas.create_rectangle(box_x1, box_y3, box_x2, box_y4, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y3 + 5, anchor="nw", text="Completed Today", fill="#000000", font=("Inter Bold", 10))
        # Declined Today
        self.canvas.create_rectangle(box_x3, box_y3, box_x4, box_y4, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y3 + 5, anchor="nw", text="Declined Today", fill="#000000", font=("Inter Bold", 10))
        # Revenue Today
        self.canvas.create_rectangle(box_x1, box_y5, box_x2, box_y6, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x1 + 10, box_y5 + 5, anchor="nw", text="Revenue Today (₱)", fill="#000000", font=("Inter Bold", 10))
        # Total Users
        self.canvas.create_rectangle(box_x3, box_y5, box_x4, box_y6, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(box_x3 + 10, box_y5 + 5, anchor="nw", text="Total Users", fill="#000000", font=("Inter Bold", 10))

        # --- STATUS PRINT REQUESTS Section (Keep as is) ---
        req_x1, req_y1 = 276.0, 271.0; req_x2, req_y2 = 660.0, 507.0
        self.canvas.create_rectangle(req_x1, req_y1, req_x2, req_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(req_x1 + 10, req_y1 + 8, anchor="nw", text="STATUS PRINT REQUESTS", fill="#000000", font=("Inter Bold", 18))
        header_y = req_y1 + 40; self.canvas.create_line(req_x1, header_y, req_x2, header_y, fill="#000000")
        header_text_y = header_y + 8
        self.canvas.create_text(286, header_text_y, anchor="nw", text="Req ID", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(360, header_text_y, anchor="nw", text="Username", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(484, header_text_y, anchor="nw", text="Pages", fill="#000000", font=("Inter Bold", 12))
        self.canvas.create_text(545, header_text_y, anchor="nw", text="Status", fill="#000000", font=("Inter Bold", 12))

        # --- ALERTS Section (Keep as is) ---
        alert_x1, alert_y1 = 670.0, 271.0; alert_x2, alert_y2 = 865.0, 507.0
        self.canvas.create_rectangle(alert_x1, alert_y1, alert_x2, alert_y2, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text((alert_x1+alert_x2)/2, alert_y1 + 18, anchor="center", text="ALERTS", fill="#000000", font=("Inter Bold", 18))

        # --- Top Right Filter/Date Area (Keep as is) ---
        self.canvas.create_rectangle(677.0, 40.0, 763.0, 75.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(774.0, 40.0, 860.0, 75.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(720, 57.5, anchor="center", text="Date Range", fill="#000000", font=("Inter Bold", 11))
        self.canvas.create_text(817, 57.5, anchor="center", text="Filter", fill="#000000", font=("Inter Bold", 11))

        # --- Load data on init ---
        self.load_dashboard_data()

    def load_dashboard_data(self):
        """Public method to refresh all dynamic data on the dashboard."""
        self.fetch_and_display_requests()
        self.update_stat_boxes()

    # --- **** MODIFIED: update_stat_boxes **** ---
    def update_stat_boxes(self):
        """Fetches and displays all dashboard statistics in one go."""
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database for stats.", parent=self)
                return

            cursor = conn.cursor()
            today = date.today()

            # 1. Total Users (from users table)
            cursor.execute("SELECT COUNT(*) FROM users") # Count all registered users
            total_users_result = cursor.fetchone()
            total_users = total_users_result[0] if total_users_result else 0

            # 2. Get job status counts based on your new logic
            query_jobs = """
                SELECT
                    SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending_total,
                    SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as paid_total,
                    SUM(CASE WHEN status = 'Completed' AND DATE(updated_at) = %s THEN 1 ELSE 0 END) as completed_today,
                    SUM(CASE WHEN status = 'Declined' AND DATE(updated_at) = %s THEN 1 ELSE 0 END) as declined_today
                FROM print_jobs
            """
            # Pass today's date for 'Completed' and 'Declined'
            cursor.execute(query_jobs, (today, today))
            job_stats = cursor.fetchone()

            pending_count = int(job_stats[0] or 0)
            in_progress_count = int(job_stats[1] or 0) # This now counts 'Paid'
            completed_today = int(job_stats[2] or 0)
            declined_today = int(job_stats[3] or 0)

            # 3. Get Revenue Today from the NEW payments table
            query_revenue = """
                SELECT COALESCE(SUM(payment_amount), 0)
                FROM payments
                WHERE DATE(payment_timestamp) = %s
            """
            cursor.execute(query_revenue, (today,))
            revenue_result = cursor.fetchone()
            revenue_today = Decimal(revenue_result[0] or 0).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # --- Clear old values ---
            self.canvas.delete("pending_count")
            self.canvas.delete("in_progress_count")
            self.canvas.delete("completed_today_count")
            self.canvas.delete("declined_today_count")
            self.canvas.delete("revenue_today_count")
            self.canvas.delete("users_count")

            # --- Place new values ---
            val_x1, val_y1 = 358, 122.5 # Top-left box center
            val_x2, val_y2 = 521, 122.5 # Top-right box center
            val_y3 = 176.5             # Middle row Y center
            val_y4 = 235.5             # Bottom row Y center

            # Row 1
            self.canvas.create_text(val_x1, val_y1, text=str(pending_count), fill="#000000",
                               font=("Inter Bold", 20), tags="pending_count", anchor="center")
            self.canvas.create_text(val_x2, val_y1, text=str(in_progress_count), fill="#000000",
                               font=("Inter Bold", 20), tags="in_progress_count", anchor="center") # Now shows 'Paid' count
            # Row 2
            self.canvas.create_text(val_x1, val_y3, text=str(completed_today), fill="#000000",
                               font=("Inter Bold", 20), tags="completed_today_count", anchor="center")
            self.canvas.create_text(val_x2, val_y3, text=str(declined_today), fill="#000000",
                               font=("Inter Bold", 20), tags="declined_today_count", anchor="center")
            # Row 3
            revenue_text = f"₱{revenue_today:,.2f}"
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
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()
    # --- **** END MODIFICATION **** ---

    # --- fetch_and_display_requests (Keep as is, already shows 'Paid') ---
    def fetch_and_display_requests(self):
        self.canvas.delete("request_row")
        conn = None; cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)
            sql_query = """
                SELECT pj.job_id, u.username, pj.pages, pj.status
                FROM print_jobs pj LEFT JOIN users u ON pj.user_id = u.user_id
                ORDER BY
                    CASE
                        WHEN pj.status = 'Pending' THEN 1
                        WHEN pj.status = 'Approved' THEN 2
                        WHEN pj.status = 'Paid' THEN 3
                        WHEN pj.status = 'In Progress' THEN 4
                        WHEN pj.status = 'Completed' THEN 5
                        WHEN pj.status = 'Declined' THEN 6
                        ELSE 7
                    END,
                    pj.updated_at DESC, pj.created_at DESC
                LIMIT 5
            """
            cursor.execute(sql_query)
            requests = cursor.fetchall()

            y_pos = 345; row_height = 32
            color_map = {
                "Approved": "#2E7D32", "Paid": "#388E3C", "Declined": "#D32F2F",
                "Pending": "#F9A825", "Completed": "#1976D2", "In Progress": "#7B1FA2"
            }

            for i, request in enumerate(requests):
                job_id = request.get('job_id', 'N/A')
                username = request.get('username', 'N/A')
                pages = request.get('pages', 'N/A')
                status = str(request.get('status', 'N/A'))
                status_color = color_map.get(status, "#333333")

                self.canvas.create_text(286, y_pos, text=job_id, anchor="nw", fill="#333333", font=("Inter", 11), tags="request_row")
                self.canvas.create_text(360, y_pos, text=username, anchor="nw", fill="#333333", font=("Inter", 11), tags="request_row")
                self.canvas.create_text(484, y_pos, text=pages, anchor="nw", fill="#333333", font=("Inter", 11), tags="request_row")
                self.canvas.create_text(545, y_pos, text=status, anchor="nw", fill=status_color, font=("Inter Bold", 11), tags="request_row")
                y_pos += row_height

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to fetch requests: {err}", parent=self)
        except Exception as e:
            print(f"Error in fetch_and_display_requests: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred fetching requests:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    # --- Reusable Button Creation (Keep as is) ---
    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + w/2, y + h/2, text=text, anchor="center", fill="#000000", font=("Inter Bold", 15))
        button_tag = f"button_{text.replace(' ', '_').lower()}"
        def on_click(event):
            if command: command()
        def on_hover(event): self.canvas.itemconfig(rect, fill="#E8E8E8"); self.config(cursor="hand2")
        def on_leave(event): self.canvas.itemconfig(rect, fill="#FFFFFF"); self.config(cursor="")
        self.canvas.addtag_withtag(button_tag, rect); self.canvas.addtag_withtag(button_tag, txt)
        self.canvas.tag_bind(button_tag, "<Button-1>", on_click); self.canvas.tag_bind(button_tag, "<Enter>", on_hover); self.canvas.tag_bind(button_tag, "<Leave>", on_leave)


    # --- Sidebar Navigation (Keep as is) ---
    def open_admin_user(self): self.controller.show_admin_user()
    def open_admin_print(self): self.controller.show_admin_print()
    def open_admin_report(self): self.controller.show_admin_report()
    def open_admin_notification(self): self.controller.show_admin_notification()
    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure you want to log out?", parent=self):
            self.controller.show_login_frame()