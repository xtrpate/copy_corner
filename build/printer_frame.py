import sys
import subprocess
from pathlib import Path
from tkinter import (
    Tk, Canvas, Entry, Text, messagebox, filedialog,
    Checkbutton, IntVar, DISABLED, NORMAL, StringVar, OptionMenu, PhotoImage, Label, Button
)
import tkinter as tk  # Import this
import os
from datetime import datetime
import mysql.connector
from utils import get_db_connection, round_rectangle

# --- Setup paths ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"  # Assuming this is the correct path


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)


# --- MAIN PRINTER FRAME CLASS ---
class PrinterFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Get user data FROM THE CONTROLLER ---
        self.user_id = controller.user_id
        self.fullname = controller.fullname
        # --- END OF CHANGE ---

        self.selected_file = None
        self.request_y = 470  # For request status

        self.canvas = Canvas(self, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- UI Elements ---
        round_rectangle(self.canvas, 21, 16, 850, 520, r=0, fill="#FFFFFF", outline="#000000", width=1.5)
        round_rectangle(self.canvas, 21, 15, 850, 100, r=0, fill="#000000", outline="#000000")

        # --- Use self.fullname ---
        self.canvas.create_text(80, 45, anchor="nw", text=f"Welcome! {self.fullname}", fill="#FFFFFF",
                                font=("Inter Bold", 30))
        # --- END OF CHANGE ---

        self.canvas.create_rectangle(239, 100, 240, 520, fill="#000000", outline="", width=3)

        self.create_rounded_menu_button(56, 129, 151, 38, "Profile", self.open_user_py)
        self.create_rounded_menu_button(56, 178, 151, 38, "Notifications", self.open_notification_py)
        self.create_rounded_menu_button(56, 227, 151, 38, "Pricelist", self.open_prices_py)
        self.create_rounded_menu_button(56, 276, 151, 38, "Help", self.open_help_py)

        round_rectangle(self.canvas, 249, 112, 832, 222, r=15, fill="#FFFFFF", outline="#000000", width=1)
        self.canvas.create_text(432, 143, anchor="nw", text="Drag and drop file here or", fill="#000000",
                                font=("Inter Bold", 15))
        self.choose_btn = round_rectangle(self.canvas, 472, 178, 578, 213, r=10, fill="#000000", outline="#000000")
        self.choose_text = self.canvas.create_text(487, 185, anchor="nw", text="Choose File", fill="#FFFFFF",
                                                   font=("Inter Bold", 12))
        self.file_label = self.canvas.create_text(610, 185, anchor="nw", text="No file selected", fill="#000000",
                                                  font=("Inter", 11))

        self.canvas.create_text(249, 232, anchor="nw", text="Number of Pages", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 254, 351, 282, r=10, fill="#FFFFFF", outline="#000000")
        self.pages_entry = Entry(self, bd=0, bg="#FFFFFF", relief="flat", highlightthickness=0)
        self.pages_entry.place(x=255, y=260, width=90, height=20)

        self.canvas.create_text(249, 288, anchor="nw", text="Paper Size", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 310, 351, 338, r=10, fill="#FFFFFF", outline="#000000")
        self.paper_size_var = StringVar(self)
        self.paper_size_var.set("A4")
        paper_sizes = ["Short", "A4", "Long"]
        self.size_dropdown = OptionMenu(self, self.paper_size_var, *paper_sizes)
        self.size_dropdown.config(width=9, font=("Inter", 10), bg="#FFFFFF", highlightthickness=0, relief="flat",
                                  borderwidth=0,
                                  indicatoron=0)
        self.size_dropdown.place(x=252, y=312, width=97, height=24)

        self.canvas.create_text(249, 344, anchor="nw", text="Copies", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 366, 351, 394, r=10, fill="#FFFFFF", outline="#000000")
        self.copies_entry = Entry(self, bd=0, bg="#FFFFFF", relief="flat", highlightthickness=0)
        self.copies_entry.place(x=255, y=372, width=90, height=20)

        self.canvas.create_text(462, 232, anchor="nw", text="Color Option", fill="#000000", font=("Inter Bold", 13))
        self.color_choice = StringVar(value="")
        self.bw_check = Checkbutton(self, text="Black & White", variable=self.color_choice, onvalue="bw", offvalue="",
                                    bg="#FFFFFF",
                                    command=lambda: self.color_choice.set("bw"))
        self.color_check = Checkbutton(self, text="Color", variable=self.color_choice, onvalue="color", offvalue="",
                                       bg="#FFFFFF",
                                       command=lambda: self.color_choice.set("color"))
        self.bw_check.place(x=436, y=257)
        self.color_check.place(x=558, y=257)

        self.canvas.create_text(525, 285, anchor="nw", text="Additional Notes", fill="#000000", font=("Inter Bold", 13))
        self.notes_var = IntVar()
        self.notes_toggle = Checkbutton(self, variable=self.notes_var, bg="#FFFFFF", command=self.toggle_notes)
        self.notes_toggle.place(x=497, y=280)
        round_rectangle(self.canvas, 372, 309, 819, 455, r=10, fill="#FFFFFF", outline="#000000", width=1)
        self.notes_text = Text(self, bd=0, relief="flat", wrap="word", highlightthickness=0)
        self.notes_text.place(x=375, y=312, width=440, height=140)
        self.notes_text.config(state=DISABLED)

        self.submit_rect = round_rectangle(self.canvas, 249, 404, 351, 432, r=15, fill="#000000", outline="#000000")
        self.submit_text = self.canvas.create_text(273, 410, anchor="nw", text="Submit", fill="#FFFFFF",
                                                   font=("Inter Bold", 12))

        self.history_rect = round_rectangle(self.canvas, 683, 240, 812, 294, r=10, fill="#000000", outline="#000000")
        self.history_text = self.canvas.create_text(690, 258, anchor="nw", text="Request History", fill="#FFFFFF",
                                                    font=("Inter Bold", 12))

        self.bind_events()

        self.canvas.create_text(254, 442, anchor="nw", text="Request Status", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 465, 832, 510, r=10, fill="#FFFFFF", outline="#000000", width=1)

        self.load_user_requests()

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + 35, y + 10, text=text, anchor="nw", fill="#000000", font=("Inter Bold", 15))

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#E8E8E8");
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#FFFFFF");
            self.config(cursor="")

        for tag in (rect, txt):
            self.canvas.tag_bind(tag, "<Button-1>", on_click)
            self.canvas.tag_bind(tag, "<Enter>", on_hover)
            self.canvas.tag_bind(tag, "<Leave>", on_leave)

    def bind_events(self):
        for tag in (self.submit_rect, self.submit_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.submit_request())
        for tag in (self.choose_btn, self.choose_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.choose_file())
        for tag in (self.history_rect, self.history_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.open_history_py())

    # --- MODIFIED: Navigation Functions ---
    def open_user_py(self):
        self.controller.show_user_frame()

    def open_notification_py(self):
        self.controller.show_notification_frame()

    def open_prices_py(self):
        self.controller.show_prices_frame()

    def open_help_py(self):
        self.controller.show_help_frame()

    def open_history_py(self):
        self.controller.show_history_frame()
    # --- END OF MODIFICATIONS ---

    def load_user_requests(self):
        if not self.user_id: return
        conn = None
        try:
            conn = create_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)
            sql_query = """
            SELECT f.file_name, pj.status, pj.created_at 
            FROM print_jobs pj
            JOIN files f ON pj.file_id = f.file_id
            WHERE pj.user_id = %s 
            ORDER BY pj.created_at DESC LIMIT 1
            """
            cursor.execute(sql_query, (self.user_id,))
            request = cursor.fetchone()
            self.canvas.delete("request_status")
            if request:
                filename = request['file_name']
                date_str = request['created_at'].strftime("%B %d, %Y")
                status = request['status']
                self.add_request_status(filename, date_str, status)
        except mysql.connector.Error as err:
            print(f"Could not load request history: {err}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()

    def add_request_status(self, filename, date, status):
        self.canvas.delete("request_status")  # Clear old ones
        self.canvas.create_text(265, 482, anchor="nw", text=filename, fill="#000000", font=("Inter", 11),
                                tags="request_status")
        self.canvas.create_text(580, 482, anchor="nw", text=date, fill="#000000", font=("Inter", 11),
                                tags="request_status")
        self.canvas.create_text(740, 482, anchor="nw", text=status, fill="#000000", font=("Inter", 11, "bold"),
                                tags="request_status")

    def choose_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("PDF files", "*.pdf"), ("Word documents", "*.docx"), ("All files", "*.*")]
        )
        if filepath:
            self.selected_file = filepath
            filename = os.path.basename(filepath)
            self.canvas.itemconfig(self.file_label, text=f"Selected: {filename}")
        else:
            self.selected_file = None
            self.canvas.itemconfig(self.file_label, text="No file selected")

    def toggle_notes(self):
        if self.notes_var.get() == 1:
            self.notes_text.config(state=NORMAL)
        else:
            self.notes_text.delete("1.0", "end")
            self.notes_text.config(state=DISABLED)

    def clear_form(self):
        self.selected_file = None
        self.canvas.itemconfig(self.file_label, text="No file selected")
        self.pages_entry.delete(0, "end")
        self.copies_entry.delete(0, "end")
        self.paper_size_var.set("A4")
        self.color_choice.set("")
        self.notes_var.set(0)
        self.notes_text.delete("1.0", "end")
        self.notes_text.config(state=DISABLED)

    def submit_request(self):
        if not self.user_id:
            messagebox.showerror("Error", "No user is logged in. Cannot submit request.")
            return
        if not self.selected_file:
            messagebox.showwarning("Missing File", "Please select a file to print.")
            return
        pages = self.pages_entry.get().strip()
        if not pages.isdigit() or int(pages) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of pages.")
            return
        copies = self.copies_entry.get().strip()
        if not copies.isdigit() or int(copies) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of copies.")
            return
        color_option = self.color_choice.get()
        if not color_option:
            messagebox.showwarning("Missing Option", "Please select a color option.")
            return

        filename = os.path.basename(self.selected_file)
        paper_size = self.paper_size_var.get()
        color_value = "Color" if color_option == 'color' else "Black & White"
        notes = self.notes_text.get("1.0", "end").strip() if self.notes_var.get() == 1 else ""

        conn = None
        try:
            conn = create_db_connection()
            if conn is None: return
            cursor = conn.cursor()
            file_name = os.path.basename(self.selected_file)
            file_ext = os.path.splitext(file_name)[1].lower().replace(".", "")
            file_path = self.selected_file
            insert_file_query = """
                    INSERT INTO files (user_id, file_name, file_path, file_type)
                    VALUES (%s, %s, %s, %s)
                    """
            cursor.execute(insert_file_query, (self.user_id, file_name, file_path, file_ext))
            file_id = cursor.lastrowid
            sql_query = """
                   INSERT INTO print_jobs 
                   (user_id, file_id, pages, paper_size, color_option, copies, notes, status) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                   """
            job_data = (self.user_id, file_id, int(pages), paper_size, color_value, int(copies), notes, "Pending")
            cursor.execute(sql_query, job_data)
            conn.commit()
            messagebox.showinfo("Success", f"Print request for '{filename}' submitted successfully!")
            date_now = datetime.now().strftime("%B %d, %Y")
            self.add_request_status(filename, date_now, "Pending")
            self.clear_form()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"An error occurred: {err}")
        finally:
            if conn and conn.is_connected():
                cursor.close()
                conn.close()