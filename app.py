from flask import Flask, session
from functools import wraps
import random
, render_template, request, redirect, url_for, flash
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

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
