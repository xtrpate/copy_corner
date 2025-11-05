from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, messagebox, ttk, Listbox
import mysql.connector
from datetime import datetime
from utils import get_db_connection, round_rectangle

# --- Asset Path Setup ---
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame5"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_notification) not found at {asset_file}")
    return asset_file


class AdminNotificationFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.all_users = []
        self.selected_user_id = None

        if not self.create_notifications_table():
            messagebox.showerror("Setup Error", "Could not create or verify the notifications database table.")

        window_width = 905
        window_height = 567
        self.canvas = Canvas(
            self,
            bg="#FFFFFF",
            height=window_height,
            width=window_width,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- Backgrounds ---
        self.canvas.create_rectangle(19.0, 15.0, window_width - 19, window_height - 15, fill="#FFF6F6",
                                     outline="#000000")
        self.canvas.create_rectangle(40.0, 33.0, window_width - 40, window_height - 33, fill="#FFFFFF",
                                     outline="#000000")
        self.canvas.create_rectangle(50.0, 41.0, 253.0, window_height - 40, fill="#FFFFFF", outline="#000000")

        try:
            self.logo_image = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(151.0, 79.0, image=self.logo_image)
        except tk.TclError as e:
            print(f"ERROR loading logo in admin_notification: {e}")

        # --- Sidebar Content ---
        self.canvas.create_text(151, 140, anchor="center", text="ADMIN", fill="#000000", font=("Inter Bold", 15))
        sidebar_y_start = 162
        sidebar_y_offset = 56
        self.create_rounded_menu_button(73, sidebar_y_start, 151, 38, "Dashboard", self.open_admin_dashboard)
        self.create_rounded_menu_button(73, sidebar_y_start + sidebar_y_offset, 151, 38, "User", self.open_admin_user)
        self.create_rounded_menu_button(73, sidebar_y_start + 2 * sidebar_y_offset, 151, 38, "Print Jobs",
                                        self.open_admin_print)
        self.create_rounded_menu_button(73, sidebar_y_start + 3 * sidebar_y_offset, 151, 38, "Reports",
                                        self.open_admin_report)
        self.create_rounded_menu_button(73, sidebar_y_start + 4 * sidebar_y_offset, 151, 38, "Inventory",
                                        self.open_admin_inventory)
        self.create_rounded_menu_button(89, 485, 111, 38, "Logout", self.logout)

        # --- Main Content Area ---
        self.canvas.create_text(281.0, 48.0, anchor="nw", text="Notifications", fill="#000000", font=("Inter Bold", 40))
        self.canvas.create_rectangle(260.0, 32.0, 261.0, window_height - 33, fill="#000000", outline="")
        self.canvas.create_rectangle(281.0, 100.0, 655.0, 517.0, fill="#FFFFFF", outline="#000000")

        self.canvas.create_text(300.0, 119.0, anchor="nw", text="Send to:", fill="#000000", font=("Inter Bold", 14))
        self.send_to_var = tk.StringVar(value=None)
        style = ttk.Style()
        style.configure("TRadiobutton", background="white", font=("Inter", 11))

        single_user_rb = ttk.Radiobutton(self, text="Single User", variable=self.send_to_var, value="single",
                                         command=self.toggle_user_entry, style="TRadiobutton")
        single_user_rb.place(x=375.0, y=117.0)
        all_user_rb = ttk.Radiobutton(self, text="All Users", variable=self.send_to_var, value="all",
                                      command=self.toggle_user_entry, style="TRadiobutton")
        all_user_rb.place(x=489.0, y=117.0)

        self.canvas.create_text(300.0, 161.0, anchor="nw", text="User:", fill="#000000", font=("Inter Bold", 14))
        self.user_entry = Entry(self, bd=0, bg="#F0F0F0", highlightthickness=1, highlightcolor="#000000",
                                highlightbackground="#CCCCCC", font=("Inter", 12), state=tk.DISABLED)
        self.user_entry.place(x=395.0, y=159.0, width=248.0, height=26.0)
        self.user_listbox = Listbox(self, bd=1, relief="solid", font=("Inter", 10), height=4, highlightthickness=0)

        self.user_entry.bind("<KeyRelease>", self.update_user_suggestions)
        self.user_listbox.bind("<<ListboxSelect>>", self.select_user_from_list)
        self.user_entry.bind("<FocusOut>", self.hide_suggestions)
        self.user_listbox.bind("<FocusOut>", self.hide_suggestions)

        self.canvas.create_text(300.0, 200.0, anchor="nw", text="Subject:", fill="#000000", font=("Inter Bold", 14))
        self.subject_entry = Text(self, bd=0, bg="white", highlightthickness=1, highlightcolor="#000000",
                                  highlightbackground="#CCCCCC", font=("Inter", 12), height=1, wrap="none")
        self.subject_entry.place(x=395.0, y=198.0, width=248.0, height=26.0)
        self.subject_entry.bind("<Return>", lambda event: "break")

        self.canvas.create_text(297.0, 238.0, anchor="nw", text="Message:", fill="#000000", font=("Inter Bold", 14))
        message_frame = tk.Frame(self, bd=1, relief='solid')
        message_frame.place(x=297.0, y=260.0, width=343.0, height=204.0)
        self.message_text = Text(message_frame, bd=0, bg="white", highlightthickness=0, font=("Inter", 12),
                                 wrap=tk.WORD)
        message_scrollbar = ttk.Scrollbar(message_frame, orient="vertical", command=self.message_text.yview)
        self.message_text.configure(yscrollcommand=message_scrollbar.set)
        message_scrollbar.pack(side="right", fill="y")
        self.message_text.pack(side="left", fill="both", expand=True)

        # --- Buttons (REMOVED TTK, REPLACED WITH create_rounded_button) ---
        self.create_rounded_button(380, 473, 90, 35, "Clear", self.clear_form,
                                   fill="#F0F0F0", text_color="#000000")
        self.create_rounded_button(480, 473, 90, 35, "Send", self.send_notification,
                                   fill="#000000", text_color="#FFFFFF")

        # --- Activity Feed ---
        feed_area_x = 665.0
        feed_area_y = 100.0
        feed_area_w = 190.0
        feed_area_h = 417.0

        self.canvas.create_rectangle(feed_area_x, feed_area_y, feed_area_x + feed_area_w, feed_area_y + feed_area_h,
                                     fill="#FFFFFF", outline="#000000")
        self.canvas.create_text(feed_area_x + feed_area_w / 2, feed_area_y + 15, anchor="center", text="Activity Feed",
                                fill="#000000", font=("Inter Bold", 14))
        self.canvas.create_line(feed_area_x + 10, feed_area_y + 35, feed_area_x + feed_area_w - 10, feed_area_y + 35,
                                fill="#CCCCCC")

        feed_container = tk.Frame(self, bg="#FFFFFF", bd=0)
        feed_container.place(x=feed_area_x + 2, y=feed_area_y + 40, width=feed_area_w - 4, height=feed_area_h - 45)

        self.feed_canvas = Canvas(feed_container, bg="#FFFFFF", highlightthickness=0)
        feed_scrollbar = ttk.Scrollbar(feed_container, orient="vertical", command=self.feed_canvas.yview)
        self.feed_inner_frame = tk.Frame(self.feed_canvas, bg="#FFFFFF")
        self.feed_inner_frame.bind("<Configure>",
                                   lambda e: self.feed_canvas.configure(scrollregion=self.feed_canvas.bbox("all")))
        self.feed_canvas.create_window((0, 0), window=self.feed_inner_frame, anchor="nw", width=feed_area_w - 22)
        self.feed_canvas.configure(yscrollcommand=feed_scrollbar.set)
        feed_scrollbar.pack(side="right", fill="y")
        self.feed_canvas.pack(side="left", fill="both", expand=True)

        self.feed_canvas.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.feed_canvas))
        self.feed_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel(e))
        self.feed_inner_frame.bind("<Enter>", lambda e: self._bind_mousewheel(e, self.feed_canvas))
        self.feed_inner_frame.bind("<Leave>", lambda e: self._unbind_mousewheel(e))

        self.load_notifications_admin()

    def load_notifications_admin(self):
        self.fetch_users_for_autocomplete()
        self.toggle_user_entry()
        self.refresh_activity_feed()

    def clear_form(self):
        self.send_to_var.set(None)
        self.user_entry.delete(0, tk.END)
        self.subject_entry.delete("1.0", tk.END)
        self.message_text.delete("1.0", tk.END)
        self.toggle_user_entry()

    def fetch_users_for_autocomplete(self):
        conn = get_db_connection()
        if not conn: return
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT user_id, username FROM users WHERE status = 'active' ORDER BY username ASC"
            cursor.execute(query)
            self.all_users = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Error fetching users: {err}")
            self.all_users = []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def fetch_notification_history(self):
        if not self.all_users:
            self.fetch_users_for_autocomplete()
        conn = get_db_connection()
        if not conn: return []
        cursor = None
        try:
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT
                    notif_id, user_id, subject, message, created_at
                FROM notifications
                ORDER BY created_at DESC
                LIMIT 20
            """
            cursor.execute(query)
            notifications = cursor.fetchall()
            enriched_notifications = []
            for notification in notifications:
                enriched_notif = notification.copy()
                user_id = notification.get('user_id')
                if user_id:
                    user = next((u for u in self.all_users if u['user_id'] == user_id), None)
                    enriched_notif['recipient'] = user['username'] if user else f"User ID:{user_id}"
                else:
                    enriched_notif['recipient'] = "All Users"
                enriched_notifications.append(enriched_notif)
            return enriched_notifications
        except mysql.connector.Error as err:
            print(f"Error fetching notification history: {err}")
            return []
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def create_notifications_table(self):
        conn = get_db_connection()
        if not conn: return False
        cursor = None
        try:
            cursor = conn.cursor()
            create_table_query = """
                CREATE TABLE IF NOT EXISTS notifications (
                  notif_id int(11) NOT NULL AUTO_INCREMENT,
                  user_id int(11) DEFAULT NULL,
                  subject varchar(255) NOT NULL,
                  message text DEFAULT NULL,
                  status enum('Unread','Read') DEFAULT 'Unread',
                  created_at timestamp NOT NULL DEFAULT current_timestamp(),
                  PRIMARY KEY (notif_id),
                  KEY user_id (user_id),
                  CONSTRAINT notifications_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """
            cursor.execute(create_table_query)
            conn.commit()
            print("Notifications table created/verified successfully")
            return True
        except mysql.connector.Error as err:
            print(f"Error creating/verifying notifications table: {err}")
            return False
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def toggle_user_entry(self):
        if self.send_to_var.get() == "single":
            self.user_entry.config(state=tk.NORMAL, bg="white")
            self.user_entry.delete(0, tk.END)
            self.selected_user_id = None
            self.user_entry.focus()
        else:
            self.user_entry.config(state=tk.DISABLED, bg="#F0F0F0")
            self.user_entry.delete(0, tk.END)
            self.hide_suggestions()
            self.selected_user_id = None

    def update_user_suggestions(self, event=None):
        search_term = self.user_entry.get().lower()
        self.user_listbox.delete(0, tk.END)
        self.selected_user_id = None
        if not search_term:
            self.hide_suggestions()
            return
        matches = [user for user in self.all_users if search_term in user.get('username', '').lower()]
        if matches:
            for user in matches:
                self.user_listbox.insert(tk.END, f"{user['username']}")

            entry_x = self.user_entry.winfo_x()
            entry_y = self.user_entry.winfo_y()
            entry_height = self.user_entry.winfo_height()
            entry_width = self.user_entry.winfo_width()
            self.user_listbox.place(x=entry_x, y=entry_y + entry_height, width=entry_width)
            self.user_listbox.lift()
        else:
            self.hide_suggestions()

    def select_user_from_list(self, event=None):
        selection_indices = self.user_listbox.curselection()
        if not selection_indices: return
        selected_text = self.user_listbox.get(selection_indices[0])
        try:
            selected_user = next((u for u in self.all_users if u['username'] == selected_text), None)
            if selected_user:
                self.selected_user_id = selected_user['user_id']
                self.user_entry.delete(0, tk.END)
                self.user_entry.insert(0, selected_user['username'])
                self.hide_suggestions()
                self.subject_entry.focus()
            else:
                self.selected_user_id = None
                self.hide_suggestions()
        except (IndexError, ValueError, TypeError):
            self.selected_user_id = None
            self.hide_suggestions()

    def hide_suggestions(self, event=None):
        focused_widget = self.focus_get()
        if focused_widget != self.user_listbox:
            self.after(150, self.user_listbox.place_forget)

    def update_activity_feed(self):
        for widget in self.feed_inner_frame.winfo_children():
            widget.destroy()
        notifications = self.fetch_notification_history()
        if not notifications:
            tk.Label(self.feed_inner_frame, text="No notifications sent yet", font=("Inter", 10), bg="#FFFFFF",
                     fg="#666666", justify="center").pack(pady=20, padx=5)
            return
        for notification in notifications:
            self.create_feed_item(notification)
        self.feed_inner_frame.update_idletasks()
        self.feed_canvas.configure(scrollregion=self.feed_canvas.bbox("all"))
        self.feed_canvas.yview_moveto(0)

    def create_feed_item(self, notification):
        item_frame = tk.Frame(self.feed_inner_frame, bg="#FFFFFF", relief="solid", bd=1)
        item_frame.pack(fill="x", padx=5, pady=(0, 3))
        created_at = notification.get('created_at')
        date_str = created_at.strftime("%m/%d %H:%M") if isinstance(created_at, datetime) else "Unknown"
        recipient = notification.get('recipient', 'Unknown Recipient')
        subject = notification.get('subject', 'No Subject')
        if len(subject) > 20: subject = subject[:17] + "..."
        item_frame.columnconfigure(0, weight=1)
        tk.Label(item_frame, text=f"To: {recipient}", font=("Inter Bold", 9), bg="#FFFFFF", fg="#000000",
                 anchor="w").grid(row=0, column=0, sticky="ew", padx=5, pady=(3, 0))
        tk.Label(item_frame, text=f"{subject}", font=("Inter", 9), bg="#FFFFFF", fg="#333333", anchor="w").grid(row=1,
                                                                                                                column=0,
                                                                                                                sticky="ew",
                                                                                                                padx=5)
        tk.Label(item_frame, text=date_str, font=("Inter", 8), bg="#FFFFFF", fg="#666666", anchor="w").grid(row=2,
                                                                                                            column=0,
                                                                                                            sticky="ew",
                                                                                                            padx=5,
                                                                                                            pady=(0, 3))

        def on_enter(event, frame=item_frame):
            frame.config(bg="#F0F8FF")
            for child in frame.winfo_children():
                if isinstance(child, tk.Label): child.config(bg="#F0F8FF")

        def on_leave(event, frame=item_frame):
            frame.config(bg="#FFFFFF")
            for child in frame.winfo_children():
                if isinstance(child, tk.Label): child.config(bg="#FFFFFF")

        item_frame.bind("<Enter>", on_enter)
        item_frame.bind("<Leave>", on_leave)
        for child in item_frame.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)

    def refresh_activity_feed(self):
        self.update_activity_feed()

    def send_notification(self):
        send_to = self.send_to_var.get()
        user_text = self.user_entry.get().strip()
        subject = self.subject_entry.get("1.0", "end-1c").strip()
        message = self.message_text.get("1.0", "end-1c").strip()

        if not send_to: messagebox.showerror("Input Error", "Please select 'Single User' or 'All User'."); return
        recipient_user_id = None
        if send_to == "single":
            if not user_text: messagebox.showerror("Input Error", "Please enter or select a username."); return
            if self.selected_user_id is None:
                matches = [user for user in self.all_users if user['username'].lower() == user_text.lower()]
                if len(matches) == 1:
                    recipient_user_id = matches[0]['user_id']
                    recipient_name = matches[0]['username']
                else:
                    messagebox.showerror("Input Error",
                                         "User not found or ambiguous. Please select from the list or type the exact username.");
                    return
            else:
                recipient_user_id = self.selected_user_id
                recipient_name = user_text
        if not subject: messagebox.showerror("Input Error", "Please enter a subject."); return
        if len(subject) > 255: messagebox.showerror("Input Error", "Subject is too long (max 255 characters)."); return
        if not message: messagebox.showerror("Input Error", "Please enter a message."); return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()
            if send_to == "single":
                sql = "INSERT INTO notifications (user_id, subject, message, status) VALUES (%s, %s, %s, 'Unread')"
                cursor.execute(sql, (recipient_user_id, subject, message))
                conn.commit()
                messagebox.showinfo("Success", f"Notification sent to {recipient_name}!")
            elif send_to == "all":
                cursor.execute("SELECT user_id FROM users WHERE status = 'active'")
                user_ids = [row[0] for row in cursor.fetchall()]
                if not user_ids:
                    messagebox.showwarning("No Users", "There are no active users to send notifications to.");
                    return
                sql = "INSERT INTO notifications (user_id, subject, message, status) VALUES (%s, %s, %s, 'Unread')"
                data_to_insert = [(user_id, subject, message) for user_id in user_ids]
                cursor.executemany(sql, data_to_insert)
                conn.commit()
                messagebox.showinfo("Success", f"Notification sent to all {len(user_ids)} active users!")

            self.clear_form()
            self.refresh_activity_feed()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to send notification: {err}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def _on_mousewheel(self, event, canvas):
        scroll_info = canvas.yview()
        if scroll_info[0] == 0.0 and scroll_info[1] == 1.0:
            return
        if event.delta > 0 or event.num == 4:
            if scroll_info[0] > 0.0: canvas.yview_scroll(-1, "units")
        elif event.delta < 0 or event.num == 5:
            if scroll_info[1] < 1.0: canvas.yview_scroll(1, "units")

    def _bind_mousewheel(self, event, canvas):
        self.bind_all("<MouseWheel>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-4>", lambda ev: self._on_mousewheel(ev, canvas))
        self.bind_all("<Button-5>", lambda ev: self._on_mousewheel(ev, canvas))

    def _unbind_mousewheel(self, event):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    # --- **** ADDED: create_rounded_button (copied from admin_inventory.py) **** ---
    def create_rounded_button(self, x, y, w, h, text, command, fill, text_color):
        """Creates a generic rounded action button."""
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill=fill, outline="")
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, font=("Inter Bold", 10), fill=text_color)

        try:
            # Simple hover logic
            if fill == "#000000":
                hover_fill = "#333333"
            elif fill == "#F0F0F0":
                hover_fill = "#DEDEDE"
            else: # Default darken
                r_hex, g_hex, b_hex = fill[1:3], fill[3:5], fill[5:7]
                r, g, b = int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)
                hover_r, hover_g, hover_b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
                hover_fill = f'#{hover_r:02x}{hover_g:02x}{hover_b:02x}'
        except Exception:
            hover_fill = "#333333" # Fallback

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill=hover_fill)
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill=fill)
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="")

        self.canvas.tag_bind(rect, "<Button-1>", on_click)
        self.canvas.tag_bind(txt, "<Button-1>", on_click)
        self.canvas.tag_bind(rect, "<Enter>", on_hover)
        self.canvas.tag_bind(txt, "<Enter>", on_hover)
        self.canvas.tag_bind(rect, "<Leave>", on_leave)
        self.canvas.tag_bind(txt, "<Leave>", on_leave)
    # --- **** END ADDITION **** ---

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

    def open_admin_dashboard(self):
        self.controller.show_admin_dashboard()

    def open_admin_print(self):
        self.controller.show_admin_print()

    def open_admin_report(self):
        self.controller.show_admin_report()

    def open_admin_user(self):
        self.controller.show_admin_user()

    def open_admin_inventory(self):
        self.controller.show_admin_inventory()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?"):
            self.controller.show_login_frame()