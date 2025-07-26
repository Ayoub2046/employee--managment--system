# database.py
import sqlite3
import bcrypt  # For password hashing: pip install bcrypt
import os

DATABASE_NAME = 'employees.db'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_NAME)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def create_tables():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Employees Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS employees (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT NOT NULL,
                           phone TEXT NOT NULL,
                           role TEXT NOT NULL,
                           gender TEXT NOT NULL,
                           salary REAL NOT NULL,
                           status TEXT NOT NULL DEFAULT 'Active',
                           date_of_birth TEXT,
                           date_of_joining TEXT,
                           profile_picture_path TEXT
                           )''')
        # Check and add 'status' column if it doesn't exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'status' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN status TEXT NOT NULL DEFAULT 'Active'")
            conn.commit()
        # Check and add 'date_of_birth' column if it doesn't exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'date_of_birth' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN date_of_birth TEXT")
            conn.commit()
        # Check and add 'date_of_joining' column if it doesn't exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'date_of_joining' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN date_of_joining TEXT")
            conn.commit()
        # Check and add 'profile_picture_path' column if it doesn't exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'profile_picture_path' not in columns:
            cursor.execute("ALTER TABLE employees ADD COLUMN profile_picture_path TEXT")
            conn.commit()

        # Users Table (for login)
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           username TEXT UNIQUE NOT NULL,
                           password_hash TEXT NOT NULL,
                           role TEXT NOT NULL DEFAULT 'user')''')  # Added role
        conn.commit()

        # Create a default admin user if none exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                           ('admin', hashed_password.decode('utf-8'), 'admin'))  # Added role
            conn.commit()
            print("Default admin user created (admin/admin123) with role 'admin'. Please change it.")


# --- User Management Functions ---
def add_user(username, password, role='user'):  # Added role parameter
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                           (username, hashed_password.decode('utf-8'), role))
            conn.commit()
        return True
    except sqlite3.IntegrityError:  # For UNIQUE constraint on username
        print(f"Username '{username}' already exists.")
        return False


def verify_user(username, password):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        user_record = cursor.fetchone()
        if user_record:
            stored_hash = user_record['password_hash'].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False


def get_user_role(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE username = ?', (username,))
        user_record = cursor.fetchone()
        if user_record:
            return user_record['role']
    return None


def update_user_password(username, old_password, new_password):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # First, verify the old password
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        user_record = cursor.fetchone()

        if user_record:
            stored_hash = user_record['password_hash'].encode('utf-8')
            if bcrypt.checkpw(old_password.encode('utf-8'), stored_hash):
                # Old password is correct, proceed to update with new password
                hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?',
                               (hashed_new_password.decode('utf-8'), username))
                conn.commit()
                return conn.total_changes > 0
            else:
                return False # Old password does not match
        return False # User not found or no record


# --- Employee Management Functions ---
def insert_employee(employee_data):
    # name, phone, role, gender, salary, status, dob, doj, profile_picture_path
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO employees
                          (name, phone, role, gender, salary, status, date_of_birth, date_of_joining, profile_picture_path)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', employee_data)
        conn.commit()


def fetch_all_employees(filters=None, sort_by=None, sort_order='ASC'):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query_string = 'SELECT * FROM employees'
        params = []

        if filters:
            conditions = []
            for key, value in filters.items():
                if value and value != 'All':  # Ensure value is not empty or 'All'
                    conditions.append(f"LOWER({key}) = LOWER(?)")  # Case-insensitive filter
                    params.append(value)
            if conditions:
                query_string += " WHERE " + " AND ".join(conditions)

        if sort_by:
            allowed_sort_columns = ['id', 'name', 'phone', 'role', 'gender', 'salary', 'status', 'date_of_birth',
                                    'date_of_joining']
            if sort_by.lower() not in allowed_sort_columns:
                print(f"Warning: Invalid sort column '{sort_by}' attempted.")  # Log or raise error
                # Default sort or no sort if invalid
            else:
                order = 'ASC' if sort_order.upper() == 'ASC' else 'DESC'
                # For date sorting, ensure NULLs are handled if necessary (SQLite usually puts them first on ASC)
                if sort_by.lower() in ['date_of_birth', 'date_of_joining']:
                    query_string += f" ORDER BY CASE WHEN {sort_by.lower()} IS NULL THEN 1 ELSE 0 END, {sort_by.lower()} {order}"
                else:
                    query_string += f" ORDER BY {sort_by.lower()} {order}"

        cursor.execute(query_string, params)
        return cursor.fetchall()


def fetch_employees_by_criteria(column, query_text):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        valid_columns = ['id', 'name', 'phone', 'role', 'gender', 'salary', 'status']
        db_column_name = column.lower()

        if db_column_name not in valid_columns:
            raise ValueError("Invalid search column")

        if db_column_name == 'id' and query_text.upper().startswith('EMP'):
            try:
                actual_id = int(query_text[3:])
                cursor.execute(f'SELECT * FROM employees WHERE id = ?', (actual_id,))
            except ValueError:
                return []
        elif db_column_name == 'salary':
            try:
                salary_val = float(query_text)
                # Search for salaries greater than or equal to, for example, or exact
                cursor.execute(f'SELECT * FROM employees WHERE {db_column_name} >= ?', (salary_val,))
            except ValueError:
                return []  # Not a valid number for salary search
        else:
            # Case-insensitive search for text fields
            cursor.execute(f'SELECT * FROM employees WHERE LOWER({db_column_name}) LIKE LOWER(?)',
                           ('%' + query_text + '%',))
        return cursor.fetchall()


def update_employee_data(employee_data_with_id):
    # name, phone, role, gender, salary, status, dob, doj, id, profile_picture_path
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''UPDATE employees SET
                          name=?, phone=?, role=?, gender=?, salary=?,
                          status=?, date_of_birth=?, date_of_joining=?, profile_picture_path=?
                          WHERE id=?''', employee_data_with_id)
        conn.commit()


def delete_employee_by_id(employee_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employees WHERE id=?', (employee_id,))
        conn.commit()


def delete_all_employees_records():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM employees')
        conn.commit()


def ensure_users_table_has_role_column():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            conn.commit()


# Initialize database and tables when this module is first imported
if __name__ != '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    photos_dir = os.path.join(script_dir, "employee_photos")
    if not os.path.exists(photos_dir):
        os.makedirs(photos_dir)

    backups_dir = os.path.join(script_dir, "backups")
    if not os.path.exists(backups_dir):
        os.makedirs(backups_dir)

    create_tables()
    ensure_users_table_has_role_column()