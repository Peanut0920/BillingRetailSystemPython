import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import pandas as pd
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
import os,logging
from sklearn.linear_model import LinearRegression
import numpy as np
from decimal import Decimal, ROUND_UP
import base64
from tkcalendar import Calendar
import locale,json,copy


# Constants for file paths
ITEMS_FILE = 'Excel/items.xlsx'
DAILY_SALES_FILE = 'Excel/daily_sales.xlsx'
USERS_FILE = 'Excel/users.xlsx'
FEEDBACK_FILE = 'Excel/feedback.xlsx'
SUPPLIER_FILE = 'Excel/suppliers.xlsx'
LANGUAGE_FILE = 'Json/language.json'

PIN_LENGTH = 4
global app
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Hash function for password
def hash_password(password, salt=None, iterations=100000):
    if salt is None:
        salt = os.urandom(16)  # Generate a random salt
    hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',                  # The hash digest algorithm
        password.encode(),         # Convert the password to bytes
        salt,                      # Provide the salt
        iterations                 # Number of iterations
    )
    # Encode the salt and hash for storage
    salt_b64 = base64.urlsafe_b64encode(salt).decode('utf-8')
    hash_b64 = base64.urlsafe_b64encode(hash_bytes).decode('utf-8')
    return f"{salt_b64}${hash_b64}"

def verify_password(stored_password, provided_password, iterations=100000):
    # Split the stored password into salt and hash
    salt_b64, stored_hash_b64 = stored_password.split('$')
    salt = base64.urlsafe_b64decode(salt_b64)
    # Hash the provided password with the stored salt
    new_hash_bytes = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode(),
        salt,
        iterations
    )
    new_hash_b64 = base64.urlsafe_b64encode(new_hash_bytes).decode('utf-8')
    # Compare the new hash with the stored hash
    return new_hash_b64 == stored_hash_b64

def center_window(window, w=0, h=0):
    # Calculate the position to center the window
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()   
    x = (screen_width // 2) - (w // 2)
    y = (screen_height // 2) - (h // 2)
    window.geometry(f'{w}x{h}+{x}+{y}')

def translate(text):
    # Read the JSON file
    with open(LANGUAGE_FILE, 'r', encoding='utf-8') as file:
        df = json.load(file)
    return df['expression'][df['language']['Select']][text]

def show_language_message():
        with open(LANGUAGE_FILE, 'r', encoding='utf-8') as file:
            df = json.load(file)
        if df['language']['Select'] == 'Chinese':
            messagebox.showinfo(translate("Language"), translate("Switched to Chinese"))
        elif df['language']['Select'] == 'English':
            messagebox.showinfo(translate("Language"), translate("Switched to English"))

class UserAuthentication:
    def __init__(self, root):
        self.root = root
        self.root.title(translate("UserAuthentication"))
        center_window(self.root, w=450, h=600)
        self.root.configure(bg='#d3d3d3')
        self.entered_pin = tk.StringVar()
        self.role = None

        # Create UI components
        self.pin_display = tk.Label(root, textvariable=self.entered_pin, font=("Helvetica", 24, 'bold'), bg="white", width=15, height=2)
        self.pin_display.pack(pady=10)

        # Create number pad
        self.create_number_pad()

        # Create login button
        tk.Button(root, text=translate("Login"), command=self.login, font=("Helvetica", 14, 'bold'), width=10, height=1).pack(pady=15)

        # Create clear button
        tk.Button(root, text=translate("Clear"), command=self.clear_pin, font=("Helvetica", 14, 'bold'), width=10, height=1).pack(pady=5)

        # Bind number keys to the number pad
        self.bind_number_keys()

        # Load users
        self.load_users()

    def create_number_pad(self):
        number_pad_frame = tk.Frame(self.root, bg='#d3d3d3')
        number_pad_frame.pack(pady=10)

        for i in range(3):
            for j in range(3):
                number = i * 3 + j + 1
                tk.Button(number_pad_frame, text=str(number), font=("Helvetica", 12, 'bold'), command=lambda num=number: self.append_pin(num),
                          width=8, height=3).grid(row=i, column=j, padx=5, pady=5)

        # Add the zero button at the bottom
        tk.Button(number_pad_frame, text="0", font=("Helvetica", 12, 'bold'), command=lambda: self.append_pin(0),
                  width=8, height=3).grid(row=3, column=1, padx=5, pady=5)

    def bind_number_keys(self):
        # Bind the number keys 0-9 to the append_pin function
        for number in range(10):
            self.root.bind(str(number), self.handle_keypress)

        # Bind Enter key to login
        self.root.bind('<Return>', lambda event: self.login())

        # Bind Backspace key to clear
        self.root.bind('<BackSpace>', lambda event: self.clear_pin())

    def handle_keypress(self, event):
        # Handle keypress events for number keys
        if event.char.isdigit():
            self.append_pin(int(event.char))

    def append_pin(self, num):
        # Add a digit to the PIN display if the max length is not exceeded
        if len(self.entered_pin.get()) < PIN_LENGTH:
            self.entered_pin.set(self.entered_pin.get() + str(num))
        if len(self.entered_pin.get()) == PIN_LENGTH:
            self.root.after(100, self.login)

    def clear_pin(self):
        # Clear the entered PIN
        self.entered_pin.set("")

    def load_users(self):
        try:
            self.users_df = pd.read_excel(USERS_FILE)
        except FileNotFoundError:
            # Create a default admin user with a PIN of "1234" if the file does not exist
            self.users_df = pd.DataFrame({
                'Username': ['admin'],
                'PIN': [hash_password('1234')],
                'Role': ['admin']
            })
            self.users_df.to_excel(USERS_FILE, index=False)
            messagebox.showinfo(translate("User Created"), translate("Default admin user created with PIN: 1234"))

    def login(self):
        entered_pin = self.entered_pin.get()

        # Check if the entered PIN matches any stored PIN
        user = self.users_df[self.users_df['PIN'].apply(lambda x: verify_password(x, entered_pin))]

        if not user.empty:
            self.role = user.iloc[0]['Username']
            self.root.destroy()  # Close login window
            main_table_app(self.role)
        else:
            messagebox.showerror(translate("Login Failed"), translate("Invalid PIN."))
        
        self.clear_pin()

    def refresh_root(self):
            main_table_app(self.role)

class AddItemDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(translate("Add New Item"))
        center_window(self, w=400, h=500)
        self.resizable(False, False)

        self.item_name = tk.StringVar()
        self.item_price = tk.DoubleVar()
        self.item_category = tk.StringVar()
        self.item_stock = tk.IntVar()
        self.item_cost = tk.DoubleVar()

        self.create_widgets()
        self.result = None

    def create_widgets(self):
        tk.Label(self, text=f"{translate('Item Name')}:").pack(pady=5)
        tk.Entry(self, textvariable=self.item_name).pack(pady=5)

        tk.Label(self, text=f"{translate('Item Price')}:").pack(pady=5)
        tk.Entry(self, textvariable=self.item_price).pack(pady=5)

        tk.Label(self, text=f"{translate('Item Category')}:").pack(pady=5)
        tk.Entry(self, textvariable=self.item_category).pack(pady=5)

        tk.Label(self, text=f"{translate('Item Stock')}:").pack(pady=5)
        tk.Entry(self, textvariable=self.item_stock).pack(pady=5)

        tk.Label(self, text=f"{translate('Item Cost')}:").pack(pady=5)
        tk.Entry(self, textvariable=self.item_cost).pack(pady=5)

        tk.Button(self, text=f"{translate('Add Item')}", command=self.on_submit).pack(pady=10)

    def on_submit(self):
        item_name = self.item_name.get().strip()
        item_price = float(self.item_price.get())
        item_category = self.item_category.get().strip()
        item_stock = self.item_stock.get()
        item_cost = self.item_cost.get()
        if item_name and item_price > 0 and item_category and item_stock >= 0:
            self.result = (item_name, item_price, item_category, item_stock,item_cost)
            self.destroy()
        else:
            messagebox.showerror(translate("Invalid Input"), translate("Please enter valid item details."))
            self.destroy()

class RetailBillingSystem:
    def __init__(self, root, role, table):
        self.root = root
        self.role = role
        self.table = table
        self.root.title(translate("Retail Billing System"))
        system_photo = tk.PhotoImage(file = "Photo/system_icon.png")
        self.root.iconphoto(False, system_photo, system_photo)
        self.root.iconbitmap('Photo/system_icon.png')
        self.root.state('zoomed')
        self.root.resizable(True, True)
        self.fullscreen = False
        self.root.attributes('-fullscreen', self.fullscreen)
        self.root.configure(bg='#D3D3D3')
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(2, weight=1)

        # Bind keyboard shortcuts
        self.root.bind('<Delete>', lambda event: self.delete_selected_item())
        self.root.bind('<Control-r>', lambda event: self.remark_selected_item())
        self.root.bind('<Control-p>', lambda event: self.change_price())
        self.root.bind('<Control-z>', lambda event: self.undo_last_action())
        self.root.bind('<Control-y>', lambda event: self.redo_last_action())

        # Bind keyboard numbers to toolbar buttons
        self.root.bind('1', lambda event: self.add_new_item())
        self.root.bind('2', lambda event: self.delete_selected_item())
        self.root.bind('3', lambda event: self.remark_selected_item())
        self.root.bind('4', lambda event: self.reset())
        self.root.bind('5', lambda event: self.show_payment_methods())
        self.root.bind('6', lambda event: self.show_daily_total())
        self.root.bind('7', lambda event: self.view_item_details())
        self.root.bind('8', lambda event: self.discount_screen())
        self.root.bind('9', lambda event: self.change_price())
        self.root.bind('0', lambda event: self.undo_last_action())
        self.root.bind('-', lambda event: self.redo_last_action())

        # Variables
        self.remarks = []
        self.orders = []
        self.last_item = None
        self.qty = 1
        self.position_index = 0
        self.total_cost = 0.0
        self.discount_rate = 0.0
        self.receipt_ID = self.get_last_table_id_from_json() if self.get_last_table_id_from_json() is not None else 1
        self.receipts = []
        self.undo_stack = []  # Stack to hold actions for undo functionality
        self.redo_stack = []  # Stack to hold actions for redo functionality]\
        self.load_before_continue()

        # Set language options
        with open(LANGUAGE_FILE, 'r', encoding='utf-8') as file:
            df = json.load(file)
        select = df['language']['Select']
        self.language = tk.StringVar(value=select)
        self.languages = {translate('English'): self.load_english, translate('Chinese'): self.load_chinese}

        self.setup_ui()
        self.auto_save()
        self.load_data_table_data()
        self.load_items_from_excel(ITEMS_FILE)
        self.update_receipt_listbox()

    def toggle_fullscreen(self, event=None, button = False):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        if self.fullscreen or button:
            self.fullscreen_mode.config(label="Exit Full-Screen")
        else:
            self.fullscreen_mode.config(label="Enter Full-Screen")

    def refresh_root(self):
        self.root.destroy()
        UserAuthentication.refresh_root(app)    

    def exit_app(self):
        if self.fullscreen:
            self.toggle_fullscreen(button=True)
            self.root.after(100, self.root.destroy)  # Delay to ensure fullscreen mode is exited
        else:
            self.root.destroy()

    def setup_ui(self):
        self.create_menu()
        self.create_title()
        self.create_datetime_label()
        self.create_toolbar()
        self.create_main_frames()

    def create_menu(self):
        menubar = tk.Menu(self.root, bg='#d9d9d9')
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("File"), menu=file_menu)
        file_menu.add_command(label=translate("Reset"), command=self.reset)
        file_menu.add_command(label=translate("Save Receipt"), command=self.save_receipt)
        file_menu.add_command(label=translate("Generate Reports"), command=self.generate_reports)
        file_menu.add_command(label=translate("Load Back Receipt"), command=self.show_historical_receipt_screen)
        file_menu.add_separator()
        self.fullscreen_mode = file_menu.add_command(label=translate("Fullscreen"), command=self.toggle_fullscreen)
        file_menu.add_command(label=translate("Exit"), command=self.exit_app)
        file_menu.add_command(label=("Back To Table App"), command=self.back_to_table_app)
        file_menu.add_command(label=translate("Back To Login"), command=lambda: login_out(self.root))

        # Manage menu
        manage_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("Manage"), menu=manage_menu)
        manage_menu.add_command(label=translate("Delete Items"), command=self.open_delete_screen)
        manage_menu.add_command(label=translate("Manage Inventory"), command=self.manage_inventory)
        manage_menu.add_separator()
        manage_menu.add_command(label=translate("Apply Dynamic Pricing"), command=self.apply_dynamic_pricing_ui)
        manage_menu.add_command(label=translate("Manage Promotions"), command=self.manage_promotions)
        manage_menu.add_separator()
        manage_menu.add_command(label=translate("Manage Suppliers"), command=self.manage_suppliers)
        manage_menu.add_command(label=translate("Checking Inventory"), command=self.check_inventory)
        if self.role == 'admin':
            manage_menu.add_command(label=translate("Manage Users"), command=self.manage_users)

        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("Reports"), menu=reports_menu)
        reports_menu.add_command(label=translate("Sales Report"), command=self.show_sales_report)
        reports_menu.add_command(label=translate("Item Popularity"), command=self.show_item_popularity)
        reports_menu.add_command(label=translate("Inventory Turnover"), command=self.show_inventory_turnover)
        reports_menu.add_separator()
        reports_menu.add_command(label=translate("Profit Analysis"), command=self.show_profit_analysis)
        reports_menu.add_command(label=translate("Show Financial Summary"), command=self.show_financial_summary)
        reports_menu.add_command(label=translate("Plot Turnover Rates"), command=self.plot_turnover_rates)
        reports_menu.add_command(label="Historical Receipt", command=self.show_historical_receipt_screen)
        reports_menu.add_separator()
        reports_menu.add_command(label=translate("Calculate Break Even Point"), command=self.break_even_point_ui)
        reports_menu.add_command(label=translate("Calculate Historical Sales"), command=self.calculate_historical_sales)
        reports_menu.add_command(label=translate("Compare Product Performance"), command=self.compare_product_performance)
        reports_menu.add_command(label=translate("Forecast Inventory"), command=self.forecast_inventory)

        # Language menu
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("Language"), menu=language_menu)
        for lang in self.languages:
            language_menu.add_radiobutton(label=lang, variable=self.language, command=self.set_language)

        # Help menu
        menubar.add_cascade(label=translate("Help"), command=self.show_help)

        # Feedback menu
        feedback_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=translate("Feedback"), menu=feedback_menu)
        feedback_menu.add_command(label=translate("Comment"), command=self.collect_feedback_ui)
        feedback_menu.add_command(label=translate("Rate"), command=self.rating_ui)

    def create_title(self):
        title_label = tk.Label(self.root, text=translate("Retail Billing System"), font=('Georgia', 24, 'italic', 'bold'), bg='#d3d3d3')
        title_label.grid(row=0, column=0, columnspan=2, pady=5, sticky="nsew")

    def create_datetime_label(self):
        df = pd.read_excel(USERS_FILE)
        self.subtitle_frame = tk.Frame(self.root, bg='#d3d3d3')
        self.subtitle_frame.grid(row=0, column=2, pady=5, sticky="nsew")
        self.subtitle_frame.columnconfigure(0, weight=1)

        self.datetime_label = tk.Label(self.subtitle_frame, text="", font=('Arial', 12), bg='#d3d3d3')
        self.datetime_label.grid(row=0, column=0, pady=5, sticky="nsew")
        self.update_datetime()

        role_value = df.loc[df['Username'] == self.role, 'Role'].str.strip().values[0]
        self.role_label = tk.Label(self.subtitle_frame, text=f"{role_value.capitalize()}: {self.role}", font=('Arial', 12), bg='#d3d3d3')
        self.role_label.grid(row=1, column=0, pady=5, sticky="nsew")
        image = tk.PhotoImage(file="Photo/exit_icon.png").subsample(9, 9)
        button = tk.Button(self.subtitle_frame, text="Exit To Table", font = ('Georgia', 10, 'italic', 'bold'), image=image, compound="top", command=self.back_to_table_app, bg='#FF0000')
        button.image = image
        button.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")
        
    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg='#D3D3D3')
        toolbar.grid(row=1, column=0, columnspan=3, sticky="nsew")

        # Create buttons with icons and tooltips
        self.create_toolbar_button(toolbar, "Add Item", "Photo/add_icon.png", self.add_new_item, row=0, column=0, shortcut="1")
        self.create_toolbar_button(toolbar, "Delete Item", "Photo/delete_icon.png", self.delete_selected_item, row=0, column=1, shortcut="2")
        self.create_toolbar_button(toolbar, "Remark Item", "Photo/remark_icon.png", self.remark_selected_item, row=0, column=2, shortcut="3")
        self.create_toolbar_button(toolbar, "Clear", "Photo/clear_icon.png", self.reset, row=0, column=3)
        self.create_toolbar_button(toolbar, "Payment", "Photo/payment_icon.png", self.show_payment_methods, row=0, column=4, shortcut="4")
        self.create_toolbar_button(toolbar, "Daily Total", "Photo/total_icon.png", self.show_daily_total, row=0, column=5, shortcut="5")
        self.create_toolbar_button(toolbar, "View Details", "Photo/details_icon.png", self.view_item_details, row=0, column=6, shortcut="6")
        self.create_toolbar_button(toolbar, "Discount", "Photo/discount_icon.png", self.discount_screen, row=0, column=7, shortcut="7")
        self.create_toolbar_button(toolbar, "Change Price", "Photo/changeprice_icon.png", self.change_price, row=0, column=8, shortcut="8")
        self.create_toolbar_button(toolbar, "Undo", "Photo/undo_icon.png", self.undo_last_action, row=0, column=9, shortcut="9")
        self.create_toolbar_button(toolbar, "Redo", "Photo/redo_icon.png", self.redo_last_action, row=0, column=10, shortcut="0")
        toolbar.grid_columnconfigure(tuple(range(11)), weight=1)

    def create_toolbar_button(self, parent, text, icon_path, command, row, column, scale_factor=9, shortcut=None):
        image = tk.PhotoImage(file=icon_path)
        resized_image = image.subsample(scale_factor, scale_factor)
        text = translate(text)
        button = tk.Button(parent, text=text, font = ('Georgia', 10, 'italic', 'bold'), image=resized_image, compound="top", command=command, bg='#87CEEB')
        button.image = resized_image  # Keep a reference to avoid garbage collection
        button.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        button.configure(width=12, height=80)
        label = tk.Label(button, text=shortcut, font=('Arial', 8), bg='#87CEEB')
        label.place(relx=1.0, rely=1.0, anchor='se')

    def create_main_frames(self):
        self.create_scroll_frame()
        self.create_listbox_frame()
        self.create_category_frame()

    def create_scroll_frame(self):
        self.scroll_frame = tk.Frame(self.root, bg='#b0c4de')
        self.scroll_frame.grid(row=2, column=0, pady=10, padx=5, sticky="nsew")

        self.button_canvas = tk.Canvas(self.scroll_frame, bg='#e1e1e1')
        self.button_canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient="vertical", command=self.button_canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.button_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.button_canvas.bind('<Configure>', lambda e: self.button_canvas.configure(scrollregion=self.button_canvas.bbox("all")))

        self.button_frame = tk.Frame(self.button_canvas, bg='#e1e1e1')
        self.button_canvas.create_window((0, 0), window=self.button_frame, anchor="nw")

    def create_listbox_frame(self):
        self.listbox_frame = tk.Frame(self.root, bg='#b0c4de')
        self.listbox_frame.grid(row=2, column=2, padx=20, pady=30, sticky="nsew")

        self.receipt_listbox = tk.Listbox(self.listbox_frame, font = ('Courier', 14, 'italic', 'bold'), bg='#e1e1e1', selectmode=tk.SINGLE)
        self.receipt_listbox.grid(pady=30, sticky="nsew")
        self.receipt_listbox.pack(side="left", fill='both', expand=True)

        self.listbox_scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.receipt_listbox.yview)
        self.receipt_listbox.configure(yscrollcommand=self.listbox_scrollbar.set)
        self.listbox_scrollbar.pack(side="right", fill="y")
        self.listbox_frame.grid_rowconfigure(0, weight=1)
        self.listbox_frame.grid_columnconfigure(0, weight=1)
        self.listbox_row = []

    def create_category_frame(self):
        self.category_frame = tk.Frame(self.root, bg='#D3D3D3')
        self.category_frame.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
        self.root.grid_columnconfigure(1, weight=0 )

        self.category_button_canvas = tk.Canvas(self.category_frame, bg='#f0f0f0')
        self.category_button_canvas.pack(side="left", fill="both", expand=True)

        self.load_categories_from_excel(ITEMS_FILE)

    def load_categories_from_excel(self, file_path):
        try:
            for widget in self.category_frame.winfo_children():
                widget.destroy()
            df = pd.read_excel(file_path)
            self.categories = df['Category'].unique().tolist()
            self.categories.insert(0, "All")  # Add "All" category
            self.category_buttons = []

            for category in self.categories:
                btn = tk.Button(self.category_frame, text=category, font = ('Georgia', 10, 'italic', 'bold'), width=12, height=3, command=lambda c=category: self.load_category(c), bg='#FFD700')
                btn.pack(side="top", padx=0, pady=5)
                self.category_buttons.append(btn)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('The file')} {file_path} {translate('was not found.')}")
        except Exception as e:
            messagebox.showerror(translate("Error"), f"{translate('Failed to load categories')}: {e}")

    def create_button(self, frame, text, row, column, command):
        button = tk.Button(frame, text=text, font = ('Georgia', 10, 'italic', 'bold'), width=14, height=3, command=command, bg='#90EE90')
        button.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")
        return button

    def load_items_from_excel(self, file_path, category="All"):
        self.buttons = []
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        try:
            df = pd.read_excel(file_path)
            if 'Category' not in df.columns:
                df['Category'] = 'Uncategorized'  # Assign a default category if not present

            if category != "All":
                df = df[df['Category'] == category]

            self.items = list(zip(df['Item'], df['Price'], df['Category'], df['Stock']))
            for i, (item, price, category, stock) in enumerate(self.items):
                price = float(price)
                button = self.create_button(self.button_frame, text=f"{item}\n${price:.2f}", row=i // 5, column=i % 5, command=lambda item=item, price=price: self.add_text(item, price))
                self.buttons.append(button)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('The file')} {file_path} {translate('was not found')}.")
        except Exception as e:
            messagebox.showerror(translate("Error"), f"{translate('Failed to load items')}: {e}")

    def open_delete_screen(self):
        """Opens a new window to select and delete items."""
        try:
            df = pd.read_excel(ITEMS_FILE)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('Could not find the file')}: {ITEMS_FILE}")
            return

        if 'Item' not in df.columns:
            messagebox.showwarning(translate("Data Error"), translate("The dataset does not contain 'Item' information."))
            return

        # Create a new Toplevel window
        delete_window = tk.Toplevel(self.root)
        delete_window.title(translate("Delete Items"))
        center_window(delete_window, w=400, h=500)

        # Create a Listbox to display items
        listbox = tk.Listbox(delete_window, selectmode=tk.MULTIPLE, width=50, height=20)
        listbox.pack(pady=20)

        for item in df['Item'].unique():
            listbox.insert(tk.END, item)

        def delete_selected_items_from_excel():
            """Deletes the selected items from the Excel file."""
            selected_indices = listbox.curselection()

            if not selected_indices:
                messagebox.showinfo(translate("No Selection"), translate("No items selected. Please select items to delete."))
                return

            selected_items = [listbox.get(i) for i in selected_indices]

            # Confirm deletion
            confirm = messagebox.askyesno(translate("Confirm Deletion"), f"{translate('Are you sure you want to delete the selected items')}: {', '.join(selected_items)}?")
            if not confirm:
                return

            # Remove the selected items from the DataFrame
            updated_df = df[~df['Item'].isin(selected_items)]

            # Save the updated DataFrame back to the Excel file
            try:
                updated_df.to_excel(ITEMS_FILE, index=False)
                messagebox.showinfo(translate("Success"), translate("Selected items were successfully deleted."))
                # Refresh the listbox
                listbox.delete(0, tk.END)
                for item in updated_df['Item'].unique():
                    listbox.insert(tk.END, item)
            except Exception as e:
                messagebox.showerror(translate("Save Error"), f"{translate('An error occurred while saving the file')}: {e}")
            self.load_categories_from_excel(ITEMS_FILE)
            self.load_items_from_excel(ITEMS_FILE)
            delete_window.destroy()

        # Add a button to delete the selected items
        tk.Button(delete_window, text=translate("Delete Selected Items"), command=delete_selected_items_from_excel).pack(pady=10)

    def add_text(self, item_name, price):
        if not self.orders or self.orders[-1]["item"] != item_name:
            self.last_item = item_name
            self.qty = 1
            self.position_index += 1
            order = {"item": item_name, "price": price, "qty": self.qty}
            self.orders.append(order)
            self.remarks.append("")
            self.undo_stack.append({"action": "add", "index": (self.position_index -1), "order": self.orders[-1]})
        else:
            self.qty += 1
            self.orders[-1]["qty"] = self.qty
            self.orders[-1]["price"] = price * self.qty
            del self.undo_stack[-1]
            self.undo_stack.append({"action": "update", "index": (self.position_index -1), "order": self.orders[-1]})
        self.total_cost += price
        self.redo_stack.clear()  # Clear redo stack when a new action is taken
        self.update_receipt_listbox()

    def update_receipt_listbox(self):
        """Update the receipt listbox with current order details."""
        self.receipt_listbox.delete(0, tk.END)
        if len(self.orders) == 0:
            return
        self.receipt_listbox.insert(tk.END, "-" * 50)
        self.receipt_listbox.insert(tk.END, "{:<50}".format(translate("Franchise: Your Franchise Name")))
        self.receipt_listbox.insert(tk.END, "{:<50}".format(translate("Address: 1234 Main St, City, Country")))
        self.receipt_listbox.insert(tk.END, "{:<50}".format(translate("Phone: (123)-456 7890")))
        self.receipt_listbox.insert(tk.END, "{:<20}:{:<20}".format(translate("Receipt ID"), self.receipt_ID))
        self.receipt_listbox.insert(tk.END, "-" * 50)
        self.receipt_listbox.insert(tk.END, "{:<20} {:<5} {:<10} {}".format(
            translate("Item"), translate("Qty"), translate("Price"), translate("Remark"))
        )
        self.receipt_listbox.insert(tk.END, "-" * 50)
        for order, remark in zip(self.orders, self.remarks):
            self.receipt_listbox.insert(tk.END, "{:<20} {:<5} ${:<10.2f} {}".format(
                order["item"], order["qty"], order["price"], remark
            ))

        self.receipt_listbox.insert(tk.END, "-" * 50)
        self.receipt_listbox.insert(tk.END, "{:<20} {:<5} ${:<10.2f}".format(f"{translate('Total Cost')}:", "", self.total_cost))

        if self.discount_rate > 0 and self.discount_rate <= 1:
            decimal_value = Decimal(self.total_cost * (1 - self.discount_rate)).quantize(Decimal('0.01'), rounding=ROUND_UP)
            self.rounded_up = (decimal_value * 10).quantize(Decimal('1'), rounding=ROUND_UP) / 10
            self.receipt_listbox.insert(
                tk.END, "{:<20} {:<5} {:<10}%".format(f"{translate('Discount')}:", "", (int(self.discount_rate * 100)))
            )
            self.receipt_listbox.insert(
                tk.END, "{:<30} {:<5} ${:<10.2f}".format(f"{translate('Total Cost After Discount')}:", "", self.rounded_up)
            )

    def delete_selected_item(self):
        selection = self.receipt_listbox.curselection()
        if selection:
            index = selection[0]
            if 7 <= index < (self.receipt_listbox.size() - 2):
                adjusted_index = index - 8
                self.total_cost -= self.orders[adjusted_index]["price"]
                removed_order = self.orders.pop(adjusted_index)
                removed_remark =  self.remarks.pop(adjusted_index)
                self.undo_stack.append({"action": "delete", "order": removed_order, "remark": removed_remark, "index": adjusted_index})
                self.redo_stack.clear()
                self.update_receipt_listbox()
            else:
                messagebox.showerror(
                    translate("Selection Error"),
                    translate("Invalid selection or no item selected.")
                )
        else:
            messagebox.showerror(
                translate("Selection Error"),
                translate("No item selected. Please select an item to delete.")
            )
         
    def remark_selected_item(self):
        selection = self.receipt_listbox.curselection()
        if selection:
            index = selection[0]
            if 7 <= index < (self.receipt_listbox.size() - 2):
                adjusted_index = index - 8
                current_remark = self.remarks[adjusted_index] if self.remarks[adjusted_index] is not None else ""
                new_remark = simpledialog.askstring(
                            "Input", f"Enter remark for {self.orders[adjusted_index]['item']}:\n(Current remark: {current_remark})"
                        )
                if new_remark is not None:
                    self.remarks[adjusted_index] += ", " + new_remark if self.remarks[adjusted_index] else new_remark
                    self.undo_stack.append({"action": "remark", "index": adjusted_index, "previous_remark": current_remark, "new_remark": new_remark})
                    self.redo_stack.clear()  # Clear redo stack when a new action is taken
                    self.update_receipt_listbox()  
                else:
                    messagebox.showerror(
                        translate("Invalid Input"),
                        translate("Invalid remark entered.")
                    )
            else:
                messagebox.showerror(
                    translate("Selection Error"),
                    translate("Invalid selection or no item selected.")
                )
        else:
            messagebox.showerror(
                translate("Selection Error"),
                translate("No item selected. Please select an item to add a remark.")
            )

    def reset(self):
        if len(self.orders) == 0:
            messagebox.showinfo(translate("Order Empty"), translate("All orders have been cleared"))
        else:
            self.undo_stack.append({"action": "reset", 
                                    "all_orders": copy.deepcopy(self.orders), 
                                    "all_remarks": copy.deepcopy(self.remarks), 
                                    "total_cost": self.total_cost, 
                                    "index": self.position_index, 
                                    "discount_rate": self.discount_rate}) 
            self.orders.clear()
            self.remarks.clear()
            self.total_cost = 0
            self.position_index = 0
            self.discount_rate = 0.0
            self.update_receipt_listbox()

    def add_new_item(self):
        dialog = AddItemDialog(self.root)
        self.root.wait_window(dialog)
        result = dialog.result
        if result:
            item_name, item_price, item_category, item_stock, item_cost = result
            new_item = pd.DataFrame({'Item': [item_name], 'Price': [item_price], 'Category': [item_category], 'Stock': [item_stock], 'Sold': [0], 'Cost': [item_cost], 'counted Price': [0]})
            try:
                df = pd.read_excel(ITEMS_FILE)
                df = pd.concat([df, new_item], ignore_index=True)
                df.to_excel(ITEMS_FILE, index=False)
                self.load_items_from_excel(ITEMS_FILE)
                self.load_categories_from_excel(ITEMS_FILE)
            except Exception as e:
                messagebox.showerror(translate("Error"), f"{translate('Failed to add item')}: {e}")

    def show_payment_methods(self):
        if len(self.orders) == 0:
            messagebox.showerror(translate("Invalid Payment"), translate("There is no order."))
        else:
            payment_window = tk.Toplevel(self.root)
            payment_window.title(translate("Select Payment Method"))
            center_window(payment_window, w=300, h=400)
            payment_window.configure(bg='#ADD8E6')

            tk.Label(payment_window, text=translate("Select Payment Method"), font=('Arial', 14), bg='#ADD8E6').pack(pady=10)

            payment_methods = ["Cash", "Credit Card", "Debit Card", "Mobile Payment"]
            for method in payment_methods:
                tk.Button(payment_window, text=translate(method), font=('Arial', 12), width=20, height=2, command=lambda m=method: self.print_receipt_and_close(payment_window, m)).pack(pady=5)

    def print_receipt_and_close(self, window, payment_method):
        self.receipt_listbox.insert(tk.END, f"{translate('Payment Method')}: {payment_method}")
        self.receipt_listbox.insert(tk.END, "-" * 50)
        self.receipt_listbox.insert(tk.END, translate("Thank you for shopping with us!"))
        self.receipt_listbox.insert(tk.END, "-" * 50)
        try:
            new_sales = pd.DataFrame({
                'Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                'Amount': [self.total_cost],
                'Discount': [self.discount_rate]
            })
            try:
                df = pd.read_excel(DAILY_SALES_FILE)
                df = pd.concat([df, new_sales], ignore_index=True)
            except FileNotFoundError:
                df = new_sales
            df.to_excel(DAILY_SALES_FILE, index=False)
        except Exception as e:
            messagebox.showerror(translate("Save Error"), f"{translate('Failed to save transaction')}: {e}")

        # Display receipt in a new window
        self.save_receipt()
        self.save_order_to_json()
        self.display_receipt(payment_method)
        self.update_inventory()
        self.reset()
        window.destroy()

    def display_receipt(self, payment_method):
        """Display the receipt in a new window."""
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title(translate("Receipt"))
        center_window(receipt_window, w=600, h=650)
        receipt_window.configure(bg='#f0f0f0')

        receipt_text = tk.Text(receipt_window, font=('Courier', 12), bg='#ffffff')
        receipt_text.pack(expand=True, fill='both', padx=10, pady=10)

        receipt_content = f"{translate('Receipt')}\n\n"
        receipt_content += "-" * 50 + "\n"
        receipt_content += "{:<50}\n".format(translate("Franchise: Your Franchise Name"))
        receipt_content += "{:<50}\n".format(translate("Address: 1234 Main St, City, Country"))
        receipt_content += "{:<50}\n".format(translate("Phone: (123)-456 7890"))
        receipt_content +=  "{:<20}:{:<20}\n".format(translate("Receipt ID"), self.receipt_ID)
        receipt_content += "-" * 50 + "\n"
        receipt_content += "{:<20} {:<5} {:<10} {}\n".format(translate("Item"), translate("Qty"), translate("Price"), translate("Remark"))
        receipt_content += "-" * 50 + "\n"
        for order, remark in zip(self.orders, self.remarks):
            receipt_content += "{:<20} {:<5} ${:<10.2f} {}\n".format(order["item"], order["qty"], order["price"], remark)
        receipt_content += "\n"
        receipt_content += "-" * 50 + "\n"
        receipt_content += "{:<20} {:<5} ${:<10}\n".format(f"{translate('Total Cost')}:", "", self.total_cost)

        if self.discount_rate > 0 and self.discount_rate <= 1:
            decimal_value = Decimal(self.total_cost * (1 - self.discount_rate)).quantize(Decimal('0.01'), rounding=ROUND_UP)
            rounded_up = (decimal_value * 10).quantize(Decimal('1'), rounding=ROUND_UP) / 10
            receipt_content += "{:<20} {:<5} {:<10}%\n".format(f"{translate('Discount')}:", "", int(self.discount_rate * 100))
            receipt_content += "{:<20} {:<5} ${:<10}\n".format(f"{translate('Total Cost After Discount')}:", "", rounded_up)

        receipt_content += f"{translate('Payment Method')}: {payment_method}\n"
        receipt_content += "-" * 50 + "\n"
        receipt_content += translate("Thank you for shopping with us!")

        receipt_text.insert(tk.END, receipt_content)
        receipt_text.config(state='disabled')

    def show_daily_total(self):
        daily_total = 0
        try:
            df = pd.read_excel(DAILY_SALES_FILE)
            daily_total = df['Amount'].sum()
            amount = df['Amount']
            dates = df['Date']
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('The file')} {DAILY_SALES_FILE} {translate('was not found.')}")
        except Exception as e:
            messagebox.showerror(translate("Error"), f"{translate('Failed to retrieve daily total')}: {e}")
        plt.figure(figsize=(10, 5))
        plt.plot(dates, amount, label='Total Costs')  # Corrected plotting function
        plt.title(('Daily Sales'))
        plt.xlabel(('Date'))
        plt.ylabel(('Amount'))
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)  # Rotate date labels for better readability

        # Adding text annotation for daily total
        plt.text(dates.iloc[-1], amount.iloc[-1], f"{translate('Total')}: ${daily_total:.2f}",
                horizontalalignment='left', verticalalignment='bottom',
                fontsize=12, color='black', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

        plt.tight_layout()
        plt.show()

    def save_receipt(self):
        # Get current date and time
        current_time = datetime.now()
        folder = current_time.strftime("Receipts/Text/%Y%m%d/")
        filename = current_time.strftime("%H%M%S.txt")
        file_path = os.path.join(folder, filename)

        # Ensure the folder exists
        os.makedirs(folder, exist_ok=True)

        try:
            with open(file_path, 'w') as f:
                for line in self.receipt_listbox.get(0, tk.END):
                    f.write(line + '\n')
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save receipt: {e}")

    def view_item_details(self):
        selection = self.receipt_listbox.curselection()
        if selection:
            # Exclude the header and footer lines
            if selection[0] > 1 and selection[0] < self.receipt_listbox.size() - 2:
                item_line = self.receipt_listbox.get(selection[0])
                
                # Split the line into parts
                parts = item_line.split()
                
                # Find the price and quantity
                try:
                    price_index = next(i for i, part in enumerate(parts) if part.startswith('$'))
                    qty_index = price_index - 1
                    
                    price_str = parts[price_index].replace("$", "").strip()
                    qty_str = parts[qty_index].strip()
                    
                    price = float(price_str.replace(" ", ""))
                    qty = int(qty_str.replace(" ", ""))
                    
                    # The item name is everything before the quantity
                    item = " ".join(parts[:qty_index])
                    
                    # The remarks are everything after the price
                    remarks = " ".join(parts[price_index + 1:])
                    
                    messagebox.showinfo(translate("Item Details"), f"{translate('Item')}: \t{item}\n{translate('Quantity')}: \t{qty}\n{translate('Price')}: \t${price}\n{translate('Remarks')}: \t{remarks}")
                except (ValueError, StopIteration):
                    messagebox.showerror(translate("Parsing Error"), translate("Could not parse the quantity or price."))
        else:
            messagebox.showerror(translate("Selection Error"), translate("No item selected. Please select an item to view details."))

    def apply_dynamic_pricing_ui(self):
        df = pd.read_excel(ITEMS_FILE)
        self.dynamic_price_root = tk.Toplevel(self.root)
        center_window(self.dynamic_price_root, w=600, h=500)
        self.dynamic_price_listbox = tk.Listbox(self.dynamic_price_root, font=("Helvetica", 14), width=50, height=10)
        self.dynamic_price_listbox.pack(pady=20)
        self.newprice = tk.DoubleVar()

        for item, price in zip(df['Item'], df['Price']):
            self.dynamic_price_listbox.insert(tk.END, f"{item}\t${price}")

        self.demand_factor_label = tk.Label(self.dynamic_price_root, text=f"{translate('New Price')}: ", font=("Helvetica", 14))
        self.demand_factor_label.pack(pady=10)  
        self.demand_factor_entry = tk.Entry(self.dynamic_price_root, textvariable=self.newprice, font=("Helvetica", 14))
        self.demand_factor_entry.pack(pady=10) 
        self.demand_factor_entry.bind("<FocusIn>", self.demand_factor_entry.delete(0, tk.END))
        
        apply_button = tk.Button(self.dynamic_price_root, text=translate("Apply Dynamic Pricing"), command=self.apply_dynamic_pricing, font=("Helvetica", 14), width=20)
        apply_button.pack(pady=20)

        self.dynamic_price_listbox.bind('<<ListboxSelect>>', self.store_selected_item)

    def store_selected_item(self):
        try:
            selected_item_index = self.dynamic_price_listbox.curselection()[0]
            self.selected_item = self.dynamic_price_listbox.get(selected_item_index)
        except IndexError:
            self.selected_item = None

    def apply_dynamic_pricing(self):
        try:
            if self.selected_item is None:
                raise IndexError("No item selected")
            df = pd.read_excel(ITEMS_FILE)
            selected_item_index = self.dynamic_price_listbox.curselection()[0]
            selected_item = self.dynamic_price_listbox.get(selected_item_index)
            item_name, current_price = selected_item.split('\t$')
            demand_factor = float(self.newprice.get())
            item_name = item_name.strip()
            df.loc[df['Item'].str.strip() == item_name, 'Price'] = demand_factor

            df.to_excel(ITEMS_FILE, index=False)
            self.load_categories_from_excel(ITEMS_FILE)
            self.load_items_from_excel(ITEMS_FILE)
            
            
            messagebox.showinfo(translate("Success"), f"{translate('Price for')} {item_name} {translate('updated successfully to')} {demand_factor:.2f}.")
        except IndexError:
            messagebox.showwarning(translate("Selection Error"), translate("Please select an item from the list."))
        except ValueError:
            messagebox.showwarning(translate("Input Error"), translate("Please enter a valid demand factor."))
        except Exception as e:
            messagebox.showerror(translate("Error"), str(e))
        self.dynamic_price_root.destroy()

    def discount_screen(self):
        """Opens a window to enter discount rate and apply to items."""
        discount_root = tk.Toplevel(self.root)
        discount_root.title(translate("Apply Discount"))
        center_window(discount_root, w=300, h=150)
        discount_root.configure(bg="#f0f0f0")

        tk.Label(discount_root, text=f"{translate('Enter Discount Rate')} (%):", bg="#f0f0f0").pack(pady=10)
        discount_entry = tk.Entry(discount_root)
        discount_entry.pack(pady=5)

        def apply_discount():
            try:
                discount_rate = float(discount_entry.get()) / 100
                if not (0 <= discount_rate <= 1):
                    raise ValueError(translate("Discount rate must be between 0 and 100."))
                self.discount_rate = discount_rate
                self.undo_stack.append({"action": "discount", "discount_rate": self.discount_rate})
                discount_root.destroy()
                self.update_receipt_listbox()

            except ValueError as e:
                messagebox.showerror(translate("Invalid Input"), f"{translate('Please enter a valid discount rate.')} {translate('Error')}: {e}")

        tk.Button(discount_root, text=translate("Apply Discount"), command=apply_discount).pack(pady=10)

    def manage_promotions(self, discount_rate):
        """Applies a discount to all items."""
        try:
            self.df = pd.read_excel(ITEMS_FILE)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('Could not find the file')}: {ITEMS_FILE}")
            self.df = pd.DataFrame()  # Use an empty DataFrame if file not found
        if self.df.empty:
            messagebox.showwarning(translate("No Data"), translate("No data available to apply discounts."))
            return

        self.df['Discounted Price'] = self.df['Price'] * (1 - discount_rate)
        
        # Save the updated DataFrame back to the Excel file
        try:
            self.df.to_excel(ITEMS_FILE, index=False)
            messagebox.showinfo(translate("Promotions"), f"{translate('A')} {discount_rate * 100:.0f}% {translate('discount has been applied to all items.')}")
        except Exception as e:
            messagebox.showerror(translate("Save Error"), f"{translate('An error occurred while saving the file')}: {e}")

    def change_price(self):
        selection = self.receipt_listbox.curselection()
        if selection:
            index = selection[0]
            if 7 <= index < (self.receipt_listbox.size() - 2):
                adjusted_index = index - 8
                current_price = self.orders[adjusted_index]["price"]
                try:
                    new_price = float(simpledialog.askstring(
                    "Input", f"Enter new price for {self.orders[adjusted_index]['item']}:\n(Current price: ${current_price:.2f})"
                    ))
                    self.undo_stack.append({"action": "price", "index": adjusted_index, "previous_price": current_price, "new_price": new_price})
                    self.total_cost -= current_price
                    self.total_cost += new_price
                    self.orders[adjusted_index]["price"] = new_price
                    self.update_receipt_listbox()
                    self.redo_stack.clear()
                except ValueError:
                        messagebox.showerror("Input Error", "Invalid price entered.")
            else:
                messagebox.showerror(
                    translate("Selection Error"),
                    translate("Invalid selection or no item selected.")
                )
        else:
            messagebox.showerror(
                translate("Selection Error"),
                translate("No item selected. Please select an item to change its price.")
            )

    def undo_last_action(self):
        if not self.undo_stack:
            messagebox.showinfo(translate("Undo"), translate("No actions to undo."))
            return
        last_action = self.undo_stack.pop()
        if last_action["action"] == "add":
            self.orders.remove(last_action["order"])
            self.total_cost -= last_action["order"]["price"]
     
        elif last_action["action"] == "update":
            price_unit =  last_action["order"]["price"] / last_action["order"]["qty"]
            last_action["order"]["price"] -= price_unit
            last_action["order"]["qty"] -= 1
            if last_action["order"]["qty"] == 1:
                last_action["action"] = "add"
            self.total_cost -= price_unit
            self.undo_stack.append(last_action)
            
        elif last_action["action"] == "delete":
            if 0 <= last_action["index"] < len(self.orders):
                self.orders.insert(last_action["index"], last_action["order"])
                self.remarks.insert(last_action["index"], last_action["remark"])
                self.total_cost += last_action["order"]["price"]

        elif last_action["action"] == "remark":
            if 0 <= last_action["index"] < len(self.orders):
                self.remarks[last_action["index"]] = last_action["previous_remark"]

        elif last_action["action"] == "price":
            if 0 <= last_action["index"] < len(self.orders):
                self.orders[last_action["index"]]["price"] = last_action["previous_price"]
                self.total_cost -= last_action["new_price"]
                self.total_cost += last_action["previous_price"]
                
        elif last_action["action"] == "reset":
            self.orders = copy.deepcopy(last_action["all_orders"])
            self.remarks = copy.deepcopy(last_action["all_remarks"])
            self.total_cost = last_action["total_cost"]
            self.position_index = last_action["index"]
            self.discount_rate = last_action["discount_rate"]

        elif last_action["action"] == "discount":
            self.discount_rate = 0.0

        self.redo_stack.append(last_action)  # Push the undone action to the redo stack
        self.update_receipt_listbox()

    def redo_last_action(self):
        if not self.redo_stack:
            messagebox.showinfo(translate("Redo"), translate("No actions to redo."))
            return 
        last_action = self.redo_stack.pop()
        if last_action["action"] == "add":
            if last_action["order"]["qty"] >= 1:
                last_action["action"] = "update"
            self.orders.append(last_action["order"])
            self.total_cost += last_action["order"]["price"]

        elif last_action["action"] == "update":
            price_unit = last_action["order"]["price"] / last_action["order"]["qty"]
            last_action["order"]["price"] += price_unit
            last_action["order"]["qty"] += 1
            self.total_cost += price_unit

        elif last_action["action"] == "delete":
            if 0 <= last_action["index"] < len(self.orders):
                self.orders.pop(last_action["index"])
                self.remarks.insert(last_action["index"])
                self.total_cost += last_action["order"]["price"]

        elif last_action["action"] == "remark":
            if 0 <= last_action["index"] < len(self.orders):
                self.orders[last_action["index"]] = last_action["new_remark"]

        elif last_action["action"] == "price":
            if 0 <= last_action["index"] < len(self.orders):
                self.orders[last_action["index"]]["price"] = last_action["new_price"]
                self.total_cost -= last_action["previous_price"]
                self.total_cost += last_action["new_price"]

        elif last_action["action"] == "reset":
            self.orders.clear()
            self.remarks.clear()
            self.total_cost = 0
            self.position_index = 0
            self.discount_rate = 0.0
        
        elif last_action["action"] == "discount":
            self.discount_rate = last_action["discount_rate"]

        self.undo_stack.append(last_action)  # Push the redone action back to the undo stack
        self.update_receipt_listbox()

    def collect_feedback_ui(self):
        self.feedback_root = tk.Toplevel(self.root, bg='#d4d4d4')
        center_window(self.feedback_root, w=600, h=500)
        self.feedback_root.title(translate("Feedback Form"))
        
        tk.Label(self.feedback_root, text=f"{translate('Name')}:", font=("Helvetica", 14)).grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.name_entry = tk.Entry(self.feedback_root, width=30, font=("Helvetica", 14))
        self.name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(self.feedback_root, text=f"{translate('Phone Number')}:", font=("Helvetica", 14)).grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.phone_entry = tk.Entry(self.feedback_root, width=30, font=("Helvetica", 14))
        self.phone_entry.grid(row=1, column=1, padx=10, pady=10)
        
        tk.Label(self.feedback_root, text=f"{translate('Feedback')}:", font=("Helvetica", 14)).grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.feedback_entry = tk.Text(self.feedback_root, width=30, height=10, font=("Helvetica", 14))
        self.feedback_entry.grid(row=2, column=1, padx=10, pady=10)

        submit_button = tk.Button(self.feedback_root, text=translate("Submit"), command=self.collect_feedback, font=("Helvetica", 14), bg='darkblue', fg='white', padx=10, pady=5)
        submit_button.grid(row=3, column=1, pady=20)
    
    def collect_feedback(self):
        if self.name_entry and self.phone_entry and self.feedback_entry:
            new_feedback = pd.DataFrame({
                'Name': [self.name_entry.get()],
                'Phone': [self.phone_entry.get()],
                'Feedback': [self.feedback_entry.get("1.0", tk.END).strip()],
                'Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            })
            try:
                try:
                    df = pd.read_excel(FEEDBACK_FILE, sheet_name="Feedbacks")
                    df = pd.concat([df, new_feedback], ignore_index=True)
                except FileNotFoundError:
                    df = new_feedback
                with pd.ExcelWriter(FEEDBACK_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name='Feedbacks', index=False)
                messagebox.showinfo(translate("Feedback"), translate("Thank you for your feedback!"))
                self.feedback_root.destroy()
            except Exception as e:
                messagebox.showerror(translate("Feedback Error"), f"{translate('Failed to save feedback')}: {e}")
        else:
            messagebox.showerror(translate("Feedback Error"), translate("All fields are required."))
    
    def rating_ui(self):
        self.rating_root = tk.Toplevel(self.root)
        self.rating_value = tk.IntVar(value=0)
        self.rating_root.title(translate("Rate Us!"))
        center_window(self.rating_root, w=500, h=200)
        self.rating_root.configure(bg="#f0f0f0")
        rating_frame = tk.Frame(self.rating_root, bg="#f0f0f0")
        rating_frame.pack(pady=20)

        star_filled_path = os.path.join("Photo", "star_filled.png")
        star_empty_path = os.path.join("Photo", "star_empty.png")

        self.star_filled = tk.PhotoImage(file=star_filled_path).subsample(8, 8)
        self.star_empty = tk.PhotoImage(file=star_empty_path).subsample(8, 8)

        self.stars = []
        for i in range(5):
            star_button = tk.Button(
                rating_frame,
                image=self.star_empty,
                command=lambda i=i: self.set_rating(i + 1),
                borderwidth=0,
                bg="#f0f0f0"
            )
            star_button.grid(row=0, column=i, padx=5)
            self.stars.append(star_button)

        self.rating_label = tk.Label(self.rating_root, text=f"{translate('Current Rating')}: 0", font=("Arial", 14), bg="#f0f0f0", fg="#333")
        self.rating_label.pack(pady=10)

        tk.Button(self.rating_root, text=translate("Submit"), command=self.submit_rating, font=("Arial", 12), bg="#6c8ebf", fg="white").pack(pady=10)

    def set_rating(self, value):
        self.rating_value.set(value)
        self.update_stars()

    def update_stars(self):
        rating = self.rating_value.get()
        for i, star in enumerate(self.stars):
            star.config(image=self.star_filled if i < rating else self.star_empty)
        self.rating_label.config(text=f"{translate('Current Rating')}: {rating}")

    def submit_rating(self):
        self.rating_root.destroy()
        if self.save_rating_to_excel(self.rating_value.get()):
            self.show_thank_you_message()

    def save_rating_to_excel(self, rating):
        try:
            if os.path.exists(FEEDBACK_FILE):
                feedback_df = pd.read_excel(FEEDBACK_FILE, sheet_name='Ratings')
            else:
                pd.DataFrame(columns=["Rating"])

            # Append the new rating
            new_data = pd.DataFrame({"Rating": [rating], 'Date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]})
            feedback_df = pd.concat([feedback_df, new_data], ignore_index=True)
            with pd.ExcelWriter(FEEDBACK_FILE, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                feedback_df.to_excel(writer, sheet_name='Ratings', index=False)

            logging.info(translate("Rating saved successfully."))
            messagebox.showinfo(translate("Success"), translate("Rating saved successfully."))
        except FileNotFoundError as fnf_error:
            logging.error(f"{translate('File not found')}: {fnf_error}")
            messagebox.showerror(translate("Error"), f"{translate('File not found')}: {fnf_error}")
        except PermissionError as perm_error:
            logging.error(f"{translate('Permission error')}: {perm_error}")
            messagebox.showerror(translate("Error"), f"{translate('Permission error')}: {perm_error}")
        except Exception as e:
            logging.error(f"{translate('Error saving rating to Excel')}: {e}")
            messagebox.showerror(translate("Error"), f"{translate('Could not save the rating')}: {e}")
        
    def show_thank_you_message(self):
        thank_you_root = tk.Tk()
        thank_you_root.title(translate("Thank You"))
        center_window(thank_you_root, w=200, h=100)
        thank_you_root.configure(bg="#f7f7f7")

        tk.Label(thank_you_root, text=translate("Thank You!"), font=("Arial", 16), bg="#f7f7f7", fg="#333").pack(pady=10)
        tk.Button(thank_you_root, text=translate("Okay"), command=thank_you_root.destroy, font=("Arial", 12), bg="#6c8ebf", fg="white").pack(pady=10)

        thank_you_root.mainloop()

    def show_help(self):
        help_window = tk.Toplevel(self.root)
        help_window.title(translate("Help"))
        center_window(help_window, w=600, h=610)

        help_label = tk.Label(help_window, text=translate('help_message'), font=("Helvetica", 10), justify=tk.LEFT, padx=5, pady=5)
        help_label.pack(fill=tk.BOTH, expand=True)

        close_button = tk.Button(help_window, text=translate("Close"), command=help_window.destroy, font=("Helvetica", 12))
        close_button.pack()

    def update_datetime(self):
        if self.root.winfo_exists():  # Check if the root window still exists
            now = datetime.now()
            date_str = now.strftime(f"{translate('Date')}: %Y/%m/%d  {translate('Time')}: %H:%M:%S")
            self.datetime_label.config(text=date_str)
            self.root.after(1000, self.update_datetime)
        else:
            pass
            
    def load_category(self, category):
        self.load_items_from_excel(ITEMS_FILE, category)

    def set_language(self):
        self.languages[self.language.get()]()

    def load_english(self):
        # Load English labels and messages
        with open(LANGUAGE_FILE, 'r', encoding='utf-8') as file:
            df = json.load(file)
        select = df['language']['English']
        df['language']['Select'] = select
        with open(LANGUAGE_FILE, 'w', encoding='utf-8') as file:
            json.dump(df, file, ensure_ascii=False, indent=4)
        self.refresh_root()
        
    def load_chinese(self):
        # Load Chinese labels and messages
        with open(LANGUAGE_FILE, 'r', encoding='utf-8') as file:
            df = json.load(file)
        df['language']['Select'] = df['language']['Chinese']
        with open(LANGUAGE_FILE, 'w', encoding='utf-8') as file:
            json.dump(df, file, ensure_ascii=False, indent=4)
        self.refresh_root()

    def manage_users(self):
        if self.role != 'admin':
            messagebox.showerror(translate("Access Denied"), translate("Only admin users can manage users."))
            return

        def add_user():
            username = simpledialog.askstring(translate("New User"), f"{translate('Enter new username')}:")
            if username:
                pin = simpledialog.askstring(translate("New User PIN"), f"{translate('Enter new user PIN')}:")
                if pin and len(pin) == PIN_LENGTH and pin.isdigit():
                    role = simpledialog.askstring(translate("Role"), f"{translate('Enter user role')} (admin/user):")

                    if role in ['admin', 'user']:
                        new_user = pd.DataFrame({'Username': [username], 'PIN': [hash_password(pin)], 'Role': [role]})
                        try:
                            df = pd.read_excel(USERS_FILE)
                            df = pd.concat([df, new_user], ignore_index=True)
                            df.to_excel(USERS_FILE, index=False)
                            messagebox.showinfo(translate("User Management"), translate("New user added successfully."))
                            update_user_list()  # Refresh the user list
                        except Exception as e:
                            messagebox.showerror(translate("Error"), f"{translate('Failed to add user')}: {e}")
                    else:
                        messagebox.showerror(translate("Input Error"), translate("Invalid role specified."))
                else:
                    messagebox.showerror(translate("Input Error"), translate("Invalid PIN. Please enter a 4-digit PIN."))
            else:
                messagebox.showerror(translate("Input Error"), translate("Username cannot be empty."))

        def remove_user():
            selected_user = user_listbox.selection()
            if not selected_user:
                messagebox.showwarning(translate("Selection Error"), translate("No user selected for removal."))
                return

            username = user_listbox.item(selected_user, 'values')[0]
            confirm = messagebox.askyesno(translate("Confirm Deletion"), f"{translate('Are you sure you want to delete user')} '{username}'?")
            if confirm:
                try:
                    df = pd.read_excel(USERS_FILE)
                    df = df[df['Username'] != username]
                    df.to_excel(USERS_FILE, index=False)
                    messagebox.showinfo(translate("User Management"), translate("User removed successfully."))
                    update_user_list()  # Refresh the user list
                except Exception as e:
                    messagebox.showerror(translate("Error"), f"{translate('Failed to remove user')}: {e}")

        def update_user_list():
            try:
                df = pd.read_excel(USERS_FILE)
                user_listbox.delete(*user_listbox.get_children())  # Clear the listbox
                for index, row in df.iterrows():
                    user_listbox.insert("", "end", values=(row['Username'], row['Role']))
            except Exception as e:
                messagebox.showerror(translate("Error"), f"{translate('Failed to load users')}: {e}")

        # Create a window for user management
        user_window = tk.Toplevel(self.root)
        user_window.title(translate("Manage Users"))
        center_window(user_window, w=400, h=400)
        user_window.configure(bg='#ADD8E6')

        # Create list to display users
        user_listbox = ttk.Treeview(user_window, columns=('Username', 'Role'), show='headings')
        user_listbox.heading('Username', text=translate('Username'))
        user_listbox.heading('Role', text=translate('Role'))
        user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create buttons for add and remove
        tk.Button(user_window, text=translate("Add User"), font=('Arial', 12), command=add_user, bg='#87CEEB').pack(pady=10)
        tk.Button(user_window, text=translate("Remove User"), font=('Arial', 12), command=remove_user, bg='#87CEEB').pack(pady=5)

        # Create close button
        tk.Button(user_window, text=translate("Close"), font=('Arial', 12), command=user_window.destroy, bg='#87CEEB').pack(pady=10)

        update_user_list()  # Initialize the user list

    def manage_inventory(self):
        def update_item(item, stock, price, reorder_threshold):
            df = pd.read_excel(ITEMS_FILE)
            df.loc[df['Item'] == item, ['Stock', 'Price', 'Reorder_Threshold']] = [stock, price, reorder_threshold]
            df.to_excel(ITEMS_FILE, index=False)

        inventory_window = tk.Toplevel(self.root)
        inventory_window.title(translate("Manage Inventory"))
        center_window(inventory_window, w=600, h=600)
        inventory_window.configure(bg='#d3d3d3')

        tk.Label(inventory_window, text=translate("Inventory Management"), font=('Arial', 18, 'bold'), bg='#d3d3d3').grid(row=0, column=0, pady=10)

        canvas = tk.Canvas(inventory_window, bg='#d3d3d3', width=580, height=600)
        scrollbar = ttk.Scrollbar(inventory_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set, bg='#d3d3d3')

        def on_mouse_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)

        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")

        df = pd.read_excel(ITEMS_FILE)
        for _, row in df.iterrows():
            item = row['Item']
            stock = row['Stock']
            price = row['Price']
            reorder_threshold = row['Reorder_Threshold']

            frame = ttk.Frame(scrollable_frame, style="TFrame")
            frame.pack(fill='x', padx=10, pady=5)  # Reduced pady for frame

            # Item label
            tk.Label(frame, text=item, font=('Arial', 14), width=15, bg='#d3d3d3').grid(row=2, column=0, pady=(0, 5))  # Reduced pady

            # Stock label and entry
            tk.Label(frame, text="Stock", font=('Arial', 12)).grid(row=1, column=1, pady=(0, 2))  # Reduced pady
            stock_var = tk.IntVar(value=stock)
            tk.Entry(frame, textvariable=stock_var, width=5, font=('Arial', 12)).grid(row=2, column=1, padx=5, pady=(0, 5))  # Reduced pady

            # Price label and entry
            tk.Label(frame, text="Price", font=('Arial', 12)).grid(row=1, column=2, pady=(0, 2))  # Reduced pady
            price_var = tk.DoubleVar(value=price)
            tk.Entry(frame, textvariable=price_var, width=10, font=('Arial', 12)).grid(row=2, column=2, padx=5, pady=(0, 5))  # Reduced pady

            # Reorder Threshold label and entry
            tk.Label(frame, text="Reorder Threshold", font=('Arial', 12)).grid(row=1, column=3, pady=(0, 2))  # Reduced pady
            reorder_threshold_var = tk.IntVar(value=reorder_threshold)
            tk.Entry(frame, textvariable=reorder_threshold_var, width=10, font=('Arial', 12)).grid(row=2, column=3, padx=5, pady=(0, 5))  # Reduced pady

            # Update button
            tk.Button(frame, text=translate("Update"), font=('Arial', 12),
                      command=lambda item=item, stock_var=stock_var, price_var=price_var, reorder_threshold_var=reorder_threshold_var:
                      update_item(item, stock_var.get(), price_var.get(), reorder_threshold_var.get())).grid(row=2, column=4, padx=5, pady=(0, 5))  # Reduced pady

        close_button = tk.Button(inventory_window, text=translate("Close"), font=('Arial', 14), command=inventory_window.destroy)
        close_button.grid(row=2, column=0, pady=5)  # Reduced pady

        inventory_window.grid_rowconfigure(1, weight=1)
        inventory_window.grid_rowconfigure(2, weight=0)
        inventory_window.grid_columnconfigure(0, weight=1)

    def update_inventory(self):
        df = pd.read_excel(ITEMS_FILE)
        for order in self.orders:
            item = order['item']
            df.loc[df['Item'] == item, 'Stock'] -= order['qty']
            df.loc[df['Item'] == item, 'Sold'] += order['qty']
            df.to_excel(ITEMS_FILE, index=False)

    def manage_suppliers(self):
        """Manages supplier information and reorder processes."""
        try:
            # Read suppliers data from the Excel file
            suppliers_df = pd.read_excel(SUPPLIER_FILE)

            # Check if required columns are present
            required_columns = ['Supplier Name', 'Email', 'Phone']
            if not all(col in suppliers_df.columns for col in required_columns):
                messagebox.showerror(translate("Data Error"), translate("Suppliers Excel file is missing required columns."))
                return

            # Prepare supplier information
            supplier_info = "\n".join([
                f"{row['Supplier Name']}: {row['Email']}, {row['Phone']}"
                for _, row in suppliers_df.iterrows()
            ])

            # Display supplier information
            messagebox.showinfo(translate("Suppliers"), f"{translate('Supplier Information')}:\n{supplier_info}")

        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), translate("Suppliers Excel file not found."))
        except Exception as e:
            messagebox.showerror(translate("Error"), f"{translate('An error occurred while managing suppliers')}: {e}")

    def check_inventory(self):
        """Automates reordering of items based on stock levels."""
        df = pd.read_excel(ITEMS_FILE)
        reorder_items = df[df['Stock'] < df['Reorder_Threshold']]['Item']
        if not reorder_items.empty:
            messagebox.showinfo(translate("Reordering"), f"{translate('Reorder items')}: {', '.join(reorder_items)}")
        else:
            messagebox.showinfo(translate("Reordering"), translate("All items are above their reorder thresholds."))

    def generate_reports(self):
        report_window = tk.Toplevel(self.root)
        report_window.title(translate("Generate Reports"))
        center_window(report_window, w=300, h=300)
        report_window.configure(bg='#ADD8E6')

        tk.Label(report_window, text=translate("Reports"), font=('Arial', 14), bg='#ADD8E6').pack(pady=10)

        tk.Button(report_window, text=translate("Sales Report"), font=('Arial', 12), command=self.show_sales_report, bg='#87CEEB').pack(pady=10)
        tk.Button(report_window, text=translate("Item Popularity"), font=('Arial', 12), command=self.show_item_popularity, bg='#87CEEB').pack(pady=10)
        tk.Button(report_window, text=translate("Inventory Turnover"), font=('Arial', 12), command=self.show_inventory_turnover, bg='#87CEEB').pack(pady=10)
        tk.Button(report_window, text=translate("Profit Analysis"), font=('Arial', 12), command=self.show_profit_analysis, bg='#87CEEB').pack(pady=10)

    def show_sales_report(self):
        try:
            df = pd.read_excel(DAILY_SALES_FILE)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            df.set_index('Date', inplace=True)
            daily_sales = df.groupby('Date').sum()

            plt.figure(figsize=(10, 6))
            plt.plot(daily_sales.index, daily_sales['Amount'], marker='o', linestyle='-')
            plt.title(('Daily Sales'))
            plt.xlabel(('Date'))
            plt.ylabel(('Amount'))
            plt.grid(True)
            plt.show()

        except Exception as e:
            messagebox.showerror(translate("Report Error"), f"{translate('Failed to generate sales report')}: {e}")

    def show_item_popularity(self):
        df = pd.read_excel(ITEMS_FILE)
        # Check if the DataFrame is empty
        if df.empty or 'Item' not in df.columns or 'Sold' not in df.columns:
            messagebox.showinfo(translate("Item Popularity"), translate("No data available or incorrect format."))
            return

        # Find the item with the highest quantity sold
        most_popular_item = df.loc[df['Sold'].idxmax()]

        # Extract the item name and the sold count
        item_name = most_popular_item['Item']
        sold_count = most_popular_item['Sold']

        # Check if any items have been sold
        if sold_count == 0:
            messagebox.showinfo(translate("Item Popularity"), translate("No items sold yet."))
            return

        # Display the most popular item using a bar chart
        plt.figure(figsize=(6, 4))
        plt.bar([item_name], [sold_count], color='skyblue')
        plt.title(('Most Popular Item'))
        plt.xlabel(('Item'))
        plt.ylabel(('Quantity Sold'))
        plt.ylim(0, sold_count + 10)  # Add some space above the bar for better visualization
        plt.tight_layout()
        plt.show()

    def show_inventory_turnover(self):
        try:
            # Read the Excel file
            df = pd.read_excel(ITEMS_FILE)

            # Calculate total inventory and cost of goods sold
            df['Total_Inventory'] = df['Stock'] - df['Sold']  # Number of items left
            df['COGS'] = df['Sold'] * df['Price']  # Cost of goods sold

            # Sum total inventory and COGS
            total_inventory = df['Total_Inventory'].sum()
            total_cogs = df['COGS'].sum()

            # Initialize lists for items and turnover rates
            turnover_data = []

            # Calculate turnover rate for each item
            for _, row in df.iterrows():
                item = row['Item']
                count = row['Sold']
                initial_stock = row['Stock']

                if initial_stock == 0:
                    turnover_rate = 0
                else:
                    turnover_rate = count / initial_stock

                turnover_data.append((item, turnover_rate))

            # Check if any items have been processed
            if not turnover_data:
                messagebox.showinfo(translate("Inventory Turnover"), translate("No items have been processed yet."))
                return

            # Unzip items and rates for plotting
            items, rates = zip(*turnover_data)

            # Plot the turnover rates
            plt.figure(figsize=(10, 5))
            plt.bar(items, rates, color='skyblue')
            plt.title(('Inventory Turnover Rate'))
            plt.xlabel(('Item'))
            plt.ylabel(('Turnover Rate'))
            plt.xticks(rotation=45)
            plt.ylim(0, max(rates) * 1.1)  # Add some space above the bars
            plt.text(0.5, 0.5, f"{('Total Inventory')}: {total_inventory}\n{('Cost of Goods Sold')}: {total_cogs}", fontsize=12, ha='left', va='top')
            plt.tight_layout()
            plt.show()

        except Exception as e:
            messagebox.showerror(translate("Report Error"), f"{translate('Failed to generate inventory turnover report')}: {e}")

    def show_profit_analysis(self):
        try:
            df_sales = pd.read_excel(DAILY_SALES_FILE)
            df_items = pd.read_excel(ITEMS_FILE)

            sales_amount = df_sales['Amount'].sum()
            cost_of_goods_sold = df_items['Price'].sum()  # Assuming all items are sold

            profit = sales_amount - cost_of_goods_sold

            labels = ['Profit', 'Cost']
            sizes = [profit, cost_of_goods_sold]

            plt.figure(figsize=(7, 7))
            plt.pie(sizes, labels=(labels), autopct='%1.1f%%', startangle=140)
            plt.title(('Profit Analysis'))
            plt.show()
        except Exception as e:
            messagebox.showerror(translate("Analysis Error"), f"{translate('Failed to perform profit analysis')}: {e}")

    def calculate_total_inventory(self):
        """Calculates the total inventory (number of items left)."""
        df = pd.read_excel(ITEMS_FILE)
        df['Total_Inventory'] = df['Stock'] - df['Sold']
        total_inventory = df['Total_Inventory'].sum()
        return total_inventory

    def calculate_cogs(self):
        """Calculates the Cost of Goods Sold (COGS)."""
        df = pd.read_excel(ITEMS_FILE)
        df['COGS'] = df['Sold'] * df['Price']
        total_cogs = df['COGS'].sum()
        return total_cogs

    def calculate_total_revenue(self):
        """Calculates the total sales revenue."""
        df = pd.read_excel(ITEMS_FILE)
        df['Revenue'] = df['Sold'] * df['Price']
        total_revenue = df['Revenue'].sum()
        return total_revenue

    def calculate_profit(self):
        """Calculates the profit."""
        total_revenue = self.calculate_total_revenue()
        total_cogs = self.calculate_cogs()
        profit = total_revenue - total_cogs
        return profit

    def calculate_profit_margin(self):
        """Calculates the profit margin."""
        total_revenue = self.calculate_total_revenue()
        profit = self.calculate_profit()
        profit_margin = (profit / total_revenue * 100) if total_revenue != 0 else 0
        return profit_margin

    def calculate_turnover_rate(self):
        """Calculates inventory turnover rates for each item."""
        df = pd.read_excel(ITEMS_FILE)
        turnover_data = []
        for _, row in df.iterrows():
            item = row['Item']
            count = row['Sold']
            initial_stock = row['Stock']

            if initial_stock == 0:
                turnover_rate = 0
            else:
                turnover_rate = count / initial_stock

            turnover_data.append((item, turnover_rate))
        return turnover_data

    def plot_turnover_rates(self):
        """Plots inventory turnover rates."""
        turnover_data = self.calculate_turnover_rate()

        if not turnover_data:
            messagebox.showinfo(translate("Inventory Turnover"), translate("No items have been processed yet."))
            return

        items, rates = zip(*turnover_data)
        plt.figure(figsize=(10, 5))
        plt.bar(items, rates, color='skyblue')
        plt.title(('Inventory Turnover Rate'))
        plt.xlabel(('Item'))
        plt.ylabel(('Turnover Rate'))
        plt.xticks(rotation=45)
        plt.ylim(0, max(rates) * 1.1)
        plt.tight_layout()
        plt.show()

    def show_financial_summary(self):
        """Displays a financial summary including inventory, COGS, revenue, profit, and profit margin."""
        total_inventory = self.calculate_total_inventory()
        total_cogs = self.calculate_cogs()
        total_revenue = self.calculate_total_revenue()
        profit = self.calculate_profit()
        profit_margin = self.calculate_profit_margin()

        messagebox.showinfo(
            translate("Financial Summary"),
            f"{translate('Total Inventory')}: {total_inventory}\n"
            f"{translate('Cost of Goods Sold')}: {total_cogs}\n"
            f"{translate('Total Revenue')}: {total_revenue}\n"
            f"{translate('Profit')}: {profit}\n"
            f"{translate('Profit Margin')}: {profit_margin:.2f}%"
        )
    
    def calculate_historical_sales(self, period='M'):
        """Calculates and plots historical sales trends over time."""
        df = pd.read_excel(DAILY_SALES_FILE)
        if 'Date' not in df.columns:
            messagebox.showwarning(translate("Data Error"), translate("The dataset does not contain 'Date' information."))
            return

        # Ensure 'Date' column is in datetime format
        df['Date'] = pd.to_datetime(df['Date'])

        # Resample sales data by the specified period
        sales_trend = df.resample(period, on='Date')['Amount'].sum()

        plt.figure(figsize=(10, 5))
        sales_trend.plot(marker='o')
        for value in sales_trend:
            plt.axhline(y=value, color='r', linestyle='--', linewidth=0.5)
        plt.title(('Historical Sales Trend'))
        plt.xlabel(('Date'))
        plt.ylabel(('Units Sold'))
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def break_even_point_ui(self):
        # Create a Toplevel window

        self.break_even = tk.Toplevel(self.root)
        center_window(self.break_even, w=500, h=200)
        self.break_even.configure(bg="#f0f0f0")

        # Define StringVar for Entry widgets
        self.fixed_costs_var = tk.DoubleVar()
        self.variable_costs_per_unit_var = tk.DoubleVar()

        tk.Label(self.break_even, text=f"{translate('Fixed Costs')}:", bg="#f0f0f0").pack(pady=5)
        tk.Entry(self.break_even, textvariable=self.fixed_costs_var).pack(pady=5)

        tk.Label(self.break_even, text=f"{translate('Variable Costs Per Unit')}:", bg="#f0f0f0").pack(pady=5)
        tk.Entry(self.break_even, textvariable=self.variable_costs_per_unit_var).pack(pady=5)

        tk.Button(self.break_even, text=f"{translate('Calculate Break-even Point')}", command=self.calculate_break_even_point).pack(pady=10)
        
    def calculate_break_even_point(self):
        # Retrieve user inputs
        self.break_even.destroy()
        fixed_costs = self.fixed_costs_var.get()
        variable_costs_per_unit = self.variable_costs_per_unit_var.get()

        # Read Excel file
        try:
            df = pd.read_excel(ITEMS_FILE)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('Could not find the file')}: {ITEMS_FILE}")
            return

        if 'Price' not in df.columns:
            messagebox.showwarning(translate("Data Error"), translate("The dataset does not contain 'Price' information."))
            return

        average_price = df['Price'].mean()
        if average_price <= variable_costs_per_unit:
            messagebox.showwarning(translate("Data Error"), translate("Average price must be greater than variable costs per unit."))
            return

        break_even_units = fixed_costs / (average_price - variable_costs_per_unit)

        # Plot break-even analysis
        units = range(0, int(break_even_units * 2))
        total_costs = [fixed_costs + variable_costs_per_unit * u for u in units]
        total_revenue = [average_price * u for u in units]

        plt.figure(figsize=(10, 5))
        plt.plot(units, total_costs, label=('Total Costs'))
        plt.plot(units, total_revenue, label=('Total Revenue'))
        plt.axvline(x=break_even_units, color='red', linestyle='--', label=('Break-even Point'))
        plt.title(('Break-even Analysis'))
        plt.xlabel(('Units Sold'))
        plt.ylabel(('Cost/Revenue'))
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.text(0.5, 0.5, f"{('Break-even Point')}: {break_even_units:.2f} {('units')}", 
         fontsize=12, ha='center', va='center')
        plt.show()

    def compare_product_performance(self):
        """Compares product performance based on sales and profitability."""
        try:
            df = pd.read_excel(ITEMS_FILE)
        except FileNotFoundError:
            messagebox.showerror(translate("File Error"), f"{translate('Could not find the file')}: {ITEMS_FILE}")
            return

        required_columns = ['Price', 'Cost', 'Sold', 'Item']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            messagebox.showwarning(translate("Data Error"), f"{translate('The dataset is missing the following columns')}: {', '.join(missing_columns)}.")
            return

        # Calculate profit for each product
        df['Profit'] = (df['Price'] - df['Cost']) * df['Sold']
        
        # Group by item and sum the sales and profits
        performance_df = df.groupby('Item').agg({'Sold': 'sum', 'Profit': 'sum'}).sort_values(by='Profit', ascending=False)

        # Plot the product performance comparison
        fig, ax1 = plt.subplots(figsize=(12, 6))

        performance_df['Sold'].plot(kind='bar', ax=ax1, color='b', position=0, width=0.4, label=('Units Sold'))
        ax1.set_ylabel('Units Sold', color='b')
        ax1.tick_params(axis='y', labelcolor='b')
        ax1.set_xticklabels(performance_df.index, rotation=45, ha='right')

        ax2 = ax1.twinx()
        performance_df['Profit'].plot(kind='bar', ax=ax2, color='g', position=1, width=0.4, label=('Profit'))
        ax2.set_ylabel('Profit', color='g')
        ax2.tick_params(axis='y', labelcolor='g')

        plt.title(('Product Performance Comparison'))
        ax1.set_xlabel(('Item'))
        ax1.grid(True)
        plt.tight_layout()
        plt.show()

    def forecast_inventory(self, future_periods=12):
        """Forecasts future inventory needs using a simple linear regression model."""
        df = pd.read_excel(DAILY_SALES_FILE)
        if 'Date' not in df.columns:
            messagebox.showwarning(translate("Data Error"), translate("The dataset does not contain 'Date' information."))
            return

        # Ensure 'Date' column is in datetime format and set as index
        df['Date'] = pd.to_datetime(df['Date']).dt.normalize()
        df.set_index('Date', inplace=True)

        # Prepare data for forecasting
        sales_trend = df.resample('M')['Amount'].sum().reset_index()

        # Convert 'Date' back to datetime for plotting
        sales_trend['Date'] = pd.to_datetime(sales_trend['Date'])

        # Create a numerical index for the regression model
        sales_trend['Index'] = np.arange(len(sales_trend))

        # Train a simple linear regression model
        model = LinearRegression()
        model.fit(sales_trend[['Index']], sales_trend['Amount'])

        # Predict future sales
        future_times = np.arange(len(sales_trend), len(sales_trend) + future_periods)
        future_sales = model.predict(future_times.reshape(-1, 1))

        # Generate future dates for plotting
        last_date = sales_trend['Date'].iloc[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=future_periods, freq='M')

        # Plot forecast
        plt.figure(figsize=(10, 5))
        plt.plot(sales_trend['Date'], sales_trend['Amount'], label=('Historical Sales'))
        plt.plot(future_dates, future_sales, label=('Forecasted Sales'), linestyle='--')
        plt.title(('Inventory Forecast'))
        plt.xlabel(('Date'))
        plt.ylabel(('Units Sold'))
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def save_order_to_json(self):
        """Save the orders of all tables into a single JSON file without overwriting existing data."""
        current_time = datetime.now()
        date = current_time.strftime("%Y/%m/%d")
        time = current_time.strftime("%H:%M:%S") 
        folder = os.path.join('Receipts', 'Json', date)
        file = 'orders.json'
        file_path = os.path.join(folder, file)
        os.makedirs(folder, exist_ok=True)
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        receipt_ID = self.receipt_ID
        new_orders = []
        for order, remark in zip(self.orders, self.remarks):
            order_data = {
                'Item': order['item'],
                'Price': order['price'],
                'Qty': order['qty'],
                'Remark': remark if remark is not None else ""
            }
            new_orders.append(order_data)
        new_data = {'Receipt ID': receipt_ID, 'Time': time, 'order': new_orders}
        data.append(new_data)
        if not os.path.exists(file_path):
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)
        else:
            with open(file_path, 'w') as json_file:
                json.dump(data, json_file, indent=4)

    def get_last_table_id_from_json(self):
        """Load the last table ID from the JSON data."""
        current_time = datetime.now()
        date = current_time.strftime("%Y%m%d")
        time = current_time.strftime("%H%M%S") 
        folder = os.path.join('Receipts', 'Json', date)
        file = 'orders.json'
        file_path = os.path.join(folder, file)
        os.makedirs(folder, exist_ok=True)
        if not os.path.exists(file_path):
            data = []
            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file)
        else:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file )
            if data:
                try:
                    return data[-1]['Table ID'] + 1
                except (IndexError, KeyError):
                    return None
        return None

    def load_receipt_from_json(self, receipt):
        """Load orders from a JSON file for all tables."""
        self.details_window.destroy()
        self.table_number = receipt["Receipt ID"]
        for order in receipt["order"]:
            order_data = {
                'item': order['Item'],
                'price': order['Price'],
                'qty': order['Qty']
            }
            self.remarks.append(order['Remark'])
            self.orders.append(order_data)
            self.total_cost += order['Price']
        self.update_receipt_listbox()

    def show_historical_receipt_screen(self):
        root = tk.Tk()
        root.title("Select Date")
        cal = Calendar(root, selectmode='day', date_pattern='yyyyMMdd')
        cal.pack(pady=20)
        select_button = tk.Button(root, text="Select Date", command=lambda: self.show_receipts_for_date(cal.get_date(), root))
        select_button.pack(pady=10)
        root.mainloop()

    def load_receipts_by_date(self, date, folder='Receipts/Json'):
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

    def show_receipt_details(self, receipt):
        self.receipt_window.destroy()
        self.details_window = tk.Toplevel()
        details_window = self.details_window
        details_window.title("Receipt Details")

        tree = ttk.Treeview(details_window, columns=("Item", "Price", "Quantity"), show='headings')
        tree.heading("Item", text="Item")
        tree.heading("Price", text="Price")
        tree.heading("Quantity", text="Quantity")

        for order in receipt["order"]:
            tree.insert("", "end", values=(order['Item'], order['Price'], order['Qty']))

        tree.pack(fill=tk.BOTH, expand=True)

        button_frame = tk.Frame(details_window)
        button_frame.pack(fill=tk.X, pady=10)
        
        load_button = tk.Button(button_frame, text="Load", command=lambda: self.load_receipt_from_json(receipt))
        load_button.pack(side=tk.LEFT, padx=10)

        close_button = tk.Button(button_frame, text="Close", command=details_window.destroy)
        close_button.pack(side=tk.RIGHT, padx=10)

    def show_receipts_for_date(self, date, root):
        root.destroy()  # Destroy the root window when a date is selected
        receipts = self.load_receipts_by_date(date)
        
        if not receipts:
            messagebox.showinfo("No Receipts", "No receipts found for the selected date.")
            return
        self.receipt_window = tk.Toplevel()
        receipts_window = self.receipt_window
        receipts_window.title(f"Receipts for {date}")
        tree = ttk.Treeview(receipts_window, columns=("Receipt ID", "Time"), show='headings')
        tree.heading("Receipt ID", text="Receipt ID")
        tree.heading("Time", text="Time")

        for receipt in receipts:
            tree.insert("", "end", values=(receipt["Receipt ID"], receipt["Time"]))

        tree.pack(fill=tk.BOTH, expand=True)

        tree.bind("<Double-1>", lambda event: self.show_receipt_details(receipts[int(tree.selection()[0].replace('I00', ''))-1]))

        back_button = tk.Button(receipts_window, text="Back", command=receipts_window.destroy)
        back_button.pack(pady=10)

    def load_data_table_data(self):
        filename = 'Json/table_data.json'
        if filename:
            with open(filename, "r") as file:
                self.tables_data = json.load(file)

    def load_before_continue(self):
        filename = 'Json/table_data.json'
        try:
            with open(filename, "r") as file:
                tables = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            tables = []
        if tables[self.table]["order"] is not None:
            for order in tables[self.table]["order"]:
                order_data = {
                    'item': order['Item'],
                    'price': order['Price'],
                    'qty': order['Qty']
                }
                self.remarks.append(order['Remark'])
                self.orders.append(order_data)
                self.total_cost += order['Price']
        else:
            self.orders = []

    def save_before_exit(self):
        filename = 'Json/table_data.json'
        data = []
        try:
            with open(filename, "r") as file:
                tables = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            tables = []
        for order, remark in zip(self.orders, self.remarks):
            order_data = {
                'Item': order['item'],
                'Price': order['price'],
                'Qty': order['qty'],
                'Remark': remark if remark is not None else ""
            }
            data.append(order_data)
        tables[self.table]["order"] = data
        tables[self.table]["last change"] = datetime.now().strftime("%Y/%m/%d (%H:%M:%S)")
        with open(filename, "w") as file:
            json.dump(tables, file, indent=4)

    def auto_save(self):
        self.save_before_exit()
        self.root.after(1000, self.auto_save)

    def back_to_table_app(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.root.destroy()
        main_table_app(self.role)

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
        center_window(self.edit_window, w=400, h=300)
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
        self.tables[f"table{table_id}"] = {"id": table_id, "status": "Available", "x": 50 + (table_id % 5) * 100, "y": 50 + (table_id // 5) * 100, "remark": "", "order":[], "last change": ""}
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

    def open_order_system(self, table_id):
        self.root.destroy()
        main_order_app(self.role, table_id)

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


def main_table_app(role):
    global app
    root = tk.Tk()
    app = TableMapApp(root, role)
    root.mainloop()

def main_order_app(role, table_id):
    global app
    root = tk.Tk()
    app = RetailBillingSystem(root, role, table_id)
    root.mainloop()

def login_out(oldroot):
    oldroot.destroy()
    root = tk.Tk()
    UserAuthentication(root)

if __name__ == "__main__":
    root = tk.Tk()
    UserAuthentication(root)
    root.mainloop()
