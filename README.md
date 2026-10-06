# HRM Internship Project

This project is a Human Resource Management System developed as part of the VIBGYOR Integrated Internship.

The system is built using Python and Flask and provides different modules for managing employees, departments, roles, tasks, performance reviews and leaves.

## Live Project

https://hrm-internship-project-production.up.railway.app

## Features

- Login
- Forgot Password
- OTP Verification
- Reset Password
- Dashboard
- Department Management
- Role Management
- Employee Management
- Task Management
- Performance Review
- Leave Management
- Leave Quota Management
- Role Based Access Control

## Modules

### Department Management
- Add departments
- Update departments
- Search departments
- Activate/Deactivate departments
- View departments

### Role Management
- Add roles
- Update roles
- Search roles
- Activate/Deactivate roles
- View roles

### Employee Management
- Manage employee details
- View employee records

### Task Management
- Manage employee tasks
- Track task details and status

### Performance Review
- Add performance reviews
- View performance reviews
- Update reviews
- Filter reviews
- Delete reviews

### Leave Management
- Apply for leave
- View applied leaves
- Update leave requests
- Check leave status
- Leave types include PL, CL, SL and LWP

### Leave Quota
- Add leave quota for employees
- Update leave quota
- Manage PL, CL, SL and LWP quotas

## Technologies Used

- Python
- Flask
- HTML
- CSS
- SQLite
- Gunicorn

## Database

SQLite database is used for storing the application data.

Database file:

`hrm.db`

## Project Structure

```text
hrm-internship-project/
│
├── app.py
├── hrm.db
├── requirements.txt
├── README.md
├── End_User_Documentation.md
├── static/
│   └── css/
└── templates/
