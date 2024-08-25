import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar

def load_receipts_by_date(date, folder='Receipts/Json'):
    receipts = []
    date_path = os.path.join(folder, date)
    if os.path.isdir(date_path):
        file_path = os.path.join(date_path, 'orders.json')
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                data = json.load(file)
                for receipt in data:
                    receipts.append({"Receipt ID": receipt["Receipt ID"], "Time": receipt["Time"], "order": receipt["order"]})
    return receipts

def show_receipt_details(receipt):
    details_window = tk.Toplevel()
    details_window.title("Receipt Details")

    tree = ttk.Treeview(details_window, columns=("Item", "Price", "Quantity"), show='headings')
    tree.heading("Item", text="Item")
    tree.heading("Price", text="Price")
    tree.heading("Quantity", text="Quantity")

    for order in receipt:
        for item, details in order.items():
            tree.insert("", "end", values=(item, details['price'], details['quantity']))

    tree.pack(fill=tk.BOTH, expand=True)

    button_frame = tk.Frame(details_window)
    button_frame.pack(fill=tk.X, pady=10)

    load_button = tk.Button(button_frame, text="Load", command=lambda: load_receipt(receipt))
    load_button.pack(side=tk.LEFT, padx=10)

    close_button = tk.Button(button_frame, text="Close", command=details_window.destroy)
    close_button.pack(side=tk.RIGHT, padx=10)

def load_receipt(receipt):
    # Implement the logic to load the selected receipt
    messagebox.showinfo("Load Receipt", "Receipt loaded successfully!")

def show_receipts_for_date(date, root):
    root.destroy()  # Destroy the root window when a date is selected
    receipts = load_receipts_by_date(date)
    
    if not receipts:
        messagebox.showinfo("No Receipts", "No receipts found for the selected date.")
        return

    receipts_window = tk.Toplevel()
    receipts_window.title(f"Receipts for {date}")

    tree = ttk.Treeview(receipts_window, columns=("Receipt ID", "Time"), show='headings')
    tree.heading("Receipt ID", text="Receipt ID")
    tree.heading("Time", text="Time")

    for receipt in receipts:
        tree.insert("", "end", values=(receipt["Receipt ID"], receipt["Time"]))

    tree.pack(fill=tk.BOTH, expand=True)

    tree.bind("<Double-1>", lambda event: show_receipt_details(receipts[int(tree.selection()[0])]["order"]))

    back_button = tk.Button(receipts_window, text="Back", command=receipts_window.destroy)
    back_button.pack(pady=10)

def show_historical_receipt_screen():
    root = tk.Tk()
    root.title("Select Date")

    cal = Calendar(root, selectmode='day', date_pattern='yyyyMMdd')
    cal.pack(pady=20)

    select_button = tk.Button(root, text="Select Date", command=lambda: show_receipts_for_date(cal.get_date(), root))
    select_button.pack(pady=10)

    root.mainloop()

# Example usage
show_historical_receipt_screen()
