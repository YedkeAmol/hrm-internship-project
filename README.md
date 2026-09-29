# HRM Internship Project

Human Resource Management System developed for the VIBGYOR Integrated Internship - Python.

## Current module
- Department Management

## Implemented functionality
- Dashboard
- Create department
- View departments
- Search departments
- Update department
- Soft delete / deactivate department
- Activate department
- SQLite database

## Run locally

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Project structure

```text
hrm_internship/
├── app.py
├── requirements.txt
├── README.md
├── hrm.db              # created automatically after first run
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── departments.html
│   └── department_form.html
└── static/
    └── css/
        └── style.css
```
