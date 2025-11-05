import sys
import subprocess
from pathlib import Path
from tkinter import (
    Canvas, Entry, Text, messagebox, filedialog,
    Checkbutton, IntVar, DISABLED, NORMAL, StringVar, OptionMenu, PhotoImage, Label
)
import tkinter as tk
import os
from datetime import datetime
import mysql.connector
from decimal import Decimal, InvalidOperation
from utils import get_db_connection, round_rectangle

# --- Setup paths ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    # Add defensive check
    if not asset_file.is_file():
        print(f"Warning: Asset file not found at {asset_file}")
    return asset_file


# --- MAIN PRINTER FRAME CLASS ---
class PrinterFrame(tk.Frame):
    # --- Price List Data ---
    PRICES = {
        ('Black & White', 'Short'): Decimal('3.00'),
        ('Black & White', 'A4'): Decimal('3.00'),
        ('Black & White', 'Long'): Decimal('3.00'),
        ('Color', 'Short'): Decimal('10.00'),
        ('Color', 'A4'): Decimal('10.00'),
        ('Color', 'Long'): Decimal('15.00'),
        ('Partially Colored', 'Short'): Decimal('7.00'),
        ('Partially Colored', 'A4'): Decimal('7.00'),
        ('Partially Colored', 'Long'): Decimal('8.00'),
    }

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.user_id = controller.user_id
        self.fullname = controller.fullname
        self.selected_file = None

        self.canvas = Canvas(self, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- Load Assets ---
        try:
            self.icon_profile = PhotoImage(file=relative_to_assets("account.png"))
            self.icon_notif = PhotoImage(file=relative_to_assets("image_14.png"))
            self.icon_prices = PhotoImage(file=relative_to_assets("image_15.png"))
            self.icon_help = PhotoImage(file=relative_to_assets("image_16.png"))
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not load menu icons for PrinterFrame:\n{e}")

        # --- UI Elements ---
        round_rectangle(self.canvas, 21, 16, 850, 520, r=0, fill="#FFFFFF", outline="#000000", width=1.5)
        round_rectangle(self.canvas, 21, 15, 850, 100, r=0, fill="#000000", outline="#000000")

        # --- ADDED: tags="welcome_text" ---
        self.canvas.create_text(80, 45, anchor="nw", text=f"Welcome! {self.fullname}", fill="#FFFFFF",
                                font=("Inter Bold", 30), tags="welcome_text")

        self.canvas.create_rectangle(239, 100, 240, 520, fill="#000000", outline="", width=3)

        # --- Left Menu Buttons ---
        BTN_X, BTN_Y_START, BTN_W, BTN_H, PADDING = 56, 129, 151, 38, 11
        self.create_rounded_menu_button(BTN_X, BTN_Y_START, BTN_W, BTN_H, "Profile", self.open_user_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + BTN_H + PADDING, BTN_W, BTN_H, "Notifications",
                                        self.open_notification_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + 2 * (BTN_H + PADDING), BTN_W, BTN_H, "Pricelist",
                                        self.open_prices_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + 3 * (BTN_H + PADDING), BTN_W, BTN_H, "Help",
                                        self.open_help_py)

        # --- Left Menu Icons ---
        icon_x = BTN_X + 20
        icon_y_offset = BTN_H / 2
        if hasattr(self, 'icon_profile'):
            lbl_profile = Label(self, image=self.icon_profile, bg="white", bd=0)
            lbl_profile.place(x=icon_x, y=BTN_Y_START + icon_y_offset, anchor="center")
            self.make_icon_clickable(lbl_profile, self.open_user_py)
        if hasattr(self, 'icon_notif'):
            lbl_notif = Label(self, image=self.icon_notif, bg="white", bd=0)
            lbl_notif.place(x=icon_x, y=BTN_Y_START + BTN_H + PADDING + icon_y_offset, anchor="center")
            self.make_icon_clickable(lbl_notif, self.open_notification_py)
        if hasattr(self, 'icon_prices'):
            lbl_prices = Label(self, image=self.icon_prices, bg="white", bd=0)
            lbl_prices.place(x=icon_x, y=BTN_Y_START + 2 * (BTN_H + PADDING) + icon_y_offset, anchor="center")
            self.make_icon_clickable(lbl_prices, self.open_prices_py)
        if hasattr(self, 'icon_help'):
            lbl_help = Label(self, image=self.icon_help, bg="white", bd=0)
            lbl_help.place(x=icon_x, y=BTN_Y_START + 3 * (BTN_H + PADDING) + icon_y_offset, anchor="center")
            self.make_icon_clickable(lbl_help, self.open_help_py)

        # --- Form UI Elements ---
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
        self.paper_size_var = StringVar(self, value="A4")
        paper_sizes = ["Short", "A4", "Long"]
        self.size_dropdown = OptionMenu(self, self.paper_size_var, *paper_sizes)
        self.size_dropdown.config(width=9, font=("Inter", 10), bg="#FFFFFF", highlightthickness=0, relief="flat",
                                  borderwidth=0, indicatoron=0)
        self.size_dropdown.place(x=252, y=312, width=97, height=24)
        self.canvas.create_text(249, 344, anchor="nw", text="Copies", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 366, 351, 394, r=10, fill="#FFFFFF", outline="#000000")
        self.copies_entry = Entry(self, bd=0, bg="#FFFFFF", relief="flat", highlightthickness=0)
        self.copies_entry.place(x=255, y=372, width=90, height=20)
        self.canvas.create_text(462, 232, anchor="nw", text="Color Option", fill="#000000", font=("Inter Bold", 13))

        # --- Color Option Checkbuttons ---
        self.color_choice = StringVar(value="")
        self.bw_check = Checkbutton(self, text="Black & White", variable=self.color_choice, onvalue="bw", offvalue="",
                                    bg="#FFFFFF", command=lambda: self.color_choice.set("bw"))
        self.color_check = Checkbutton(self, text="Color", variable=self.color_choice, onvalue="color", offvalue="",
                                       bg="#FFFFFF", command=lambda: self.color_choice.set("color"))
        self.pc_check = Checkbutton(self, text="Partially Colored", variable=self.color_choice, onvalue="pc",
                                    offvalue="",
                                    bg="#FFFFFF", command=lambda: self.color_choice.set("pc"))
        self.bw_check.place(x=436, y=257)
        self.color_check.place(x=558, y=280)
        self.pc_check.place(x=558, y=257)

        # --- Additional Notes ---
        self.canvas.create_text(395, 285, anchor="nw", text="Additional Notes", fill="#000000", font=("Inter Bold", 13))
        self.notes_var = IntVar()
        self.notes_toggle = Checkbutton(self, variable=self.notes_var, bg="#FFFFFF", command=self.toggle_notes)
        self.notes_toggle.place(x=367, y=280)
        round_rectangle(self.canvas, 372, 309, 819, 455, r=10, fill="#FFFFFF", outline="#000000", width=1)
        self.notes_text = Text(self, bd=0, relief="flat", wrap="word", highlightthickness=0)
        self.notes_text.place(x=375, y=312, width=440, height=140)
        self.notes_text.config(state=DISABLED)

        # --- Action Buttons ---
        self.submit_rect = round_rectangle(self.canvas, 249, 404, 351, 432, r=15, fill="#000000", outline="#000000")
        self.submit_text = self.canvas.create_text(273, 410, anchor="nw", text="Submit", fill="#FFFFFF",
                                                   font=("Inter Bold", 12))
        self.history_rect = round_rectangle(self.canvas, 683, 240, 812, 294, r=10, fill="#000000", outline="#000000")
        self.history_text = self.canvas.create_text(690, 258, anchor="nw", text="Request History", fill="#FFFFFF",
                                                    font=("Inter Bold", 12))

        # --- Request Status Area (SCROLLABLE) ---
        self.canvas.create_text(254, 442, anchor="nw", text="Request Status", fill="#000000", font=("Inter Bold", 13))

        # Create the main container frame for the scrollable area
        status_container = tk.Frame(self, bg="#FFFFFF")
        # Position it where the old white box was
        status_container.place(x=249, y=465, width=832 - 249, height=510 - 465)
        status_container.config(bd=1, relief="solid")  # Add a border like the old one

        # Create the canvas and scrollbar
        self.scroll_canvas = Canvas(status_container, bg="#FFFFFF", bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(status_container, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        # Create the frame inside the canvas that will hold the requests
        self.scrollable_frame = tk.Frame(self.scroll_canvas, bg="#FFFFFF")

        # Add the scrollable_frame to the canvas
        self.scroll_canvas_window = self.scroll_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Bind resizing events
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.scroll_canvas.bind("<Configure>", self.on_canvas_configure)

        # Bind mouse wheel scrolling
        self.bind_all("<MouseWheel>", self.on_mouse_wheel, add="+")
        self.bind_all("<Button-4>", self.on_mouse_wheel, add="+")  # For Linux
        self.bind_all("<Button-5>", self.on_mouse_wheel, add="+")  # For Linux

        self.bind_events()
        self.load_user_requests()

    # --- Scrolling Helper Methods ---

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Adjust the width of the inner frame to match the canvas"""
        canvas_width = event.width
        self.scroll_canvas.itemconfig(self.scroll_canvas_window, width=canvas_width)

    def on_mouse_wheel(self, event):
        """Scroll the canvas on mouse wheel"""
        # Check if the mouse is over the scrollable area
        x, y = self.winfo_pointerxy()
        widget_at_pointer = self.winfo_containing(x, y)

        is_over_scroll_area = False
        curr_widget = widget_at_pointer
        while curr_widget is not None:
            if curr_widget == self.scroll_canvas:
                is_over_scroll_area = True
                break
            try:
                curr_widget = curr_widget.master
            except Exception:
                break

        if is_over_scroll_area:
            if sys.platform == "win32":
                self.scroll_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif sys.platform == "darwin":  # macOS
                self.scroll_canvas.yview_scroll(int(-1 * event.delta), "units")
            else:  # Linux
                if event.num == 4:
                    self.scroll_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.scroll_canvas.yview_scroll(1, "units")

    # --- Data Loading and UI Update Methods ---

    def load_user_data(self):
        """Fetches the latest user data from the controller and updates the UI."""
        self.user_id = self.controller.user_id
        self.fullname = self.controller.fullname

        try:
            if self.canvas.winfo_exists():
                self.canvas.itemconfig("welcome_text", text=f"Welcome! {self.fullname}")
        except tk.TclError as e:
            print(f"Error updating welcome text: {e}")

        self.clear_form()
        # main.py will automatically call load_user_requests() after this

    def load_user_requests(self):
        """Loads recent print requests for the current user into the scrollable list."""

        # Clear the existing items in the scrollable frame
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.user_id:
            print("load_user_requests: No user_id found.")
            no_requests_label = tk.Label(self.scrollable_frame, text="Not logged in.",
                                         font=("Inter Italic", 11), bg="#FFFFFF", fg="#888888")
            no_requests_label.pack(pady=10, padx=10, anchor="w")
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                print("load_user_requests: Database connection failed.")
                return

            cursor = conn.cursor(dictionary=True)

            # --- MODIFIED SQL ---
            # Added `pj.payment_method`
            # Changed to `LIMIT 10` to get multiple requests
            sql_query = """
                SELECT pj.job_id, f.file_name, pj.status, pj.created_at, pj.total_amount,
                       pj.pages, pj.copies, pj.paper_size, pj.color_option, pj.payment_method
                FROM print_jobs pj
                JOIN files f ON pj.file_id = f.file_id
                WHERE pj.user_id = %s
                ORDER BY pj.created_at DESC
                LIMIT 10
            """
            cursor.execute(sql_query, (self.user_id,))
            requests = cursor.fetchall()

            if requests:
                for request in requests:
                    job_id = request.get('job_id')
                    filename = request.get('file_name', 'N/A')
                    created_at = request.get('created_at')
                    date_str = created_at.strftime("%b %d, %Y") if created_at else "N/A"  # Shorter date
                    status = request.get('status', 'N/A')
                    db_total_amount = request.get('total_amount')
                    pages = request.get('pages')
                    copies = request.get('copies')
                    paper_size = request.get('paper_size')
                    color_option = request.get('color_option')
                    payment_method = request.get('payment_method')  # Get new field

                    # Create a widget for this single request
                    self.create_request_widget(
                        job_id, filename, date_str, status, db_total_amount, pages, copies,
                        paper_size, color_option, payment_method
                    )
            else:
                no_requests_label = tk.Label(self.scrollable_frame, text="No recent print requests found.",
                                             font=("Inter Italic", 11), bg="#FFFFFF", fg="#888888")
                no_requests_label.pack(pady=10, padx=10, anchor="w")

        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load request status:\n{err}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred loading request status:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

        # Update the scrollregion *after* adding all widgets
        self.scrollable_frame.update_idletasks()
        self.on_frame_configure()

    # ---
    # --- ALIGNMENT CHANGE: This function is rewritten to use .pack() and fixed widths ---
    # ---
    def create_request_widget(self, job_id, filename, date, status, db_total_amount, pages, copies, paper_size,
                              color_option, payment_method):
        """Creates a single, ALIGNED request widget and packs it into the scrollable_frame."""

        # Create the main frame for this row
        row_frame = tk.Frame(self.scrollable_frame, bg="#FFFFFF")
        row_frame.pack(fill="x", expand=True, pady=3)  # Add vertical padding

        # --- Calculate all display values first ---
        display_filename = filename[:20] + "..." if len(filename) > 20 else filename

        color_map = {
            "Approved": "#2E7D32", "Paid": "#388E3C", "Declined": "#D32F2F",
            "Pending": "#F9A825", "Completed": "#1976D2", "In Progress": "#7B1FA2"
        }
        status_color = color_map.get(status, "#333333")

        display_status = status
        if status == 'Paid':
            if payment_method == 'Cash':
                display_status = "Paid (Cash)"
            elif payment_method:  # e.g., 'G-Cash' or other
                display_status = f"Paid ({payment_method})"

        amount_to_display = Decimal('0.00')
        amount_str = ""
        amount_color = "#000000"

        if status in ['Approved', 'Paid', 'Completed']:
            if db_total_amount is not None:
                try:
                    db_decimal = Decimal(db_total_amount).quantize(Decimal("0.01"))
                    if db_decimal > 0:
                        amount_to_display = db_decimal
                    elif pages is not None and copies is not None and paper_size and color_option:
                        amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)
                except (InvalidOperation, TypeError):
                    if pages is not None and copies is not None and paper_size and color_option:
                        amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)
            elif pages is not None and copies is not None and paper_size and color_option:
                amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)

            if amount_to_display > Decimal('0.00'):
                amount_str = f"₱{amount_to_display:.2f}"
            elif pages is not None and copies is not None:
                amount_str = "Error"
                amount_color = "red"

        # --- Create and Pack Widgets ---

        # Pack Button (if needed) to the RIGHT first
        if status == 'Approved' and amount_to_display > Decimal('0.00'):
            pay_button = tk.Button(row_frame, text="Pay", font=("Inter Bold", 9),
                                   command=lambda jid=job_id, amt=amount_to_display: self.open_pay_script(jid, amt),
                                   relief="raised", bd=1, bg="#000000", fg="#FFFFFF", activebackground="#333333",
                                   activeforeground="white", cursor="hand2", padx=5)
            pay_button.pack(side="right", padx=(5, 10))

        # Pack Labels to the LEFT
        # Use fixed 'width' (in text units) and anchor='w' for left-alignment

        # --- Filename ---
        # width=25 means it reserves space for 25 characters
        filename_label = tk.Label(row_frame, text=display_filename, font=("Inter", 10),
                                  bg="#FFFFFF", anchor="w", width=25, padx=1)
        filename_label.pack(side="left", padx=(1))  # Add extra padding on the far left

        # --- Date ---
        # width=12 for "Nov 05, 2025"
        date_label = tk.Label(row_frame, text=date, font=("Inter", 10), bg="#FFFFFF", anchor="w", width=12)
        date_label.pack(side="left", padx=0)

        # --- Status ---
        # width=15 for "Paid (G-Cash)"
        status_label = tk.Label(row_frame, text=display_status, font=("Inter", 10, "bold"),
                                fg=status_color, bg="#FFFFFF", anchor="w", width=15)
        status_label.pack(side="left", padx=0)

        # --- Amount ---
        # width=10 for "₱1,234.56"
        # We create the label even if amount_str is empty, so it acts as a spacer
        amount_label = tk.Label(row_frame, text=amount_str, font=("Inter", 10, "bold"),
                                fg=amount_color, bg="#FFFFFF", anchor="w", width=10)
        amount_label.pack(side="left", padx=0)

        # Add a thin separator line after each row
        separator = tk.Frame(self.scrollable_frame, height=1, bg="#EEEEEE")
        separator.pack(fill="x", expand=True, padx=5)

    # --- Internal Helper Methods ---

    def _calculate_price(self, pages, copies, paper_size, color_option):
        try:
            num_pages = int(pages)
            num_copies = int(copies)
            if num_pages <= 0 or num_copies <= 0:
                return Decimal('0.00')

            color_key = color_option
            price_key = (color_key, paper_size)
            price_per_page = self.PRICES.get(price_key)

            if price_per_page is None:
                print(f"Warning: Price not found for key {price_key}")
                # Fallback to B&W price if specific key fails
                fallback_key = ('Black & White', paper_size)
                price_per_page = self.PRICES.get(fallback_key, Decimal('0.00'))
                if price_per_page == Decimal('0.00'):
                    print(f"Error: Fallback price also not found for {fallback_key}")

            total = price_per_page * num_pages * num_copies
            return total.quantize(Decimal("0.01"))
        except (ValueError, TypeError, InvalidOperation) as e:  # Catch InvalidOperation too
            print(f"Error calculating price: {e} (Inputs: p={pages}, c={copies}, s={paper_size}, clr={color_option})")
            return Decimal('0.00')

    # --- Widget Creation Methods ---

    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        icon_space = 40
        text_start_x = x + icon_space
        txt = self.canvas.create_text(text_start_x, y + h / 2, text=text, anchor="w", fill="#000000",
                                      font=("Inter Bold", 15))

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#E8E8E8")
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#FFFFFF")
            self.config(cursor="")

        for tag in (rect, txt):
            self.canvas.tag_bind(tag, "<Button-1>", on_click)
            self.canvas.tag_bind(tag, "<Enter>", on_hover)
            self.canvas.tag_bind(tag, "<Leave>", on_leave)

    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    def bind_events(self):
        # Submit Button
        for tag in (self.submit_rect, self.submit_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.submit_request())
        # Choose File Button
        for tag in (self.choose_btn, self.choose_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.choose_file())
        # History Button
        for tag in (self.history_rect, self.history_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#333333"),
                                                            self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#000000"),
                                                            self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.open_history_py())

    # --- Navigation Functions ---

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

    # --- Form and Event Handlers ---

    def choose_file(self):
        filepath = filedialog.askopenfilename(title="Select a file",
                                              filetypes=[("PDF files", "*.pdf"), ("Word documents", "*.docx"),
                                                         ("All files", "*.*")])
        if filepath:
            self.selected_file = filepath
            filename = os.path.basename(filepath)
            # Truncate long filenames for display
            display_name = filename if len(filename) <= 30 else filename[:27] + "..."
            self.canvas.itemconfig(self.file_label, text=f"Selected: {display_name}")
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
        self.color_choice.set("")  # Clear radio button selection
        self.notes_var.set(0)  # Uncheck notes toggle
        self.notes_text.config(state=NORMAL)
        self.notes_text.delete("1.0", "end")
        self.notes_text.config(state=DISABLED)
        # Reset checkbutton visual state
        self.bw_check.deselect()
        self.color_check.deselect()
        self.pc_check.deselect()

    def submit_request(self):
        if not self.user_id:
            messagebox.showerror("Error", "No user logged in.", parent=self)
            return
        if not self.selected_file:
            messagebox.showwarning("Missing File", "Please select a file.", parent=self)
            return

        pages_str = self.pages_entry.get().strip()
        copies_str = self.copies_entry.get().strip()
        color_option = self.color_choice.get()  # Gets 'bw', 'color', or 'pc'

        # --- Input Validation ---
        if not pages_str.isdigit() or int(pages_str) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of pages (must be > 0).", parent=self)
            return
        if not copies_str.isdigit() or int(copies_str) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of copies (must be > 0).", parent=self)
            return
        if not color_option:
            messagebox.showwarning("Missing Option", "Please select a color option.", parent=self)
            return

        pages = int(pages_str)
        copies = int(copies_str)
        filename = os.path.basename(self.selected_file)
        paper_size = self.paper_size_var.get()

        # Convert shorthand 'pc'/'color' to full string for DB
        # This logic is correct and passes "Partially Colored"
        if color_option == 'color':
            color_value_db = "Color"
        elif color_option == 'pc':
            color_value_db = "Partially Colored"
        else:
            color_value_db = "Black & White"

        notes = self.notes_text.get("1.0", "end-1c").strip() if self.notes_var.get() == 1 else ""

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if conn is None:
                return  # Error handled in get_db_connection

            cursor = conn.cursor()

            # --- File Handling ---
            file_name = os.path.basename(self.selected_file)
            allowed_extensions = {".pdf", ".docx"}
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in allowed_extensions:
                messagebox.showerror("Invalid File Type",
                                     f"Only PDF and DOCX files are allowed.\nYou selected: {file_ext}", parent=self)
                return

            file_type_for_db = file_ext.replace(".", "")
            upload_dir = Path("./uploads")
            upload_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            safe_filename_base = "".join(
                c for c in os.path.splitext(file_name)[0] if c.isalnum() or c in (' ', '_', '-')).rstrip()
            unique_filename = f"{timestamp}_{self.user_id}_{safe_filename_base}{file_ext}"
            destination_path = (upload_dir / unique_filename).resolve()

            try:
                import shutil
                shutil.copy2(self.selected_file, destination_path)
            except Exception as e:
                messagebox.showerror("File Error",
                                     f"Could not save the selected file.\nError: {e}", parent=self)
                return

            # --- Database Insertion ---
            # Insert into files table first
            insert_file_query = """
                INSERT INTO files (user_id, file_name, file_path, file_type, upload_date)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_file_query, (self.user_id, file_name, str(destination_path), file_type_for_db))
            file_id = cursor.lastrowid

            # Insert into print_jobs table
            insert_job_query = """
                INSERT INTO print_jobs
                (user_id, file_id, pages, paper_size, color_option, copies, notes, status, created_at, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            # Calculate price before inserting
            calculated_amount = self._calculate_price(pages, copies, paper_size, color_value_db)

            job_data = (self.user_id, file_id, pages, paper_size, color_value_db, copies, notes, "Pending",
                        calculated_amount)
            cursor.execute(insert_job_query, job_data)

            conn.commit()

            messagebox.showinfo("Success", f"Print request for '{filename}' submitted successfully!", parent=self)
            self.load_user_requests()  # Refresh the status display
            self.clear_form()  # Clear the form fields

        except mysql.connector.Error as err:
            if conn: conn.rollback()
            messagebox.showerror("Database Error", f"An error occurred while submitting the request:\n{err}",
                                 parent=self)
        except Exception as e:
            if conn: conn.rollback()
            messagebox.showerror("Error", f"An unexpected error occurred:\Hn{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    # --- External Process ---

    def open_pay_script(self, job_id, amount):
        print(f"Opening payment window for Job ID: {job_id}, Amount: {amount}")
        # Withdraw the main window
        if self.controller and self.controller.winfo_exists():
            self.controller.withdraw()
        try:
            python_exe = sys.executable  # Use the current Python interpreter
            pay_script = Path(__file__).parent / "pay.py"

            process = subprocess.Popen([python_exe, str(pay_script), str(job_id), f"{amount:.2f}"])
            process.wait()  # Wait for the pay.py window to close

        except FileNotFoundError:
            messagebox.showerror("Error", f"pay.py script not found at:\n{pay_script}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open payment window:\n{e}", parent=self)
        finally:
            # Bring the main window back
            if self.controller and self.controller.winfo_exists():
                self.controller.deiconify()
                self.controller.lift()
                self.controller.focus_force()
            self.load_user_requests()  # Refresh the status