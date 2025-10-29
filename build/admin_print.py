from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, ttk
import mysql.connector
import os
import shutil
from tkinter import filedialog
from utils import get_db_connection, round_rectangle  # <--- IMPORT from utils

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4"  # Ensure this path is correct


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_print) not found at {asset_file}")
    return asset_file


class AdminPrintFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_job_ref = [None]  # Store the selected job dict

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=570, width=894, # Adjusted width slightly
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- UI Elements ---
        self.canvas.create_rectangle(33.0, 31.0, 863.0, 535.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(41.0, 39.0, 244.0, 527.0, fill="#FFFFFF", outline="#000000")
        try:
            self.image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(143.0, 79.0, image=self.image_image_1)
        except tk.TclError:
            self.canvas.create_text(143.0, 79.0, text="Logo Missing", fill="#000000")
        self.canvas.create_text(117.0, 130.0, anchor="nw", text="ADMIN", fill="#000000", font=("Inter Bold", 15 * -1))
        self.canvas.create_text(272.0, 40.0, anchor="nw", text="Print Jobs Management", fill="#000000", font=("Inter Bold", 32 * -1))
        self.canvas.create_rectangle(258.0, 32.0, 258.0, 536.0, fill="#000000", outline="")
        self.canvas.create_rectangle(660.0, 79.0, 846.0, 527.0, fill="#FFFFFF", outline="#000000") # Details panel
        self.canvas.create_rectangle(260.0, 86.0, 657.0, 138.0, fill="#FFFFFF", outline="#000000") # Search panel
        self.canvas.create_text(269.0, 86.0, anchor="nw", text="Search Username:", fill="#000000", font=("Inter Bold", 12 * -1))
        self.canvas.create_rectangle(482.0, 101.0, 579.0, 132.0, fill="#FFFFFF", outline="#000000") # Status dropdown area

        # --- **** REMOVED Action button creation from __init__ **** ---
        # The visual elements are now created in add_print_job_buttons

        self.canvas.create_text(462.0, 86.0, anchor="nw", text="Status:", fill="#000000", font=("Inter Bold", 12 * -1))
        self.canvas.create_text(677.0, 94.0, anchor="nw", text="Selected Job Details", fill="#000000", font=("Inter Bold", 15 * -1))
        self.canvas.create_rectangle(257.0, 183.0, 659.99, 185.03, fill="#000000", outline="#000000")
        # Table column headers
        headers = [
            (261.0, "Req ID"), (307.0, "Username"), (385.0, "File"), (420.0, "Pages"),
            (465.0, "Size"), (497.0, "Color"), (536.0, "Status"), (588.0, "Submitted")
        ]
        for x_pos, text in headers:
            self.canvas.create_text(x_pos, 167.0, anchor="nw", text=text, fill="#000000", font=("Inter Bold", 12 * -1))

        self.canvas.create_text(671.0, 246.0, anchor="nw", text="Admin Notes/Reason if Declined", fill="#000000", font=("Inter Bold", 11 * -1))
        self.canvas.create_rectangle(666.0, 262.0, 841.0, 318.0, fill="#FFFFFF", outline="#000000")

        # --- Widgets ---
        self.search_entry = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, highlightcolor="#000000", font=("Inter", 11))
        self.search_entry.place(x=303, y=105, width=150, height=22)

        self.status_var = tk.StringVar(value="All")
        self.status_dropdown = ttk.Combobox(self, textvariable=self.status_var, values=["All", "Pending", "Approved", "Paid", "Declined", "Completed", "In Progress"], state="readonly", font=("Inter", 11))
        self.status_dropdown.place(x=485, y=105, width=85, height=22)

        x1, y1, width, height = 590, 103, 55, 25; x2, y2 = x1 + width, y1 + height
        filter_rect = round_rectangle(self.canvas, x1, y1, x2, y2, r=5, fill="#FFFFFF", outline="#000000", width=1, tags="filter_btn_canvas")
        filter_txt = self.canvas.create_text(x1 + (width / 2), y1 + (height / 2), text="Filter", fill="#000000", font=("Inter Bold", 11), tags="filter_btn_canvas")
        self.canvas.tag_bind("filter_btn_canvas", "<Button-1>", lambda e: self.on_filter_click())
        self.canvas.tag_bind("filter_btn_canvas", "<Enter>", self.on_filter_hover)
        self.canvas.tag_bind("filter_btn_canvas", "<Leave>", self.on_filter_leave)

        # Sidebar Buttons
        self.create_rounded_menu_button(74, 170, 151, 38, "Dashboard", self.open_admin_dashboard)
        self.create_rounded_menu_button(74, 226, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(74, 283, 151, 38, "Reports", self.open_admin_report)
        self.create_rounded_menu_button(74, 340, 151, 38, "Notifications", self.open_admin_notification)
        self.create_rounded_menu_button(74, 397, 151, 38, "Settings")
        self.create_rounded_menu_button(97, 473, 111, 38, "Logout", self.logout)

        self.notes_text = Text(self, bd=0, relief="flat", wrap="word", highlightthickness=1, highlightbackground="#000000")
        self.notes_text.place(x=670, y=265, width=165, height=50)
        self.notes_text.insert("1.0", "")

        # Call the modified function to create buttons
        self.add_print_job_buttons()
        self.load_print_jobs() # Load initial data

    # --- load_print_jobs, fetch_print_jobs, display_print_jobs, enable_job_selection, filter_print_jobs ---
    # (Keep these methods as they were in the corrected version you provided)
    def load_print_jobs(self):
        """Public method to refresh the job list."""
        self.display_print_jobs()
        self.update_job_details(None) # Clear details panel
        self.notes_text.delete("1.0", tk.END) # Clear notes
        self.selected_job_ref[0] = None # Deselect job

    def fetch_print_jobs(self):
        """Fetches all print jobs with user and file info."""
        # ... (implementation from your previous correct version) ...
        conn = None; cursor = None
        try:
            conn = get_db_connection(); #... rest of try ...
            if not conn: return []
            cursor = conn.cursor(dictionary=True)
            query = """ SELECT pj.job_id, u.username, u.user_id, f.file_id, f.file_name, f.file_type,
                           pj.pages, pj.paper_size, pj.color_option, pj.copies, pj.payment_method,
                           pj.total_amount, pj.status, pj.notes, pj.created_at
                        FROM print_jobs pj LEFT JOIN users u ON pj.user_id = u.user_id
                        LEFT JOIN files f ON pj.file_id = f.file_id ORDER BY pj.created_at DESC """
            cursor.execute(query); rows = cursor.fetchall()
            return rows if rows else []
        except mysql.connector.Error as err: print(f"DB Error: {err}"); return []
        except Exception as e: print(f"Error: {e}"); return []
        finally: # ... close connection ...
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()


    def display_print_jobs(self, jobs_to_display=None):
        """Displays the provided list of jobs or fetches all jobs if None."""
        # ... (implementation from your previous correct version) ...
        self.canvas.delete("job_row"); jobs = jobs_to_display if jobs_to_display is not None else self.fetch_print_jobs()
        y_position = 194; status_map = {"Pending": "P", "Approved": "A", "Completed": "C", "Declined": "D", "In Progress": "IP", "Paid": "P"}
        for index, job in enumerate(jobs):
            job_id_val = job.get("job_id", "N/A"); username_val = job.get("username", "-"); file_id_val = job.get("file_id", "-"); pages_val = job.get("pages", "-"); size_val = job.get("paper_size", "-"); color_option_val = job.get("color_option", "-"); color_val = "B&W" if color_option_val == "Black & White" else "C" if color_option_val == "Color" else color_option_val; status_text_val = job.get("status", "-"); status_val = status_map.get(status_text_val, status_text_val); file_name_full = job.get("file_name", f"File {file_id_val}"); file_name_val = file_name_full[:17] + "..." if len(file_name_full) > 20 else file_name_full; submitted_dt = job.get("created_at"); submitted_val = submitted_dt.strftime("%m/%d %H:%M") if submitted_dt else "-"; row_tag = f"row_{index}"
            row_data = [(261, f"#{job_id_val}"), (307, username_val), (385, file_name_val), (430, pages_val), (465, size_val), (502, color_val), (536, status_val), (575, submitted_val)]
            for x_pos, text_val in row_data: self.canvas.create_text(x_pos, y_position, text=text_val, fill="#000000", font=("Inter Bold", 11), anchor="nw", tags=("job_row", row_tag))
            y_position += 25
        self.enable_job_selection(jobs)

    def enable_job_selection(self, jobs):
        """Binds events to job rows for selection and highlighting."""
        # ... (implementation from your previous correct version) ...
        selected_box = [None]; self.canvas.delete("highlight")
        def highlight_row(index, color): y = 194 + (index * 25); self.canvas.delete(selected_box[0]) if selected_box[0] else None; selected_box[0] = self.canvas.create_rectangle(255, y - 2, 655, y + 20, fill=color, outline="", tags="highlight"); self.canvas.tag_lower(selected_box[0], "job_row")
        def on_enter(event): #... logic ...
            current_item = self.canvas.find_withtag("current"); #... rest of function
            if not current_item: return
            tags = self.canvas.gettags(current_item[0])
            for t in tags:
                if t.startswith("row_"):
                    try:
                        index = int(t.split("_")[1])
                        if 0 <= index < len(jobs) and jobs[index] != self.selected_job_ref[0]: highlight_row(index, "#E0F0FF")
                        self.config(cursor="hand2"); return
                    except (IndexError, ValueError): continue
        def on_leave(event): #... logic ...
             self.config(cursor=""); #... rest of function
             if self.selected_job_ref[0] is None: self.canvas.delete("highlight")
             elif selected_box[0]:
                  try: selected_index = jobs.index(self.selected_job_ref[0]); highlight_row(selected_index, "#CCE5FF")
                  except (ValueError, IndexError): self.canvas.delete("highlight")
        def on_click(event): #... logic ...
             current_item = self.canvas.find_withtag("current"); #... rest of function
             if not current_item: return
             tags = self.canvas.gettags(current_item[0])
             for t in tags:
                 if t.startswith("row_"):
                     try:
                         index = int(t.split("_")[1])
                         if 0 <= index < len(jobs): self.selected_job_ref[0] = jobs[index]; highlight_row(index, "#CCE5FF"); self.update_job_details(jobs[index])
                         return
                     except (IndexError, ValueError): continue
        self.canvas.tag_unbind("job_row", "<Enter>"); self.canvas.tag_unbind("job_row", "<Leave>"); self.canvas.tag_unbind("job_row", "<Button-1>")
        self.canvas.tag_bind("job_row", "<Enter>", on_enter); self.canvas.tag_bind("job_row", "<Leave>", on_leave); self.canvas.tag_bind("job_row", "<Button-1>", on_click)

    def filter_print_jobs(self, username_filter, status_filter):
        """Filters jobs based on username and status, then updates display."""
        # ... (implementation from your previous correct version) ...
        conn = None; cursor = None
        try: # ... build query, execute, update display ...
            conn = get_db_connection(); #... rest of try ...
            if not conn: return
            cursor = conn.cursor(dictionary=True)
            query = """ SELECT pj.job_id, u.username, u.user_id, f.file_id, f.file_name, f.file_type, pj.pages, pj.paper_size, pj.color_option, pj.copies, pj.payment_method, pj.total_amount, pj.status, pj.notes, pj.created_at FROM print_jobs pj LEFT JOIN users u ON pj.user_id = u.user_id LEFT JOIN files f ON pj.file_id = f.file_id WHERE 1=1 """
            params = []
            if username_filter: query += " AND u.username LIKE %s"; params.append(f"%{username_filter}%")
            if status_filter and status_filter != "All": query += " AND pj.status = %s"; params.append(status_filter)
            query += " ORDER BY pj.created_at DESC"
            cursor.execute(query, tuple(params)); rows = cursor.fetchall()
            self.display_print_jobs(jobs_to_display=rows); self.update_job_details(None); self.selected_job_ref[0] = None
        except mysql.connector.Error as err: messagebox.showerror("DB Error", f"Error filtering: {err}", parent=self)
        except Exception as e: messagebox.showerror("Error", f"Error filtering: {e}", parent=self)
        finally: # ... close connection ...
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()


    def update_job_details(self, job):
        """Updates the details panel based on the selected job."""
        # ... (implementation from your previous correct version - without Payment line) ...
        self.canvas.delete("job_details"); self.notes_text.delete("1.0", tk.END)
        if not job: return
        job_id = job.get('job_id', 'N/A'); username = job.get('username', '-'); file_id = job.get('file_id', 'N/A'); file_name_full = job.get("file_name", f"File {file_id}"); file_name_display = file_name_full[:27] + "..." if len(file_name_full) > 30 else file_name_full; pages = str(job.get('pages', '-')); status = job.get('status', '-'); created_at = job.get('created_at'); submitted_text = created_at.strftime('%Y-%m-%d %H:%M') if created_at else '-'; notes = job.get('notes', '')
        details = [("Req ID:", f"#{job_id}"), ("User:", username), ("File:", file_name_display), ("Pages:", pages), ("Status:", status)]
        y = 132
        for label, value in details: self.canvas.create_text(666.0, y, anchor="nw", text=f"{label} {value}", fill="#000000", font=("Inter Bold", 12 * -1), tags="job_details"); y += 20
        self.canvas.create_text(666.0, y, anchor="nw", text=f"Submitted: {submitted_text}", fill="#000000", font=("Inter Bold", 12 * -1), tags="job_details")
        if notes: self.notes_text.insert("1.0", notes)


    # --- **** MODIFIED: add_print_job_buttons **** ---
    def add_print_job_buttons(self):
        # --- Keep the inner functions (change_status, message_user, etc.) ---
        def change_status(new_status):
            # ... (Existing logic - make sure it returns True/False) ...
            job = self.selected_job_ref[0]; # ... rest of function
            if not job: messagebox.showwarning("No Selection", "Please select a job first."); return False
            note_content = self.notes_text.get("1.0", "end-1c").strip(); conn = None; cursor = None; success = False
            try:
                conn = get_db_connection(); #... rest of try block ...
                if not conn: messagebox.showerror("DB Error", "Connection failed."); return False
                cursor = conn.cursor()
                if new_status == "Declined":
                     if not note_content: messagebox.showwarning("Note Required", "Reason needed."); return False
                     cursor.execute("UPDATE print_jobs SET status = %s, notes = %s WHERE job_id = %s", (new_status, note_content, job.get("job_id")))
                else:
                     cursor.execute("UPDATE print_jobs SET status = %s, notes = NULL WHERE job_id = %s", (new_status, job.get("job_id")))
                     note_content = None
                conn.commit(); success = True
                job["status"] = new_status; job["notes"] = note_content
                self.update_job_details(job); self.display_print_jobs() # Refresh UI first
                if new_status == "Completed": messagebox.showinfo("Success", "Printing successful", parent=self)
                else: messagebox.showinfo("Success", f"Request marked as {new_status}.", parent=self)
            except mysql.connector.Error as err: messagebox.showerror("Database Error", f"Error updating status:\n{err}", parent=self); conn.rollback()
            except Exception as e: messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self); conn.rollback()
            finally:
                if cursor: cursor.close()
                if conn and conn.is_connected(): conn.close()
            return success

        def start_print():
            # ... (Existing logic) ...
            job = self.selected_job_ref[0]; # ... rest of function
            if not job: messagebox.showwarning("No Selection", "Select job.", parent=self); return
            current_status = job.get('status')
            if current_status not in ['Approved', 'Paid']: messagebox.showwarning("Cannot Start", f"Status is '{current_status}'.", parent=self); return
            messagebox.showinfo("Printing", "The file is now printing", parent=self)
            user_id_to_notify = job.get('user_id'); job_id_to_notify = job.get('job_id'); file_name_to_notify = job.get('file_name', f"File {job.get('file_id', 'N/A')}")
            if change_status("Completed"):
                 if user_id_to_notify and job_id_to_notify: # Send notification
                      conn_notify = None; cursor_notify = None
                      try: # ... notification sending logic ...
                           conn_notify = get_db_connection();
                           if conn_notify: # Check connection
                                cursor_notify = conn_notify.cursor()
                                subject = "Print Job Completed"; message = f"Your file ('{file_name_to_notify}') is now printed and is ready for pickup."
                                insert_query = "INSERT INTO notifications (user_id, subject, message, created_at, status) VALUES (%s, %s, %s, NOW(), 'Unread')"
                                cursor_notify.execute(insert_query, (user_id_to_notify, subject, message)); conn_notify.commit()
                                print(f"Notification sent for job {job_id_to_notify}.")
                           else: print(f"Could not connect to send notification for job {job_id_to_notify}.")
                      except mysql.connector.Error as err: print(f"DB Error sending notification: {err}"); conn_notify.rollback()
                      except Exception as e: print(f"Error sending notification: {e}"); conn_notify.rollback()
                      finally:
                           if cursor_notify: cursor_notify.close()
                           if conn_notify and conn_notify.is_connected(): conn_notify.close()
                 else: print(f"Could not send notification for job {job_id_to_notify}: Missing ID.")

        def message_user():
            # ... (Existing logic) ...
             job = self.selected_job_ref[0]; # ... rest of function
             if not job: messagebox.showwarning("No Selection", "Select job."); return
             note_content = self.notes_text.get("1.0", "end-1c").strip()
             if job.get("status") != "Declined": messagebox.showwarning("Not Declined", "Only message Declined."); return
             if not note_content: messagebox.showwarning("Empty Note", "Type message."); return
             conn = None; cursor = None
             try: # ... DB insert ...
                 conn=get_db_connection(); cursor=conn.cursor()
                 cursor.execute("INSERT INTO notifications (user_id, subject, message, created_at, status) VALUES (%s, %s, %s, NOW(), 'Unread')", (job.get("user_id"), "Declined Request Notice", note_content))
                 conn.commit(); messagebox.showinfo("Message Sent", f"Sent to {job.get('username', 'N/A')}.")
             except mysql.connector.Error as err: messagebox.showerror("DB Error", f"Error: {err}"); conn.rollback()
             except Exception as e: messagebox.showerror("Error", f"Error: {e}"); conn.rollback()
             finally: # ... close connection ...
                 if cursor: cursor.close()
                 if conn and conn.is_connected(): conn.close()

        def download_file():
            # ... (Existing logic) ...
             job = self.selected_job_ref[0]; # ... rest of function
             if not job: messagebox.showwarning("No Selection", "Select job."); return
             file_id_to_download = job.get("file_id")
             if not file_id_to_download: messagebox.showerror("Error", "No file ID."); return
             conn = None; cursor = None
             try: # ... get path, ask save, copy ...
                 conn=get_db_connection(); cursor=conn.cursor(dictionary=True)
                 cursor.execute("SELECT file_name, file_path FROM files WHERE file_id = %s", (file_id_to_download,)); file_record = cursor.fetchone()
                 if not file_record: messagebox.showerror("Error", "File record not found."); return
                 file_name = file_record.get("file_name"); file_path = file_record.get("file_path")
                 if not file_name or not file_path: messagebox.showerror("Error", "Record incomplete."); return
                 if not os.path.exists(file_path): messagebox.showerror("Error", f"File not found:\n{file_path}"); return
                 save_path = filedialog.asksaveasfilename(initialfile=file_name, title="Save As", defaultextension=os.path.splitext(file_name)[1], filetypes=[("All Files", "*.*")])
                 if save_path: shutil.copy2(file_path, save_path); messagebox.showinfo("Download Complete", f"Saved to:\n{save_path}")
             except mysql.connector.Error as err: messagebox.showerror("DB Error", f"Error: {err}")
             except IOError as e: messagebox.showerror("File Error", f"Error: {e}")
             except Exception as e: messagebox.showerror("Error", f"Error: {e}")
             finally: # ... close connection ...
                 if cursor: cursor.close()
                 if conn and conn.is_connected(): conn.close()

        # --- Helper to create and bind a single action button ---
        def create_action_button(x1, y1, x2, y2, text, command):
            rect_tag = f"btn_rect_{text.replace(' ', '_').lower()}"
            text_tag = f"btn_text_{text.replace(' ', '_').lower()}"
            full_tag = f"btn_full_{text.replace(' ', '_').lower()}" # Tag for both items

            # Draw visible button
            # Use r=5 for slightly rounded corners, adjust fill/outline as needed
            rect = round_rectangle(self.canvas, x1, y1, x2, y2, r=5, fill="#FFFFFF", outline="#000000", width=1, tags=(rect_tag, full_tag))
            # Center text within the rectangle bounds
            txt = self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text=text, fill="#000000", font=("Inter Bold", 11), tags=(text_tag, full_tag)) # Adjusted font size

            # Hover/Leave effect - bind to the shared tag
            self.canvas.tag_bind(full_tag, "<Enter>", lambda e: (self.canvas.itemconfig(rect, fill="#E0E0E0"), self.config(cursor="hand2")))
            self.canvas.tag_bind(full_tag, "<Leave>", lambda e: (self.canvas.itemconfig(rect, fill="#FFFFFF"), self.config(cursor="")))

            # Click effect - bind to the shared tag
            self.canvas.tag_bind(full_tag, "<Button-1>", lambda e: command())

        # --- Create the actual buttons ---
        create_action_button(671, 335, 834, 366, "Approve", lambda: change_status("Approved"))
        create_action_button(671, 372, 834, 403, "Start Print", start_print)
        create_action_button(672, 409, 835, 440, "Decline", lambda: change_status("Declined"))
        create_action_button(671, 446, 834, 477, "Download File", download_file)
        create_action_button(672, 483, 835, 514, "Message User", message_user)
    # --- **** END MODIFICATION **** ---


    # --- Filter Button Callbacks (Keep as is) ---
    def on_filter_click(self): username = self.search_entry.get().strip(); status = self.status_var.get().strip(); self.filter_print_jobs(username, status)
    def on_filter_hover(self, event): self.canvas.itemconfig("filter_btn_canvas", fill="#E8E8E8"); self.config(cursor="hand2")
    def on_filter_leave(self, event): self.canvas.itemconfig("filter_btn_canvas", fill="#FFFFFF"); self.config(cursor="")

    # --- Sidebar Navigation (Keep as is) ---
    def open_admin_user(self): self.controller.show_admin_user()
    def open_admin_dashboard(self): self.controller.show_admin_dashboard()
    def open_admin_report(self): self.controller.show_admin_report()
    def open_admin_notification(self): self.controller.show_admin_notification()
    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?", parent=self): self.controller.show_login_frame()

    # --- Reusable Button Creation (Keep as is) ---
    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center", fill="#000000", font=("Inter Bold", 15))
        button_tag = f"button_{text.replace(' ', '_').lower()}"
        def on_click(event):
            if command: command()
        def on_hover(event): self.canvas.itemconfig(rect, fill="#E8E8E8"); self.config(cursor="hand2")
        def on_leave(event): self.canvas.itemconfig(rect, fill="#FFFFFF"); self.config(cursor="")
        self.canvas.addtag_withtag(button_tag, rect); self.canvas.addtag_withtag(button_tag, txt)
        self.canvas.tag_bind(button_tag, "<Button-1>", on_click); self.canvas.tag_bind(button_tag, "<Enter>", on_hover); self.canvas.tag_bind(button_tag, "<Leave>", on_leave)