# ems.py
from customtkinter import *
from PIL import Image # Keep this import
from tkinter import ttk, messagebox, filedialog, StringVar, VERTICAL, END
import database  # Use your refined database module
import shutil
import csv
from datetime import datetime
# from PIL import ImageTk # Not strictly needed if CTkImage is handling this internally
try:
    from tkcalendar import DateEntry
except ImportError:
    messagebox.showerror('Missing Dependency', 'Please install tkcalendar: pip install tkcalendar')
    raise
import uuid
import os
from customtkinter import CTkFont # Explicitly import CTkFont
import pandas as pd # Import pandas for Excel operations

# --- Global Variables ---
current_editing_id = None
bg_img_ctk = None # Keep reference for background image
_bg_pil_image_ref = None # Keep reference for background PIL image
_logo_pil_image_ref = None # Keep reference for logo PIL image
profile_picture_path = "" # Global variable for profile picture path
profile_image_ctk = None # Keep reference for profile image CTkImage

sort_options = ['ID', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Status', 'Date of Birth', 'Date of Joining']

# Define option lists here (before window creation if used by CTkImage, and before widget creation)
role_option = ['Web Developer', 'Python Developer', 'Project Manager', 'Accountant', 'HR Specialist', 'Data Analyst',
               'IT Support', 'Marketing Manager',
                'Sales Representative', 'Graphic Designer', 
                'General Worker', 'security','Driver','Receptionist',
                'Admin-finance','Admin-HR','Admin-IT','Admin-Marketing',
                'Admin-Sales','Admin-Security','Admin-Maintenance',
                'Admin-Cleaning','Admin-Cooking','Admin-Laundry','Admin-Security',
                'Admin-Maintenance']
gender_option = ['Male', 'Female', 'Other']
status_option = ['Active', 'Inactive']
search_option = ['ID', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Status', 'Date of Birth', 'Date of Joining']

# --- Create the main window and frames ---
window = CTk()
window.title('Employee Management System')
window.configure(fg_color='#0A1128')
window.geometry('1300x750') # Set initial window size for better fit
window.resizable(True, True)

# Variables for Sorting and Filtering
sort_by_var = StringVar()
sort_order_var = StringVar(value='ASC')
filter_gender_var = StringVar(value='All')
filter_status_var = StringVar(value='Active')

# --- Functions ---

def treeview_data(data=None):
    tree.delete(*tree.get_children())
    if data is None:
        rows = database.fetch_all_employees()
    else:
        rows = data

    for row in rows:
        status = row['status'] if 'status' in row.keys() else 'Active'
        tag = 'active' if status == 'Active' else 'inactive'

        employee_id = row['id'] if 'id' in row.keys() else None
        name = row['name'] if 'name' in row.keys() else None
        phone = row['phone'] if 'phone' in row.keys() else None
        role = row['role'] if 'role' in row.keys() else None
        gender = row['gender'] if 'gender' in row.keys() else None
        salary = row['salary'] if 'salary' in row.keys() else None
        date_of_birth = row['date_of_birth'] if 'date_of_birth' in row.keys() else None
        date_of_joining = row['date_of_joining'] if 'date_of_joining' in row.keys() else None
        # profile_picture_path = row['profile_picture_path'] if 'profile_picture_path' in row.keys() else '' # Don't add to treeview directly, use for load

        # Calculate age from date_of_birth for the treeview display
        age = 'N/A'
        if date_of_birth:
            try:
                birth_date = datetime.strptime(str(date_of_birth), '%Y-%m-%d')
                today = datetime.today()
                age_val = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                age = str(age_val)
            except Exception:
                pass # age remains 'N/A'

        tree.insert('', 'end', values=(employee_id, name, phone, role, gender, salary, status, date_of_birth, date_of_joining, age), tags=(tag,))
    tree.tag_configure('active', foreground='white', font=('arial', 11))
    tree.tag_configure('inactive', foreground='gray', font=('arial', 11))


def get_next_employee_id():
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM employees")
        max_id = cursor.fetchone()[0]
        if max_id is None:
             return 'EMP001'
        return f'EMP{max_id+1:03d}'
    except Exception as e:
        print(f"Error getting next employee ID: {e}")
        return 'EMP_Error'


def clear_input_fields(event=None):
    global current_editing_id, profile_picture_path
    current_editing_id = None
    profile_picture_path = "" # Clear profile picture path
    display_profile_picture("default_profile.png") # Display default image

    idEntry.configure(state='normal')
    idEntry.delete(0, END)
    idEntry.insert(0, get_next_employee_id())
    idEntry.configure(state='disabled')
    nameEntry.delete(0, END)
    phoneEntry.delete(0, END)
    roleBox.set(role_option[0])
    genderbox.set(gender_option[0])
    salaryEntry.delete(0, END)
    statusBox.set('Active')
    # Use datetime.today() for DateEntry clear
    dobEntry.set_date(datetime.today())
    dojEntry.set_date(datetime.today())
    ageEntry.configure(state='normal')
    ageEntry.delete(0, END)
    ageEntry.configure(state='readonly')
    nameEntry.focus_set()

def add_employee_action(event=None):
    global profile_picture_path
    try:
        dob_date = dobEntry.get_date()
        doj_date = dojEntry.get_date()

        dob_str = dob_date.strftime('%Y-%m-%d') if dob_date else None
        doj_str = doj_date.strftime('%Y-%m-%d') if doj_date else None
    except ValueError:
        messagebox.showerror('Date Error', 'Please enter valid dates in YYYY-MM-DD format.')
        return

    name = nameEntry.get().title()
    phone = phoneEntry.get()
    role = roleBox.get()
    gender = genderbox.get()
    salary = salaryEntry.get()
    status = statusBox.get()

    if not all([name, phone, salary]):
        messagebox.showerror('Error', 'Name, Phone, and Salary fields are required')
        return
    try:
        float(salary)
    except ValueError:
        messagebox.showerror('Error', 'Salary must be a valid number')
        return

    # Include profile_picture_path in employee_data
    employee_data = (name, phone, role, gender, salary, status, dob_str, doj_str, profile_picture_path)
    database.insert_employee(employee_data)
    messagebox.showinfo('Success', 'Employee added successfully!')
    treeview_data()
    clear_input_fields()


def search_employee_action():
    query = searchEntry.get()
    option = searchbox.get()

    column_map = {'ID': 'id', 'Name': 'name', 'Phone': 'phone', 'Role': 'role', 'Gender': 'gender',
                      'Salary': 'salary', 'Status': 'status', 'Date of Birth': 'date_of_birth', 'Date of Joining': 'date_of_joining'}
    db_column = column_map.get(option)
    if not db_column or query == '':
        treeview_data()
        return

    try:
        results = database.fetch_employees_by_criteria(db_column, query)
        if results:
            treeview_data(results)
        else:
            tree.delete(*tree.get_children())
    except ValueError as e:
        messagebox.showerror('Error', f"Search error: {e}")
        tree.delete(*tree.get_children())
    except Exception as e:
        messagebox.showerror('Error', f"An unexpected error occurred during search: {e}")
        tree.delete(*tree.get_children())


def update_employee_action():
    global current_editing_id, profile_picture_path
    if current_editing_id is None:
        messagebox.showerror('Error', 'Please select an employee from the list to update.')
        return

    try:
        dob_date = dobEntry.get_date()
        doj_date = dojEntry.get_date()
        
        dob_str = dob_date.strftime('%Y-%m-%d') if dob_date else None
        doj_str = doj_date.strftime('%Y-%m-%d') if doj_date else None
    except ValueError:
        messagebox.showerror('Date Error', 'Please enter valid dates in YYYY-MM-DD format.')
        return

    name = nameEntry.get().title()
    phone = phoneEntry.get()
    role = roleBox.get()
    gender = genderbox.get()
    salary = salaryEntry.get()
    status = statusBox.get()

    if not all([name, phone, salary]):
        messagebox.showerror('Error', 'Name, Phone, and Salary fields are required')
        return
    try:
        float(salary)
    except ValueError:
        messagebox.showerror('Error', 'Salary must be a valid number')
        return

    # Include profile_picture_path in updated_employee_data
    updated_employee_data = (name, phone, role, gender, salary, status, dob_str, doj_str, profile_picture_path, current_editing_id)
    database.update_employee_data(updated_employee_data)
    messagebox.showinfo('Success', 'Employee updated successfully!')
    treeview_data()
    clear_input_fields()


def delete_employee_action():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror('Error', 'Please select an employee to delete')
        return

    if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this employee?"):
        values = tree.item(selected_item, 'values')
        try:
            employee_id = int(values[0][3:]) # Assuming EMP prefix
        except (ValueError, IndexError):
            try:
                employee_id = int(values[0])
            except ValueError:
                messagebox.showerror('Error', 'Invalid employee ID format.')
                return

        database.delete_employee_by_id(employee_id)
        messagebox.showinfo('Success', 'Employee deleted successfully!')
        treeview_data()
        clear_input_fields()


def delete_all_action():
    if messagebox.askyesno("Confirm Delete All",
                           "ARE YOU SURE you want to delete ALL employees? This cannot be undone."):
        database.delete_all_employees_records()
        messagebox.showinfo('Success', 'All employees have been deleted.')
        treeview_data()
        clear_input_fields()


def on_tree_select(event):
    global current_editing_id, profile_picture_path
    selected_item = tree.focus()
    if not selected_item:
        return

    values = tree.item(selected_item, 'values')
    if not values:
        return

    clear_input_fields() # This clears the form and sets idEntry state to disabled

    # Extract ID from EMPxxx format from treeview values
    emp_id_display = str(values[0])
    try:
        if emp_id_display.upper().startswith('EMP'):
            current_editing_id = int(emp_id_display[3:])
        else:
            current_editing_id = int(emp_id_display)
    except (ValueError, IndexError):
        print(f"Warning: Could not parse employee ID from treeview: {emp_id_display}")
        current_editing_id = None
        return # Cannot proceed if ID is invalid

    # Now fetch the complete employee data from the database using the numeric ID
    emp_record = database.fetch_employees_by_criteria('id', str(current_editing_id))
    if not emp_record:
        messagebox.showerror('Error', f'Employee with ID {emp_id_display} not found in database.')
        current_editing_id = None
        return
    emp = emp_record[0] # Get the first (and only) row

    # Populate ID field (still disabled)
    idEntry.configure(state='normal')
    idEntry.delete(0, END)
    idEntry.insert(0, emp_id_display) # Use the EMPxxx format from treeview
    idEntry.configure(state='disabled')

    # Populate other fields safely
    nameEntry.insert(0, emp['name'] if 'name' in emp.keys() else '')
    phoneEntry.insert(0, emp['phone'] if 'phone' in emp.keys() else '')

    role = emp['role'] if 'role' in emp.keys() else role_option[0]
    if role in role_option:
        roleBox.set(role)
    else:
        roleBox.set(role_option[0])

    gender = emp['gender'] if 'gender' in emp.keys() else gender_option[0]
    if gender in gender_option:
        genderbox.set(gender)
    else:
        genderbox.set(gender_option[0])

    salaryEntry.insert(0, emp['salary'] if 'salary' in emp.keys() else '')

    status = emp['status'] if 'status' in emp.keys() else 'Active'
    if status in status_option:
        statusBox.set(status)
    else:
        statusBox.set('Active') # Default to Active

    # Set DOB, DOJ, and calculate Age
    dob_db = emp['date_of_birth'] if 'date_of_birth' in emp.keys() else None
    doj_db = emp['date_of_joining'] if 'date_of_joining' in emp.keys() else None
    profile_picture_path_db = emp['profile_picture_path'] if 'profile_picture_path' in emp.keys() else ''

    if dob_db:
        try:
            dobEntry.set_date(dob_db)
        except Exception as e:
            print(f"Error setting DOB from DB: {e}")
            dobEntry.set_date(datetime.today()) # Fallback
    else:
        dobEntry.set_date(datetime.today()) # Clear to today if None in DB

    if doj_db:
        try:
            dojEntry.set_date(doj_db)
        except Exception as e:
            print(f"Error setting DOJ from DB: {e}")
            dojEntry.set_date(datetime.today()) # Fallback
    else:
        dojEntry.set_date(datetime.today()) # Clear to today if None in DB

    profile_picture_path = profile_picture_path_db # Set global path
    display_profile_picture(profile_picture_path if profile_picture_path else "default_profile.png") # Display image

    calculate_age_from_dob() # Recalculate age based on newly set DOB

# Data Backup button function
def backup_database():
    file_path = filedialog.asksaveasfilename(
        defaultextension='.db',
        filetypes=[('SQLite DB', '*.db')],
        title='Backup Database'
    )
    if not file_path:
        return
    import shutil
    shutil.copy('employees.db', file_path)
    messagebox.showinfo('Success', f'Database backed up to {file_path}')

# Export to CSV function
def export_to_csv():
    file_path = filedialog.asksaveasfilename(
        defaultextension='.csv',
        filetypes=[('CSV files', '*.csv')],
        title='Save as CSV'
    )
    if not file_path:
        return
    rows = database.fetch_all_employees()
    if not rows:
        messagebox.showinfo('Info', 'No employee data to export.')
        return
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Ensure headers match the keys used in the treeview data
        headers = ['id', 'name', 'phone', 'role', 'gender', 'salary', 'status', 'date_of_birth', 'date_of_joining', 'age']
        writer.writerow([h.replace('_', ' ').title() for h in headers]) # Format headers nicely
        for row in rows:
            # Safely get values, matching headers
            row_values = [
                row[h] if h in row.keys() and row[h] is not None else ''
                for h in ['id', 'name', 'phone', 'role', 'gender', 'salary', 'status', 'date_of_birth', 'date_of_joining']
            ]
            # Calculate age for export if date_of_birth exists
            age_for_export = 'N/A'
            if 'date_of_birth' in row.keys() and row['date_of_birth']:
                try:
                    birth_date_obj = datetime.strptime(str(row['date_of_birth']), '%Y-%m-%d')
                    today_obj = datetime.today()
                    age_val_export = today_obj.year - birth_date_obj.year - ((today_obj.month, today_obj.day) < (birth_date_obj.month, birth_date_obj.day))
                    age_for_export = str(age_val_export)
                except Exception:
                    pass
            row_values.append(age_for_export)
            writer.writerow(row_values)
    messagebox.showinfo('Success', f'Employee data exported to {file_path}')

# Real-time search function
def realtime_search(event=None):
    query = searchEntry.get()
    option = searchbox.get()
    # Get the actual database column name from the display option
    column_map = {'ID': 'id', 'Name': 'name', 'Phone': 'phone', 'Role': 'role', 'Gender': 'gender',
                  'Salary': 'salary', 'Status': 'status', 'Date of Birth': 'date_of_birth', 'Date of Joining': 'date_of_joining'}
    db_column = column_map.get(option)

    if not db_column or query == '':
        treeview_data()
        return

    try:
        results = database.fetch_employees_by_criteria(db_column, query)
        treeview_data(results)
    except ValueError as e:
        tree.delete(*tree.get_children()) # Clear results on invalid search
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")
        tree.delete(*tree.get_children())

# Print preview function
def print_preview():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror('Error', 'Please select an employee to preview')
        return

    values = tree.item(selected_item, 'values')
    if not values:
         messagebox.showerror('Error', 'No employee data found for preview')
         return

    # Extract employee details from the treeview values
    # Assuming the order in treeview is: ID, Name, Phone, Role, Gender, Salary, Status, DOB, DOJ, Age
    try:
        employee_id, name, phone, role, gender, salary, status, date_of_birth, date_of_joining, age = values
    except ValueError:
        messagebox.showerror('Error', 'Could not retrieve complete employee data for preview.')
        return

    # Format the details for display in a message box
    preview_text = f"Employee Details:\n\n"
    preview_text += f"ID: {employee_id}\n"
    preview_text += f"Name: {name}\n"
    preview_text += f"Phone: {phone}\n"
    preview_text += f"Role: {role}\n"
    preview_text += f"Gender: {gender}\n"
    preview_text += f"Salary: {salary}\n"
    preview_text += f"Status: {status}\n"
    preview_text += f"Date of Birth: {date_of_birth if date_of_birth else 'N/A'}\n"
    preview_text += f"Date of Joining: {date_of_joining if date_of_joining else 'N/A'}\n"
    preview_text += f"Age: {age if age else 'N/A'}\n"

    # Display the formatted details in a message box
    messagebox.showinfo('Employee Print Preview', preview_text)

def download_printable_document():
    selected_item = tree.focus()
    if not selected_item:
        messagebox.showerror('Error', 'Please select an employee to download their information.')
        return

    values = tree.item(selected_item, 'values')
    if not values:
        messagebox.showerror('Error', 'No employee data found for download.')
        return

    try:
        employee_id, name, phone, role, gender, salary, status, date_of_birth, date_of_joining, age = values

        # Fetch profile picture path from the database
        emp_record = database.fetch_employees_by_criteria('id', str(employee_id).replace('EMP', ''))
        profile_picture_path_db = emp_record[0]['profile_picture_path'] if emp_record and 'profile_picture_path' in emp_record[0].keys() else 'default_profile.png'
        
        # Construct absolute path for the image in the HTML (if it exists)
        image_src = ""
        if profile_picture_path_db and os.path.exists(profile_picture_path_db):
            # For a simple HTML file for printing, it's safer to embed the image as base64
            # or instruct the user to ensure the image is in the same directory.
            # For now, let's just use a relative path if it's within the project structure, or fallback.
            # A full path might not work if moved.
            # For simplicity for print, we'll try to embed as data URI if possible.
            try:
                with open(profile_picture_path_db, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
                    image_src = f"data:image/png;base64,{encoded_string}" # Assume PNG for simplicity
            except Exception as e:
                print(f"Could not embed image {profile_picture_path_db}: {e}")
                image_src = "" # Fallback if embedding fails

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Employee Details - {name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
        .container {{ width: 800px; margin: auto; border: 1px solid #ddd; padding: 20px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #0A1128; border-bottom: 2px solid #0A1128; padding-bottom: 10px; margin-bottom: 20px; }}
        .detail-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; }}
        .detail-label {{ font-weight: bold; width: 45%; }}
        .detail-value {{ width: 50%; text-align: right; }}
        .profile-picture {{ text-align: center; margin-bottom: 20px; }}
        .profile-picture img {{ width: 150px; height: 150px; border-radius: 50%; border: 2px solid #0A1128; object-fit: cover; }}
        @media print {{ body {{ margin: 0; }} .container {{ width: auto; border: none; box-shadow: none; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Employee Details</h1>
        <div class="profile-picture">
            {f'<img src="{image_src}" alt="Profile Picture">' if image_src else '<div style="width:150px;height:150px;line-height:150px;text-align:center;border-radius:50%;border:2px solid #0A1128;background-color:#eee;"></div>'}
        </div>
        <div class="detail-row"><span class="detail-label">ID:</span> <span class="detail-value">{employee_id}</span></div>
        <div class="detail-row"><span class="detail-label">Name:</span> <span class="detail-value">{name}</span></div>
        <div class="detail-row"><span class="detail-label">Phone:</span> <span class="detail-value">{phone}</span></div>
        <div class="detail-row"><span class="detail-label">Role:</span> <span class="detail-value">{role}</span></div>
        <div class="detail-row"><span class="detail-label">Gender:</span> <span class="detail-value">{gender}</span></div>
        <div class="detail-row"><span class="detail-label">Salary:</span> <span class="detail-value">{salary}</span></div>
        <div class="detail-row"><span class="detail-label">Status:</span> <span class="detail-value">{status}</span></div>
        <div class="detail-row"><span class="detail-label">Date of Birth:</span> <span class="detail-value">{date_of_birth if date_of_birth else 'N/A'}</span></div>
        <div class="detail-row"><span class="detail-label">Date of Joining:</span> <span class="detail-value">{date_of_joining if date_of_joining else 'N/A'}</span></div>
        <div class="detail-row"><span class="detail-label">Age:</span> <span class="detail-value">{age if age else 'N/A'}</span></div>
    </div>
</body>
</html>
        """

        file_path = filedialog.asksaveasfilename(
            defaultextension='.html',
            filetypes=[('HTML files', '*.html')],
            title='Save Employee Document'
        )

        if not file_path:
            return

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        messagebox.showinfo('Success', f'Employee document saved to {file_path}')

    except Exception as e:
        messagebox.showerror('Error', f'Failed to generate document: {e}')

def import_from_excel():
    file_path = filedialog.askopenfilename(
        filetypes=[('Excel files', '*.xlsx *.xls')],
        title='Select Excel File'
    )
    if not file_path:
        return

    try:
        df = pd.read_excel(file_path) # Read Excel file into a pandas DataFrame
        # Assuming Excel columns are: Name, Phone, Role, Gender, Salary, Status, Date of Birth, Date of Joining
        # (Profile Picture Path will be left empty or default for imported data)

        imported_count = 0
        for index, row in df.iterrows():
            name = row.get('Name', '')
            phone = row.get('Phone', '')
            role = row.get('Role', 'General Worker') # Default role if not provided
            gender = row.get('Gender', 'Other') # Default gender
            salary = row.get('Salary', 0.0)
            status = row.get('Status', 'Active') # Default status

            dob_excel = row.get('Date of Birth', None)
            doj_excel = row.get('Date of Joining', None)

            # Convert dates from Excel (which might be datetime objects or numbers) to YYYY-MM-DD strings
            date_of_birth_str = None
            if pd.notna(dob_excel):
                try:
                    if isinstance(dob_excel, datetime):
                        date_of_birth_str = dob_excel.strftime('%Y-%m-%d')
                    else: # Assume it's a string, try to parse it
                        date_of_birth_str = pd.to_datetime(str(dob_excel)).strftime('%Y-%m-%d')
                except Exception:
                    pass # Keep as None if parsing fails

            date_of_joining_str = None
            if pd.notna(doj_excel):
                try:
                    if isinstance(doj_excel, datetime):
                        date_of_joining_str = doj_excel.strftime('%Y-%m-%d')
                    else:
                        date_of_joining_str = pd.to_datetime(str(doj_excel)).strftime('%Y-%m-%d')
                except Exception:
                    pass

            profile_picture_path_import = "" # No profile picture import from Excel

            if name and phone and salary is not None:
                employee_data = (name, phone, role, gender, float(salary), status, date_of_birth_str, date_of_joining_str, profile_picture_path_import)
                database.insert_employee(employee_data)
                imported_count += 1

        messagebox.showinfo('Success', f'{imported_count} employees imported successfully from Excel!')
        treeview_data() # Refresh the Treeview

    except FileNotFoundError:
        messagebox.showerror('Error', 'Excel file not found.')
    except Exception as e:
        messagebox.showerror('Error', f'An error occurred during import: {e}')

def apply_sort_filter():
    sort_by = sort_by_var.get()
    sort_order = sort_order_var.get()
    filter_gender = filter_gender_var.get()
    filter_status = filter_status_var.get()

    # Map display names to database column names
    column_map = {'ID': 'id', 'Name': 'name', 'Phone': 'phone', 'Role': 'role', 'Gender': 'gender',
                  'Salary': 'salary', 'Status': 'status', 'Date of Birth': 'date_of_birth', 'Date of Joining': 'date_of_joining'}
    db_sort_column = column_map.get(sort_by, 'id') # Default to ID if not found

    filters = {}
    if filter_gender != 'All':
        filters['gender'] = filter_gender
    if filter_status != 'All':
        filters['status'] = filter_status

    # Fetch data with sorting and filtering using the single fetch_all_employees function
    filtered_data = database.fetch_all_employees(filters=filters, sort_by=db_sort_column, sort_order=sort_order)
    treeview_data(filtered_data)

# Function to calculate age from DOB 
def calculate_age_from_dob(event=None):
    dob = dobEntry.get_date()
    try:
        if isinstance(dob, datetime): 
             birth_date = dob
        else:
             birth_date = datetime(dob.year, dob.month, dob.day)

        today = datetime.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        ageEntry.configure(state='normal')
        ageEntry.delete(0, END)
        ageEntry.insert(0, str(age))
        ageEntry.configure(state='readonly')
    except Exception:
        ageEntry.configure(state='normal')
        ageEntry.delete(0, END)
        ageEntry.insert(0, '')
        ageEntry.configure(state='readonly')

# Function to handle background image resize
def on_left_frame_configure(event):
    global _bg_pil_image_ref # Access the global PIL image reference
    try:
        current_width = leftFrame.winfo_width()
        current_height = leftFrame.winfo_height()
        if current_width > 0 and current_height > 0 and _bg_pil_image_ref:
            resized_bg_img = _bg_pil_image_ref.resize((current_width, current_height), Image.Resampling.LANCZOS) # Use LANCZOS for better quality
            bg_img_ctk = CTkImage(light_image=resized_bg_img, dark_image=resized_bg_img, size=(current_width, current_height))
            bg_label.configure(image=bg_img_ctk)
            bg_label.image = bg_img_ctk # Keep a reference to prevent garbage collection
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
    except Exception as e:
        print(f"Error resizing background: {e}")

# Function to handle logo image resize
def on_logo_configure(event):
    global _logo_pil_image_ref
    try:
        current_width = logolabel.winfo_width()
        target_height = 100 # Set a target height for the logo to make it "small"
        if current_width > 0 and _logo_pil_image_ref:
            resized_logo_img = _logo_pil_image_ref.resize((current_width, target_height), Image.Resampling.LANCZOS)
            logo_ctk = CTkImage(light_image=resized_logo_img, dark_image=resized_logo_img, size=(current_width, target_height))
            logolabel.configure(image=logo_ctk)
            logolabel.image = logo_ctk # Keep a reference to prevent garbage collection
    except Exception as e:
        print(f"Error resizing logo: {e}")

# Helper function to display profile image
def display_profile_picture(image_path):
    global profile_image_ctk
    if not image_path or not os.path.exists(image_path):
        image_path = "default_profile.png" # Fallback to a default image

    try:
        # Ensure the default image exists or create a blank one
        if image_path == "default_profile.png" and not os.path.exists("default_profile.png"):
            from PIL import ImageDraw
            blank_image = Image.new('RGB', (150, 150), color = '#2B2B2B') # Dark gray background
            d = ImageDraw.Draw(blank_image)
            d.text((10, 60), "", fill="white")
            blank_image.save("default_profile.png")

        pil_image = Image.open(image_path)
        pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
        profile_image_ctk = CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
        profile_image_label.configure(image=profile_image_ctk)
        profile_image_label.image = profile_image_ctk # Keep reference
    except Exception as e:
        print(f"Error loading profile image {image_path}: {e}")
        # Fallback to a text label if image loading fails
        profile_image_label.configure(text="Image Error", image=None) # Clear image, show text
        profile_image_ctk = None

# Function to browse for profile image
def browse_profile_image():
    global profile_picture_path
    file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
    if file_path:
        try:
            # Define a target directory for employee photos within your project
            target_dir = "employee_photos"
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # Create a unique filename to avoid overwriting
            unique_filename = f"{uuid.uuid4()}{os.path.splitext(file_path)[1]}"
            destination_path = os.path.join(target_dir, unique_filename)

            # Copy the selected image to the project's employee_photos directory
            shutil.copy(file_path, destination_path)

            profile_picture_path = destination_path
            display_profile_picture(profile_picture_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or save image: {e}")
            profile_picture_path = "" # Reset on error
            display_profile_picture("default_profile.png") # Display default on error

# --- Create Widgets ---
# Logo
try:
    _logo_pil_image_ref = Image.open('img.png') # Load once and store global reference
    logo = CTkImage(light_image=_logo_pil_image_ref, dark_image=_logo_pil_image_ref, size=(1,1)) # Give a dummy size initially
    logolabel = CTkLabel(window, image=logo, text='') # Removed fixed height from label
except Exception as e:
    print(f"Error loading logo: {e}")
    logolabel = CTkLabel(window, text='Employee Management System', font=('arial', 24, 'bold')) # Fallback to text
    logo = None # Ensure 'logo' is defined even if image loading fails

# Frames
leftFrame = CTkFrame(window, fg_color='#0A1128')
rightFrame = CTkFrame(window, fg_color='#0A1128')
buttonFrame = CTkFrame(window, fg_color='#0A1128')

# LeftFrame Form Widgets (Ordered: Profile Image, ID, Name, Phone, Role, Gender, Salary, Status, DOB, DOJ, Age)
# Profile Image
profile_image_label = CTkLabel(leftFrame, text="", width=150, height=150, fg_color="#2B2B2B") # Placeholder for image
browse_image_button = CTkButton(leftFrame, text='Browse Image', command=lambda: browse_profile_image()) # Browse button

# ID
idlabel = CTkLabel(leftFrame, text='ID', font=('arial', 20, 'bold'), text_color='white')
idEntry = CTkEntry(leftFrame, font=('arial', 17, 'bold'), width=180, state='disabled')

# Name
namelabel = CTkLabel(leftFrame, text='Name', font=('arial', 20, 'bold'), text_color='white')
nameEntry = CTkEntry(leftFrame, font=('arial', 17, 'bold'), width=180)

# Phone
phonelabel = CTkLabel(leftFrame, text='Phone', font=('arial', 20, 'bold'), text_color='white')
phoneEntry = CTkEntry(leftFrame, font=('arial', 17, 'bold'), width=180)

# Role
rolelabel = CTkLabel(leftFrame, text='Role', font=('arial', 20, 'bold'), text_color='white')
roleBox = CTkComboBox(leftFrame, values=role_option, width=180, font=('arial', 17, 'bold'), state='readonly')

# Gender
genderlabel = CTkLabel(leftFrame, text='Gender', font=('arial', 20, 'bold'), text_color='white')
genderbox = CTkComboBox(leftFrame, values=gender_option, width=180, font=('arial', 17, 'bold'), state='readonly')

# Salary
salarylabel = CTkLabel(leftFrame, text='Salary', font=('arial', 20, 'bold'), text_color='white')
salaryEntry = CTkEntry(leftFrame, font=('arial', 17, 'bold'), width=180)

# Status
status_label = CTkLabel(leftFrame, text='Status', font=('arial', 20, 'bold'), text_color='white')
statusBox = CTkComboBox(leftFrame, values=status_option, width=180, font=('arial', 17, 'bold'), state='readonly')

# Date of Birth
dob_label = CTkLabel(leftFrame, text='Date of Birth', font=('arial', 16, 'bold'), text_color='white')
dobEntry = DateEntry(leftFrame, width=17, font=('arial', 15, 'bold'), background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')

# Date of Joining
doj_label = CTkLabel(leftFrame, text='Date of Joining', font=('arial', 16, 'bold'), text_color='white')
dojEntry = DateEntry(leftFrame, width=17, font=('arial', 15, 'bold'), background='darkblue', foreground='white', date_pattern='yyyy-mm-dd')

# Age (Moved below DOJ)
age_label = CTkLabel(leftFrame, text='Age', font=('arial', 16, 'bold'), text_color='white')
ageEntry = CTkEntry(leftFrame, font=('arial', 15, 'bold'), width=180, state='readonly')

# LeftFrame background image - REINSTATED
try:
    _bg_pil_image_ref = Image.open('bg.jpg') # Load once and store global reference
    bg_img_initial = _bg_pil_image_ref # Use the original PIL image for initial sizing
    bg_img_ctk = CTkImage(light_image=bg_img_initial, dark_image=bg_img_initial, size=(300, 600)) # Initial size will be overridden by configure
    bg_label = CTkLabel(leftFrame, image=bg_img_ctk, text='')
    bg_label.place(x=0, y=0, relwidth=1, relheight=1) # Place here to ensure it exists
    bg_label.lower() # Keep background behind other widgets
except Exception as e:
    print(f"Error loading background image initially: {e}")
    # Fallback if image fails to load
    bg_label = CTkLabel(leftFrame, text='', fg_color='#0A1128') # Create a solid color label as fallback
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

# RightFrame Widgets (Search, Sort/Filter, Treeview)
searchbox = CTkComboBox(rightFrame, values=search_option, state='readonly', width=120)
searchEntry = CTkEntry(rightFrame, placeholder_text="Enter search term...")
searchButton = CTkButton(rightFrame, text='Search', width=100, command=search_employee_action)
showallButton = CTkButton(rightFrame, text='Show All', width=100, command=lambda: treeview_data(None))

# Sort/Filter controls
sort_by_combo = CTkComboBox(rightFrame, values=sort_options, width=120, state='readonly', variable=sort_by_var)
sort_order_combo = CTkComboBox(rightFrame, values=['ASC', 'DESC'], width=80, state='readonly', variable=sort_order_var)
filter_gender_combo = CTkComboBox(rightFrame, values=['All'] + gender_option, width=100, state='readonly', variable=filter_gender_var)
filter_status_combo = CTkComboBox(rightFrame, values=['All'] + status_option, width=100, state='readonly', variable=filter_status_var)
sort_button = CTkButton(rightFrame, text='Sort/Filter', width=100, command=apply_sort_filter)

# Treeview and scrollbar
style = ttk.Style()
style.theme_use("clam") # Ensure this theme is available or use a default CTk theme
style.configure("Treeview",
                background="#141D2B",
                foreground="white",
                rowheight=22, # Adjusted row height for less space
                fieldbackground="#141D2B",
                borderwidth=2,  # Added border
                relief="solid")  # Added border style
style.map('Treeview', background=[('selected', '#347083')])
style.configure("Treeview.Heading", font=('arial', 11, 'bold'), background="#0F182A",
                foreground="white")

tree = ttk.Treeview(rightFrame, show='headings')
scrollbar = ttk.Scrollbar(rightFrame, orient=VERTICAL, command=tree.yview)

# Define Treeview columns
tree['columns'] = ('ID', 'Name', 'Phone', 'Role', 'Gender', 'Salary', 'Status', 'Date of Birth', 'Date of Joining', 'Age')
for col in tree['columns']:
    tree.heading(col, text=col, anchor='w')

tree.column('ID', width=60, anchor='w', stretch=NO)
tree.column('Name', width=150, anchor='w')
tree.column('Phone', width=100, anchor='w')
tree.column('Role', width=120, anchor='w')
tree.column('Gender', width=70, anchor='w', stretch=NO)
tree.column('Salary', width=90, anchor='w', stretch=NO)
tree.column('Status', width=70, anchor='w', stretch=NO)
tree.column('Date of Birth', width=90, anchor='w', stretch=NO)
tree.column('Date of Joining', width=90, anchor='w', stretch=NO)
tree.column('Age', width=40, anchor='center', stretch=NO)

# ButtonFrame Widgets
common_button_props = {'font': ('arial', 10.5, 'bold'), 'corner_radius': 10,
                       'height': 34.5}

newButton = CTkButton(buttonFrame, text='Clear Fields (Ctrl+C)', **common_button_props, command=clear_input_fields, width=110)
addButton = CTkButton(buttonFrame, text='Add Employee (Ctrl+A)', **common_button_props, command=add_employee_action, width=110)
updateButton = CTkButton(buttonFrame, text='Update Employee (Ctrl+U)', **common_button_props, command=lambda event: update_employee_action(), width=110)
deleteButton = CTkButton(buttonFrame, text='Delete Employee (Ctrl+D)', **common_button_props, command=lambda event: delete_employee_action(), width=110)
deleteAllButton = CTkButton(buttonFrame, text='Delete All (Ctrl+L)', **common_button_props, fg_color="red",
                            hover_color="darkred", command=lambda event: delete_all_action(), width=110)
exportButton = CTkButton(buttonFrame, text='Export to CSV (Ctrl+E)', **common_button_props, command=lambda event: export_to_csv(), width=110)
printPreviewButton = CTkButton(buttonFrame, text='Print Preview (Ctrl+P)', **common_button_props, command=lambda event: print_preview(), width=110)
backupButton = CTkButton(buttonFrame, text='Backup Data (Ctrl+B)', **common_button_props, command=lambda event: backup_database(), width=110)
DownloadDocumentButton = CTkButton(buttonFrame, text='Download Doc (Ctrl+M)', **common_button_props, command=download_printable_document, width=110)
ImportExcelButton = CTkButton(buttonFrame, text='Import from Excel (Ctrl+I)', **common_button_props, command=import_from_excel, width=110)

# --- Position Widgets using Grid ---
# Logo
logolabel.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=0) # Added padx=0

# Frames (row 1)
leftFrame.grid(row=1, column=0, padx=10, pady=5, sticky="ns")
rightFrame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

# ButtonFrame (row 2, columnspan 2)
buttonFrame.grid(row=2, column=0, columnspan=2, pady=(10, 15))

# Configure grid weights for responsiveness
window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=2) # Increased weight for rightFrame to make it larger
window.grid_rowconfigure(0, weight=0) # Ensure row 0 doesn't expand vertically
window.grid_rowconfigure(1, weight=1)
rightFrame.grid_columnconfigure(0, weight=1)
rightFrame.grid_columnconfigure(1, weight=1)
rightFrame.grid_columnconfigure(2, weight=0)
rightFrame.grid_columnconfigure(3, weight=0)
rightFrame.grid_columnconfigure(4, weight=0) # Sort/Filter button column
rightFrame.grid_columnconfigure(5, weight=0) # Scrollbar column
rightFrame.grid_rowconfigure(1, weight=1) # Treeview row
rightFrame.grid_rowconfigure(2, weight=0) # Sort/Filter row

# LeftFrame Form Widget Positioning (Order: Profile Image, ID, Name, Phone, Role, Gender, Salary, Status, DOB, DOJ, Age)
# Profile Image (new, top of form)
profile_image_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))
browse_image_button.grid(row=1, column=0, columnspan=2, pady=(0, 5))

# ID (row 2, shifted down)
idlabel.grid(row=2, column=0, padx=(20, 5), pady=5, sticky='w')
idEntry.grid(row=2, column=1, padx=(0, 20), pady=5)

# Name (row 3)
namelabel.grid(row=3, column=0, padx=(20, 5), pady=5, sticky='w')
nameEntry.grid(row=3, column=1, padx=(0, 20), pady=5)

# Phone (row 4)
phonelabel.grid(row=4, column=0, padx=(20, 5), pady=5, sticky='w')
phoneEntry.grid(row=4, column=1, padx=(0, 20), pady=5)

# Role (row 5)
rolelabel.grid(row=5, column=0, padx=(20, 5), pady=5, sticky='w')
roleBox.grid(row=5, column=1, padx=(0, 20), pady=5)

# Gender (row 6)
genderlabel.grid(row=6, column=0, padx=(20, 5), pady=5, sticky='w')
genderbox.grid(row=6, column=1, padx=(0, 20), pady=5)

# Salary (row 7)
salarylabel.grid(row=7, column=0, padx=(20, 5), pady=5, sticky='w')
salaryEntry.grid(row=7, column=1, padx=(0, 20), pady=5)

# Status (row 8)
status_label.grid(row=8, column=0, padx=(20, 5), pady=5, sticky='w')
statusBox.grid(row=8, column=1, padx=(0, 20), pady=5)

# Date of Birth (row 9)
dob_label.grid(row=9, column=0, padx=(20, 5), pady=5, sticky='w')
dobEntry.grid(row=9, column=1, padx=(0, 20), pady=5)

# Date of Joining (row 10)
doj_label.grid(row=10, column=0, padx=(20, 5), pady=5, sticky='w')
dojEntry.grid(row=10, column=1, padx=(0, 20), pady=5)

# Age (row 11)
age_label.grid(row=11, column=0, padx=(20, 5), pady=5, sticky='w')
ageEntry.grid(row=11, column=1, padx=(0, 20), pady=5)

# LeftFrame background (reinstated)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
bg_label.lower()

# RightFrame Widget Positioning
# Search/Filter row (row 0)
searchbox.grid(row=0, column=0, padx=5, pady=10, sticky='ew')
searchEntry.grid(row=0, column=1, padx=5, pady=10, sticky='ew')
searchButton.grid(row=0, column=2, padx=5, pady=10)
showallButton.grid(row=0, column=3, padx=(5, 10), pady=10)

# Sort/Filter controls
sort_by_combo.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
sort_order_combo.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
filter_gender_combo.grid(row=2, column=2, padx=5, pady=5, sticky='ew')
filter_status_combo.grid(row=2, column=3, padx=5, pady=5, sticky='ew')
sort_button.grid(row=2, column=4, padx=5, pady=5)

# Treeview and scrollbar (row 1)
tree.grid(row=1, column=0, columnspan=5, padx=5, pady=5, sticky='nsew')
scrollbar.grid(row=1, column=5, sticky='ns', pady=5, padx=(0, 5))
tree.configure(yscrollcommand=scrollbar.set)

# ButtonFrame Button Positioning (row 0)
newButton.grid(row=0, column=0, pady=5, padx=5)
addButton.grid(row=0, column=1, pady=5, padx=5)
updateButton.grid(row=0, column=2, pady=5, padx=5)
deleteButton.grid(row=0, column=3, pady=5, padx=5)
exportButton.grid(row=0, column=4, pady=5, padx=5)
printPreviewButton.grid(row=0, column=5, pady=5, padx=5)
backupButton.grid(row=0, column=6, pady=5, padx=5)
DownloadDocumentButton.grid(row=0, column=7, pady=5, padx=5)
ImportExcelButton.grid(row=0, column=8, pady=5, padx=5)
deleteAllButton.grid(row=0, column=9, pady=5, padx=5)

# Add column configurations for buttonFrame
buttonFrame.grid_columnconfigure(0, weight=1)
buttonFrame.grid_columnconfigure(1, weight=1)
buttonFrame.grid_columnconfigure(2, weight=1)
buttonFrame.grid_columnconfigure(3, weight=1)
buttonFrame.grid_columnconfigure(4, weight=1)
buttonFrame.grid_columnconfigure(5, weight=1)
buttonFrame.grid_columnconfigure(6, weight=1)
buttonFrame.grid_columnconfigure(7, weight=1)
buttonFrame.grid_columnconfigure(8, weight=1)
buttonFrame.grid_columnconfigure(9, weight=1)

# --- Event Bindings ---
dobEntry.bind('<<DateEntrySelected>>', calculate_age_from_dob)
dobEntry.bind('<FocusOut>', calculate_age_from_dob)
searchEntry.bind('<KeyRelease>', realtime_search)
tree.bind('<<TreeviewSelect>>', on_tree_select)
leftFrame.bind('<Configure>', on_left_frame_configure)
logolabel.bind('<Configure>', on_logo_configure) # Re-added binding

# --- Keyboard Shortcuts ---
window.bind('<Control-c>', clear_input_fields) # Ctrl+C for Clear Fields
window.bind('<Control-a>', add_employee_action) # Ctrl+A for Add Employee
window.bind('<Control-u>', lambda event: update_employee_action()) # Ctrl+U for Update Employee
window.bind('<Control-d>', lambda event: delete_employee_action()) # Ctrl+D for Delete Employee
window.bind('<Control-l>', lambda event: delete_all_action()) # Ctrl+L for Delete All
window.bind('<Control-e>', lambda event: export_to_csv()) # Ctrl+E for Export to CSV
window.bind('<Control-p>', lambda event: print_preview()) # Ctrl+P for Print Preview
window.bind('<Control-b>', lambda event: backup_database()) # Ctrl+B for Backup Data
window.bind('<Control-s>', lambda event: search_employee_action()) # Ctrl+S for Search
window.bind('<Control-h>', lambda event: treeview_data(None)) # Ctrl+H for Show All
window.bind('<Control-f>', lambda event: apply_sort_filter()) # Ctrl+F for Sort/Filter
window.bind('<Control-m>', lambda event: download_printable_document()) # Ctrl+M for Download Document
window.bind('<Control-i>', lambda event: import_from_excel()) # Ctrl+I for Import from Excel

# --- Initial Data Load ---
treeview_data()
display_profile_picture("default_profile.png") # Display default image on startup

# --- Main Loop ---
def on_closing():
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()