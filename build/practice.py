import tkinter as tk

class RadioTile(tk.Frame):
    def __init__(self, master, text, variable, value, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable
        self.value = value
        self.text = text

        self.button = tk.Button(
            self,
            text=self.text,
            relief="ridge",
            width=15,
            height=3,
            bg="#f0f0f0",
            font=("Segoe UI", 12, "bold"),
            command=self.select_tile
        )
        self.button.pack(fill="both", expand=True)
        self.update_style()

    def select_tile(self):
        self.variable.set(self.value)
        for sibling in self.master.winfo_children():
            if isinstance(sibling, RadioTile):
                sibling.update_style()

    def update_style(self):
        if self.variable.get() == self.value:
            # Selected state → black background, white text
            self.button.config(bg="black", fg="white", relief="sunken")
        else:
            # Unselected state → light gray background, black text
            self.button.config(bg="#f0f0f0", fg="black", relief="ridge")

# --- Example usage ---
root = tk.Tk()
root.title("Select Role")
root.geometry("300x200")

selected_role = tk.StringVar(value="")

admin_tile = RadioTile(root, "Admin", selected_role, "Admin")
admin_tile.grid(row=0, column=0, padx=20, pady=20)

user_tile = RadioTile(root, "User", selected_role, "User")
user_tile.grid(row=0, column=1, padx=20, pady=20)

# Label to show selected role
tk.Label(
    root,
    textvariable=selected_role,
    font=("Segoe UI", 11)
).grid(row=1, column=0, columnspan=2, pady=10)

root.mainloop()
