from pathlib import Path
import tkinter as tk
from tkinter import Canvas, Button, PhotoImage, Label, messagebox, filedialog
import math
import sys
import subprocess
import shutil
import os  # <-- ADDED
from utils import get_db_connection, round_rectangle

# Import frame classes needed for navigation
from printer_frame import PrinterFrame
from user_frame import UserFrame
from prices_frame import PricesFrame

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame2"


# --- NEW HELPER FUNCTION ---
def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Not running in a bundle, use the script's directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def relative_to_assets(path: str) -> Path:
    # This function is now only for this frame's *image* assets
    asset_file = ASSETS_PATH / Path(path)
    if not asset_file.is_file():
        print(f"Warning: Asset not found at {asset_file}")
    return asset_file


# --------- Rounded border helper ----------
def rounded_box(cnv, x1, y1, x2, y2, r=12, fill="#FFFFFF", outline="#000000", width=1):
    r = max(0, min(int(r), int(min(x2 - x1, y2 - y1) / 2)))
    pts = []

    def arc(cx, cy, a0, a1, step=6):
        step = step if a1 >= a0 else -step
        for a in range(a0, a1 + step, step):
            rad = math.radians(a)
            pts.extend([cx + r * math.cos(rad), cy + r * math.sin(rad)])

    pts += [x1 + r, y1, x2 - r, y1];
    arc(x2 - r, y1 + r, 270, 360)
    pts += [x2, y2 - r];
    arc(x2 - r, y2 - r, 0, 90)
    pts += [x1 + r, y2];
    arc(x1 + r, y2 - r, 90, 180)
    pts += [x1, y1 + r];
    arc(x1 + r, y1 + r, 180, 270)
    return cnv.create_polygon(pts, smooth=True, fill=fill, outline=outline, width=width)


# --- MAIN HELP FRAME CLASS ---
class HelpFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        controller.center_window(controller.default_width, controller.default_height)

        FONT_BTN_SM = ("Inter Bold", -13)
        FONT_BTN_MED = ("Inter Bold", -15)
        WHITE = "#FFFFFF"
        BLACK = "#000000"

        canvas = Canvas(
            self, bg="#FFF6F6", height=540, width=871,
            bd=0, highlightthickness=0, relief="ridge"
        )
        canvas.place(x=0, y=0)
        self.canvas = canvas

        try:
            self.image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
            self.image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
            self.image_image_4 = PhotoImage(file=relative_to_assets("image_4.png"))
            self.button_image_7 = PhotoImage(file=relative_to_assets("button_7.png"))
            self.button_image_8 = PhotoImage(file=relative_to_assets("button_8.png"))
            self.icon_edit = PhotoImage(file=relative_to_assets("account.png"))
            self.icon_pr = PhotoImage(file=relative_to_assets("image_6.png"))
            self.icon_bell = PhotoImage(file=relative_to_assets("image_8.png"))
            self.icon_sheet = PhotoImage(file=relative_to_assets("image_7.png"))
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not load assets for HelpFrame:\n{e}")
            return

        # ======= OUTER CONTAINER + HEADER =======
        rounded_box(canvas, 22.0, 16.0, 837.0, 518.0, r=0, fill=WHITE, outline=BLACK, width=2)
        rounded_box(canvas, 22.0, 16.0, 837.0, 101.0, r=0, fill=BLACK, outline=BLACK, width=2)
        canvas.create_text((22 + 837) / 2, (16 + 101) / 2, text="Help", fill=WHITE, font=("Inter Bold", -40),
                           anchor="center")
        canvas.create_rectangle(239.0, 16.0, 240.0, 518.0, fill=BLACK, outline="")

        # ======= CARDS (Adjust Y slightly if needed) =======
        card_y_offset = -7
        rounded_box(canvas, 250.0, 118.0 + card_y_offset, 553.0, 283.0 + card_y_offset, r=14, fill=WHITE, outline=BLACK,
                    width=1)  # FAQ
        rounded_box(canvas, 563.0, 118.0 + card_y_offset, 790.0, 256.0 + card_y_offset, r=14, fill=WHITE, outline=BLACK,
                    width=1)  # Contact
        rounded_box(canvas, 250.0, 293.0 + card_y_offset, 553.0, 458.0 + card_y_offset, r=14, fill=WHITE, outline=BLACK,
                    width=1)  # User Guide
        rounded_box(canvas, 567.0, 270.0 + card_y_offset, 833.0, 499.0 + card_y_offset, r=14, fill=WHITE, outline=BLACK,
                    width=1)  # About

        # ======= TEXT/ICONS INSIDE CARDS (Adjust Y slightly) =======
        text_y_offset = card_y_offset
        canvas.create_text(605.0, 153.0 + text_y_offset, anchor="nw", text="copycorner56@gmail.com", fill=BLACK,
                           font=("Inter Bold", -13))
        canvas.create_image(590.0, 163.0 + text_y_offset, image=self.image_image_3)
        canvas.create_image(589.0, 185.0 + text_y_offset, image=self.image_image_4)
        canvas.create_text(580.0, 129.0 + text_y_offset, anchor="nw", text="Contact Support", fill=BLACK,
                           font=("Inter Bold", -16))
        canvas.create_text(289.0, 129.0 + text_y_offset, anchor="nw", text="Frequency Asked Questions", fill=BLACK,
                           font=("Inter Bold", -16))
        canvas.create_text(607.0, 176.0 + text_y_offset, anchor="nw", text="09531948289", fill=BLACK,
                           font=("Inter Bold", -13))
        canvas.create_text(263.0, 156.0 + text_y_offset, anchor="nw", text="•How to create a print job?", fill=BLACK,
                           font=("Inter Bold", -14))
        canvas.create_text(263.0, 178.0 + text_y_offset, anchor="nw", text="•How to view my  past print jobs?",
                           fill=BLACK, font=("Inter Bold", -14))
        canvas.create_text(263.0, 201.0 + text_y_offset, anchor="nw", text="•How to know the price of printing?",
                           fill=BLACK, font=("Inter Bold", -14))
        canvas.create_text(263.0, 223.0 + text_y_offset, anchor="nw", text="•How can i edit my profile Information?",
                           fill=BLACK, font=("Inter Bold", -14))
        canvas.create_text(263.0, 245.0 + text_y_offset, anchor="nw", text="•Who can access  the admin features?",
                           fill=BLACK, font=("Inter Bold", -14))
        canvas.create_text(310.0, 310.0 + text_y_offset, anchor="nw", text="User Guide/Quick Start", fill=BLACK,
                           font=("Inter Bold", -16))
        canvas.create_image(399.0, 350.0 + text_y_offset, image=self.image_image_2)
        canvas.create_text(578.0, 380.0 + text_y_offset, anchor="nw", text="Johnnnnyyyy Sisisins", fill=BLACK,
                           font=("Inter Bold", -16))
        canvas.create_text(580.0, 310.0 + text_y_offset, anchor="nw", text="Copy Corner Printing & \nInventory System",
                           fill=BLACK, font=("Inter", -16))
        canvas.create_text(580.0, 283.0 + text_y_offset, anchor="nw", text="About System", fill=BLACK,
                           font=("Inter Bold", -16))
        canvas.create_text(580.0, 356.0 + text_y_offset, anchor="nw", text="Version 1.0", fill=BLACK,
                           font=("Inter", -16))
        canvas.create_text(580.0, 402.0 + text_y_offset, anchor="nw",
                           text=("A simple system to manage  \nprinting jobs, customers and\n"
                                 " inventory for copy corner,\n Includes sales and stock ."), fill=BLACK,
                           font=("Inter", -16))

        # --- Left Menu Buttons (Adjust Y slightly) ---
        menu_y_offset = -7
        self.create_rounded_menu_button(46, 129 + menu_y_offset, 161, 38, "Profile", self.open_user_py)
        self.create_rounded_menu_button(46, 178 + menu_y_offset, 161, 38, "Print Request", self.open_printer_py)
        self.create_rounded_menu_button(46, 227 + menu_y_offset, 161, 38, "Pricelist", self.open_prices_py)
        self.create_rounded_menu_button(46, 276 + menu_y_offset, 161, 38, "Notification", self.open_notification_py)

        # --- Other Buttons (Adjust Y slightly) ---
        button_7 = Button(self, image=self.button_image_7, borderwidth=0, highlightthickness=0,
                          command=lambda: print("Report a Problem clicked"), relief="flat")
        button_7.place(x=590.0, y=209.0 + card_y_offset, width=165.0, height=33.0)
        button_7.configure(text="Report a Problem", compound="center", fg=WHITE, font=FONT_BTN_SM)

        button_8 = Button(self, image=self.button_image_8, borderwidth=0, highlightthickness=0,
                          command=self.download_user_manual, relief="flat")  # <-- UPDATED
        button_8.place(x=289.0, y=367.0 + card_y_offset, width=221.0, height=64.0)
        button_8.configure(text="View Full User Manual(PDF)", compound="center", fg=WHITE, font=FONT_BTN_MED)

        # ======= LEFT ICONS AS LABELS (Adjust Y slightly) =======
        icon_y_offset = menu_y_offset
        lbl_edit = Label(self, image=self.icon_edit, bg=WHITE, bd=0)
        lbl_pr = Label(self, image=self.icon_pr, bg=WHITE, bd=0)
        lbl_bell = Label(self, image=self.icon_bell, bg=WHITE, bd=0)
        lbl_sheet = Label(self, image=self.icon_sheet, bg=WHITE, bd=0)
        lbl_edit.place(x=64.0, y=148.0 + icon_y_offset, anchor="center")
        lbl_pr.place(x=64.0, y=198.0 + icon_y_offset, anchor="center")
        lbl_bell.place(x=64.0, y=248.0 + icon_y_offset, anchor="center")
        lbl_sheet.place(x=64.0, y=298.0 + icon_y_offset, anchor="center")
        self.make_icon_clickable(lbl_edit, self.open_user_py)
        self.make_icon_clickable(lbl_pr, self.open_printer_py)
        self.make_icon_clickable(lbl_sheet, self.open_prices_py)
        self.make_icon_clickable(lbl_bell, self.open_notification_py)

    # --- Reusable Rounded Menu Button Method ---
    def create_rounded_menu_button(self, x, y, w, h, text, command=None):
        rect = round_rectangle(self.canvas, x, y, x + w, y + h, r=10, fill="#FFFFFF", outline="#000000", width=1)
        txt = self.canvas.create_text(x + 35, y + (h / 2), text=text, anchor="w", fill="#000000",
                                      font=("Inter Bold", 15))

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

    def make_icon_clickable(self, widget, command):
        widget.bind("<Button-1>", lambda e: command())
        widget.bind("<Enter>", lambda e: self.config(cursor="hand2"))
        widget.bind("<Leave>", lambda e: self.config(cursor=""))

    # --- UPDATED FUNCTION for downloading the manual ---
    def download_user_manual(self):
        # 1. Define the relative path to the PDF (inside the 'assets' folder)
        relative_file_path = "assets/Help.pdf"

        # 2. Get the absolute, correct path (works for script or .exe)
        try:
            source_file = Path(get_resource_path(relative_file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Could not determine file path: {e}", parent=self)
            return

        # 3. Check if the source file actually exists
        if not source_file.is_file():
            messagebox.showerror("File Not Found",
                                 f"The user manual 'Help.pdf' could not be found.\n"
                                 f"Looked for: {source_file}",
                                 parent=self)
            return

        # 4. Open the "Save As" dialog
        save_path = filedialog.asksaveasfilename(
            initialfile="Help.pdf",
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            title="Save User Manual As..."
        )

        # 5. If the user selected a path (didn't cancel)
        if save_path:
            try:
                # 6. Copy the file from the source to the chosen destination
                shutil.copy2(source_file, save_path)
                messagebox.showinfo("Download Complete",
                                    f"User manual saved successfully to:\n{save_path}",
                                    parent=self)
            except Exception as e:
                messagebox.showerror("Copy Error",
                                     f"Failed to save the file. Error:\n{e}",
                                     parent=self)

    # --- Navigation Methods ---
    def open_user_py(self):
        self.controller.show_frame(UserFrame)

    def open_printer_py(self):
        self.controller.show_frame(PrinterFrame)

    def open_prices_py(self):
        self.controller.show_frame(PricesFrame)

    def open_notification_py(self):
        self.controller.show_notification_frame()