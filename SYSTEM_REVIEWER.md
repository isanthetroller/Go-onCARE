# Go-onCARE System — Complete Reviewer & Defense Guide

> **Purpose:** This document explains how the entire system works, feature by feature, so you can confidently answer any question during your capstone defense.

---

## TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Glossary — Technical Terms Explained](#2-glossary--technical-terms-explained)
3. [Technology Stack](#3-technology-stack)
4. [Database Design](#4-database-design)
5. [How the App Starts (Login Flow)](#5-how-the-app-starts-login-flow)
6. [Role-Based Access Control](#6-role-based-access-control)
7. [Feature Breakdown](#7-feature-breakdown)
   - [Dashboard](#71-dashboard)
   - [Patient Management](#72-patient-management)
   - [Appointment Scheduling](#73-appointment-scheduling)
   - [Clinical & POS (Queue + Billing)](#74-clinical--pos)
   - [Employee Management](#75-employee-management)
   - [HR Module](#76-hr-module)
   - [Data Analytics](#77-data-analytics)
   - [Settings & Administration](#78-settings--administration)
   - [Activity Log](#79-activity-log)
   - [Global Search](#710-global-search)
8. [How the Backend Works](#8-how-the-backend-works)
9. [How the UI Works](#9-how-the-ui-works)
10. [Database Relationships Explained](#10-database-relationships-explained)
11. [Doctor Data Isolation](#11-doctor-data-isolation)
12. [Input Validation System](#12-input-validation-system)
13. [System Analysis — What Makes Sense & What Doesn't](#13-system-analysis)
14. [Common Defense Questions & Answers](#14-common-defense-questions--answers)

---

## 1. SYSTEM OVERVIEW

**Go-onCARE** is a desktop clinic management system that handles:
- Patient registration and medical records
- Appointment scheduling with conflict detection
- Clinical patient queue (doctor workflow)
- Billing / Point-of-Sale with invoicing and payments
- Employee and HR management (payroll, leave requests)
- Analytics and reporting
- Activity logging (audit trail)

It uses **5 user roles** — Admin, Doctor, Cashier, Receptionist, HR — each seeing only the pages and buttons relevant to their job.

---

## 2. GLOSSARY — TECHNICAL TERMS EXPLAINED

Read this section first. Every technical word used later in the document is explained here in plain language.

### Programming Concepts

| Term | Plain English Explanation |
|------|--------------------------|
| **CRUD** | Stands for **Create, Read, Update, Delete** — the 4 basic operations you can do with data. Example: Add a patient (Create), view patient list (Read), change patient phone (Update), remove patient (Delete). Almost every feature in the system is CRUD. |
| **Backend** | The "brain" of the app — the code that talks to the database, processes data, and enforces rules. The user never sees the backend. It runs behind the scenes. In this project, the backend is all the Python files inside the `backend/` folder. |
| **Frontend / UI** | The part the user actually sees and clicks — buttons, tables, forms, popups. In this project, the UI is all the Python files inside the `ui/` folder. |
| **Class** | A blueprint for creating objects. Think of it like a template. Example: `PatientDialog` is a class — every time you click "Add Patient", a new dialog object is created from that blueprint. |
| **Object** | An instance of a class. If `PatientDialog` is the blueprint, then the actual popup window you see is the object. |
| **Method / Function** | A block of code that does one specific thing. Example: `add_patient()` is a method that inserts a new patient into the database. Methods live inside classes. |
| **Parameter / Argument** | Data you pass into a method. Example: `add_patient(data)` — `data` is the parameter (a dictionary containing name, phone, etc.). |
| **Dictionary (dict)** | A Python data structure that stores key-value pairs, like a mini-database. Example: `{"name": "Maria Santos", "phone": "+639171234567", "status": "Active"}`. You access values by key: `data["name"]` returns `"Maria Santos"`. |
| **List** | An ordered collection of items. Example: `["Active", "Inactive"]` is a list of two strings. You access items by position: `list[0]` returns `"Active"`. |
| **Mixin** | A class that adds specific functionality to another class. Instead of putting ALL the code in one giant file, we split it into mixins: `PatientMixin` handles patients, `AppointmentMixin` handles appointments, etc. Then we combine them: `class AuthBackend(PatientMixin, AppointmentMixin, ...)`. Each mixin "mixes in" its methods. Think of it like Lego blocks — each block adds a feature, and you snap them together. |
| **Inheritance** | When a class gets all the methods from a parent class. Example: `HREmployeeDialog` inherits from `EmployeeDialog` — it gets all the employee form fields, then adds salary and emergency contact fields on top. The child class reuses the parent's code without rewriting it. |
| **Multiple Inheritance** | When a class inherits from MORE than one parent. This is how mixins work: `AuthBackend` inherits from `DatabaseBase`, `PatientMixin`, `AppointmentMixin`, etc. — getting all their methods at once. |
| **Import** | Loading code from another file so you can use it. `from backend.patients import PatientMixin` means "bring in the PatientMixin class from the patients.py file so I can use it here." |
| **Module** | A single Python file (`.py`). Each file in the project is a module. |
| **Package** | A folder of Python files with an `__init__.py`. The `backend/` and `ui/` folders are packages. |

### Database Concepts

| Term | Plain English Explanation |
|------|--------------------------|
| **Database** | An organized collection of data stored on your computer. Think of it as a big spreadsheet application with many sheets (tables). We use MySQL. |
| **Table** | Like a single spreadsheet sheet — has rows (records) and columns (fields). Example: the `patients` table has one row per patient. |
| **Row / Record** | One entry in a table. One row in `patients` = one patient (Maria Santos, Female, O+, Active). |
| **Column / Field** | A specific piece of data in a table. `first_name`, `phone`, `status` are columns in the `patients` table. |
| **Primary Key (PK)** | A unique ID for each row. `patient_id` is the primary key of the `patients` table. No two patients can have the same `patient_id`. The database auto-generates it (AUTO_INCREMENT). |
| **Foreign Key (FK)** | A column that points to another table's primary key. It creates a link between tables. Example: `appointments.patient_id` is a foreign key pointing to `patients.patient_id`. This means every appointment MUST belong to a real patient. If you try to create an appointment for patient_id=999 but that patient doesn't exist, the database will reject it. |
| **JOIN** | A SQL command that combines data from two or more tables based on a related column. Example: To show "Maria Santos has an appointment with Dr. Ana Reyes", you JOIN the `appointments` table with `patients` and `employees` tables. Without JOINs, you'd only see ID numbers. |
| **LEFT JOIN** | A JOIN that keeps ALL rows from the left table, even if there's no match in the right table. Example: `patients LEFT JOIN appointments` shows ALL patients, even those with zero appointments (their appointment columns would be NULL). |
| **SELECT** | The SQL command to READ data from the database. `SELECT * FROM patients` means "get all columns from the patients table." |
| **INSERT** | The SQL command to CREATE a new record. `INSERT INTO patients (first_name) VALUES ('Maria')` adds a new patient. |
| **UPDATE** | The SQL command to MODIFY an existing record. `UPDATE patients SET phone='123' WHERE patient_id=1` changes patient #1's phone. |
| **DELETE** | The SQL command to REMOVE a record. `DELETE FROM patients WHERE patient_id=1` removes patient #1. |
| **WHERE** | A filter for SQL queries. `SELECT * FROM patients WHERE status='Active'` only returns active patients. Like an IF condition for the database. |
| **GROUP BY** | Groups rows that share a value together, used with aggregate functions. `SELECT status, COUNT(*) FROM patients GROUP BY status` returns the count of patients per status (e.g., Active: 10, Inactive: 3). |
| **COUNT / SUM / AVG** | Aggregate functions. COUNT counts rows, SUM adds up numbers, AVG calculates the average. Used in dashboard KPIs and analytics. |
| **LIKE** | Pattern matching in SQL. `WHERE name LIKE '%Santos%'` finds any name containing "Santos" anywhere. The `%` means "any characters." Used in the search feature. |
| **INDEX** | A database optimization that makes searches faster. Like a book's index — instead of reading every page to find "Hypertension," you check the index. We have indexes on `appointment_date`, `status`, `patient_id`, etc. |
| **Transaction** | A group of SQL queries that must ALL succeed or ALL fail. Example: creating an invoice needs INSERT into `invoices` AND INSERT into `invoice_items`. If the second INSERT fails, the first one is rolled back (undone). This prevents half-created data. |
| **Schema** | The structure/design of the database — which tables exist, what columns they have, how they relate. The `carecrud.sql` file defines the schema. |
| **Seed Data** | Pre-loaded sample data inserted when the database is first created. Our seed data includes 5 user accounts, 8 employees, sample patients, services, departments, etc. Used for testing. |
| **CASCADE** | Automatic chain reaction when deleting. If `ON DELETE CASCADE` is set on a foreign key, deleting a patient automatically deletes their conditions too. We do most cascading manually in code for more control. |
| **NULL** | Means "no value" or "empty." Different from zero or blank string. Example: a patient with no discount has `discount_type_id = NULL`. |
| **ENUM** | A column type that only allows specific values. Example: `status ENUM('Active', 'Inactive')` means status can ONLY be "Active" or "Inactive" — nothing else. |
| **AUTO_INCREMENT** | The database automatically assigns the next number. Patient #1, #2, #3... You never set the ID manually. |

### UI / PyQt6 Concepts

| Term | Plain English Explanation |
|------|--------------------------|
| **PyQt6** | A Python library for building desktop application windows with buttons, tables, forms, etc. Qt is the underlying C++ framework; PyQt6 is the Python wrapper. The "6" is the version number. |
| **Widget** | Any visible element on screen — a button, a text field, a label, a table, a checkbox. Everything you see is a widget. In PyQt6, all widgets inherit from `QWidget`. |
| **Layout** | An invisible container that arranges widgets. `QVBoxLayout` stacks widgets vertically (top to bottom). `QHBoxLayout` arranges them horizontally (left to right). `QFormLayout` creates label-field pairs (like a form). |
| **Signal / Slot** | Qt's event system. A **signal** is emitted when something happens (button clicked, text changed). A **slot** is the function that runs in response. `button.clicked.connect(self.save)` means "when button is clicked, run the save() method." |
| **QDialog** | A popup window. When you click "Add Patient," a QDialog appears with the form. It blocks interaction with the main window until closed (modal). |
| **QComboBox** | A dropdown selector. Used for selecting role, department, status, blood type, etc. |
| **QTableWidget** | A table widget with rows and columns. Used to display patient lists, appointment lists, invoices, etc. |
| **QStackedWidget** | Shows one page at a time, like a deck of cards. The main content area uses this — clicking "Patients" in the sidebar shows page 1, clicking "Appointments" shows page 2, etc. |
| **QSS (Qt Style Sheets)** | CSS-like styling for Qt widgets. Controls colors, borders, fonts, padding, rounded corners. Written in `.qss` files. Example: `QPushButton { background-color: #388087; color: white; border-radius: 10px; }` |
| **Object Name** | An ID you give to a widget so QSS can target it specifically. `button.setObjectName("dialogSaveBtn")` lets you style it with `QPushButton#dialogSaveBtn { ... }`. Like CSS class selectors. |
| **Event Filter** | A way to intercept events (keyboard, mouse, focus) before they reach a widget. Used for the phone input: when the text field gets focus, the surrounding frame's border turns teal. |

### General Software Concepts

| Term | Plain English Explanation |
|------|--------------------------|
| **API** | Application Programming Interface — a set of methods/functions you can call. The backend is essentially an API for the UI: the UI calls `backend.get_patients()` and gets data back. |
| **Audit Trail** | A record of who did what and when. The `activity_log` table is the audit trail. Important for accountability in medical systems. |
| **Validation** | Checking that user input is correct before saving. Examples: phone must be 10 digits, name can't be empty, date can't be in the past. Prevents bad data from entering the database. |
| **Regex (Regular Expression)** | A pattern for matching text. `^\d{10}$` means "exactly 10 digits." Used for phone validation. `^` = start, `\d` = digit, `{10}` = exactly 10, `$` = end. |
| **Plaintext Password** | Storing passwords as-is without encryption. This is a **security weakness** in this system. In production, passwords should be hashed (scrambled) so even if the database is stolen, passwords can't be read. |
| **KPI** | Key Performance Indicator — important numbers that show how things are going. Examples: Today's Revenue, Active Patients, Appointment Count. Displayed on the Dashboard. |
| **POS** | Point of Sale — the billing/payment system where transactions happen. In this app, it's the Billing tab of the Clinical page where invoices are created and payments are processed. |
| **Cascading Delete** | When deleting one record requires deleting all related records first. Deleting a patient means first deleting their invoice items, invoices, queue entries, appointments, and conditions. Like pulling a thread that unravels connected things. |
| **Refactoring** | Restructuring existing code without changing what it does. Making it cleaner, more organized, or more efficient. |

---

## 3. TECHNOLOGY STACK

| Layer | Technology | Why |
|-------|-----------|-----|
| **Programming Language** | Python | Easy to read, large library ecosystem |
| **Desktop UI Framework** | PyQt6 | Cross-platform GUI toolkit, professional-looking widgets |
| **Database** | MySQL | Relational database, supports foreign keys, transactions, and JOINs |
| **Database Connector** | mysql-connector-python | Official MySQL driver for Python |
| **Styling** | QSS (Qt Style Sheets) | CSS-like, controls how every widget looks |
| **Charts** | Custom QWidget painting | Drawn using QPainter for bar charts and pie charts |

### Project Structure
```
main.py                  ← Entry point (starts the app)
backend/
  base.py                ← Database connection + helper methods (fetch, exec)
  __init__.py            ← Combines all backend mixins into one class
  auth.py                ← Login, password management
  patients.py            ← Patient CRUD operations
  appointments.py        ← Appointment CRUD + conflict checking
  clinical.py            ← Queue management, invoicing, services
  employees.py           ← Employee CRUD + leave system
  dashboard.py           ← Dashboard KPI queries
  analytics.py           ← Charts and report data
  settings.py            ← Admin settings, discount types, cleanup
  search.py              ← Global search across tables
ui/
  auth_window.py         ← Login screen
  main_window.py         ← Main app window (sidebar + pages)
  styles.py              ← Reusable UI helper functions
  styles/
    auth.qss             ← Login screen stylesheet
    main.qss             ← Main app stylesheet
  shared/                ← All page widgets (used by multiple roles)
    dashboard_page.py
    patients_page.py
    patient_dialogs.py
    appointments_page.py
    appointment_dialog.py
    clinical_page.py
    clinical_dialogs.py
    employees_page.py
    employee_dialogs.py
    hr_employees_page.py
    hr_employee_dialogs.py
    analytics_page.py
    settings_page.py
    activity_log_page.py
    chart_widgets.py
database/
  carecrud.sql           ← Full database schema + seed data
  sample_data.sql        ← Additional sample data
  drop_all_data.sql      ← Reset script
```

---

## 4. DATABASE DESIGN

### All Tables (16 total)

#### Lookup Tables (store fixed reference data)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `departments` | Hospital departments | department_id, department_name |
| `roles` | User roles (Doctor, Cashier, etc.) | role_id, role_name |
| `services` | Medical services with prices | service_id, service_name, price, category, is_active |
| `payment_methods` | How patients pay (Cash, GCash, etc.) | method_id, method_name |
| `standard_conditions` | Common medical conditions list | condition_id, condition_name |
| `discount_types` | Discount categories (Senior, PWD) | discount_id, type_name, discount_percent, legal_basis |

#### Main Tables (core data)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | Login accounts | user_id, email, password, full_name, role_id, must_change_password |
| `user_preferences` | User settings | pref_id, user_email, dark_mode |
| `employees` | Staff records | employee_id, first_name, last_name, role_id, department_id, phone, email, hire_date, status, salary |
| `patients` | Patient records | patient_id, first_name, last_name, sex, date_of_birth, phone, email, blood_type, discount_type_id, status |
| `patient_conditions` | Patient medical conditions | condition_id, patient_id, condition_name |

#### Transaction Tables (things that happen)
| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `appointments` | Scheduled visits | appointment_id, patient_id, doctor_id, service_id, date, time, status |
| `queue_entries` | Daily patient queue | queue_id, patient_id, doctor_id, appointment_id, status |
| `invoices` | Bills | invoice_id, patient_id, total_amount, amount_paid, status, discount_percent |
| `invoice_items` | Line items on each bill | item_id, invoice_id, service_id, quantity, unit_price, subtotal |
| `activity_log` | Audit trail | log_id, user_email, action, record_type, record_detail |
| `leave_requests` | Employee leave applications | request_id, employee_id, leave_from, leave_until, status |
| `notifications` | Messages to employees | notification_id, employee_id, message, is_read |

### How Tables Connect (Foreign Keys)

```
departments ←── employees ──→ roles
                    ↑
                    │ (doctor_id)
patients ──→ appointments ──→ services
   ↑              ↑
   │              │
   ├── patient_conditions
   │
   └── invoices ──→ payment_methods
         ↑
         └── invoice_items ──→ services

users ──→ roles
employees ──→ leave_requests
employees ──→ notifications
activity_log (standalone, tracks everything)
```

### What is a Foreign Key?
A foreign key is a column that **references** another table's primary key. It ensures data integrity.
- Example: `appointments.patient_id` references `patients.patient_id`
- This means you **can't** create an appointment for a patient that doesn't exist
- If you delete a patient, you must first delete their appointments (cascading delete)

### What is a JOIN?
A JOIN combines rows from two tables based on a related column.
```sql
-- Example: Get appointment with patient name and doctor name
SELECT a.appointment_date, 
       CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
       CONCAT(e.first_name, ' ', e.last_name) AS doctor_name
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN employees e ON a.doctor_id = e.employee_id
```
This query **joins** the appointments table with patients and employees to get human-readable names instead of just IDs.

---

## 5. HOW THE APP STARTS (LOGIN FLOW)

### Step-by-Step:

1. **`main.py` runs** → Creates the `QApplication` and `AuthWindow` (login screen)
2. **User enters email + password** → Clicks "Sign In"
3. **`AuthBackend.login(email, password)`** is called:
   ```sql
   SELECT u.*, r.role_name FROM users u 
   JOIN roles r ON u.role_id = r.role_id 
   WHERE u.email = %s
   ```
   - Checks if email exists
   - Compares password (plaintext match)
   - Returns: success/fail, role name, full name, must_change_password flag
4. **If `must_change_password = 1`** → Forces user to set a new password before continuing
5. **On success** → `login_success` signal emits `(email, role, full_name)`
6. **`MainWindow` is created** with the user's role → sidebar shows only allowed pages
7. **Login window hides**, main window shows

### First-Time Password Change:
- When an admin creates a new account, the password is set to something like "doctor123"
- The `must_change_password` flag is set to `1`
- On first login, a dialog forces the user to pick a new password
- After changing, `must_change_password` is set to `0`

---

## 6. ROLE-BASED ACCESS CONTROL

### What Each Role Can See:

| Page | Admin | Doctor | Cashier | Receptionist | HR |
|------|:-----:|:------:|:-------:|:------------:|:--:|
| Dashboard | ✅ | ✅ | ✅ | ✅ | ✅ |
| Patients | ✅ Full CRUD | 👁️ View own | 👁️ Read-only | ✅ Full CRUD | ❌ |
| Appointments | ✅ Full CRUD | 👁️ View/Confirm own | 👁️ Read-only | ✅ Full CRUD | ❌ |
| Clinical Queue | ✅ View | ✅ Call Next/Complete | ❌ | ❌ | ❌ |
| Billing/POS | ✅ View | ❌ | ✅ Pay/Void | ✅ Create invoices | ❌ |
| Services & Pricing | ✅ Full CRUD | ❌ | ❌ | ❌ | ❌ |
| Employees (Admin) | ✅ Full CRUD | ❌ | ❌ | ❌ | ❌ |
| HR Module | ✅ + User Accounts | ❌ | ❌ | ❌ | ✅ |
| Analytics | ✅ Full | ✅ Own stats | ❌ | ❌ | ❌ |
| Activity Log | ✅ Full | ✅ | ✅ | ✅ | ✅ Logins only |
| Settings | ✅ Full + DB mgmt | ✅ Profile only | ✅ Profile only | ✅ Profile only | ✅ Profile only |

### How It's Implemented:
1. **Sidebar filtering**: `main_window.py` checks the role and only adds allowed menu items
2. **Page-level**: Each page's `__init__` receives the `role` parameter and hides/shows widgets
3. **Button-level**: Individual buttons check `self._role` before appearing
   ```python
   # Example: Only Admin and Receptionist see the "Add Patient" button
   if self._role not in ("Cashier", "Doctor"):
       banner_btn.setVisible(True)
   ```
4. **Data-level**: Doctors only see their own patients/appointments (filtered SQL queries)

---

## 7. FEATURE BREAKDOWN

### 7.1 Dashboard

**What it shows:**
- Greeting with current date/time (updates every second)
- 4 KPI cards: Today's Appointments, Active Patients, Today's Revenue, Active Staff
- Delta percentages (↑/↓ compared to last month)
- Quick action buttons (New Patient, New Appointment, Clinical Queue, Analytics)
- Today's Schedule (upcoming appointments)
- Monthly Visits bar chart (last 6 months)
- My Leave Requests (for employees, not Admin/HR)
- Recent Activity (Admin only)

**How KPIs are calculated:**
```sql
-- Today's Appointments
SELECT COUNT(*) FROM appointments WHERE appointment_date = CURDATE()

-- Active Patients
SELECT COUNT(*) FROM patients WHERE status = 'Active'

-- Today's Revenue
SELECT COALESCE(SUM(amount_paid), 0) FROM invoices 
WHERE DATE(created_at) = CURDATE() AND status IN ('Paid', 'Partial')

-- Active Staff
SELECT COUNT(*) FROM employees WHERE status = 'Active'
```

**Delta % calculation:**
```
delta = ((current_month_value - last_month_value) / last_month_value) × 100
```

**Auto-refresh:** Every 10 seconds, KPIs and schedule are reloaded from the database.

---

### 7.2 Patient Management

**CRUD Operations:**

| Operation | Who Can | What Happens |
|-----------|---------|-------------|
| **Create** | Admin, Receptionist | Opens form → fills name, sex, DOB, phone, email, emergency contact, blood type, discount, conditions, status, notes → INSERT into `patients` + `patient_conditions` |
| **Read** | All roles | Table shows all patients (Doctor sees only own patients via JOIN with appointments) |
| **Update** | Admin, Receptionist | Opens same form pre-filled → UPDATE `patients` + DELETE/re-INSERT `patient_conditions` |
| **Delete** | Admin, Receptionist | Confirmation dialog → Cascading delete: invoice_items → invoices → queue_entries → appointments → patient_conditions → patients |

**Patient Conditions System:**
- Standard conditions (Hypertension, Diabetes, etc.) stored in `standard_conditions` table
- When adding a patient, user checks conditions from a checkbox list
- Can also type custom conditions in a text field
- All conditions stored as separate rows in `patient_conditions` table (one row per condition per patient)
- When updating, all old conditions are deleted and new ones inserted

**Patient Merge Feature:**
- Admin/Receptionist can merge duplicate patients
- Select "Keep" patient and "Remove" patient
- All appointments, invoices, queue entries from "Remove" are transferred to "Keep"
- "Remove" patient's unique conditions are added to "Keep"
- "Remove" patient record is deleted

**Discount System:**
- Each patient can have one discount type (Senior Citizen 20%, PWD 20%, etc.)
- Stored as `discount_type_id` foreign key
- When an invoice is created, the system looks up the patient's discount and **enforces it from the database** — the UI cannot override this

**How the View Profile works:**
```sql
-- 4 separate queries combined into one profile:
-- 1. Patient info (name, sex, dob, phone, etc.)
-- 2. Appointments history (date, doctor, service, status)
-- 3. Invoices history (invoice #, total, paid, status)
-- 4. Queue history (queue #, time, doctor, purpose)
```

---

### 7.3 Appointment Scheduling

**How creating an appointment works:**
1. User clicks "+ New Appointment"
2. Dialog opens with: Patient (searchable dropdown), Doctor, Date, Time, Service, Status, Notes
3. **Patient search**: Editable combo box with autocomplete — user types a name, suggestions filter as they type
4. **Date validation**: Cannot schedule in the past; cannot schedule beyond next month's last day
5. **Conflict detection**: Before saving, checks if the doctor already has an appointment at the same date+time
   ```sql
   SELECT COUNT(*) FROM appointments 
   WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s 
   AND status != 'Cancelled'
   ```
6. If conflict found, warns user but allows saving anyway (with confirmation)
7. On save: resolves patient name to `patient_id` via:
   ```sql
   SELECT patient_id FROM patients 
   WHERE CONCAT(first_name, ' ', last_name) = %s LIMIT 1
   ```
8. INSERT into `appointments` table

**Quick Filter Tabs:**
- Today, Tomorrow, This Week, This Month, All
- These filter the table rows client-side (no new query needed)

**Status Flow:**
```
Pending → Confirmed → Completed
              ↘ Cancelled
```
- **Doctor** can: View details, Confirm (Pending→Confirmed), Cancel (with reason)
- **Admin/Receptionist** can: Create, Edit all fields, Delete

---

### 7.4 Clinical & POS

This is the most complex page with **3 tabs**:

#### Tab 1: Patient Queue (Admin, Doctor)

**How the queue works:**
1. When the page loads, it **syncs** today's confirmed appointments to the queue:
   ```sql
   -- For each confirmed appointment today that's not already in the queue:
   INSERT INTO queue_entries (patient_id, doctor_id, appointment_id, queue_time, purpose, status)
   ```
2. Queue shows: Queue #, Patient, Doctor, Time, Purpose, Status
3. **Doctor workflow:**
   - Doctor clicks **"Call Next"** → system finds the first "Waiting" entry for that doctor and sets it to "In Progress"
   - Doctor can only have **one** "In Progress" patient at a time
   - After consultation, clicks **"Complete"** → marks queue entry as Completed, marks appointment as Completed, auto-creates an invoice
   - Or clicks **"Cancel"** → marks both queue entry and appointment as Cancelled

**Auto-invoice on completion:**
```python
# When doctor completes a queue entry:
# 1. Look up the appointment's service and price
# 2. Check if patient has a discount (from discount_types table)
# 3. Calculate: subtotal = price × quantity, then apply discount
# 4. INSERT invoice + INSERT invoice_item
# 5. Invoice status = 'Unpaid' (cashier handles payment later)
```

**Wait Time Estimation:**
```sql
-- Average consultation time from last 30 days:
SELECT AVG(TIMESTAMPDIFF(MINUTE, queue_time, completed_time)) 
FROM queue_entries WHERE status = 'Completed' AND created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)

-- Estimated wait = waiting_count × avg_minutes
```

#### Tab 2: Billing / POS (Admin, Receptionist, Cashier)

**Invoice table shows:** Invoice #, Patient, Services, Total, Paid, Status, Actions

**Creating a new invoice manually:**
1. Click "+ New Invoice"
2. Select patient (searchable), add service line items (service + quantity)
3. System auto-calculates: subtotal per item, discount (from patient's record), grand total
4. Select payment method, enter amount paid
5. Status auto-determined: amount_paid >= total → "Paid", partial → "Partial", zero → "Unpaid"

**How discount is enforced (important!):**
```python
# The system IGNORES any discount from the UI
# Instead, it looks up the patient's discount from the database:
SELECT discount_percent FROM discount_types 
WHERE discount_id = (SELECT discount_type_id FROM patients WHERE patient_id = %s)

# This prevents cashiers from giving unauthorized discounts
```

**Payment processing (Cashier only):**
1. Click "Pay" on an unpaid/partial invoice
2. Dialog shows remaining balance
3. Enter payment amount (capped at remaining balance)
4. UPDATE invoice: add to amount_paid, update status

**Void (Admin, Cashier):**
- Sets invoice status to "Voided" — the invoice remains in the system for audit trail

**Role restrictions:**
- **Receptionist**: Can create invoices, but CANNOT pay or void
- **Cashier**: Can pay and void, can create invoices
- **Admin**: Can view but buttons are hidden (oversight role)

#### Tab 3: Services & Pricing (Admin only)

- View all medical services with name, price, category, active/inactive status
- Add new services, edit existing ones
- Bulk price update: change multiple prices at once
- Usage count: shows how many times each service has been invoiced

---

### 7.5 Employee Management (Admin Side)

**Where:** Employees page (Admin only)

**What it shows:**
- 4 stat cards: Total Staff, Doctors, Active, On Leave
- Staff per Department mini-table
- Full employee table with search/filter

**CRUD:**
| Operation | What Happens |
|-----------|-------------|
| **Add** | Dialog: name, role, department, type, phone (+63 prefix), email, hire date, status, notes → INSERT into `employees` → **Auto-creates a user account** |
| **Edit** | Same dialog pre-filled → UPDATE `employees` → syncs email to `users` table |
| **Fire** | "Fire" button in edit dialog → cascade deletes all related data (appointments, invoices, queue, notifications, leave requests) |
| **View** | Profile dialog with tabs: Info, Appointments (last 20), Performance (total appts, completed, revenue) |

**Auto-create user account:**
When you add a new employee with an email, the system:
1. Splits "Ana Reyes" into first_name="Ana", last_name="Reyes"
2. Creates a user account with password = `{role}123` (e.g., "doctor123")
3. Sets `must_change_password = 1` so they must change it on first login

**Duplicate phone check:**
Before saving, checks if the phone number is already used by another employee.

---

### 7.6 HR Module

**Where:** HR Employees page (HR and Admin)

**4 Tabs:**

#### Tab 1: Employees (enhanced with salary/emergency contact)
- Everything the Admin employee page has, PLUS salary and emergency contact fields
- HR stats: Total, Active, On Leave, Inactive, Average Salary, Total Payroll

#### Tab 2: Leave Management
**Leave Request Workflow:**
```
Employee submits request (from Dashboard)
         ↓
   Status: "Pending"
         ↓
HR reviews (in Leave Management tab)
         ↓
    ┌─────┴─────┐
 Approve      Decline
    ↓            ↓
Employee      Employee gets
status →     notification
"On Leave"   with reason
    ↓
All pending/confirmed
appointments during
leave period → Cancelled
    ↓
After leave_until date:
auto_expire_leaves() runs
    ↓
Employee status → "Active"
```

**How approval works (SQL):**
```sql
-- 1. Update leave request status
UPDATE leave_requests SET status='Approved', hr_decided_by=%s, decided_at=NOW()

-- 2. Update employee status and dates
UPDATE employees SET status='On Leave', leave_from=%s, leave_until=%s

-- 3. Cancel all conflicting appointments
UPDATE appointments SET status='Cancelled', cancellation_reason='Employee on approved leave'
WHERE doctor_id=%s AND appointment_date BETWEEN %s AND %s 
AND status IN ('Pending', 'Confirmed')

-- 4. Send notification to employee
INSERT INTO notifications (employee_id, message) VALUES (%s, 'Your leave request has been approved')
```

**Auto-expire:** Every 5 minutes, `main_window.py` calls `auto_expire_leaves()` which checks:
```sql
UPDATE employees SET status='Active', leave_from=NULL, leave_until=NULL
WHERE status='On Leave' AND leave_until <= CURDATE()
```

#### Tab 3: Payroll & Staffing
- Department Payroll table: Department, Headcount, Total Salary, Average Salary
- Employment Type Breakdown: Full-time, Part-time, Contract counts
- Read-only summary (no editing)

#### Tab 4: User Accounts (Admin only)
- View all system login accounts
- Create new account (for existing employee)
- Reset password (sets `must_change_password = 1`)
- Delete account

---

### 7.7 Data Analytics

**Admin sees (hospital-wide):**

| Section | What It Shows | SQL Logic |
|---------|-------------|-----------|
| **KPI Cards** | Monthly Revenue, Total Patients, Appointments, Active Doctors, Avg Visit/Day | Aggregate queries with period comparison |
| **Patient Conditions** | Pie chart of most common conditions | `GROUP BY condition_name` from `patient_conditions` |
| **Appointment Status** | Pie chart (Pending/Confirmed/Completed/Cancelled) | `GROUP BY status` from `appointments` |
| **Revenue by Department** | Pie chart | JOIN invoices → appointments → employees → departments, SUM amount_paid |
| **Patient Demographics** | Pie chart by age groups (0-17, 18-35, 36-50, 51-65, 65+) | `CASE WHEN` age calculation from date_of_birth |
| **Patient Retention** | New vs Returning patients per month | Subquery: first appointment date per patient |
| **Cancellation Rate** | Trend over 6 months | cancelled / total × 100 per month |
| **Doctor Performance** | Table: Doctor, Total Appts, Completed, Revenue | GROUP BY doctor |
| **Top Services** | Table: Service, Usage Count, Revenue | JOIN invoice_items → services, GROUP BY service |
| **Monthly Revenue Trend** | Chart/Table over 6 months | SUM amount_paid per month |
| **Summary with Date Range** | Filterable KPI table | WHERE between from_date AND to_date |

**Doctor sees (own stats only):**
- Own KPI cards: Total Appointments, Completed, Cancelled, Revenue, Completion Rate
- Own monthly revenue bar chart
- Own monthly breakdown table

**How retention is calculated:**
```sql
-- "New" patient = their FIRST appointment ever is in this month
-- "Returning" patient = they had appointments before this month
SELECT DATE_FORMAT(a.appointment_date, '%Y-%m') AS month,
  COUNT(DISTINCT CASE WHEN a.appointment_date = sub.first_date THEN a.patient_id END) AS new_patients,
  COUNT(DISTINCT CASE WHEN a.appointment_date > sub.first_date THEN a.patient_id END) AS returning_patients
FROM appointments a
JOIN (SELECT patient_id, MIN(appointment_date) AS first_date FROM appointments GROUP BY patient_id) sub
```

---

### 7.8 Settings & Administration

**All roles can:**
- Change their own password (current → new → confirm)

**Admin can also:**

| Feature | What It Does |
|---------|-------------|
| **Discount Management** | Add/Edit/Delete discount types (Senior 20%, PWD 20%, etc.) with legal basis |
| **Database Overview** | Shows row counts for all 16 tables (auto-refreshes every 10 seconds) |
| **Cleanup: Completed Appointments** | Delete completed appointments before a chosen date (cascades to invoices, queue) |
| **Cleanup: Cancelled Appointments** | Delete ALL cancelled appointments |
| **Cleanup: Inactive Patients** | Delete ALL inactive patients and their linked data |
| **Truncate Table** | Empties a table completely (restricted to safe list: queue_entries, invoice_items, invoices, appointments, patient_conditions, activity_log) |

**Discount deletion safety:**
```python
# Before deleting a discount type, unlink all patients using it:
UPDATE patients SET discount_type_id = NULL WHERE discount_type_id = %s
# Then delete the discount type:
DELETE FROM discount_types WHERE discount_id = %s
```

---

### 7.9 Activity Log

**What gets logged:**
Every important action in the system is recorded with:
- Timestamp, User email, User role, Action, Entity type, Detail text

**Actions tracked:** Login, Created, Edited, Deleted, Requested, Approved, Declined, Voided, Merged, Synced, Called, Cleaned, Cleared

**Example entries:**
```
2026-03-09 14:30:22 | admin@carecrud.com | Admin | Created | Patient | Maria Santos
2026-03-09 15:00:00 | ana.reyes@carecrud.com | Doctor | Called | Queue | Called next patient: Juan Dela Cruz
2026-03-09 15:30:00 | sofia.reyes@carecrud.com | Cashier | Created | Invoice | Payment received for Juan Dela Cruz
```

**Role filtering:**
- **Admin**: Sees everything, can filter by user/action/type/date
- **HR**: Only sees Login activity from Doctors and Receptionists
- **Others**: See the full log but with limited filter options

---

### 7.10 Global Search

**How it works:**
1. User types in the search bar at the top of the main window
2. After 2+ characters, backend runs 3 LIKE queries:
   ```sql
   -- Search patients by name, phone, or email
   WHERE CONCAT(first_name,' ',last_name) LIKE '%query%' OR phone LIKE '%query%'
   
   -- Search appointments by patient name
   WHERE CONCAT(p.first_name,' ',p.last_name) LIKE '%query%'
   
   -- Search employees by name or email
   WHERE CONCAT(first_name,' ',last_name) LIKE '%query%' OR email LIKE '%query%'
   ```
3. Results shown in a popup table (max 10 per category)
4. Employee results hidden from non-admin roles

---

## 8. HOW THE BACKEND WORKS

### Architecture: Mixin Pattern

The backend uses **mixin classes** — each file defines a class with specific methods, and they're all combined into one:

```python
# backend/__init__.py
class AuthBackend(
    DatabaseBase,     # Connection + helpers (fetch, exec)
    AuthMixin,        # login(), update_password()
    PatientMixin,     # get_patients(), add_patient()
    AppointmentMixin, # get_appointments(), add_appointment()
    ClinicalMixin,    # get_queue(), add_invoice()
    EmployeeMixin,    # get_employees(), add_employee()
    DashboardMixin,   # get_dashboard_summary()
    AnalyticsMixin,   # get_monthly_revenue()
    SettingsMixin,    # get_discount_types(), truncate_table()
    SearchMixin,      # global_search()
):
    pass
```

**Why mixins?** Each file handles one feature area, keeping the code organized. But they all share the same database connection from `DatabaseBase`.

### Three Core Database Methods:

```python
# SELECT queries → Returns list of dictionaries
self.fetch("SELECT * FROM patients WHERE status=%s", ("Active",))
# Returns: [{"patient_id": 1, "first_name": "Maria", ...}, ...]

# Single SELECT → Returns one dictionary
self.fetch("SELECT * FROM patients WHERE patient_id=%s", (1,), one=True)
# Returns: {"patient_id": 1, "first_name": "Maria", ...}

# INSERT/UPDATE/DELETE → Returns row count or ID
self.exec("INSERT INTO patients (first_name) VALUES (%s)", ("Maria",))
# Returns: 1 (the new patient_id)

# Multiple queries in one transaction (all succeed or all fail)
self.exec_many([
    ("INSERT INTO invoices ...", (params,)),
    ("INSERT INTO invoice_items ...", (params,)),
])
```

### What is a Transaction?
A transaction groups multiple SQL queries so they **all succeed or all fail**. Example:
- When creating an invoice, you INSERT into `invoices` AND `invoice_items`
- If the invoice_items INSERT fails, the invoice INSERT is **rolled back** (undone)
- This prevents incomplete/broken data

### Activity Logging:
```python
# Called after every important action:
self.log_activity("Created", "Patient", "Added patient Maria Santos")
# This INSERTs into the activity_log table with the current user's email and role
```

---

## 9. HOW THE UI WORKS

### PyQt6 Concepts You Need to Know:

| Concept | What It Is | Example |
|---------|-----------|---------|
| **QWidget** | Base class for all UI elements | Every button, label, text field is a QWidget |
| **Layout** | Arranges widgets inside a container | QVBoxLayout (vertical), QHBoxLayout (horizontal), QFormLayout (label + field pairs) |
| **Signal/Slot** | Event system — when something happens, call a function | `button.clicked.connect(self.on_click)` → when button is clicked, call on_click() |
| **QDialog** | Popup window for forms | Add Patient dialog, Appointment dialog |
| **QStackedWidget** | Shows one page at a time (like browser tabs) | Main content area switches between Dashboard/Patients/etc. |
| **QTableWidget** | Data table with rows and columns | Patient list, appointment list, invoice list |
| **QSS** | CSS-like styling for Qt widgets | Colors, borders, fonts, spacing |

### How a Page Loads:

```
User clicks "Patients" in sidebar
        ↓
main_window._on_nav(index=1)
        ↓
self.stack.setCurrentIndex(1)  ← shows Patients page
        ↓
self._patients_page._load_from_db()  ← refreshes from database
        ↓
Backend.get_patients()  ← SQL query
        ↓
Results populate the QTableWidget rows
```

### How a Dialog Works (Add Patient example):

```
User clicks "+ Add Patient"
        ↓
PatientDialog() created  ← form with empty fields
        ↓
User fills in fields, clicks "Save"
        ↓
dialog.accept() called  ← validates phone format
        ↓
dialog.get_data() returns a dictionary:
{
  "name": "Maria Santos",
  "sex": "Female",
  "phone": "+639171234567",
  "email": "maria@email.com",
  "blood_type": "O+",
  "conditions": "Hypertension, Diabetes",
  ...
}
        ↓
Backend.add_patient(data)  ← SQL INSERT
        ↓
Table refreshes to show new patient
```

### Styling:
- **QSS files** (`auth.qss`, `main.qss`) define the look — colors, borders, fonts, etc.
- **`styles.py`** has helper functions like `make_card()`, `make_banner()`, `make_table_btn()` that create consistently styled widgets
- **Color palette**: Teal (#388087), Light blue (#BADFE7), Off-white (#F6F6F2), Dark text (#2C3E50)

---

## 10. DATABASE RELATIONSHIPS EXPLAINED

### One-to-Many Relationships:
- One **department** has many **employees**
- One **patient** has many **appointments**
- One **patient** has many **conditions** (in patient_conditions)
- One **invoice** has many **line items** (in invoice_items)
- One **doctor** (employee) has many **appointments**
- One **employee** has many **leave requests**

### Why Cascading Deletes?
When you delete a patient, you need to also delete:
1. Their invoice items (because invoice_items → invoices → patients)
2. Their invoices
3. Their queue entries
4. Their appointments
5. Their conditions

The code does this manually in order to respect foreign key constraints:
```python
def delete_patient(self, patient_id):
    queries = [
        ("DELETE FROM invoice_items WHERE invoice_id IN (SELECT invoice_id FROM invoices WHERE patient_id=%s)", (pid,)),
        ("DELETE FROM invoices WHERE patient_id=%s", (pid,)),
        ("DELETE FROM queue_entries WHERE patient_id=%s", (pid,)),
        ("DELETE FROM appointments WHERE patient_id=%s", (pid,)),
        ("DELETE FROM patient_conditions WHERE patient_id=%s", (pid,)),
        ("DELETE FROM patients WHERE patient_id=%s", (pid,)),
    ]
    return self.exec_many(queries)
```

---

## 11. DOCTOR DATA ISOLATION

### The Problem
In a multi-doctor clinic, each doctor should ONLY see data related to their own patients and appointments — not every doctor's data. This is both a **privacy** and **UX** requirement.

### How It Works
When a Doctor logs in, the system stores their email (e.g., `ana.reyes@carecrud.com`). This email is used to look up their `employee_id` (which is their `doctor_id` in appointments/queue tables). Every query then filters by this ID.

### Isolation Points

| Feature | How It's Filtered | Backend Method |
|---------|-------------------|----------------|
| **Dashboard KPIs** | Passes `doctor_email` to count only the doctor's own appointments, patients, and revenue | `get_dashboard_summary(doctor_email=)` |
| **Dashboard Schedule** | Only shows upcoming appointments assigned to this doctor | `get_upcoming_appointments(doctor_email=)` |
| **Dashboard Chart** | Monthly visits chart shows only this doctor's patient visits | `get_patient_stats_monthly(doctor_email=)` |
| **Patient List** | JOINs through appointments to show only patients who have appointments with this doctor | `get_patients_for_doctor(email)` |
| **Appointment List** | Filters appointments WHERE doctor's email matches | `get_appointments(doctor_email=)` |
| **Clinical Queue** | Filters queue entries WHERE doctor_id matches | `get_queue_entries(doctor_id=)` |
| **Call Next** | Only calls the next patient in THIS doctor's queue | `call_next_queue(doctor_id=)` |
| **Analytics** | Shows only the doctor's own stats (appointments, revenue, completion rate) | `get_doctor_own_stats(email)` |
| **Global Search** | Searches only patients/appointments linked to this doctor | `global_search(doctor_email=)` |
| **Patient Profile** | Verifies the patient has appointments with this doctor before returning data | `get_patient_full_profile(patient_id, doctor_email=)` |

### How the SQL Filtering Works (Example)
```sql
-- Normal query (Admin sees all patients):
SELECT * FROM patients ORDER BY patient_id

-- Doctor-filtered query (Doctor sees only their patients):
SELECT DISTINCT p.* FROM patients p
INNER JOIN appointments a ON p.patient_id = a.patient_id
INNER JOIN employees e ON a.doctor_id = e.employee_id
WHERE e.email = 'ana.reyes@carecrud.com'
```

### Defense-in-Depth
The isolation works at **two layers**:
1. **UI layer** — the page checks `if self._role == "Doctor"` and calls the filtered backend method
2. **Backend layer** — the method itself accepts a `doctor_email` or `doctor_id` parameter and alters the SQL query

This means even if someone bypasses the UI check, the backend still enforces the filter.

---

## 12. INPUT VALIDATION SYSTEM

### The Problem
Users may type invalid data into input fields — numbers in name fields, letters in phone fields, malformed emails, excessively long text, etc. This must be caught before it corrupts the database.

### Two-Layer Approach

**Layer 1: Real-Time Keystroke Blocking (QValidator)**
- Prevents invalid characters from being typed at all
- The cursor simply doesn't move when the user presses an invalid key
- Defined in `ui/validators.py`

| Validator | What It Allows | Applied To |
|-----------|---------------|------------|
| `NameValidator` | Letters, spaces, hyphens, dots, apostrophes only | Patient name, Employee name |
| `PhoneDigitsValidator` | Digits only (max 10) | Phone fields |
| `PriceValidator` | Digits and one decimal point | Service price field |

**Layer 2: Submit-Time Validation (in `accept()` method)**
- Runs when the user clicks "Save"
- Checks for empty required fields, format rules, and minimum lengths
- Shows a warning dialog and blocks save if validation fails

| Check | Rule | Where Used |
|-------|------|-----------|
| `validate_name()` | Min 2 characters, letters only, required | Patient dialog, Employee dialog |
| `validate_email()` | Must match `name@domain.ext` pattern | Patient dialog, Employee dialog, Login |
| `validate_phone_digits()` | Exactly 10 digits | Patient dialog, Employee dialog |
| `validate_price()` | Must be a valid positive number | Service dialog |
| `validate_required()` | Cannot be empty/whitespace | Service name, Discount type name |

**Layer 3: Max Length Enforcement**
All text fields have `setMaxLength()` to prevent excessively long input:

| Field | Max Length |
|-------|-----------|
| Names | 100 characters |
| Email | 150 characters |
| Emergency contact | 150 characters |
| Service name | 150 characters |
| Cancel/reschedule reasons | 300 characters |
| Other conditions | 300 characters |
| Invoice notes | 300 characters |
| Legal basis | 200 characters |
| Discount type name | 100 characters |
| Phone digits | 10 characters |
| Price | 12 characters |

### Example: What Happens When a User Tries to Type "123" in the Patient Name Field
1. User presses "1" → `NameValidator.validate()` returns `Invalid` → character is rejected
2. The text field doesn't change — the "1" never appears
3. User tries "Maria" → each letter passes validation → text appears normally
4. On Save, `validate_name("Maria")` confirms it's ≥ 2 chars and letters-only → passes

---

## 13. SYSTEM ANALYSIS

### What Makes Sense (and Why)

#### 1. Role System — Well-Designed
Each of the 5 roles (Admin, Doctor, Cashier, Receptionist, HR) has appropriate access. Admin controls everything, Doctor sees only their own data, Cashier handles billing, Receptionist handles front-desk intake, HR manages personnel. Roles are enforced at three levels: sidebar visibility, page-level button hiding, and SQL query filtering.

#### 2. Patient Workflow — Textbook Outpatient Flow
Registration → Appointment → Queue → Clinical Visit → Invoice → Payment. This mirrors how a real outpatient clinic operates. The automated steps (appointment sync to queue, auto-invoice on completion) reduce manual work.

#### 3. Appointment Conflict Detection — Prevents Double-Booking
Before saving an appointment, the system checks if the doctor already has a non-cancelled appointment at the same date and time. If a conflict exists, it warns the user but allows override (because real clinics sometimes intentionally double-book). Appointments are date-range limited to prevent scheduling too far in advance.

#### 4. Clinical Queue — Correct State Machine
The queue follows a logical flow: Waiting → In Progress → Completed/Cancelled. A doctor can only have one "In Progress" patient at a time (prevents serving two simultaneously). The "Call Next" button picks the earliest waiting patient (FIFO). Estimated wait time uses the average consultation duration from the last 30 days.

#### 5. Discount Enforcement — Security-Conscious
When an invoice is created, the system ignores any discount value from the UI and re-fetches the patient's discount from the database. This prevents cashiers from giving unauthorized discounts. The discount is based on Philippine laws (RA 9994 for Senior Citizens, RA 7277 for PWDs).

#### 6. Leave Request Auto-Cancellation — Real-World Awareness
When HR approves a leave request, all the doctor's appointments during the leave period are automatically cancelled with the reason "Employee on approved leave." This prevents patients from showing up when their doctor isn't available. The auto-expire mechanism restores the employee to "Active" after their leave ends.

#### 7. Activity Logging — Full Audit Trail
Every important action is logged with timestamp, user, role, action, and details. This is essential for accountability in healthcare and supports Philippine DOH record-keeping requirements.

#### 8. Patient Merge — Practical Deduplication
Receptionists and Admins can merge duplicate patient records. The "Remove" patient's data (appointments, invoices, queue, conditions) is transferred to the "Keep" patient, then the duplicate is deleted. This handles real-world data entry mistakes.

#### 9. Billing System — Multi-Line Items with Partial Payments
Invoices support multiple service line items, quantity, per-item discounts, and partial payments. Status tracks correctly: Unpaid → Partial → Paid. Void preserves the record for audit trail rather than deleting it.

### What Could Be Improved (and Why)

#### 1. Plaintext Passwords — Security Risk
Passwords are stored as plain strings in the database. If the database were compromised, all passwords would be readable. **Industry standard**: use bcrypt or argon2 to hash passwords.

#### 2. No Time-Slot Duration for Appointments
The conflict check only matches exact time — if two appointments are at 10:00 and 10:05, no conflict is detected. Real clinics need duration-based slots (e.g., 30-minute blocks).

#### 3. No Walk-In Patient Shortcut
Currently, a patient **must** have an appointment to enter the queue (the queue syncs from confirmed appointments). A walk-in patient who arrives without an appointment has no streamlined entry path. A "Walk-In" button that creates an appointment + queue entry in one step would improve workflow.

#### 4. No Leave Balance Tracking
Employees can request unlimited leave — there's no concept of leave entitlement (e.g., 15 vacation days, 10 sick days per year). HR has no way to enforce leave quotas.

#### 5. Minimum Password Length Is Only 4 Characters
Healthcare systems handling patient data should enforce stronger password policies (8+ characters with complexity requirements).

#### 6. Cashier Sees Full Patient Medical Records
Cashiers have access to the Patients page with full details including blood type, medical conditions, and emergency contacts. For privacy, cashiers should only see billing-relevant information (name, ID, discount status).

---

## 14. COMMON DEFENSE QUESTIONS & ANSWERS

### Architecture & Design

**Q: Why did you use a desktop application instead of a web application?**
> A: We used PyQt6 for a desktop app because clinics typically run on local machines with local databases. A desktop app provides faster performance, works offline, and doesn't require internet. PyQt6 also gives us native-looking UI elements and full control over the interface.

**Q: Why MySQL?**
> A: MySQL is a relational database that supports foreign keys, transactions, and complex JOINs — all essential for a system with interconnected data (patients → appointments → invoices). It ensures data integrity through referential constraints.

**Q: What design pattern does your backend use?**
> A: We use the **Mixin pattern**. Each feature area (patients, appointments, billing, etc.) is a separate Python class. These are combined into one backend class through multiple inheritance. This keeps the code organized — each file handles one responsibility — while sharing the same database connection.

**Q: How does your role-based access control work?**
> A: Access control happens at three levels: (1) **Sidebar** — only shows pages the role is allowed to see, (2) **Page** — buttons and columns are hidden/shown based on `self._role`, (3) **Data** — SQL queries filter results (e.g., doctors only see their own patients via JOINs with their employee_id).

---

### Database

**Q: How many tables does your database have and what are they for?**
> A: 16 tables total. 6 lookup tables (departments, roles, services, payment_methods, standard_conditions, discount_types), 5 main tables (users, user_preferences, employees, patients, patient_conditions), and 5 transaction tables (appointments, queue_entries, invoices, invoice_items, activity_log), plus leave_requests and notifications.

**Q: What are foreign keys and why do you use them?**
> A: Foreign keys are columns that reference another table's primary key. For example, `appointments.patient_id` references `patients.patient_id`. This ensures you can't create an appointment for a patient that doesn't exist. It maintains data integrity.

**Q: How do you handle deleting a patient that has appointments and invoices?**
> A: We use cascading deletes — we delete related records in order: invoice_items → invoices → queue_entries → appointments → patient_conditions → patients. All within one transaction so if any step fails, everything rolls back.

**Q: What indexes do you have and why?**
> A: We have indexes on frequently filtered columns: appointment_date, doctor_id, patient_id, status fields. Indexes speed up SELECT queries by creating a lookup structure, like a book's index. Without them, MySQL would scan every row.

---

### Features

**Q: How does the appointment conflict detection work?**
> A: Before saving an appointment, we query: "Does this doctor already have a non-cancelled appointment at this date and time?" If yes, we warn the user. They can still force-save (for legitimate double-bookings), but they must acknowledge the conflict.

**Q: How does the patient queue work?**
> A: Each morning, confirmed appointments are synced to the queue. The doctor clicks "Call Next" → the first waiting patient becomes "In Progress". After the consultation, the doctor marks it "Complete" → the system auto-creates an unpaid invoice for the cashier. Queue is single-day only — it resets daily.

**Q: How are discounts calculated?**
> A: Each patient can have a discount type (e.g., Senior Citizen 20%). When an invoice is created, the system reads the discount **from the database** — not from the UI. This prevents unauthorized discounts. The discount is applied: `total = subtotal × (1 - discount_percent/100)`.

**Q: How does the leave request system work?**
> A: An employee requests leave from the Dashboard. HR sees it in the Leave Management tab and can Approve or Decline. If approved: the employee's status changes to "On Leave", all their appointments during the leave period are auto-cancelled, and a notification is sent. After the leave end date, an auto-expire check restores the employee to "Active" status.

**Q: What is the activity log?**
> A: Every important action (login, create, edit, delete, void, merge, etc.) is recorded with a timestamp, user, role, and description. This creates an audit trail — you can see who did what and when. HR can only see login activity, while Admin sees everything.

---

### Technical

**Q: How does the search functionality work?**
> A: The global search uses SQL LIKE queries with wildcards: `WHERE name LIKE '%query%'`. This searches for the text anywhere in the name, phone, or email. It searches patients, appointments, and employees simultaneously, limited to 10 results each to keep it fast.

**Q: How do you prevent data inconsistency?**
> A: Three mechanisms: (1) **Foreign keys** prevent orphaned records, (2) **Transactions** (exec_many) ensure multiple related queries all succeed or all fail, (3) **Cascading deletes** remove all related data when a parent record is deleted.

**Q: How do you handle the phone number format?**
> A: Philippine format (+63 followed by 10 digits). The UI shows a styled frame with "+63" as a fixed prefix label, and the user only types the 10 digits. On save, "+63" is prepended. On edit, "+63" is stripped for display. Validation uses regex: `^\d{10}$`.

**Q: What happens when the system first connects to the database?**
> A: The `DatabaseBase.__init__()` runs `_ensure_schema()` which checks if required tables and columns exist. If any are missing (e.g., the discount_types table), it creates them. This is a basic auto-migration so the app works even on older database versions.

---

### If They Ask "Did You Use AI?"

Be honest. Here are helpful ways to frame it:
> "I used AI as a development tool to accelerate the coding process, similar to how developers use Stack Overflow, documentation, and code assistants in industry. I understand how each component works — let me walk you through [specific feature]."

Then demonstrate understanding by explaining the SQL, the data flow, or the role-based logic in detail. **The goal of this document is to give you that understanding.**

---

## QUICK REFERENCE: SQL QUERIES YOU SHOULD KNOW

```sql
-- Get all active patients with their conditions
SELECT p.*, GROUP_CONCAT(pc.condition_name) AS conditions
FROM patients p
LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
WHERE p.status = 'Active'
GROUP BY p.patient_id

-- Get today's appointments with patient and doctor names
SELECT a.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
       CONCAT(e.first_name,' ',e.last_name) AS doctor_name,
       s.service_name
FROM appointments a
JOIN patients p ON a.patient_id = p.patient_id
JOIN employees e ON a.doctor_id = e.employee_id
JOIN services s ON a.service_id = s.service_id
WHERE a.appointment_date = CURDATE()

-- Get invoice with line items
SELECT i.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
       GROUP_CONCAT(s.service_name) AS services
FROM invoices i
JOIN patients p ON i.patient_id = p.patient_id
JOIN invoice_items ii ON i.invoice_id = ii.invoice_id
JOIN services s ON ii.service_id = s.service_id
GROUP BY i.invoice_id

-- Check appointment conflict
SELECT COUNT(*) FROM appointments
WHERE doctor_id = 1 AND appointment_date = '2026-03-09' 
AND appointment_time = '09:00:00' AND status != 'Cancelled'

-- Monthly revenue for last 6 months
SELECT DATE_FORMAT(created_at, '%Y-%m') AS month,
       SUM(amount_paid) AS total_revenue
FROM invoices
WHERE status IN ('Paid', 'Partial')
AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
GROUP BY month ORDER BY month

-- Dashboard: today's revenue
SELECT COALESCE(SUM(amount_paid), 0) 
FROM invoices 
WHERE DATE(created_at) = CURDATE() AND status IN ('Paid', 'Partial')
```

---

*Study this document, trace through the code yourself, and practice explaining each feature out loud. Good luck on your defense!*
