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
from decimal import Decimal, InvalidOperation # Import InvalidOperation too
# Import the CORRECT function name
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
    # --- ADD Price List Data ---
    PRICES = {
        ('Black & White', 'Short'): Decimal('3.00'),
        ('Black & White', 'A4'): Decimal('3.00'),
        ('Black & White', 'Long'): Decimal('3.00'),
        ('Color', 'Short'): Decimal('10.00'),
        ('Color', 'A4'): Decimal('10.00'),
        ('Color', 'Long'): Decimal('15.00'),
    }

    # --- END Price List Data ---

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Get user data FROM THE CONTROLLER ---
        self.user_id = controller.user_id
        self.fullname = controller.fullname

        self.selected_file = None

        self.canvas = Canvas(self, bg="#FFFFFF", height=540, width=871, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- Load Assets ---
        try:
            # Load icons for menu buttons
            # Store image refs on self
            self.icon_profile = PhotoImage(file=relative_to_assets("account.png"))
            self.icon_notif = PhotoImage(file=relative_to_assets("image_14.png"))  # Bell icon?
            self.icon_prices = PhotoImage(file=relative_to_assets("image_15.png"))  # Sheet icon?
            self.icon_help = PhotoImage(file=relative_to_assets("image_16.png"))  # Help icon?
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not load menu icons for PrinterFrame:\n{e}")
            # Consider returning if icons are essential, or continue without them
            # return

        # --- UI Elements ---
        round_rectangle(self.canvas, 21, 16, 850, 520, r=0, fill="#FFFFFF", outline="#000000", width=1.5)
        round_rectangle(self.canvas, 21, 15, 850, 100, r=0, fill="#000000", outline="#000000")

        self.canvas.create_text(80, 45, anchor="nw", text=f"Welcome! {self.fullname}", fill="#FFFFFF",
                                font=("Inter Bold", 30))
        self.canvas.create_rectangle(239, 100, 240, 520, fill="#000000", outline="", width=3)

        # --- Left Menu Buttons ---
        BTN_X, BTN_Y_START, BTN_W, BTN_H, PADDING = 56, 129, 151, 38, 11  # Coordinates and dimensions
        self.create_rounded_menu_button(BTN_X, BTN_Y_START, BTN_W, BTN_H, "Profile", self.open_user_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + BTN_H + PADDING, BTN_W, BTN_H, "Notifications",
                                        self.open_notification_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + 2 * (BTN_H + PADDING), BTN_W, BTN_H, "Pricelist",
                                        self.open_prices_py)
        self.create_rounded_menu_button(BTN_X, BTN_Y_START + 3 * (BTN_H + PADDING), BTN_W, BTN_H, "Help",
                                        self.open_help_py)

        # --- Left Menu Icons ---
        icon_x = BTN_X + 20  # X position for icons inside buttons
        icon_y_offset = BTN_H / 2  # Vertical offset to center icon in button
        # Place icons if they loaded successfully
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

        # --- Rest of UI elements ---
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
        self.color_choice = StringVar(value="")
        self.bw_check = Checkbutton(self, text="Black & White", variable=self.color_choice, onvalue="bw", offvalue="",
                                    bg="#FFFFFF", command=lambda: self.color_choice.set("bw"))
        self.color_check = Checkbutton(self, text="Color", variable=self.color_choice, onvalue="color", offvalue="",
                                       bg="#FFFFFF", command=lambda: self.color_choice.set("color"))
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
        self.canvas.create_text(254, 442, anchor="nw", text="Request Status", fill="#000000", font=("Inter Bold", 13))
        round_rectangle(self.canvas, 249, 465, 832, 510, r=10, fill="#FFFFFF", outline="#000000", width=1)

        self.bind_events()
        self.load_user_requests()

    # --- _calculate_price Method ---
    def _calculate_price(self, pages, copies, paper_size, color_option):
        try:
            num_pages = int(pages)
            num_copies = int(copies)
            if num_pages <= 0 or num_copies <= 0:
                return Decimal('0.00')
            color_key = "Color" if color_option == "Color" else "Black & White"
            price_key = (color_key, paper_size)
            price_per_page = self.PRICES.get(price_key)
            if price_per_page is None:
                print(f"Warning: Price not found for key {price_key}")
                fallback_key = ('Black & White', paper_size)
                price_per_page = self.PRICES.get(fallback_key, Decimal('0.00'))
                if price_per_page == Decimal('0.00'):
                    print(f"Error: Fallback price also not found for {fallback_key}")
            total = price_per_page * num_pages * num_copies
            return total.quantize(Decimal("0.01")) # Use standard rounding for currency
        except (ValueError, TypeError, InvalidOperation) as e: # Catch InvalidOperation too
            print(f"Error calculating price: {e} (Inputs: p={pages}, c={copies}, s={paper_size}, clr={color_option})")
            return Decimal('0.00')

    # --- UPDATED create_rounded_menu_button ---
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

    # --- ADDED make_icon_clickable Method ---
    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    def bind_events(self):
        for tag in (self.submit_rect, self.submit_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#333333"), self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.submit_rect, fill="#000000"), self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.submit_request())
        for tag in (self.choose_btn, self.choose_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#333333"), self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.choose_btn, fill="#000000"), self.config(cursor="")))
            self.canvas.tag_bind(tag, "<Button-1>", lambda e: self.choose_file())
        for tag in (self.history_rect, self.history_text):
            self.canvas.tag_bind(tag, "<Enter>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#333333"), self.config(cursor="hand2")))
            self.canvas.tag_bind(tag, "<Leave>", lambda e: (self.canvas.itemconfig(self.history_rect, fill="#000000"), self.config(cursor="")))
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

    # --- UPDATED load_user_requests ---
    def load_user_requests(self):
        if not self.user_id:
            print("load_user_requests: No user_id found.")
            return

        # Explicitly destroy any existing pay button first
        if hasattr(self, 'pay_button_widget') and self.pay_button_widget.winfo_exists():
            print("Destroying existing pay button.")
            self.pay_button_widget.destroy()
            delattr(self, 'pay_button_widget')

        # Clear previous status text/items
        self.canvas.delete("request_status")

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn:
                print("load_user_requests: Database connection failed.")
                return

            cursor = conn.cursor(dictionary=True)
            # Fetch the MOST RECENT job for this user
            sql_query = """
                SELECT pj.job_id, f.file_name, pj.status, pj.created_at, pj.total_amount,
                       pj.pages, pj.copies, pj.paper_size, pj.color_option
                FROM print_jobs pj
                JOIN files f ON pj.file_id = f.file_id
                WHERE pj.user_id = %s
                ORDER BY pj.created_at DESC
                LIMIT 1
            """
            cursor.execute(sql_query, (self.user_id,))
            request = cursor.fetchone()

            if request:
                print(f"Found request: {request}")
                job_id = request.get('job_id')
                filename = request.get('file_name', 'N/A')
                created_at = request.get('created_at')
                date_str = created_at.strftime("%B %d, %Y") if created_at else "N/A"
                status = request.get('status', 'N/A')
                db_total_amount = request.get('total_amount')
                pages = request.get('pages')
                copies = request.get('copies')
                paper_size = request.get('paper_size')
                color_option = request.get('color_option')

                # Call add_request_status to display this job
                self.add_request_status(job_id, filename, date_str, status, db_total_amount, pages, copies, paper_size, color_option)
            else:
                print("No recent print requests found for user.")
                self.canvas.create_text(265, 482, anchor="nw", text="No recent print requests found.", fill="#888888",
                                        font=("Inter Italic", 11), tags="request_status")

        except mysql.connector.Error as err:
            print(f"Database error loading request history: {err}")
            messagebox.showerror("Database Error", f"Failed to load request status:\n{err}", parent=self)
        except Exception as e:
            print(f"Unexpected error loading requests: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred loading request status:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()


    # --- **** MODIFIED add_request_status **** ---
    def add_request_status(self, job_id, filename, date, status, db_total_amount, pages, copies, paper_size,
                           color_option):
        # Clear previous status widgets before adding new ones
        self.canvas.delete("request_status")
        if hasattr(self, 'pay_button_widget') and self.pay_button_widget.winfo_exists():
            self.pay_button_widget.destroy()
            delattr(self, 'pay_button_widget')

        filename_x = 265
        date_x = 480
        status_x = 600
        amount_label_x = 680
        button_x = 795

        # Display filename and date (limit filename length)
        display_filename = filename[:25] + "..." if len(filename) > 28 else filename
        self.canvas.create_text(filename_x, 482, anchor="nw", text=display_filename, fill="#000000", font=("Inter", 11),
                                tags="request_status")
        self.canvas.create_text(date_x, 482, anchor="nw", text=date, fill="#000000", font=("Inter", 11),
                                tags="request_status")

        # Define status colors
        color_map = {
            "Approved": "#2E7D32",  # Dark Green
            "Paid": "#388E3C",      # Medium Green
            "Declined": "#D32F2F",    # Red
            "Pending": "#F9A825",     # Amber/Yellow
            "Completed": "#1976D2",   # Blue
            "In Progress": "#7B1FA2"  # Purple
        }
        status_color = color_map.get(status, "#333333") # Use status directly, provide default

        # Display status with color
        self.canvas.create_text(status_x, 482, anchor="nw", text=status, fill=status_color, font=("Inter", 11, "bold"),
                                tags="request_status")

        amount_to_display = Decimal('0.00')
        amount_str = ""
        amount_color = "#000000"

        # Calculate and display amount ONLY if status allows payment or shows cost
        if status in ['Approved', 'Paid', 'Completed']:
            # Prioritize db_total_amount if it's valid
            if db_total_amount is not None:
                try:
                    db_decimal = Decimal(db_total_amount).quantize(Decimal("0.01"))
                    if db_decimal > 0:
                        amount_to_display = db_decimal
                    # If db amount is 0 or invalid, fall back to calculation
                    elif pages is not None and copies is not None and paper_size and color_option:
                         amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)
                except (InvalidOperation, TypeError): # Catch errors converting db_total_amount
                     if pages is not None and copies is not None and paper_size and color_option:
                         amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)
            # If db_total_amount is NULL, calculate
            elif pages is not None and copies is not None and paper_size and color_option:
                 amount_to_display = self._calculate_price(pages, copies, paper_size, color_option)

            # Format amount string
            if amount_to_display > Decimal('0.00'):
                amount_str = f"Amount: ₱{amount_to_display:.2f}"
                amount_color = "#000000"
            # Handle cases where calculation might fail or result in 0 (and inputs existed)
            elif pages is not None and copies is not None: # Check if calculation inputs were present
                amount_str = "Amount: Error"
                amount_color = "red"
            # Else: No amount to display if calculation inputs missing and db amount invalid/null

            # Display the amount string if it was generated
            if amount_str:
                self.canvas.create_text(amount_label_x, 482, anchor="nw", text=amount_str, fill=amount_color,
                                        font=("Inter", 11, "bold"), tags="request_status")

        # --- Conditional Button ---
        # ONLY show 'Pay' button if status is 'Approved' and amount is valid
        if status == 'Approved' and amount_to_display > Decimal('0.00'):
            pay_button = tk.Button(self, text="Pay", font=("Inter Bold", 9),
                                   command=lambda jid=job_id, amt=amount_to_display: self.open_pay_script(jid, amt),
                                   relief="raised", bd=1, bg="#000000", fg="white", activebackground="#333333",
                                   activeforeground="white", cursor="hand2", padx=5)
            # Store reference AND use create_window
            self.pay_button_widget = pay_button
            self.canvas.create_window(button_x, 479, anchor="nw", window=self.pay_button_widget, tags="request_status")

    # --- **** END MODIFICATION **** ---


    # --- UPDATED open_pay_script signature ---
    def open_pay_script(self, job_id, amount):
        print(f"Opening payment window for Job ID: {job_id}, Amount: {amount}")
        # Withdraw the main window (controller)
        if self.controller and self.controller.winfo_exists():
            self.controller.withdraw()
        try:
            python_exe = sys.executable # Use the current Python interpreter
            pay_script = Path(__file__).parent / "pay.py"
            # Ensure amount is passed as a string
            process = subprocess.Popen([python_exe, str(pay_script), str(job_id), f"{amount:.2f}"])
            process.wait() # Wait for the pay.py window to close
        except FileNotFoundError:
            messagebox.showerror("Error", f"pay.py script not found at:\n{pay_script}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open payment window:\n{e}", parent=self)
        finally:
            # Bring the main window back
            if self.controller and self.controller.winfo_exists():
                self.controller.deiconify()
                self.controller.lift() # Bring it to the front
                self.controller.focus_force() # Force focus
            self.load_user_requests() # Refresh the status


    # --- choose_file ---
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


    # --- toggle_notes ---
    def toggle_notes(self):
        if self.notes_var.get() == 1:
            self.notes_text.config(state=NORMAL)
        else:
            self.notes_text.delete("1.0", "end")
            self.notes_text.config(state=DISABLED)

    # --- clear_form ---
    def clear_form(self):
        self.selected_file = None
        self.canvas.itemconfig(self.file_label, text="No file selected")
        self.pages_entry.delete(0, "end")
        self.copies_entry.delete(0, "end")
        self.paper_size_var.set("A4")
        self.color_choice.set("") # Clear radio button selection
        self.notes_var.set(0) # Uncheck notes toggle
        self.notes_text.config(state=NORMAL) # Enable to delete
        self.notes_text.delete("1.0", "end")
        self.notes_text.config(state=DISABLED) # Disable again
        # Reset checkbutton visual state (might require slightly more involved logic if needed)
        self.bw_check.deselect()
        self.color_check.deselect()

    # --- submit_request ---
    def submit_request(self):
        if not self.user_id:
            messagebox.showerror("Error", "No user logged in.", parent=self); return
        if not self.selected_file:
            messagebox.showwarning("Missing File", "Please select a file.", parent=self); return

        pages_str = self.pages_entry.get().strip()
        copies_str = self.copies_entry.get().strip()
        color_option = self.color_choice.get() # Gets 'bw' or 'color'

        # --- Input Validation ---
        if not pages_str.isdigit() or int(pages_str) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of pages (must be > 0).", parent=self); return
        if not copies_str.isdigit() or int(copies_str) <= 0:
            messagebox.showwarning("Invalid Input", "Please enter a valid number of copies (must be > 0).", parent=self); return
        if not color_option:
            messagebox.showwarning("Missing Option", "Please select a color option (Black & White or Color).", parent=self); return
        # --- End Validation ---

        pages = int(pages_str)
        copies = int(copies_str)
        filename = os.path.basename(self.selected_file)
        paper_size = self.paper_size_var.get()
        color_value_db = "Color" if color_option == 'color' else "Black & White" # Convert to DB value
        notes = self.notes_text.get("1.0", "end-1c").strip() if self.notes_var.get() == 1 else "" # Use end-1c

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if conn is None: return # Error handled in get_db_connection

            cursor = conn.cursor()

            # --- File Handling ---
            file_name = os.path.basename(self.selected_file)
            allowed_extensions = {".pdf", ".docx"}
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in allowed_extensions:
                messagebox.showerror("Invalid File Type", f"Only PDF and DOCX files are allowed.\nYou selected: {file_ext}", parent=self)
                return

            file_type_for_db = file_ext.replace(".", "")
            upload_dir = Path("./uploads") # Ensure this directory exists or is created
            upload_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            # Sanitize filename base
            safe_filename_base = "".join(c for c in os.path.splitext(file_name)[0] if c.isalnum() or c in (' ', '_', '-')).rstrip()
            unique_filename = f"{timestamp}_{self.user_id}_{safe_filename_base}{file_ext}" # Add user_id for uniqueness
            destination_path = (upload_dir / unique_filename).resolve() # Use resolve for absolute path

            try:
                import shutil
                shutil.copy2(self.selected_file, destination_path) # Use copy2 to preserve metadata
                print(f"File copied to: {destination_path}")
            except Exception as e:
                messagebox.showerror("File Error", f"Could not save the selected file.\nPlease try again.\n\nError: {e}", parent=self)
                return
            # --- End File Handling ---

            # --- Database Insertion ---
            # Insert into files table first
            insert_file_query = """
                INSERT INTO files (user_id, file_name, file_path, file_type, upload_date)
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_file_query, (self.user_id, file_name, str(destination_path), file_type_for_db))
            file_id = cursor.lastrowid # Get the ID of the inserted file

            # Insert into print_jobs table
            insert_job_query = """
                INSERT INTO print_jobs
                (user_id, file_id, pages, paper_size, color_option, copies, notes, status, created_at, total_amount)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            # Calculate price before inserting
            calculated_amount = self._calculate_price(pages, copies, paper_size, color_value_db)

            job_data = (self.user_id, file_id, pages, paper_size, color_value_db, copies, notes, "Pending", calculated_amount)
            cursor.execute(insert_job_query, job_data)

            conn.commit() # Commit transaction
            # --- End Database Insertion ---

            messagebox.showinfo("Success", f"Print request for '{filename}' submitted successfully!", parent=self)
            self.load_user_requests() # Refresh the status display
            self.clear_form() # Clear the form fields

        except mysql.connector.Error as err:
            if conn: conn.rollback() # Rollback on error
            messagebox.showerror("Database Error", f"An error occurred while submitting the request:\n{err}", parent=self)
        except Exception as e:
            if conn: conn.rollback() # Rollback on unexpected error
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()