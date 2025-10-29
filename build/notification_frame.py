from pathlib import Path
from tkinter import Canvas, Button, PhotoImage, Label, Frame, messagebox, ttk, Toplevel, Text
import tkinter as tk
import mysql.connector
from datetime import datetime
from utils import get_db_connection, round_rectangle

# Import frame classes needed for navigation
from printer_frame import PrinterFrame
from user_frame import UserFrame
from prices_frame import PricesFrame
from help_frame import HelpFrame

OUTPUT_PATH = Path(__file__).parent
# --- Make sure this points to the correct assets for Notification ---
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0" # Verify this path

def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset not found at {asset_file}")
    return asset_file

# Constants
WHITE = "#FFFFFF"
BLACK = "#000000"

# --- Fetch Notifications ---
def fetch_notifications(current_user_id):
    if current_user_id is None: return []
    notifications = []
    conn = get_db_connection()
    if not conn: return notifications
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT notif_id, subject, message, created_at, status
            FROM notifications
            WHERE (user_id = %s OR user_id IS NULL)
            ORDER BY created_at DESC
        """
        cursor.execute(query, (current_user_id,))
        notifications = cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching notifications:\n{err}")
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor: cursor.close()
            conn.close()
    return notifications

# --- Mark Notification as Read ---
def mark_notification_as_read(notif_id):
    conn = get_db_connection()
    if not conn: return
    try:
        cursor = conn.cursor()
        query = "UPDATE notifications SET status = 'Read' WHERE notif_id = %s"
        cursor.execute(query, (notif_id,))
        conn.commit()
    except mysql.connector.Error as err:
         print(f"Error marking notification {notif_id} as read: {err}")
    finally:
        if conn and conn.is_connected():
            if 'cursor' in locals() and cursor: cursor.close()
            conn.close()

# --- MAIN NOTIFICATION FRAME CLASS ---
class NotificationFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Get user data FROM THE CONTROLLER ---
        self.user_id = controller.user_id
        self.fullname = controller.fullname # Though not used directly here

        # --- Resize window for this specific frame ---
        # controller.geometry("829x504") # Match original size

        self.canvas = Canvas(self, bg=WHITE, height=504, width=829, bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # --- Load Assets ---
        try:
            # Load icons used in this frame
            self.icon_edit = PhotoImage(file=relative_to_assets("account.png"))
            self.icon_bell = PhotoImage(file=relative_to_assets("image_13.png")) # Printer icon?
            self.icon_sheet = PhotoImage(file=relative_to_assets("image_15.png")) # Pricelist icon?
            self.icon_help = PhotoImage(file=relative_to_assets("image_16.png")) # Help icon?
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not load assets for NotificationFrame:\n{e}")
            return

        # --- UI Elements ---
        self.canvas.create_rectangle(0, 0, 829, 504, fill=WHITE, outline="")
        self.canvas.create_rectangle(0, 0, 829, 85, fill=BLACK, outline="")
        self.canvas.create_text(228, 17, anchor="nw", text="Notifications", fill=WHITE, font=("Inter Bold", -36))
        self.canvas.create_rectangle(209, -1, 210, 504, fill=BLACK, outline="")

        # --- Left Menu Buttons ---
        Y_START = 129; BTN_H = 38; BTN_W = 161; PADDING = 11; BTN_X = 26
        self.create_rounded_menu_button(BTN_X, Y_START, BTN_W, BTN_H, "Profile", self.open_user_py)
        self.create_rounded_menu_button(BTN_X, Y_START + BTN_H + PADDING, BTN_W, BTN_H, "Print Request", self.open_printer_py)
        self.create_rounded_menu_button(BTN_X, Y_START + 2*(BTN_H + PADDING), BTN_W, BTN_H, "Pricelist", self.open_prices_py)
        self.create_rounded_menu_button(BTN_X, Y_START + 3*(BTN_H + PADDING), BTN_W, BTN_H, "Help", self.open_help_py)

        # --- Left icons ---
        ICON_X = 43
        lbl_edit  = Label(self, image=self.icon_edit,  bg=WHITE, bd=0); lbl_edit.place(x=ICON_X, y=Y_START + BTN_H/2, anchor="center")
        lbl_bell  = Label(self, image=self.icon_bell,  bg=WHITE, bd=0); lbl_bell.place(x=ICON_X, y=Y_START + BTN_H + PADDING + BTN_H/2, anchor="center")
        lbl_sheet = Label(self, image=self.icon_sheet, bg=WHITE, bd=0); lbl_sheet.place(x=ICON_X, y=Y_START + 2*(BTN_H + PADDING) + BTN_H/2, anchor="center")
        lbl_help  = Label(self, image=self.icon_help,  bg=WHITE, bd=0); lbl_help.place(x=ICON_X, y=Y_START + 3*(BTN_H + PADDING) + BTN_H/2, anchor="center")
        self.make_icon_clickable(lbl_edit, self.open_user_py)
        self.make_icon_clickable(lbl_bell, self.open_printer_py) # Bell icon -> Printer
        self.make_icon_clickable(lbl_sheet, self.open_prices_py) # Sheet icon -> Pricelist
        self.make_icon_clickable(lbl_help, self.open_help_py)   # Help icon -> Help

        # --- Notification Scrollable Area ---
        NOTIF_X, NOTIF_Y = 224, 97
        NOTIF_W, NOTIF_H = 589, 391

        notif_container = Frame(self, bg=WHITE, bd=1, relief="solid")
        notif_container.place(x=NOTIF_X, y=NOTIF_Y, width=NOTIF_W, height=NOTIF_H)
        self.notif_canvas = Canvas(notif_container, bg=WHITE, bd=0, highlightthickness=0)
        notif_scrollbar = ttk.Scrollbar(notif_container, orient="vertical", command=self.notif_canvas.yview)
        self.notif_canvas.configure(yscrollcommand=notif_scrollbar.set)
        notif_scrollbar.pack(side="right", fill="y")
        self.notif_canvas.pack(side="left", fill="both", expand=True)
        self.notif_content_frame = Frame(self.notif_canvas, bg=WHITE)
        self.notif_content_frame_window = self.notif_canvas.create_window((0, 0), window=self.notif_content_frame, anchor="nw")

        self.notif_content_frame.bind("<Configure>", self._on_frame_configure)
        self.notif_canvas.bind("<Configure>", lambda e: self.notif_canvas.itemconfig(self.notif_content_frame_window, width=e.width))

        # Bind mousewheel scrolling
        self.notif_canvas.bind("<Enter>", self._bind_mousewheel)
        self.notif_canvas.bind("<Leave>", self._unbind_mousewheel)
        self.notif_content_frame.bind("<Enter>", self._bind_mousewheel)
        self.notif_content_frame.bind("<Leave>", self._unbind_mousewheel)

        # --- Clear Read Button ---
        clear_button = Button(
            self, text="Clear Read", font=("Inter Bold", 10), command=self.clear_read_notifications,
            relief="raised", bd=1, bg="#F0F0F0", activebackground="#D9D9D9"
        )
        clear_button.place(x=NOTIF_X + NOTIF_W - 80, y=NOTIF_Y + NOTIF_H + 5, width=70, height=25)

        # --- Load initial notifications ---
        self.load_notifications()

    def load_notifications(self):
        """Public method called by controller to refresh notifications."""
        notifications = fetch_notifications(self.user_id)
        self.display_notifications(self.notif_content_frame, notifications)
        # Update scroll region after loading
        self.canvas.after(50, lambda: self._on_frame_configure(None)) # Delay needed

    def clear_read_notifications(self):
        """Marks all currently 'Unread' notifications for the user as 'Read'."""
        if self.user_id is None: return
        conn = get_db_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            query = "UPDATE notifications SET status = 'Read' WHERE (user_id = %s OR user_id IS NULL) AND status = 'Unread'"
            cursor.execute(query, (self.user_id,))
            affected_rows = cursor.rowcount
            conn.commit()
            messagebox.showinfo("Notifications Cleared", f"{affected_rows} notifications marked as read." if affected_rows > 0 else "No new notifications to clear.")
            self.load_notifications() # Refresh the list
        except mysql.connector.Error as err:
             messagebox.showerror("Database Error", f"Error clearing notifications: {err}")
        finally:
            if conn and conn.is_connected():
                if 'cursor' in locals() and cursor: cursor.close()
                conn.close()

    def show_message_window(self, notification_details):
        """Creates a Toplevel window to display the full notification message."""
        notif_id = notification_details['notif_id']
        subject = notification_details.get('subject', 'No Subject')
        message = notification_details.get('message', 'No Message Body')
        current_status = notification_details.get('status', 'Unread')

        if current_status == 'Unread':
            mark_notification_as_read(notif_id)

        message_win = Toplevel(self.controller) # Make it child of main Tk window
        message_win.title(f"Subject: {subject}")
        message_win.configure(bg=WHITE)
        message_win.transient(self.controller) # Keep on top
        message_win.grab_set() # Modal

        # Center relative to the main window (controller)
        win_x = self.controller.winfo_x(); win_y = self.controller.winfo_y()
        win_w = self.controller.winfo_width(); win_h = self.controller.winfo_height()
        msg_w = 450; msg_h = 300
        msg_x = win_x + (win_w // 2) - (msg_w // 2)
        msg_y = win_y + (win_h // 2) - (msg_h // 2)
        message_win.geometry(f"{msg_w}x{msg_h}+{msg_x}+{msg_y}")

        Label(message_win, text=subject, font=("Inter Bold", 14), bg=WHITE, wraplength=430, justify="left").pack(pady=(10, 5), padx=10, anchor="w")
        ttk.Separator(message_win, orient="horizontal").pack(fill="x", padx=10)

        message_frame = Frame(message_win, bg=WHITE)
        message_frame.pack(fill="both", expand=True, padx=10, pady=(5, 5))
        message_text_widget = Text(message_frame, wrap=tk.WORD, font=("Inter", 11), bg=WHITE, bd=0, highlightthickness=0, padx=5, pady=5)
        message_text_widget.insert(tk.END, message)
        message_text_widget.config(state=tk.DISABLED)
        msg_scrollbar = ttk.Scrollbar(message_frame, orient="vertical", command=message_text_widget.yview)
        message_text_widget.configure(yscrollcommand=msg_scrollbar.set)
        msg_scrollbar.pack(side="right", fill="y")
        message_text_widget.pack(side="left", fill="both", expand=True)

        Button(message_win, text="Close", font=("Inter Bold", 11), command=message_win.destroy, width=8).pack(pady=(5, 10))

        message_win.wait_window()
        self.load_notifications() # Refresh main list after closing

    def display_notifications(self, frame, notifications_data):
        """Populates the frame with notification items."""
        for widget in frame.winfo_children():
            widget.destroy()

        if not notifications_data:
            Label(frame, text="No notifications.", font=("Inter", 14), bg=WHITE, fg="grey").pack(pady=20, padx=10)
            return

        for notification in notifications_data:
            notif_id = notification['notif_id']
            status = notification.get('status', 'Unread')
            text_color = BLACK if status == 'Unread' else "grey"
            time_color = "grey"
            frame_bg = WHITE

            item_frame = Frame(frame, bg=frame_bg, bd=1, relief="solid", padx=5, pady=5)
            item_frame.pack(fill="x", padx=10, pady=(5, 0))

            subject_text = notification.get('subject', 'No Subject')
            subject_label = Label(item_frame, text=subject_text, font=("Inter Bold", 13), bg=frame_bg, fg=text_color, anchor="w", justify="left")
            subject_label.pack(fill="x")

            timestamp = notification.get('created_at', datetime.now())
            try: time_str = timestamp.strftime("%b %d, %Y - %I:%M %p")
            except AttributeError: time_str = "Invalid Date"
            time_label = Label(item_frame, text=time_str, font=("Inter", 9), bg=frame_bg, fg=time_color, anchor="w", justify="left")
            time_label.pack(fill="x")

            item_frame.bind("<Button-1>", lambda e, notif=notification: self.show_message_window(notif))
            subject_label.bind("<Button-1>", lambda e, notif=notification: self.show_message_window(notif))
            time_label.bind("<Button-1>", lambda e, notif=notification: self.show_message_window(notif))
            for w in [item_frame, subject_label, time_label]:
                w.bind("<Enter>", lambda e: self.config(cursor="hand2"))
                w.bind("<Leave>", lambda e: self.config(cursor=""))

    # --- Scrollbar Helper Functions ---
    def _on_frame_configure(self, event):
        self.notif_canvas.configure(scrollregion=self.notif_canvas.bbox("all"))
    def _on_mousewheel(self, event):
        self.notif_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    def _bind_mousewheel(self, event):
        self.bind_all("<MouseWheel>", self._on_mousewheel)
    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")

    # --- Reusable Rounded Menu Button Method ---
    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + 40, y + (h/2), text=text, anchor="w", fill="#000000", font=("Inter Bold", 15)) # Centered text vertically
        def on_click(event):
            if command: command()
        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#E8E8E8"); self.config(cursor="hand2")
        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#FFFFFF"); self.config(cursor="")
        for tag in (rect, txt):
            self.canvas.tag_bind(tag, "<Button-1>", on_click)
            self.canvas.tag_bind(tag, "<Enter>", on_hover)
            self.canvas.tag_bind(tag, "<Leave>", on_leave)

    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    # --- Navigation Methods ---
    def open_user_py(self):
        self.controller.show_frame(UserFrame)
    def open_printer_py(self):
        self.controller.show_frame(PrinterFrame)
    def open_prices_py(self):
        self.controller.show_frame(PricesFrame)
    def open_help_py(self):
        self.controller.show_frame(HelpFrame)