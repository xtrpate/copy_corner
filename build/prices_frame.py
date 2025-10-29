from pathlib import Path
from tkinter import Canvas, Button, PhotoImage, messagebox
import tkinter as tk

from printer_frame import PrinterFrame

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

# --- MAIN PRICES FRAME CLASS ---
class PricesFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # --- Resize window for this specific frame ---
        controller.geometry("829x504") # Slightly smaller than default

        canvas = Canvas(
            self, bg="#FFFFFF", height=504, width=829,
            bd=0, highlightthickness=0, relief="ridge"
        )
        canvas.place(x=0, y=0)
        self.canvas = canvas

        # --- Load Assets ---
        # Store images on self to prevent garbage collection
        try:
            self.image_image_1 = PhotoImage(file=relative_to_assets("image_6.png"))
            self.image_image_2 = PhotoImage(file=relative_to_assets("image_7.png"))
            self.image_image_3 = PhotoImage(file=relative_to_assets("image_8.png"))
            self.image_image_4 = PhotoImage(file=relative_to_assets("image_9.png"))
            self.image_image_5 = PhotoImage(file=relative_to_assets("image_10.png"))
            self.image_image_6 = PhotoImage(file=relative_to_assets("image_11.png"))
            self.button_image_1 = PhotoImage(file=relative_to_assets("button_8.png"))
        except tk.TclError as e:
            messagebox.showerror("Asset Error", f"Could not load assets for PricesFrame:\n{e}")
            return

        # --- UI Elements ---
        canvas.create_rectangle(0.0, 0.0, 829.0, 504.0, fill="#FFFFFF", outline="")
        canvas.create_rectangle(0.0, 1.0, 829.0, 74.0, fill="#000000", outline="")

        canvas.create_image(512.0, 428.0, image=self.image_image_1)
        canvas.create_image(648.0, 431.0, image=self.image_image_2)

        canvas.create_text(38.0, 81.0, anchor="nw", text="TEXT WITH PICTURE", fill="#FF9400", font=("Inter Bold", -32))
        canvas.create_text(498.0, 81.0, anchor="nw", text="EXAMPLE", fill="#FF9400", font=("Inter Bold", -32))
        canvas.create_text(29.0, 23.0, anchor="nw", text="Docs Printing Price list:", fill="#FFFFFF", font=("Inter Bold", -32))

        canvas.create_text(71.0, 128.0, anchor="nw", text="Black & White:", fill="#000000", font=("Inter Bold", -20))
        canvas.create_text(71.0, 248.0, anchor="nw", text="Partially Colored:", fill="#000000", font=("Inter Bold", -20))
        canvas.create_text(71.0, 372.0, anchor="nw", text="Full Colored:", fill="#000000", font=("Inter Bold", -20))

        # Price rows
        canvas.create_text(87.0, 162.0, anchor="nw", text="Short Size                ₱3.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(87.0, 187.0, anchor="nw", text="A4 Size                     ₱3.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(87.0, 212.0, anchor="nw", text="Long Size                 ₱3.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(86.0, 282.0, anchor="nw", text="Short Size                ₱7.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(86.0, 306.0, anchor="nw", text="A4  Size                     ₱7.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(86.0, 332.0, anchor="nw", text="Long  Size                 ₱8.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(88.0, 402.0, anchor="nw", text="Short Size                ₱10.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(88.0, 425.0, anchor="nw", text="A4  Size                     ₱10.00/per page", fill="#000000", font=("Inter Bold", -14))
        canvas.create_text(88.0, 448.0, anchor="nw", text="Long  Size                 ₱15.00/per page", fill="#000000", font=("Inter Bold", -14))

        # Example pictures
        canvas.create_image(512.0, 197.0, image=self.image_image_3)
        canvas.create_image(512.0, 314.0, image=self.image_image_4)
        canvas.create_image(649.0, 201.0, image=self.image_image_5)
        canvas.create_image(649.0, 316.0, image=self.image_image_6)

        # --- Back Button ---
        button_1 = Button(
            self, image=self.button_image_1, borderwidth=0, highlightthickness=0,
            command=self.go_back, relief="flat", text="Back", compound="center",
            fg="#FFFFFF", bg="#000000", activeforeground="#FFFFFF", activebackground="#333333",
            font=("Inter Bold", 14)
        )
        button_1.place(x=726.0, y=446.0, width=71.0, height=31.0)

    def go_back(self):
        """Resizes window and goes back to the main Printer frame."""
        # Reset window size to default
        self.controller.center_window(self.controller.default_width, self.controller.default_height)
        # Show the printer frame
        self.controller.show_frame(PrinterFrame)