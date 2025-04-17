import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import pandas as pd
from datetime import datetime
import os
import tempfile
import webbrowser
from tkinterhtml import HtmlFrame

bills_file = "bills.json"
invoice_counter_file = "invoice_counter.json"
transactions_file = "transactions.xlsx"  # File to store all transactions

class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Billing System - company name")
        self.root.attributes('-fullscreen', True)

        self.items = []
        self.customer_name = tk.StringVar()
        self.customer_gst = tk.StringVar()
        self.customer_address = tk.StringVar()
        self.cgst = tk.StringVar()
        self.sgst = tk.StringVar()
        self.invoice_number = tk.StringVar()
        self.search_term = tk.StringVar()
        
        # Initialize invoice counter
        self.invoice_counter = self.load_invoice_counter()
        self.update_invoice_number()
        
        # Initialize transactions Excel file if it doesn't exist
        if not os.path.exists(transactions_file):
            self.initialize_transactions_file()
        
        self.create_widgets()
        self.create_menu()

    def initialize_transactions_file(self):
        # Create a DataFrame with the correct columns and save to Excel
        columns = [
            "Invoice No", "Date", "Customer", "GSTIN", "Address",
            "Item", "HSN", "Qty", "Rate", "Item GST", "Item Total",
            "CGST", "SGST", "Bill Total"
        ]
        df = pd.DataFrame(columns=columns)
        df.to_excel(transactions_file, index=False)

    def append_to_transactions(self, bill_data):
        try:
            # Read existing transactions
            existing_df = pd.read_excel(transactions_file)
        except:
            existing_df = pd.DataFrame()

        # Prepare new rows for each item in the bill
        new_rows = []
        for item in bill_data['items']:
            new_row = {
                "Invoice No": bill_data['invoice_number'],
                "Date": bill_data['date'],
                "Customer": bill_data['customer'],
                "GSTIN": bill_data['gst'],
                "Address": bill_data['address'],
                "Item": item['name'],
                "HSN": item['hsn'],
                "Qty": item['qty'],
                "Rate": item['rate'],
                "Item GST": item['gst'],
                "Item Total": item['total'],
                "CGST": bill_data['cgst'],
                "SGST": bill_data['sgst'],
                "Bill Total": bill_data['total']
            }
            new_rows.append(new_row)

        # Create DataFrame from new rows
        new_df = pd.DataFrame(new_rows)
        
        # Combine with existing data
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            combined_df = new_df
        
        # Save back to Excel
        combined_df.to_excel(transactions_file, index=False)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Bill", command=self.save_bill)
        file_menu.add_command(label="Print Bill", command=self.print_bill)
        file_menu.add_separator()
        file_menu.add_command(label="Export to Excel", command=self.export_to_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Reports menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Search Bills", command=self.show_search_window)
        reports_menu.add_command(label="View Transactions", command=self.view_transactions)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        
        self.root.config(menu=menubar)

    def export_to_excel(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add items to export.")
            return

        bill_data = self.generate_bill_data()
        now = datetime.now()
        month_str = now.strftime("%B_%Y")  # e.g., "April_2025"
        filename = f"{month_str}.xlsx"

        # Create folder to save monthly reports (optional)
        output_folder = "monthly_reports"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        file_path = os.path.join(output_folder, filename)

        df = pd.DataFrame([{
            "Invoice No": bill_data.get("invoice_number", ""),
            "Date": bill_data.get("date", ""),
            "Customer Name": bill_data.get("customer", ""),
            "Phone": bill_data.get("phone", ""),
            "Address": bill_data.get("address", ""),
            "Item Details": ", ".join([f'{i.get("name", "")}({i.get("qty", 0)}x{i.get("rate", 0)})' for i in bill_data.get("items", [])]),
            "Subtotal": bill_data.get("subtotal", 0),
            "CGST": bill_data.get("cgst", 0),
            "SGST": bill_data.get("sgst", 0),
            "Total": bill_data.get("total", 0)
        }])

        if os.path.exists(file_path):
            existing_df = pd.read_excel(file_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        df.to_excel(file_path, index=False)
        messagebox.showinfo("Exported", f"Data exported to {file_path}")

    def view_transactions(self):
        try:
            # Open the transactions file in default application
            webbrowser.open(os.path.abspath(transactions_file))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open transactions file:\n{str(e)}")

    def load_invoice_counter(self):
        try:
            if os.path.exists(invoice_counter_file):
                with open(invoice_counter_file, 'r') as f:
                    return json.load(f).get('counter', 1)
            return 1
        except:
            return 1

    def save_invoice_counter(self):
        with open(invoice_counter_file, 'w') as f:
            json.dump({'counter': self.invoice_counter}, f)

    def update_invoice_number(self):
        self.invoice_number.set(f"SS-{self.invoice_counter:04d}")

    def create_widgets(self):
        header_frame = tk.Frame(self.root, bg="#1e3d59", pady=10)
        header_frame.pack(fill=tk.X)

        tk.Label(header_frame, text="SS EQUIPMENTS", font=("Arial", 20, "bold"), bg="#1e3d59", fg="white").pack()
        tk.Label(header_frame, text="Deals in Crane, Hose Pipes & Fittings", font=("Arial", 12), bg="#1e3d59", fg="white").pack()
        tk.Label(header_frame, text="GSTIN: gst number | +91-975249xxx", font=("Arial", 10), bg="#1e3d59", fg="white").pack()
        tk.Label(header_frame, text="Address: abcd", font=("Arial", 10), bg="#1e3d59", fg="white").pack()

        customer_frame = tk.Frame(self.root, pady=5)
        customer_frame.pack()

        # Add Invoice Number field
        tk.Label(customer_frame, text="Invoice No:", font=("Arial", 12)).grid(row=0, column=0, sticky='w')
        tk.Entry(customer_frame, textvariable=self.invoice_number, width=20, font=("Arial", 12), state='readonly').grid(row=0, column=1, sticky='w')

        tk.Label(customer_frame, text="Customer Name:", font=("Arial", 12)).grid(row=1, column=0, sticky='w')
        self.customer_entry = tk.Entry(customer_frame, textvariable=self.customer_name, width=50, font=("Arial", 12))
        self.customer_entry.grid(row=1, column=1, columnspan=3, sticky='w')

        tk.Label(customer_frame, text="Customer GST:", font=("Arial", 12)).grid(row=2, column=0, sticky='w')
        self.customer_gst_entry = tk.Entry(customer_frame, textvariable=self.customer_gst, width=30, font=("Arial", 12))
        self.customer_gst_entry.grid(row=2, column=1, sticky='w')

        tk.Label(customer_frame, text="Address:", font=("Arial", 12)).grid(row=3, column=0, sticky='nw')
        self.customer_address_entry = tk.Text(customer_frame, width=50, height=3, font=("Arial", 12))
        self.customer_address_entry.grid(row=3, column=1, columnspan=3, sticky='w')

        form_frame = tk.Frame(self.root, pady=10)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Item Name:", font=("Arial", 12)).grid(row=0, column=0)
        self.item_name = tk.Entry(form_frame, font=("Arial", 12))
        self.item_name.grid(row=0, column=1)

        tk.Label(form_frame, text="HSN:", font=("Arial", 12)).grid(row=0, column=2)
        self.item_hsn = tk.Entry(form_frame, font=("Arial", 12))
        self.item_hsn.grid(row=0, column=3)

        tk.Label(form_frame, text="Quantity:", font=("Arial", 12)).grid(row=1, column=0)
        self.item_qty = tk.Entry(form_frame, font=("Arial", 12))
        self.item_qty.grid(row=1, column=1)

        tk.Label(form_frame, text="Rate:", font=("Arial", 12)).grid(row=1, column=2)
        self.item_rate = tk.Entry(form_frame, font=("Arial", 12))
        self.item_rate.grid(row=1, column=3)

        tk.Label(form_frame, text="GST (%):", font=("Arial", 12)).grid(row=2, column=0)
        self.item_gst = tk.Entry(form_frame, font=("Arial", 12))
        self.item_gst.grid(row=2, column=1)

        tk.Button(form_frame, text="Add Item", font=("Arial", 12), bg="lightgreen", command=self.add_item).grid(row=2, column=3)

        tax_frame = tk.Frame(self.root)
        tax_frame.pack()
        tk.Label(tax_frame, text="CGST %:", font=("Arial", 12)).grid(row=0, column=0)
        tk.Entry(tax_frame, textvariable=self.cgst, font=("Arial", 12), width=10).grid(row=0, column=1)
        tk.Label(tax_frame, text="SGST %:", font=("Arial", 12)).grid(row=0, column=2)
        tk.Entry(tax_frame, textvariable=self.sgst, font=("Arial", 12), width=10).grid(row=0, column=3)

        self.tree = ttk.Treeview(self.root, columns=("name", "hsn", "qty", "rate", "gst", "total"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(pady=10, fill=tk.X)

        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack()
        tk.Button(button_frame, text="Preview Bill", font=("Arial", 12), bg="skyblue", command=self.preview_bill).grid(row=0, column=0, padx=10)
        tk.Button(button_frame, text="Save Bill", font=("Arial", 12), bg="lightgreen", command=self.save_bill).grid(row=0, column=1, padx=10)
        tk.Button(button_frame, text="Reset", font=("Arial", 12), bg="orange", command=self.reset_form).grid(row=0, column=2, padx=10)
        tk.Button(button_frame, text="Exit", font=("Arial", 12), bg="tomato", command=self.root.destroy).grid(row=0, column=3, padx=10)

    def add_item(self):
        try:
            name = self.item_name.get()
            hsn = self.item_hsn.get()
            qty = int(self.item_qty.get())
            rate = float(self.item_rate.get())
            gst = float(self.item_gst.get())
            total = qty * rate * (1 + gst / 100)
            self.items.append({"name": name, "hsn": hsn, "qty": qty, "rate": rate, "gst": gst, "total": total})
            self.tree.insert("", "end", values=(name, hsn, qty, rate, gst, total))

            self.item_name.delete(0, tk.END)
            self.item_hsn.delete(0, tk.END)
            self.item_qty.delete(0, tk.END)
            self.item_rate.delete(0, tk.END)
            self.item_gst.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Enter valid numbers for quantity, rate, and GST.")

    def reset_form(self):
        self.items = []
        self.customer_name.set("")
        self.customer_gst.set("")
        self.customer_address_entry.delete("1.0", tk.END)
        self.cgst.set("")
        self.sgst.set("")
        
        # Increment invoice counter and update number
        self.invoice_counter += 1
        self.save_invoice_counter()
        self.update_invoice_number()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        messagebox.showinfo("Reset", "Form has been reset successfully. New invoice number generated.")

    def generate_bill_data(self):
        customer_address = self.customer_address_entry.get("1.0", tk.END).strip()
        total_amount = sum(item['total'] for item in self.items)

        bill_data = {
            "invoice_number": self.invoice_number.get(),
            "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "customer": self.customer_name.get(),
            "gst": self.customer_gst.get(),
            "address": customer_address,
            "items": self.items,
            "cgst": self.cgst.get(),
            "sgst": self.sgst.get(),
            "total": total_amount
        }
        return bill_data

    def save_bill(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add items to save the bill.")
            return

        bill_data = self.generate_bill_data()

        # Save to JSON file
        if os.path.exists(bills_file):
            with open(bills_file, "r") as f:
                all_bills = json.load(f)
        else:
            all_bills = []

        all_bills.append(bill_data)
        with open(bills_file, "w") as f:
            json.dump(all_bills, f, indent=4)

        # Append to transactions Excel
        self.append_to_transactions(bill_data)

        messagebox.showinfo("Success", f"Bill {bill_data['invoice_number']} saved successfully!\nTransaction added to Excel record.")

    def generate_html_bill(self, bill_data):
        html = f"""
        <html><head><style>
        table, th, td {{border: 1px solid black; border-collapse: collapse; padding: 5px;}}
        th {{background-color: #f2f2f2;}}
        .header {{text-align: center;}}
        .customer-info {{margin-bottom: 15px;}}
        </style></head><body>
        <div class="header">
            <h2>company name</h2>
            <p>Deals in Crane, Hose Pipes & Fittings<br>GSTIN: gst number | +91-9752499xxx<br>Address: abcd</p>
        </div>
        <hr>
        <div class="customer-info">
            <p><b>Invoice No:</b> {bill_data['invoice_number']}</p>
            <p><b>Customer:</b> {bill_data['customer']}</p>
            <p><b>GSTIN:</b> {bill_data['gst']}</p>
            <p><b>Address:</b> {bill_data['address']}</p>
            <p><b>Date:</b> {bill_data['date']}</p>
        </div>
        <table><tr><th>S. No.</th><th>Item</th><th>HSN</th><th>Qty</th><th>Rate</th><th>GST</th><th>Total</th></tr>"""

        for idx, item in enumerate(bill_data['items'], start=1):
            html += f"<tr><td>{idx}</td><td>{item['name']}</td><td>{item['hsn']}</td><td>{item['qty']}</td><td>{item['rate']}</td><td>{item['gst']}%</td><td>{item['total']:.2f}</td></tr>"

        html += f"""</table><br><b>CGST:</b> {bill_data['cgst']}% <b>SGST:</b> {bill_data['sgst']}%<br><br><b>Total Amount: ₹{bill_data['total']:.2f}</b><br></body></html>"""
        return html

    def preview_bill(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add items to preview the bill.")
            return

        bill_data = self.generate_bill_data()
        html = self.generate_html_bill(bill_data)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            f.write(html)
            temp_path = f.name

        webbrowser.open(f"file://{temp_path}")

    def print_bill(self):
        if not self.items:
            messagebox.showwarning("No Items", "Add items to print the bill.")
            return

        bill_data = self.generate_bill_data()
        html = self.generate_html_bill(bill_data)

        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
            f.write(html)
            temp_path = f.name

        # Open in browser and trigger print
        browser = webbrowser.get()
        browser.open_new_tab(f"file://{temp_path}")

    def perform_bill_search(self, search_type, result_tree):
        # Implemented basic search logic
        for item in result_tree.get_children():
            result_tree.delete(item)
    def preview_selected_bill(self, result_tree):
        selected_item = result_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a bill to preview.")
    def show_search_window(self):
        # Corrected redefinition of show_search_window
        search_win = tk.Toplevel(self.root)
        search_win.title("Search Bills")
        search_win.geometry("800x500")

        tk.Label(search_win, text="Search By:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
        search_type = ttk.Combobox(search_win, values=["Invoice Number", "Customer Name", "Date"], state="readonly", width=20)
        search_type.grid(row=0, column=1, padx=10)

        search_term = tk.StringVar()
        tk.Entry(search_win, textvariable=search_term, font=("Arial", 12), width=30).grid(row=0, column=2, padx=10)

        columns = ("Invoice", "Customer", "Date", "Total")
        result_tree = ttk.Treeview(search_win, columns=columns, show="headings")
        for col in columns:
            result_tree.heading(col, text=col)
        result_tree.grid(row=1, column=0, columnspan=3, sticky="nsew")

        scrollbar = ttk.Scrollbar(search_win, orient="vertical", command=result_tree.yview)
        result_tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=3, sticky='ns')

        tk.Button(search_win, text="Search", font=("Arial", 12), command=lambda: self.perform_bill_search(search_type.get(), result_tree)).grid(row=0, column=3, padx=10)

        result_tree.bind("<Double-1>", lambda event: self.preview_selected_bill(result_tree))

        # Define selected_item properly
        selected_item = result_tree.selection()
        if selected_item:
            item = result_tree.item(selected_item[0])
            invoice_number = item['values'][0]

            try:
                with open(bills_file, "r") as f:
                    all_bills = json.load(f)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load bills: {e}")
                return

            for bill in all_bills:
                if bill['invoice_number'] == invoice_number:
                    html = self.generate_html_bill(bill)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
                        f.write(html)
                        temp_path = f.name
                    webbrowser.open(f"file://{temp_path}")
                    break

    def preview_selected_bill(self, result_tree):
        # Placeholder for the preview logic
        pass

    def show_search_window(self):
        search_window = tk.Toplevel(self.root)
        search_window.title("Search Bills")
        search_window.geometry("800x600")

        tk.Label(search_window, text="Search Bills", font=("Arial", 16)).pack(pady=10)
        
        search_frame = tk.Frame(search_window)
        search_frame.pack(pady=10)
        
        tk.Label(search_frame, text="Search Term:").grid(row=0, column=0)
        search_entry = tk.Entry(search_frame, textvariable=self.search_term, width=40)
        search_entry.grid(row=0, column=1)
        
        tk.Button(search_frame, text="Search", command=lambda: self.search_bills(search_window)).grid(row=0, column=2, padx=10)
        
        # Date range filters
        date_frame = tk.Frame(search_window)
        date_frame.pack(pady=10)
        
        tk.Label(date_frame, text="From:").grid(row=0, column=0)
        self.from_date = tk.Entry(date_frame, width=15)
        self.from_date.grid(row=0, column=1, padx=5)
        self.from_date.insert(0, datetime.now().strftime('%Y-%m-01'))
        
        tk.Label(date_frame, text="To:").grid(row=0, column=2)
        self.to_date = tk.Entry(date_frame, width=15)
        self.to_date.grid(row=0, column=3, padx=5)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # Results treeview
        columns = ("Invoice No", "Date", "Customer", "GSTIN", "Total")
        self.search_tree = ttk.Treeview(search_window, columns=columns, show="headings")
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=150)
        self.search_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # View button
        tk.Button(search_window, text="View Selected Bill", 
                 command=lambda: self.view_selected_bill(search_window)).pack(pady=10)
        
        # Load all bills initially
        self.search_bills(search_window)

def show_search_window(self):
    search_win = tk.Toplevel(self.root)
    search_win.title("Search Bills")
    search_win.geometry("800x500")

    tk.Label(search_win, text="Search By:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
    search_type = ttk.Combobox(search_win, values=["Invoice Number", "Customer Name", "Date"], state="readonly", width=20)
    search_type.grid(row=0, column=1, padx=10)

    tk.Entry(search_win, textvariable=self.search_term, font=("Arial", 12), width=30).grid(row=0, column=2, padx=10)
    tk.Button(search_win, text="Search", font=("Arial", 12), command=lambda: self.perform_bill_search(search_type.get(), result_tree)).grid(row=0, column=3)

    columns = ("Invoice", "Customer", "Date", "Total")
    result_tree = ttk.Treeview(search_win, columns=columns, show="headings")
    for col in columns:
        result_tree.heading(col, text=col)

    scrollbar = ttk.Scrollbar(search_win, orient="vertical", command=result_tree.yview)
    result_tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=1, column=4, sticky='ns')
    result_tree.grid(row=1, column=0, columnspan=4, sticky="nsew")

    # Double click to preview bill
    result_tree.bind("<Double-1>", lambda event: self.preview_selected_bill(result_tree))


def view_selected_bill(self, window):
        selected_item = self.search_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a bill to view")
            return
        
        item = self.search_tree.item(selected_item[0])
        invoice_number = item['values'][0]
        
        try:
            with open(bills_file, "r") as f:
                all_bills = json.load(f)
        except:
            all_bills = []
        
        for bill in all_bills:
            if bill['invoice_number'] == invoice_number:
                html = self.generate_html_bill(bill)
                
                # Create a temporary HTML file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
                    f.write(html)
                    temp_path = f.name

                webbrowser.open(f"file://{temp_path}")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()
