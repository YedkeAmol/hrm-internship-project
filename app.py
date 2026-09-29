from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DB_NAME = "hrm.db"


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
    conn.commit()
    conn.close()


@app.route("/")
def dashboard():
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM department WHERE status = 1"
    ).fetchone()[0]
    inactive = conn.execute(
        "SELECT COUNT(*) FROM department WHERE status = 0"
    ).fetchone()[0]
    conn.close()
    return render_template("dashboard.html", total=total, inactive=inactive)


@app.route("/departments")
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
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("A department with this name already exists.", "danger")
        finally:
            conn.close()
            if request.method == "POST":
                return render_template(
                    "department_form.html",
                    department={"dept_id": dept_id,
                                 "dept_name": name,
                                 "description": description}
                )

    conn.close()
    return render_template("department_form.html", department=department)


@app.post("/departments/<int:dept_id>/toggle")
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
