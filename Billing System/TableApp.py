import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error


def center_window(window, w=0, h=0):
    # Calculate the position to center the window
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()   
    x = (screen_width // 2) - (w // 2)
    y = (screen_height // 2) - (h // 2)
    window.geometry(f'{w}x{h}+{x}+{y}')

class TableMapApp:
    def __init__(self, root, role):
        self.role = role
        self.root = root
        self.root.title("Table Map")
        self.root.state('zoomed')
        self.root.resizable(True, True)
        self.drag_enabled = False
        self.tables = {}
        self.create_layout()
        self.load_tables_from_json()
        self.update_table_map()
        self.create_menu()

    def create_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="View Orders", command=self.sub_view_item)
        self.context_menu.add_command(label="Delete Table", command=self.delete_selected_table)

    def show_sub_context_menu(self, event):
        # Select the item under the mouse
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
        else:
            self.tree.selection_remove(self.tree.selection())

    def sub_view_item(self):
        pass


    def create_layout(self):
        self.root.configure(bg="white")
        self.top_frame = tk.Frame(self.root, height=50, bg="lightgray")
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
        
        self.table_frame = tk.Frame(self.root, bg="lightgray")
        self.table_frame.grid(row=1, column=0, sticky="nsew")
        
        self.editor_frame = tk.Frame(self.root, bg="lightgray")
        self.editor_frame.grid(row=1, column=1, sticky="nsew")
        
        self.root.grid_columnconfigure(0, weight=9)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=5)
        
        self.create_functional_buttons()
        self.create_table_editor()

    def create_functional_buttons(self):
        button_style = ttk.Style()
        button_style.configure("TButton", padding=5)
        ttk.Button(self.top_frame, text="Toggle Drag & Drop", command=self.toggle_drag_and_drop).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_frame, text="Add Table", command=self.add_table).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_frame, text="Next Customer", command=self.next_customer).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(self.top_frame, text="Help", command=self.show_help_message).pack(side=tk.LEFT, padx=5, pady=5)


    def load_tables_from_json(self):
        filename = 'Json/table_data.json'
        if filename:
            with open(filename, "r") as file:
                self.tables = json.load(file)
            self.update_table_map()
            self.update_table_editor()

    def save_tables_to_json(self):
        filename = 'Json/table_data.json'
        with open(filename, "w") as file:
            json.dump(self.tables, file, indent=4)


    def create_table_editor(self):
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10, "italic", "bold"))
        self.tree = ttk.Treeview(self.editor_frame, columns=("Table", "Status", "Remark"), show="headings", style="Treeview")
        self.tree.heading("Table", text="Table")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Remark", text="Remark")
        self.tree.column("Table", width=80, minwidth=50, stretch=tk.YES)
        self.tree.column("Status", width=100, minwidth=90, stretch=tk.YES)
        self.tree.column("Remark", width=250, minwidth=100, stretch=tk.YES)
        self.tree.pack(fill=tk.Y, expand=True, padx=5, pady=10)
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_sub_context_menu)
        self.tree.pack(pady=20)
        self.update_table_editor()

    def update_table_editor(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for table_id, table_info in self.tables.items():
            self.tree.insert("", "end", values=(table_id, table_info["status"], table_info.get("remark", "")))

    def on_double_click(self, event):
        if hasattr(self, 'edit_window') and self.edit_window.winfo_exists():
            self.edit_window.lift()  
            return
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        self.edit_window = tk.Toplevel(self.root)
        center_window(self.edit_window, w=500, h=500)
        edit_window = self.edit_window
        edit_window.title("Edit Table")
        
        ttk.Label(edit_window, text="Table:").grid(row=0, column=0, padx=10, pady=10)
        table_entry = ttk.Label(edit_window, text=values[0].capitalize())
        table_entry.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(edit_window, text="Status:").grid(row=1, column=0, padx=10, pady=10)
        status_var = tk.StringVar(value=values[1])
        status_frame = ttk.Frame(edit_window)
        status_frame.grid(row=1, column=1, padx=10, pady=10)
        ttk.Radiobutton(status_frame, text="Available", variable=status_var, value="Available").pack(side=tk.LEFT)
        ttk.Radiobutton(status_frame, text="Unavailable", variable=status_var, value="Unavailable").pack(side=tk.LEFT)
        ttk.Radiobutton(status_frame, text="Reservation", variable=status_var, value="Reservation").pack(side=tk.LEFT)
        ttk.Radiobutton(status_frame, text="Occupied", variable=status_var, value="Occupied").pack(side=tk.LEFT)
        
        ttk.Label(edit_window, text="Remark:").grid(row=2, column=0, padx=10, pady=10)
        remark_entry = ttk.Entry(edit_window)
        remark_entry.grid(row=2, column=1, padx=10, pady=10)
        remark_entry.insert(0, values[2] if len(values) > 2 else "")
        
        ttk.Button(edit_window, text="Save", command=lambda: self.save_changes(item, values[0], status_var.get(), remark_entry.get())).grid(row=3, column=0, columnspan=2, pady=10)


    def save_changes(self, item, table, status, remark):
        if not table or not status:
            return
        self.tree.item(item, values=(table, status, remark))
        table_id = table
        self.tables[table_id]["status"] = status
        self.tables[table_id]["remark"] = remark
        self.update_table_map()
        self.save_tables_to_json()
        self.edit_window.destroy()

    def add_table(self):
        table_id = len(self.tables) + 1
        self.tables[f"table{table_id}"] = {"id": table_id, "status": "Available", "x": 50 + (table_id % 5) * 100, "y": 50 + (table_id // 5) * 100, "remark": ""}
        self.update_table_map()
        self.update_table_editor()
        self.save_tables_to_json()

    def delete_selected_table(self):
        selected_items = self.tree.selection()
        if selected_items:
            for item in selected_items:
                values = self.tree.item(item, "values")
                table_id = values[0]
                if table_id in self.tables:
                    del self.tables[table_id]
                    self.tree.delete(item)
            self.update_table_map()
            self.save_tables_to_json()
        else:
            messagebox.showwarning("Delete Table", "No table selected to delete!")


    def update_table_map(self):
        if hasattr(self, 'canvas'):
            self.canvas.delete("all")
        else:
            self.canvas = tk.Canvas(self.table_frame, bg="#1c1c1c")  # Slightly off-black
            self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_grid()
        for table_id, table_info in self.tables.items():
            x, y = table_info["x"], table_info["y"]
            color = self.get_table_color(table_info["status"])
            table_button = self.canvas.create_rectangle(x, y, x+80, y+80, fill=color, outline="white", width=2, tags=table_id)
            self.canvas.create_text(x+40, y+40, text=f"Table {table_info['id']}", fill="white", tags=table_id)
            if self.drag_enabled:
                self.canvas.tag_bind(table_id, "<Button-1>", lambda event, table_id=table_id: self.start_drag(event, table_id))
            else:
                self.canvas.tag_bind(table_id, "<Double-1>", lambda event, table_id=table_id: self.open_order_system(table_id))
            
    def draw_grid(self):
        if self.drag_enabled:
            for i in range(0, self.root.winfo_width(), 100):
                self.canvas.create_line(i, 0, i, self.root.winfo_height(), fill="gray")
            for j in range(0, self.root.winfo_height(), 100):
                self.canvas.create_line(0, j, self.root.winfo_width(), j, fill="gray")
        else:
            self.canvas.delete("grid_line")

    def get_table_color(self, status):
        return {"Available": "green", "Unavailable": "dark slate gray", "Reservation": "orange", "Occupied": "gray"}.get(status, "gray")


    def start_drag(self, event, table_id):
        if not self.drag_enabled:
            return
        self.drag_data = {"x": event.x, "y": event.y, "table": table_id}
        self.canvas.bind("<Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drag)

    def do_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        table_id = self.drag_data["table"]
        self.canvas.move(table_id, dx, dy)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def stop_drag(self, event):
        table_id = self.drag_data["table"]
        x1, y1, x2, y2 = self.canvas.coords(table_id)
        self.tables[table_id]["x"] = x1
        self.tables[table_id]["y"] = y1
        self.canvas.unbind("<Motion>")
        self.canvas.unbind("<ButtonRelease-3>")
        self.save_tables_to_json()

    def toggle_drag_and_drop(self):
        self.drag_enabled = not self.drag_enabled
        if not self.drag_enabled:
            self.save_tables_to_json()
        self.update_table_map()


    def show_help_message(self):
        help_message = (
            "How to use Table Map:\n\n"
            "1. Toggle Drag & Drop: Enable or disable drag-and-drop to reposition tables.\n"
            "2. Add Table: Adds a new table to the map.\n"
            "3. Load/Save Tables: Load or save the current table layout.\n"
            "4. Delete Table: Delete the selected table from the map.\n"
            "5. Start Order: Click on a table to start an order for that table.\n"
            "6. Edit Table: Double-click on a table in the list to edit its status or remark.\n"
            "7. Next Customer: Use this button to clear a table and allow the next customer to be seated.\n"
        )
        messagebox.showinfo("Help", help_message)

    def next_customer(self):
        # Logic to allow the next customer to be seated (e.g., clear a table's status)
        available_tables = [tid for tid, tinfo in self.tables.items() if tinfo["status"] == "Available"]
        if available_tables:
            table_id = available_tables[0]
            self.tables[table_id]["status"] = "Occupied"  # Assuming you want to mark it as occupied
            self.update_table_map()
            self.update_table_editor()
            messagebox.showinfo("Next Customer", f"Table {table_id} is now occupied by the next customer.")
        else:
            messagebox.showinfo("Next Customer", "No available tables at the moment.")



"""
def train_wait_time_model():
    data = pd.DataFrame({   # Generate or load the data (placeholder example data)
        'status': np.random.choice(['Available', 'Unavailable', 'Reservation'], size=1000),
        'hour_of_day': np.random.randint(0, 24, size=1000),
        'day_of_week': np.random.randint(0, 7, size=1000),
        'customer_count': np.random.randint(1, 10, size=1000),
        'wait_time': np.random.randint(5, 30, size=1000)  # Placeholder for actual wait times
    })
    X = data[['status', 'hour_of_day', 'day_of_week', 'customer_count']]         # Preprocess the data
    y = data['wait_time']
    X = pd.get_dummies(X, columns=['status'], drop_first=True)      # Convert categorical 'status' to numerical values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)   # Split the data into training and testing sets
    model = RandomForestRegressor(n_estimators=100, random_state=42)    # Initialize the RandomForestRegressor model
    model.fit(X_train, y_train)  # Train the model
    y_pred = model.predict(X_test)  # Predict on the test set
    mse = mean_squared_error(y_test, y_pred)     # Evaluate the model
    print(f'Mean Squared Error: {mse}')
    return model    # Return the trained model
"""

"""
if __name__ == "__main__":
    root = tk.Tk()
    app = TableMapApp(root)
    root.mainloop()
"""



"""
Collect Real Data: Replace the placeholder data with real-world data from your application.
Hyperparameter Tuning: Experiment with different models and hyperparameters to improve accuracy.
Integration: Integrate the trained model into your application to predict wait times dynamically.
"""
