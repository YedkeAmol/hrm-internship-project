from flask import Flask, session, render_template, request, redirect, url_for, flash
from functools import wraps
import random
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_NAME = "hrm.db"



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS department (
            dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(300),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            status INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS role (
            role_id INTEGER PRIMARY KEY AUTOINCREMENT,
            role_name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(300),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            status INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user (
            employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL UNIQUE,
            mobile VARCHAR(100) NOT NULL,
            dept_id INTEGER,
            role_id INTEGER,
            reporting_manager_id INTEGER,
            date_of_joining DATE,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (dept_id) REFERENCES department (dept_id),
            FOREIGN KEY (role_id) REFERENCES role (role_id),
            FOREIGN KEY (reporting_manager_id) REFERENCES user (employee_id)
        )
    """)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS task (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_title VARCHAR(100) NOT NULL,
            task_description VARCHAR(300),
            task_priority VARCHAR(200),
            start_date DATE,
            end_date DATE,
            task_type VARCHAR(50),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS task_assignment (
            assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            assigned_by INTEGER NOT NULL,
            assigned_date DATETIME NOT NULL,
            status VARCHAR(200) DEFAULT 'Pending',
            completed_at DATETIME,
            FOREIGN KEY (task_id) REFERENCES task (task_id),
            FOREIGN KEY (employee_id) REFERENCES user (employee_id),
            FOREIGN KEY (assigned_by) REFERENCES user (employee_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS performance_review (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_title VARCHAR(100) NOT NULL,
            review_date DATE NOT NULL,
            employee_id INTEGER NOT NULL,
            reviewed_by INTEGER NOT NULL,
            review_period VARCHAR(100) NOT NULL,
            rating INTEGER NOT NULL,
            comments VARCHAR(300),
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES user (employee_id),
            FOREIGN KEY (reviewed_by) REFERENCES user (employee_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leave_quota (
            quota_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type VARCHAR(50) NOT NULL,
            total_quota INTEGER NOT NULL DEFAULT 0,
            used_quota INTEGER NOT NULL DEFAULT 0,
            remain_quota INTEGER NOT NULL DEFAULT 0,
            UNIQUE(employee_id, leave_type),
            FOREIGN KEY (employee_id) REFERENCES user (employee_id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS leave_request (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type VARCHAR(50) NOT NULL,
            reason VARCHAR(200) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_days INTEGER NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'Pending',
            approved_by INTEGER,
            FOREIGN KEY (employee_id) REFERENCES user (employee_id),
            FOREIGN KEY (approved_by) REFERENCES user (employee_id)
        )
    ''')
    conn.commit()
    conn.close()


@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    total_dept = conn.execute(
        "SELECT COUNT(*) FROM department WHERE status = 1"
    ).fetchone()[0]
    inactive_dept = conn.execute(
        "SELECT COUNT(*) FROM department WHERE status = 0"
    ).fetchone()[0]
    
    total_roles = conn.execute(
        "SELECT COUNT(*) FROM role WHERE status = 1"
    ).fetchone()[0]
    inactive_roles = conn.execute(
        "SELECT COUNT(*) FROM role WHERE status = 0"
    ).fetchone()[0]
    
    total_employees = conn.execute(
        "SELECT COUNT(*) FROM user"
    ).fetchone()[0]
    
    conn.close()
    return render_template(
        "dashboard.html", 
        total=total_dept, 
        inactive=inactive_dept,
        total_roles=total_roles,
        inactive_roles=inactive_roles,
        total_employees=total_employees
    )


@app.route("/departments")
@login_required
def departments():
    search = request.args.get("search", "").strip()
    conn = get_db()

    if search:
        rows = conn.execute("""
            SELECT * FROM department
            WHERE dept_name LIKE ? OR description LIKE ?
            ORDER BY dept_id DESC
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM department ORDER BY dept_id DESC"
        ).fetchall()

    conn.close()
    return render_template("departments.html", departments=rows, search=search)


@app.route("/departments/create", methods=["GET", "POST"])
@login_required
def create_department():
    if request.method == "POST":
        name = request.form.get("dept_name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "danger")
            return render_template("department_form.html", department=None)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO department
                (dept_name, description, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, 1)
            """, (name, description, now, now))
            conn.commit()
            flash("Department created successfully.", "success")
            return redirect(url_for("departments"))
        except sqlite3.IntegrityError:
            flash("A department with this name already exists.", "danger")
        finally:
            conn.close()

    return render_template("department_form.html", department=None)


@app.route("/departments/<int:dept_id>/edit", methods=["GET", "POST"])
@login_required
def edit_department(dept_id):
    conn = get_db()
    department = conn.execute(
        "SELECT * FROM department WHERE dept_id = ?", (dept_id,)
    ).fetchone()

    if department is None:
        conn.close()
        flash("Department not found.", "danger")
        return redirect(url_for("departments"))

    if request.method == "POST":
        name = request.form.get("dept_name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            conn.close()
            flash("Department name is required.", "danger")
            return render_template(
                "department_form.html", department=department
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn.execute("""
                UPDATE department
                SET dept_name = ?, description = ?, updated_at = ?
                WHERE dept_id = ?
            """, (name, description, now, dept_id))
            conn.commit()
            flash("Department updated successfully.", "success")
            conn.close()
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("A department with this name already exists.", "danger")
            conn.close()
            return render_template(
                "department_form.html",
                department={"dept_id": dept_id,
                             "dept_name": name,
                             "description": description}
            )

    conn.close()
    return render_template("department_form.html", department=department)


@app.post("/departments/<int:dept_id>/toggle")
@login_required
def toggle_department(dept_id):
    conn = get_db()
    department = conn.execute(
        "SELECT status FROM department WHERE dept_id = ?", (dept_id,)
    ).fetchone()

    if department is None:
        conn.close()
        flash("Department not found.", "danger")
        return redirect(url_for("departments"))

    new_status = 0 if department["status"] else 1
    conn.execute(
        "UPDATE department SET status = ?, updated_at = ? WHERE dept_id = ?",
        (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), dept_id)
    )
    conn.commit()
    conn.close()

    flash(
        "Department activated." if new_status else "Department made inactive.",
        "success"
    )
    return redirect(url_for("departments"))


@app.route("/roles")
@login_required
def roles():
    search = request.args.get("search", "").strip()
    conn = get_db()

    if search:
        rows = conn.execute("""
            SELECT * FROM role
            WHERE role_name LIKE ? OR description LIKE ?
            ORDER BY role_id DESC
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM role ORDER BY role_id DESC"
        ).fetchall()

    conn.close()
    return render_template("roles.html", roles=rows, search=search)


@app.route("/roles/create", methods=["GET", "POST"])
@login_required
def create_role():
    if request.method == "POST":
        name = request.form.get("role_name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Role name is required.", "danger")
            return render_template("role_form.html", role=None)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db()

        try:
            conn.execute("""
                INSERT INTO role
                (role_name, description, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, 1)
            """, (name, description, now, now))
            conn.commit()
            flash("Role created successfully.", "success")
            return redirect(url_for("roles"))
        except sqlite3.IntegrityError:
            flash("A role with this name already exists.", "danger")
        finally:
            conn.close()

    return render_template("role_form.html", role=None)


@app.route("/roles/<int:role_id>/edit", methods=["GET", "POST"])
@login_required
def edit_role(role_id):
    conn = get_db()
    role = conn.execute(
        "SELECT * FROM role WHERE role_id = ?", (role_id,)
    ).fetchone()

    if role is None:
        conn.close()
        flash("Role not found.", "danger")
        return redirect(url_for("roles"))

    if request.method == "POST":
        name = request.form.get("role_name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            conn.close()
            flash("Role name is required.", "danger")
            return render_template(
                "role_form.html", role=role
            )

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn.execute("""
                UPDATE role
                SET role_name = ?, description = ?, updated_at = ?
                WHERE role_id = ?
            """, (name, description, now, role_id))
            conn.commit()
            flash("Role updated successfully.", "success")
            conn.close()
            return redirect(url_for("roles"))
        except sqlite3.IntegrityError:
            flash("A role with this name already exists.", "danger")
            conn.close()
            return render_template(
                "role_form.html",
                role={"role_id": role_id,
                             "role_name": name,
                             "description": description}
            )

    conn.close()
    return render_template("role_form.html", role=role)


@app.post("/roles/<int:role_id>/toggle")
@login_required
def toggle_role(role_id):
    conn = get_db()
    role = conn.execute(
        "SELECT status FROM role WHERE role_id = ?", (role_id,)
    ).fetchone()

    if role is None:
        conn.close()
        flash("Role not found.", "danger")
        return redirect(url_for("roles"))

    new_status = 0 if role["status"] else 1
    conn.execute(
        "UPDATE role SET status = ?, updated_at = ? WHERE role_id = ?",
        (new_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role_id)
    )
    conn.commit()
    conn.close()

    flash(
        "Role activated." if new_status else "Role made inactive.",
        "success"
    )
    return redirect(url_for("roles"))



@app.route("/employees")
@login_required
def employees():
    conn = get_db()
    # Join user table with role and department tables to get their names
    # Also join with user table itself to get reporting manager's name
    query = """
        SELECT u.*, 
               d.dept_name, 
               r.role_name,
               rm.first_name AS rm_first, 
               rm.last_name AS rm_last
        FROM user u
        LEFT JOIN department d ON u.dept_id = d.dept_id
        LEFT JOIN role r ON u.role_id = r.role_id
        LEFT JOIN user rm ON u.reporting_manager_id = rm.employee_id
        ORDER BY u.employee_id DESC
    """
    rows = conn.execute(query).fetchall()
    conn.close()
    return render_template("employees.html", employees=rows)

@app.route("/employees/create", methods=["GET", "POST"])
@login_required
def create_employee():
    conn = get_db()
    departments = conn.execute("SELECT * FROM department WHERE status = 1").fetchall()
    roles = conn.execute("SELECT * FROM role WHERE status = 1").fetchall()
    managers = conn.execute("SELECT employee_id, first_name, last_name FROM user").fetchall()

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        dept_id = request.form.get("dept_id")
        role_id = request.form.get("role_id")
        reporting_manager_id = request.form.get("reporting_manager_id") or None
        date_of_joining = request.form.get("date_of_joining") or None

        if not first_name or not email or not username or not password:
            flash("First name, email, username and password are required.", "danger")
            return render_template("employee_form.html", employee=None, departments=departments, roles=roles, managers=managers)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn.execute("""
                INSERT INTO user
                (first_name, last_name, username, password, email, mobile, dept_id, role_id, reporting_manager_id, date_of_joining, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (first_name, last_name, username, password, email, mobile, dept_id, role_id, reporting_manager_id, date_of_joining, now, now))
            conn.commit()
            flash("Employee created successfully.", "success")
            return redirect(url_for("employees"))
        except sqlite3.IntegrityError:
            flash("An employee with this username or email already exists.", "danger")
        finally:
            conn.close()

    conn.close()
    return render_template("employee_form.html", employee=None, departments=departments, roles=roles, managers=managers)

@app.route("/employees/<int:employee_id>/edit", methods=["GET", "POST"])
@login_required
def edit_employee(employee_id):
    conn = get_db()
    employee = conn.execute("SELECT * FROM user WHERE employee_id = ?", (employee_id,)).fetchone()
    departments = conn.execute("SELECT * FROM department WHERE status = 1").fetchall()
    roles = conn.execute("SELECT * FROM role WHERE status = 1").fetchall()
    managers = conn.execute("SELECT employee_id, first_name, last_name FROM user WHERE employee_id != ?", (employee_id,)).fetchall()

    if employee is None:
        conn.close()
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        mobile = request.form.get("mobile", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        dept_id = request.form.get("dept_id")
        role_id = request.form.get("role_id")
        reporting_manager_id = request.form.get("reporting_manager_id") or None
        date_of_joining = request.form.get("date_of_joining") or None

        if not first_name or not email or not username or not password:
            flash("First name, email, username and password are required.", "danger")
            conn.close()
            return render_template("employee_form.html", employee=employee, departments=departments, roles=roles, managers=managers)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn.execute("""
                UPDATE user
                SET first_name = ?, last_name = ?, username = ?, password = ?, email = ?, mobile = ?, 
                    dept_id = ?, role_id = ?, reporting_manager_id = ?, date_of_joining = ?, updated_at = ?
                WHERE employee_id = ?
            """, (first_name, last_name, username, password, email, mobile, dept_id, role_id, reporting_manager_id, date_of_joining, now, employee_id))
            conn.commit()
            flash("Employee updated successfully.", "success")
            conn.close()
            return redirect(url_for("employees"))
        except sqlite3.IntegrityError:
            flash("An employee with this username or email already exists.", "danger")
            conn.close()
            return render_template("employee_form.html", employee=employee, departments=departments, roles=roles, managers=managers)

    conn.close()
    return render_template("employee_form.html", employee=employee, departments=departments, roles=roles, managers=managers)

@app.post("/employees/<int:employee_id>/delete")
@login_required
def delete_employee(employee_id):
    conn = get_db()
    employee = conn.execute("SELECT * FROM user WHERE employee_id = ?", (employee_id,)).fetchone()

    if employee is None:
        conn.close()
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))

    # Also update any employees who report to this manager to set reporting_manager_id to NULL
    conn.execute("UPDATE user SET reporting_manager_id = NULL WHERE reporting_manager_id = ?", (employee_id,))
    
    conn.execute("DELETE FROM user WHERE employee_id = ?", (employee_id,))
    conn.commit()
    conn.close()

    flash("Employee deleted successfully.", "success")
    return redirect(url_for("employees"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM user WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["employee_id"] = user["employee_id"]
            session["username"] = user["username"]
            session["name"] = f"{user['first_name']} {user['last_name']}"
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        conn = get_db()
        user = conn.execute("SELECT * FROM user WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user:
            otp = str(random.randint(100000, 999999))
            session["reset_email"] = email
            session["reset_otp"] = otp
            # Mocking email send
            print(f"\n*** MOCK EMAIL ***\nTo: {email}\nSubject: Password Reset OTP\nYour OTP is: {otp}\n******************\n")
            flash(f"An OTP has been sent to {email}. (Check server console/terminal!)", "info")
            return redirect(url_for("verify_otp"))
        else:
            flash("Email address not found.", "danger")

    return render_template("forgot_password.html")

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if "reset_email" not in session or "reset_otp" not in session:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()
        if otp == session.get("reset_otp"):
            return redirect(url_for("reset_password"))
        else:
            flash("Invalid OTP.", "danger")

    return render_template("verify_otp.html")

@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not new_password or new_password != confirm_password:
            flash("Passwords do not match or are empty.", "danger")
        else:
            conn = get_db()
            conn.execute("UPDATE user SET password = ?, updated_at = ? WHERE email = ?", (new_password, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), session["reset_email"]))
            conn.commit()
            conn.close()

            session.pop("reset_email", None)
            session.pop("reset_otp", None)

            flash("Password reset successfully. You can now log in.", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")


@app.route("/tasks")
@login_required
def tasks():
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    # Get direct reports for filtering
    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    filter_emp = request.args.get("employee_id", "")
    filter_status = request.args.get("status", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")

    query = """
        SELECT t.*, ta.status, ta.assignment_id, ta.employee_id, ta.assigned_by,
               u.first_name as assignee_first, u.last_name as assignee_last,
               mgr.first_name as assignor_first, mgr.last_name as assignor_last
        FROM task t
        JOIN task_assignment ta ON t.task_id = ta.task_id
        JOIN user u ON ta.employee_id = u.employee_id
        JOIN user mgr ON ta.assigned_by = mgr.employee_id
        WHERE (ta.assigned_by = ? OR ta.employee_id = ?)
    """
    params = [current_user_id, current_user_id]

    if filter_emp:
        query += " AND ta.employee_id = ?"
        params.append(filter_emp)
    if filter_status:
        query += " AND ta.status = ?"
        params.append(filter_status)
    if start_date and end_date:
        query += " AND (t.start_date >= ? AND t.end_date <= ?)"
        params.extend([start_date, end_date])

    query += " ORDER BY t.created_at DESC"
    tasks = conn.execute(query, params).fetchall()

    # Calculate stats
    pending = sum(1 for t in tasks if t['status'] == 'Pending')
    in_progress = sum(1 for t in tasks if t['status'] == 'In progress')
    completed = sum(1 for t in tasks if t['status'] == 'Completed')

    conn.close()
    return render_template(
        "tasks.html", 
        tasks=tasks, 
        direct_reports=direct_reports,
        stats={"pending": pending, "in_progress": in_progress, "completed": completed},
        current_user_id=current_user_id
    )

@app.route("/tasks/create", methods=["GET", "POST"])
@login_required
def create_task():
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    # "Assigned To" must show only employees reporting to logged-in user
    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    if request.method == "POST":
        title = request.form.get("task_title", "").strip()
        description = request.form.get("task_description", "").strip()
        priority = request.form.get("task_priority", "")
        employee_id = request.form.get("employee_id", "")
        start_date = request.form.get("start_date", "")
        end_date = request.form.get("end_date", "")
        task_type = request.form.get("task_type", "")

        if not title or not employee_id:
            flash("Task title and assignee are required.", "danger")
            return render_template("task_form.html", task=None, reports=direct_reports)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO task (task_title, task_description, task_priority, start_date, end_date, task_type, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, description, priority, start_date, end_date, task_type, now, now))
        
        task_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO task_assignment (task_id, employee_id, assigned_by, assigned_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, employee_id, current_user_id, now, 'Pending'))
        
        conn.commit()
        conn.close()
        flash("Task created successfully.", "success")
        return redirect(url_for("tasks"))

    conn.close()
    return render_template("task_form.html", task=None, reports=direct_reports)


@app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    task_row = conn.execute("""
        SELECT t.*, ta.employee_id, ta.assignment_id, ta.status 
        FROM task t 
        JOIN task_assignment ta ON t.task_id = ta.task_id 
        WHERE t.task_id = ?
    """, (task_id,)).fetchone()

    if not task_row:
        conn.close()
        flash("Task not found.", "danger")
        return redirect(url_for("tasks"))

    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    if request.method == "POST":
        title = request.form.get("task_title", "").strip()
        description = request.form.get("task_description", "").strip()
        priority = request.form.get("task_priority", "")
        employee_id = request.form.get("employee_id", "")
        start_date = request.form.get("start_date", "")
        end_date = request.form.get("end_date", "")
        task_type = request.form.get("task_type", "")
        status = request.form.get("status", task_row['status'])

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("""
            UPDATE task 
            SET task_title = ?, task_description = ?, task_priority = ?, start_date = ?, end_date = ?, task_type = ?, updated_at = ?
            WHERE task_id = ?
        """, (title, description, priority, start_date, end_date, task_type, now, task_id))
        
        completed_at = now if status == 'Completed' and task_row['status'] != 'Completed' else task_row.get('completed_at')
        
        conn.execute("""
            UPDATE task_assignment 
            SET employee_id = ?, status = ?, completed_at = ?
            WHERE task_id = ?
        """, (employee_id, status, completed_at, task_id))
        
        conn.commit()
        conn.close()
        flash("Task updated successfully.", "success")
        return redirect(url_for("tasks"))

    conn.close()
    return render_template("task_form.html", task=task_row, reports=direct_reports)


@app.post("/tasks/<int:task_id>/delete")
@login_required
def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM task_assignment WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM task WHERE task_id = ?", (task_id,))
    conn.commit()
    conn.close()
    flash("Task deleted successfully.", "success")
    return redirect(url_for("tasks"))



@app.route("/reviews")
@login_required
def reviews():
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    # Direct reports for filter dropdown (if manager)
    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    # Filter params
    filter_emp = request.args.get("employee_id", "")
    filter_period = request.args.get("period", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    filter_rating = request.args.get("rating_range", "")

    query = """
        SELECT pr.*, 
               u.first_name as emp_first, u.last_name as emp_last,
               mgr.first_name as mgr_first, mgr.last_name as mgr_last
        FROM performance_review pr
        JOIN user u ON pr.employee_id = u.employee_id
        JOIN user mgr ON pr.reviewed_by = mgr.employee_id
        WHERE (pr.reviewed_by = ? OR pr.employee_id = ?)
    """
    params = [current_user_id, current_user_id]

    if filter_emp:
        query += " AND pr.employee_id = ?"
        params.append(filter_emp)
    if filter_period:
        query += " AND pr.review_period = ?"
        params.append(filter_period)
    if start_date and end_date:
        query += " AND (pr.review_date >= ? AND pr.review_date <= ?)"
        params.extend([start_date, end_date])
    if filter_rating:
        if filter_rating == "1-5":
            query += " AND pr.rating BETWEEN 1 AND 5"
        elif filter_rating == "6-8":
            query += " AND pr.rating BETWEEN 6 AND 8"
        elif filter_rating == "9-10":
            query += " AND pr.rating >= 9"

    query += " ORDER BY pr.review_date DESC"
    all_reviews = conn.execute(query, params).fetchall()

    # Calculate statistics
    stats = {
        "monthly": sum(1 for r in all_reviews if r['review_period'] == 'Monthly'),
        "quarterly": sum(1 for r in all_reviews if r['review_period'] == 'Quarterly'),
        "annually": sum(1 for r in all_reviews if r['review_period'] == 'Annually' or r['review_period'] == 'Annual'),
        "rating_1_5": sum(1 for r in all_reviews if 1 <= r['rating'] <= 5),
        "rating_6_8": sum(1 for r in all_reviews if 6 <= r['rating'] <= 8),
        "rating_above_8": sum(1 for r in all_reviews if r['rating'] >= 9)
    }

    conn.close()
    return render_template(
        "reviews.html", 
        reviews=all_reviews, 
        direct_reports=direct_reports,
        stats=stats,
        current_user_id=current_user_id
    )


@app.route("/reviews/create", methods=["GET", "POST"])
@login_required
def create_review():
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    # "Select Employee" must show only direct reports
    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    if request.method == "POST":
        title = request.form.get("review_title", "").strip()
        employee_id = request.form.get("employee_id", "")
        review_date = request.form.get("review_date", "")
        period = request.form.get("review_period", "")
        rating = request.form.get("rating", type=int)
        comments = request.form.get("comments", "").strip()

        if not title or not employee_id or not rating:
            flash("Title, Employee, and Rating are required.", "danger")
            return render_template("review_form.html", review=None, reports=direct_reports)

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("""
            INSERT INTO performance_review 
            (review_title, employee_id, reviewed_by, review_date, review_period, rating, comments, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, employee_id, current_user_id, review_date, period, rating, comments, now, now))
        
        conn.commit()
        conn.close()
        flash("Review created successfully.", "success")
        return redirect(url_for("reviews"))

    conn.close()
    return render_template("review_form.html", review=None, reports=direct_reports)


@app.route("/reviews/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    review_row = conn.execute("SELECT * FROM performance_review WHERE review_id = ?", (review_id,)).fetchone()

    if not review_row:
        conn.close()
        flash("Review not found.", "danger")
        return redirect(url_for("reviews"))

    direct_reports = conn.execute(
        "SELECT employee_id, first_name, last_name FROM user WHERE reporting_manager_id = ?",
        (current_user_id,)
    ).fetchall()

    if request.method == "POST":
        title = request.form.get("review_title", "").strip()
        employee_id = request.form.get("employee_id", "")
        review_date = request.form.get("review_date", "")
        period = request.form.get("review_period", "")
        rating = request.form.get("rating", type=int)
        comments = request.form.get("comments", "").strip()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute("""
            UPDATE performance_review 
            SET review_title = ?, employee_id = ?, review_date = ?, review_period = ?, rating = ?, comments = ?, updated_at = ?
            WHERE review_id = ?
        """, (title, employee_id, review_date, period, rating, comments, now, review_id))
        
        conn.commit()
        conn.close()
        flash("Review updated successfully.", "success")
        return redirect(url_for("reviews"))

    conn.close()
    return render_template("review_form.html", review=review_row, reports=direct_reports)


@app.post("/reviews/<int:review_id>/delete")
@login_required
def delete_review(review_id):
    conn = get_db()
    conn.execute("DELETE FROM performance_review WHERE review_id = ?", (review_id,))
    conn.commit()
    conn.close()
    flash("Review deleted successfully.", "success")
    return redirect(url_for("reviews"))


from datetime import datetime

@app.route("/leaves")
@login_required
def leaves():
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    # 1. Fetch balances for current user
    balances = conn.execute(
        "SELECT leave_type, remain_quota FROM leave_quota WHERE employee_id = ?",
        (current_user_id,)
    ).fetchall()
    
    bal_dict = {"PL": 0, "CL": 0, "SL": 0}
    for b in balances:
        bal_dict[b['leave_type']] = b['remain_quota']

    # 2. Fetch my leave requests
    my_leaves = conn.execute(
        "SELECT * FROM leave_request WHERE employee_id = ? ORDER BY start_date DESC",
        (current_user_id,)
    ).fetchall()

    # 3. Fetch reportees' leaves (if manager)
    reportees_leaves = conn.execute("""
        SELECT lr.*, u.first_name, u.last_name 
        FROM leave_request lr
        JOIN user u ON lr.employee_id = u.employee_id
        WHERE u.reporting_manager_id = ?
        ORDER BY lr.start_date DESC
    """, (current_user_id,)).fetchall()
    
    conn.close()
    return render_template(
        "leaves.html", 
        balances=bal_dict, 
        my_leaves=my_leaves, 
        reportees_leaves=reportees_leaves
    )


@app.route("/leaves/apply", methods=["GET", "POST"])
@login_required
def apply_leave():
    if request.method == "POST":
        conn = get_db()
        current_user_id = session.get("employee_id")
        
        leave_type = request.form.get("leave_type")
        reason = request.form.get("reason", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        
        if not leave_type or not start_date or not end_date:
            flash("All fields are required.", "danger")
            return render_template("leave_form.html", leave=None, mode="apply")
            
        # Calculate days (simple calculation, assuming inclusive and skipping weekends is out of scope for now unless specified)
        d1 = datetime.strptime(start_date, "%Y-%m-%d")
        d2 = datetime.strptime(end_date, "%Y-%m-%d")
        total_days = (d2 - d1).days + 1
        
        if total_days <= 0:
            flash("End date must be after start date.", "danger")
            return render_template("leave_form.html", leave=None, mode="apply")

        conn.execute("""
            INSERT INTO leave_request (employee_id, leave_type, reason, start_date, end_date, total_days)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (current_user_id, leave_type, reason, start_date, end_date, total_days))
        
        conn.commit()
        conn.close()
        flash("Leave applied successfully.", "success")
        return redirect(url_for("leaves"))
        
    return render_template("leave_form.html", leave=None, mode="apply")


@app.route("/leaves/<int:leave_id>/edit", methods=["GET", "POST"])
@login_required
def edit_leave(leave_id):
    conn = get_db()
    current_user_id = session.get("employee_id")
    
    leave_req = conn.execute("""
        SELECT lr.*, u.reporting_manager_id, u.first_name, u.last_name 
        FROM leave_request lr
        JOIN user u ON lr.employee_id = u.employee_id
        WHERE lr.leave_id = ?
    """, (leave_id,)).fetchone()
    
    if not leave_req:
        conn.close()
        flash("Leave request not found.", "danger")
        return redirect(url_for("leaves"))

    is_owner = (leave_req['employee_id'] == current_user_id)
    is_manager = (leave_req['reporting_manager_id'] == current_user_id)

    if not is_owner and not is_manager:
        conn.close()
        flash("Unauthorized.", "danger")
        return redirect(url_for("leaves"))
        
    if is_owner and not is_manager and leave_req['status'] != 'Pending':
        conn.close()
        flash("Cannot edit processed leave.", "danger")
        return redirect(url_for("leaves"))

    if request.method == "POST":
        if is_manager:
            status = request.form.get("status")
            conn.execute("UPDATE leave_request SET status = ?, approved_by = ? WHERE leave_id = ?", 
                         (status, current_user_id, leave_id))
            
            # Deduct from quota if approved
            if status == "Approved" and leave_req['status'] != "Approved":
                conn.execute("""
                    UPDATE leave_quota 
                    SET used_quota = used_quota + ?, remain_quota = remain_quota - ?
                    WHERE employee_id = ? AND leave_type = ?
                """, (leave_req['total_days'], leave_req['total_days'], leave_req['employee_id'], leave_req['leave_type']))
            
        elif is_owner:
            leave_type = request.form.get("leave_type")
            reason = request.form.get("reason", "").strip()
            start_date = request.form.get("start_date")
            end_date = request.form.get("end_date")
            
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            total_days = (d2 - d1).days + 1
            
            conn.execute("""
                UPDATE leave_request 
                SET leave_type = ?, reason = ?, start_date = ?, end_date = ?, total_days = ?
                WHERE leave_id = ?
            """, (leave_type, reason, start_date, end_date, total_days, leave_id))
            
        conn.commit()
        conn.close()
        flash("Leave updated successfully.", "success")
        return redirect(url_for("leaves"))

    conn.close()
    mode = "approve" if is_manager else "update"
    return render_template("leave_form.html", leave=leave_req, mode=mode)


@app.route("/leave-quotas")
@login_required
def leave_quotas():
    conn = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 5
    offset = (page - 1) * per_page
    
    # We want to pivot the data by employee
    query = """
        SELECT u.employee_id, u.first_name, u.last_name,
               SUM(CASE WHEN lq.leave_type = 'PL' THEN lq.total_quota ELSE 0 END) as pl_quota,
               SUM(CASE WHEN lq.leave_type = 'CL' THEN lq.total_quota ELSE 0 END) as cl_quota,
               SUM(CASE WHEN lq.leave_type = 'SL' THEN lq.total_quota ELSE 0 END) as sl_quota
        FROM user u
        LEFT JOIN leave_quota lq ON u.employee_id = lq.employee_id
        GROUP BY u.employee_id, u.first_name, u.last_name
        ORDER BY u.employee_id
        LIMIT ? OFFSET ?
    """
    employees = conn.execute(query, (per_page, offset)).fetchall()
    
    total_emp = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
    total_pages = (total_emp + per_page - 1) // per_page
    
    conn.close()
    return render_template("leave_quotas.html", employees=employees, page=page, total_pages=total_pages)


@app.route("/leave-quotas/add", methods=["GET", "POST"])
@login_required
def add_leave_quota():
    conn = get_db()
    if request.method == "POST":
        employee_id = request.form.get("employee_id")
        pl_quota = int(request.form.get("pl_quota", 0))
        cl_quota = int(request.form.get("cl_quota", 0))
        sl_quota = int(request.form.get("sl_quota", 0))
        
        for l_type, val in [("PL", pl_quota), ("CL", cl_quota), ("SL", sl_quota)]:
            # Insert or replace (SQLite UPSERT)
            conn.execute("""
                INSERT INTO leave_quota (employee_id, leave_type, total_quota, used_quota, remain_quota)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(employee_id, leave_type) 
                DO UPDATE SET total_quota = excluded.total_quota, remain_quota = excluded.total_quota - used_quota
            """, (employee_id, l_type, val, val))
            
        conn.commit()
        conn.close()
        flash("Leave quota updated successfully.", "success")
        return redirect(url_for("leave_quotas"))
        
    all_users = conn.execute("SELECT employee_id, first_name, last_name FROM user").fetchall()
    conn.close()
    return render_template("leave_quota_form.html", users=all_users)


init_db()

if __name__ == "__main__":
    app.run(debug=True)
