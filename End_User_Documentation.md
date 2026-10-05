# HRM System - End User Documentation

## 1. Introduction
The HRM System is a web-based application designed to streamline internal human resources tasks. It allows administrators and HR personnel to easily manage departments, roles, and employee records in a centralized database.

## 2. Department Management Module
This module allows you to define the various departments within the organization (e.g., IT, Sales, Operations).
- **Dashboard Overview**: Access via the sidebar. See a list of all current departments.
- **Add Department**: Click `+ Create Department` to add a new one. Provide the name and description.
- **Edit/Deactivate**: You can update a department's details by clicking `Edit` or toggle its active status using the `Activate`/`Deactivate` buttons.

## 3. Role Management Module
This module handles the different job roles an employee can hold (e.g., Admin, Manager, Employee).
- **Add Role**: Navigate to the Roles page via the sidebar. Click `+ Create Role` to define a new job position.
- **Manage Roles**: You can search for existing roles, edit their descriptions, and deactivate roles that are no longer in use.

## 4. Employee Management Module
The core feature of the HRM software, enabling seamless onboarding and management of employee records.
- **Add Employee**: Click `+ Add Employee` on the Employee Management page. 
- **Employee Details**: You will be required to fill in the employee's first and last name, contact details (email and mobile), date of joining, and assign system credentials (username and password).
- **Dynamic Assignments**: 
    - **Role**: Assign a specific role to define access rights.
    - **Department**: Place the employee in the relevant department.
    - **Reporting Manager**: Select a supervisor from the list of existing users to establish the reporting hierarchy.
- **Update/Delete**: Use the `Edit` button to update an employee's data if they change roles or departments. If an employee resigns or is terminated, use the `Delete` button to remove their record.

## 5. User Authentication System
This module secures the HRM software by requiring users to log in before accessing the dashboard and records.
- **Login**: Employees must enter their unique username and password. The system authenticates these credentials against the secure database.
- **Access Control**: Unauthenticated users cannot view or manage any internal company data.
- **Logout**: A secure logout button is provided in the top navigation bar to safely end a session.
- **Password Reset**:
    - If a user forgets their password, they can click 'Forgot your password?'.
    - They will be prompted to enter their registered email address.
    - An OTP (One Time Password) is dispatched to their email.
    - Upon verifying the OTP, the user is securely redirected to a page where they can set and confirm a new password.
