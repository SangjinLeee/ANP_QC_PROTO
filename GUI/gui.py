import tkinter as tk
from tkinter import messagebox
import subprocess
import mysql.connector
import psutil
import sys

# Define the absolute paths for each script
COA_FILLING_PATH = "C:/Users/EugeneLee/OneDrive - ANP ENERTECH INC/Documents/GitHub/ANP_QC_PROTO/COA/coa_filling.py"
AUTO_UPDATE_POLL_PATH = "C:/Users/EugeneLee/OneDrive - ANP ENERTECH INC/Documents/GitHub/ANP_QC_PROTO/qcdb/auto_update_poll.py"
IMPORT_CSV_PATH = "C:/Users/EugeneLee/OneDrive - ANP ENERTECH INC/Documents/GitHub/ANP_QC_PROTO/qcdb/import_csv_to_db.py"

# Database connection function for validation
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='mysql',
            database='qcdb'
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Database connection failed: {err}")
        return None

# Validate if the entered lot number exists in the database
def validate_lot_number(lot_number):
    connection = connect_to_database()
    if not connection:
        return False

    cursor = connection.cursor()
    cursor.execute("SELECT lot_number FROM lots WHERE lot_number = %s", (lot_number,))
    result = cursor.fetchone()
    connection.close()
    return result is not None

# Function to check status based on lot_number and/or product_type
def get_lot_status(lot_number=None, product_type=None):
    connection = connect_to_database()
    if not connection:
        return None

    cursor = connection.cursor(dictionary=True)
    query = "SELECT lot_number, product, status FROM lots WHERE 1=1"
    params = []

    if lot_number:
        query += " AND lot_number = %s"
        params.append(lot_number)

    if product_type:
        query += " AND product = %s"
        params.append(product_type)

    cursor.execute(query, params)
    results = cursor.fetchall()
    connection.close()
    return results

# Function to handle the check status button click
def check_status():
    lot_number = lot_number_entry.get().strip()
    product_type = product_type_entry.get().strip()

    if not lot_number and not product_type:
        messagebox.showwarning("Warning", "Please enter at least one of Lot Number or Product Type.")
        return

    results = get_lot_status(lot_number, product_type)
    if not results:
        messagebox.showinfo("Result", "No matching lots found.")
    else:
        result_message = "\n".join([
            f"Lot Number: {row['lot_number']}, Product: {row['product']}, Status: {row['status']}"
            for row in results
        ])
        messagebox.showinfo("Result", result_message)

# Function to check if auto-update is running and run it if not
def run_auto_update():
    for process in psutil.process_iter(['cmdline']):
        if process.info['cmdline'] and "auto_update_poll.py" in process.info['cmdline']:
            messagebox.showinfo("Info", "Auto-update is already running.")
            return

    try:
        subprocess.Popen([sys.executable, AUTO_UPDATE_POLL_PATH], shell=True)
        messagebox.showinfo("Info", "Auto-update started successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start auto-update: {e}")

# Function to stop auto-update, run import_csv_to_db.py, then restart auto-update
def run_import_csv():
    try:
        # Stop auto-update if running
        for process in psutil.process_iter(['cmdline']):
            if process.info['cmdline'] and "auto_update_poll.py" in process.info['cmdline']:
                process.terminate()
                process.wait()
                break

        # Run import_csv_to_db.py
        result = subprocess.run(
            [sys.executable, IMPORT_CSV_PATH],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            messagebox.showinfo("Info", "CSV data imported successfully.")
            print("Import CSV Output:\n", result.stdout)
        else:
            messagebox.showerror("Error", f"CSV import failed:\n{result.stderr}")
            print("Import CSV Error:\n", result.stderr)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to import CSV: {e}")
        print(f"Exception during CSV import: {e}")

    finally:
        run_auto_update()

# Function to run coa_filling.py with the provided lot number
def run_coa_filling():
    lot_number = lot_number_entry.get().strip()
    if not lot_number:
        messagebox.showwarning("Warning", "Please enter a lot number.")
        return

    if not validate_lot_number(lot_number):
        messagebox.showerror("Error", "Invalid lot number. Please enter a correct lot number.")
        return

    try:
        subprocess.run([sys.executable, COA_FILLING_PATH, lot_number], check=True, shell=True)
        messagebox.showinfo("Info", f"COA filled for lot number: {lot_number}")
    except subprocess.CalledProcessError as e:
        if "PermissionError" in str(e):
            messagebox.showerror("Error", "Please close the COA file and try again.")
        else:
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fill COA: {e}")

# GUI setup
root = tk.Tk()
root.title("QC Database GUI")
root.geometry("400x400")

# Buttons and their commands
auto_update_button = tk.Button(root, text="Run Auto Update Hourly", command=run_auto_update)
auto_update_button.pack(pady=10)

import_csv_button = tk.Button(root, text="Import CSV Now", command=run_import_csv)
import_csv_button.pack(pady=10)

coa_button = tk.Button(root, text="Generate COA", command=run_coa_filling)
coa_button.pack(pady=10)

# Entry for lot number
lot_number_label = tk.Label(root, text="Enter Lot Number for COA:")
lot_number_label.pack()
lot_number_entry = tk.Entry(root)
lot_number_entry.pack(pady=5)

# Entry for checking status
status_lot_number_label = tk.Label(root, text="Status - Lot Number:")
status_lot_number_label.pack()
lot_number_entry = tk.Entry(root)
lot_number_entry.pack(pady=5)

status_product_type_label = tk.Label(root, text="Status - Product Type:")
status_product_type_label.pack()
product_type_entry = tk.Entry(root)
product_type_entry.pack(pady=5)

check_status_button = tk.Button(root, text="Check Status", command=check_status)
check_status_button.pack(pady=10)

# Run the GUI loop
root.mainloop()
