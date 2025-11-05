from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Entry, Text, Button, PhotoImage, ttk, messagebox, Frame, font
import mysql.connector
from decimal import Decimal, InvalidOperation
from utils import get_db_connection, round_rectangle

# Asset Path
OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame4"


def relative_to_assets(path: str) -> Path:
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset (admin_inventory) not found at {asset_file}")
    return asset_file


class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color="grey", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    def put_placeholder(self):
        if not self.winfo_exists(): return
        self.delete(0, "end")
        self.insert(0, self.placeholder)
        self["fg"] = self.placeholder_color

    def foc_in(self, *args):
        if not self.winfo_exists(): return
        if self["fg"] == self.placeholder_color:
            self.delete("0", "end")
            self["fg"] = self.default_fg_color

    def foc_out(self, *args):
        if not self.winfo_exists(): return
        if not self.get(): self.put_placeholder()


class AdminInventoryFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.selected_product_id = None

        self.canvas = Canvas(
            self, bg="#FFFFFF", height=550, width=880,
            bd=0, highlightthickness=0, relief="ridge"
        )
        self.canvas.place(x=0, y=0)

        # --- Backgrounds ---
        self.canvas.create_rectangle(19.0, 27.0, 848.0, 531.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(28.0, 34.0, 231.0, 523.0, fill="#FFFFFF", outline="#000000")
        self.canvas.create_rectangle(235.0, 27.0, 240.0, 531.0, fill="#000000", outline="")
        self.canvas.create_rectangle(622.0, 206.0, 839.0, 375.0, fill="#F0F0F0", outline="#000000", width=1)
        self.canvas.create_rectangle(260.0, 174.0, 617.0, 470.0, fill="#FFFFFF", outline="#000000")

        # --- Logo ---
        try:
            self.logo_image = PhotoImage(file=relative_to_assets("image_1.png"))
            self.canvas.create_image(131.0, 69.0, image=self.logo_image)
        except tk.TclError:
            self.canvas.create_text(131.0, 89.0, text="Logo Missing", fill="#000000")

        self.canvas.create_text(101.0, 97.0, anchor="nw", text="ADMIN", fill="#000000", font=("Inter Bold", 15 * -1))
        self.canvas.create_text(258.0, 29.0, anchor="nw", text="Inventory", fill="#000000",
                                font=("Inter Bold", 36 * -1))

        # --- Sidebar Buttons ---
        sidebar_y_start = 153.0
        button_height = 41.0
        button_gap = 15.0

        self.create_rounded_menu_button(48.0, sidebar_y_start, 158.0, button_height, "Dashboard",
                                        self.controller.show_admin_dashboard)
        self.create_rounded_menu_button(48.0, sidebar_y_start + (button_height + button_gap) * 1, 158.0, button_height,
                                        "User", self.controller.show_admin_user)
        self.create_rounded_menu_button(48.0, sidebar_y_start + (button_height + button_gap) * 2, 158.0, button_height,
                                        "Print Jobs", self.controller.show_admin_print)
        self.create_rounded_menu_button(48.0, sidebar_y_start + (button_height + button_gap) * 3, 158.0, button_height,
                                        "Notifications", self.controller.show_admin_notification)
        self.create_rounded_menu_button(48.0, sidebar_y_start + (button_height + button_gap) * 4, 158.0, button_height,
                                        "Reports", self.controller.show_admin_report)
        self.create_rounded_menu_button(82.0, 470.0, 91.0, 41.0, "Logout", self.controller.show_login_frame)

        # --- Search Area ---
        self.search_entry = PlaceholderEntry(self, placeholder="Search Product", bd=0, bg="#FFFFFF",
                                             highlightthickness=1, relief="solid",
                                             highlightcolor="#000000", highlightbackground="#808080")
        self.search_entry.place(x=289.0, y=97.0, width=165.0, height=27.0)
        self.search_entry.bind("<Return>", self.search_products)

        self.create_rounded_button(472.0, 97.0, 71.0, 29.0, "Search", self.search_products, fill="#000000",
                                   text_color="#FFFFFF")

        # --- Table Area ---
        self.canvas.create_text(270.0, 179.0, anchor="nw", text="Current Stock", fill="#000000",
                                font=("Inter Bold", 16 * -1))

        tree_frame = Frame(self)
        tree_frame.place(x=271.0, y=208.0, width=333.0, height=250.0)

        columns = ('id', 'product_name', 'quantity', 'price')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        self.tree.heading('id', text='ID')
        self.tree.heading('product_name', text='Product Name')
        self.tree.heading('quantity', text='Stock')
        self.tree.heading('price', text='Price (₱)')

        self.tree.column('id', width=40, anchor='center')
        self.tree.column('product_name', width=130, anchor='w')
        self.tree.column('quantity', width=60, anchor='center')
        self.tree.column('price', width=80, anchor='e')

        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Inter Bold', 10))
        style.configure("Treeview", font=('Inter', 10), rowheight=25)
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # --- Manage Product Form ---
        self.canvas.create_text(639.0, 213.0, anchor="nw", text="Manage Product", fill="#000000",
                                font=("Inter Bold", 16 * -1))
        self.canvas.create_text(631.0, 246.0, anchor="nw", text="Product Name:", fill="#000000",
                                font=("Inter Bold", 12 * -1))
        self.entry_product_name = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, relief="solid", highlightbackground="#808080", highlightcolor="#000000")
        self.entry_product_name.place(x=721.0, y=243.0, width=108.0, height=21.0)

        self.canvas.create_text(633.0, 273.0, anchor="nw", text="Quantity:", fill="#000000",
                                font=("Inter Bold", 12 * -1))
        self.entry_quantity = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, relief="solid", highlightbackground="#808080", highlightcolor="#000000")
        self.entry_quantity.place(x=721.0, y=270.0, width=108.0, height=21.0)

        self.canvas.create_text(633.0, 300.0, anchor="nw", text="Price (₱):", fill="#000000",
                                font=("Inter Bold", 12 * -1))
        self.entry_price = Entry(self, bd=0, bg="#FFFFFF", highlightthickness=1, relief="solid", highlightbackground="#808080", highlightcolor="#000000")
        self.entry_price.place(x=721.0, y=297.0, width=108.0, height=21.0)

        # --- Form Buttons (MODIFIED: Removed "New", shifted others left) ---
        self.create_rounded_button(655.0, 333.0, 60.0, 25.0, "Delete", self.delete_product, fill="#DC3545",
                                   text_color="#FFFFFF")
        self.create_rounded_button(720.0, 333.0, 69.0, 25.0, "Save", self.save_product, fill="#28A745",
                                   text_color="#FFFFFF")
        # --- END MODIFICATION ---

        self.load_products()

    def create_rounded_menu_button(self, x, y, w, h, text, command):
        """Creates a sidebar menu button."""
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1,
                               tags=f"btn_{text}_rect")
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, anchor="center", fill="#000000",
                                      font=("Inter Bold", 16 * -1), tags=f"btn_{text}_txt")
        button_tag = f"button_{text.replace(' ', '_').lower()}"

        def on_click(event):
            if command: command()

        def on_hover(event):
            self.canvas.itemconfig(rect, fill="#F0F0F0")
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="hand2")

        def on_leave(event):
            self.canvas.itemconfig(rect, fill="#FFFFFF")
            self.canvas.tag_raise(txt, rect)
            self.config(cursor="")

        self.canvas.addtag_withtag(button_tag, rect)
        self.canvas.addtag_withtag(button_tag, txt)
        self.canvas.tag_bind(button_tag, "<Button-1>", on_click)
        self.canvas.tag_bind(button_tag, "<Enter>", on_hover)
        self.canvas.tag_bind(button_tag, "<Leave>", on_leave)

    def create_rounded_button(self, x, y, w, h, text, command, fill, text_color):
        """Creates a generic rounded action button."""
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill=fill, outline="")
        txt = self.canvas.create_text(x + w / 2, y + h / 2, text=text, font=("Inter Bold", 10), fill=text_color)

        try:
            r_hex, g_hex, b_hex = fill[1:3], fill[3:5], fill[5:7]
            r, g, b = int(r_hex, 16), int(g_hex, 16), int(b_hex, 16)
            hover_r, hover_g, hover_b = max(0, r - 30), max(0, g - 30), max(0, b - 30)
            hover_fill = f'#{hover_r:02x}{hover_g:02x}{hover_b:02x}'
        except Exception:
            hover_fill = "#333333"

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

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT product_id, product_name, quantity, price FROM products ORDER BY product_id ASC")
            products = cursor.fetchall()
            for product in products:
                price_str = f"{product.get('price', 0.00):.2f}"
                self.tree.insert('', 'end', values=(
                    product.get('product_id'), product.get('product_name'),
                    product.get('quantity'), price_str
                ))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to load products:\n{err}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def on_row_select(self, event):
        try:
            selected_item = self.tree.focus()
            if not selected_item: return
            item_values = self.tree.item(selected_item, 'values')
            if not item_values: return
            self.selected_product_id = item_values[0]
            self.entry_product_name.delete(0, 'end')
            self.entry_product_name.insert(0, item_values[1])
            self.entry_quantity.delete(0, 'end')
            self.entry_quantity.insert(0, item_values[2])
            self.entry_price.delete(0, 'end')
            self.entry_price.insert(0, item_values[3])
        except (IndexError, TypeError):
            print("Error selecting row, values might be empty.")
            self.clear_form()

    def clear_form(self):
        self.entry_product_name.delete(0, 'end')
        self.entry_quantity.delete(0, 'end')
        self.entry_price.delete(0, 'end')
        self.selected_product_id = None
        selected_item = self.tree.focus()
        if selected_item:
            self.tree.selection_remove(selected_item)

    def save_product(self):
        product_name = self.entry_product_name.get().strip()
        quantity_str = self.entry_quantity.get().strip()
        price_str = self.entry_price.get().strip()

        if not product_name:
            messagebox.showwarning("Input Error", "Product Name is required.", parent=self)
            return
        try:
            quantity = int(quantity_str)
            if quantity < 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Input Error", "Quantity must be a valid positive number.", parent=self)
            return
        try:
            price = Decimal(price_str)
            if price < 0: raise InvalidOperation
        except (InvalidOperation, TypeError):
            messagebox.showwarning("Input Error", "Price must be a valid positive number (e.g., 150.00).", parent=self)
            return

        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()
            if self.selected_product_id:
                query = "UPDATE products SET product_name = %s, quantity = %s, price = %s WHERE product_id = %s"
                cursor.execute(query, (product_name, quantity, price, self.selected_product_id))
                action = "updated"
            else:
                query = "INSERT INTO products (product_name, quantity, price) VALUES (%s, %s, %s)"
                cursor.execute(query, (product_name, quantity, price))
                action = "added"
            conn.commit()
            messagebox.showinfo("Success", f"Product successfully {action}!", parent=self)
            self.load_products()
            self.clear_form()
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to save product:\n{err}", parent=self)
            if conn: conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            if conn: conn.rollback()
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def delete_product(self):
        if not self.selected_product_id:
            messagebox.showwarning("No Selection", "Please select a product from the list to delete.", parent=self)
            return
        if not messagebox.askyesno("Confirm Delete",
                                   f"Are you sure you want to permanently delete product ID #{self.selected_product_id}?",
                                   parent=self):
            return
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE product_id = %s", (self.selected_product_id,))
            conn.commit()
            messagebox.showinfo("Success", "Product deleted successfully.", parent=self)
            self.load_products()
            self.clear_form()
        except mysql.connector.Error as err:
            if err.errno == 1451:
                messagebox.showerror("Delete Error", "Cannot delete this product.\nIt is referenced by other records.",
                                     parent=self)
            else:
                messagebox.showerror("Database Error", f"Failed to delete product:\n{err}", parent=self)
            if conn: conn.rollback()
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
            if conn: conn.rollback()
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def search_products(self, event=None):
        search_term = self.search_entry.get().strip()
        if not search_term or search_term == "Search Product":
            self.load_products()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = None
        cursor = None
        try:
            conn = get_db_connection()
            if not conn: return
            cursor = conn.cursor(dictionary=True)
            query = "SELECT product_id, product_name, quantity, price FROM products WHERE product_name LIKE %s OR product_id = %s ORDER BY product_id ASC"
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_term))
            products = cursor.fetchall()
            if not products:
                self.tree.insert('', 'end', values=("", "No results found...", "", ""))
                return
            for product in products:
                price_str = f"{product.get('price', 0.00):.2f}"
                self.tree.insert('', 'end', values=(
                    product.get('product_id'), product.get('product_name'),
                    product.get('quantity'), price_str
                ))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to search products:\n{err}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{e}", parent=self)
        finally:
            if cursor: cursor.close()
            if conn and conn.is_connected(): conn.close()

    def open_admin_user(self):
        self.controller.show_admin_user()

    def open_admin_print(self):
        self.controller.show_admin_print()

    def open_admin_dashboard(self):
        self.controller.show_admin_dashboard()

    def open_admin_notification(self):
        self.controller.show_admin_notification()

    def open_admin_report(self):
        self.controller.show_admin_report()

    def logout(self):
        if messagebox.askokcancel("Logout", "Are you sure?", parent=self):
            self.controller.show_login_frame()