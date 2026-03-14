# Go-onCARE - Comprehensive User Manual

## 1. Introduction
Welcome to the Go-onCARE User Manual. This document provides an extremely detailed, step-by-step guide to using the Go-onCARE System, a robust solution designed for seamless healthcare management. The system modules covered in this manual include Authentication, Dashboard, Patients, Appointments, Clinical Records, Employee Management (HR & Regular), Payroll, Analytics, and Settings.

## 2. Getting Started & Authentication

### 2.1 Starting the Application
When you launch the system (e.g., via un.bat or executing main.py), you will be greeted by the Login Screen.

### 2.2 Logging In
1. Find your **Username** field and input your employee or admin username.
2. In the **Password** field, securely type your account password.
3. Click the **Login** button. 
4. If successful, you will be redirected to the Main Dashboard. Depending on your role limit (Admin, Doctor, HR, General Staff), some sidebar options and buttons may be disabled or hidden.

## 3. General User Interface Overview

Once logged in, the application is split into two primary areas:
- **Sidebar (Left Navigation Panel):** Displays all available modules. Click any icon/text to switch the main view.
- **Main View (Center Panel):** Displays the active modules content, data tables, charts, or forms.

### Common Controls
- **Add (+) Buttons:** Often found in the top-right corner of a module to add a new record.
- **Search Bars:** Type inside the search bar to filter table lists dynamically in real time.
- **Action Buttons (Edit/Delete):** Situated within the rows of tables to manage individual records.
- **Refresh:** Often automatically handled, but any view reload updates the most recent database entries.

## 4. Dashboard Module
The Dashboard provides a bird's-eye view of day-to-day operations.
- **Top Metrics:** Shows numeric summaries (e.g., Total Patients, Active Appointments, Today's Consultations).
- **Recent Activity / Charts:** Displays a quick graphical summary of the week's or month's performance based on the specific widget configuration in the system.

## 5. Patients Module
The Patients Module handles patient demographical data and historical registrations.

### 5.1 Adding a New Patient
1. Navigate to the **Patients** page from the sidebar.
2. Click the **Add Patient** button.
3. Fill out the mandatory fields: First Name, Last Name, Date of Birth.
4. Fill out optional items like Gender, Contact details, Address, and Emergency Contact.
5. Click **Save**. The table will update with the new entry immediately.

### 5.2 Editing/Deleting Patients
1. In the Patient List table, locate the desired patient.
2. Under the **Actions** column, click the **Edit** (pencil) icon to modify information or the **Delete** (trash) icon to remove them permanently from the registry.

## 6. Appointments Module
Manage scheduling between patients and doctors.

### 6.1 Creating an Appointment
1. Open the **Appointments** page.
2. Click **New Appointment**.
3. Select the target Patient from the dropdown list.
4. Select the assigned Doctor.
5. Choose the Date and Time.
6. Specify the Status (e.g., Scheduled, Completed, Cancelled).
7. Indicate the vital signs if doing a preliminary check (optional).
8. Click **Save**.

### 6.2 Managing Appointments
Appointments can be refined by date range using the date pickers on the upper menu of this view. Double-click or use the Edit button on an appointment to change its status as the patient is seen by the physician.

## 7. Clinical Module
The Clinical section holds all consultation notes, diagnosis, and treatment plan details.

### 7.1 Recording a Consultation
1. Navigate to the **Clinical** page.
2. Click **Record Consultation**.
3. Choose the relevant Appointment or Patient.
4. Fill out detailed subjective and objective notes in the provided text areas.
5. Specify the final **Diagnosis** and prescribe any required medications in the **Treatment** plan section.
6. Save the record. This acts as the legal medical chart for the visit.

## 8. Human Resources & Employees
The HR tools manage staff records, access levels, and employment statuses.

### 8.1 Employee Directory
- The **Employees** (or HR Employees) tab gives a roster of all active and inactive staff.
- You can search for staff by Name, Department, or Role.

### 8.2 Adding/Editing an Employee
1. Click **Add Employee** within the HR module.
2. Fill up their Personal Details, Department (Cardiology, Admin, etc.), and their Role (Doctor, Nurse, HR).
3. If giving them system access, define their credentials and access level correctly.
4. **Save** changes.

## 9. Payroll Module
Manages the distribution of wages to the recorded employees.

1. Access the **Payroll** tab.
2. Here, you will see a list of generated salary slips.
3. To generate a new run, click **Generate Payroll**.
4. Choose the specific month/period.
5. The system automatically computes base salaries depending on the employee's rank, deducting taxes and adding valid bonuses based on predetermined HR records.
6. Authorized accounts can then approve and disburse them.

## 10. Analytics Module
The analytics screen yields advanced graphical insights.
1. Head to the **Analytics** tab.
2. Review aggregated views such as: Patient Demographics, Appointment Trends (Line graphs showing busy periods), and Revenue/Payroll distribution charts.
3. Hover over chart elements for precise values.

## 11. Settings Module
Configure system preferences and base tables.
1. Navigate to **Settings**.
2. Customize the UI Theme (e.g., Light or Dark mode).
3. Database backup and general configurations might be located here depending on admin roles.
4. **Logout** option is generally placed toward the bottom of the sidebar or top right to securely lock the system.

## 12. Troubleshooting
- **Cannot Login:** Ensure Caps Lock is off, check with HR for inactive credentials.
- **Database Error:** Notify IT. Ensure you are connected to the main server housing the PostgreSQL/MySQL db.
- **Missing Functions:** Depending on your RBAC (Role-Based Access Control) limits, you may lack permissions to view Modules like Payroll. Request access from a system admin.

---
**Thank you for using Go-onCARE. System developed for maximum efficiency, care coordination, and healthcare management.**
