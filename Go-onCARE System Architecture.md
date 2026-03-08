# Go-onCARE System Architecture

## 1. Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python |
| **GUI Framework** | PyQt6 (Fusion style, light palette) |
| **Database** | MySQL / MariaDB 10.4+ (via XAMPP) |
| **DB Connector** | mysql-connector-python |
| **Dependencies** | PyQt6, mysql-connector-python |

---

## 2. Entry Point — main.py

The `App` class is the application controller:

1. Creates a `QApplication` with Fusion style and a light color palette.
2. Instantiates `AuthBackend` — the single backend object for all DB operations.
3. Shows `AuthWindow` (login screen).
4. On successful login (`login_success` signal emitting `email, role, full_name`), hides auth window and creates `MainWindow` with the user's credentials.
5. On logout (`logout_requested` signal), destroys `MainWindow` and recreates `AuthWindow`.
6. A global `sys.excepthook` catches all unhandled exceptions and shows them in a `QMessageBox`.

---

## 3. Database Schema — database/carecrud.sql

### 3.1 Lookup Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| **departments** | `department_id` PK, `department_name` UNIQUE | Hospital departments (General Medicine, Cardiology, Dentistry, Pediatrics, Laboratory, Front Desk, Management, Pharmacy, Human Resources) |
| **roles** | `role_id` PK, `role_name` UNIQUE | System roles (Doctor, Cashier, Receptionist, Admin, HR) |
| **services** | `service_id` PK, `service_name` UNIQUE, `price`, `category`, `is_active` | Hospital services with pricing and category |
| **payment_methods** | `method_id` PK, `method_name` UNIQUE | Payment options (Cash, Credit Card, GCash, Maya, Insurance) |
| **standard_conditions** | `condition_id` PK, `condition_name` UNIQUE | Medical conditions vocabulary (Hypertension, Diabetes, Asthma, etc.) |
| **discount_types** | `discount_id` PK, `type_name` UNIQUE, `discount_percent`, `legal_basis`, `is_active` | Discount categories (Senior Citizen 20%, PWD 20%, Pregnant 0%) based on Philippine law (RA 9994, RA 10754) |

### 3.2 Main Tables

| Table | Key Columns | Foreign Keys | Purpose |
|-------|------------|--------------|---------|
| **users** | `user_id` PK, `email` UNIQUE, `password`, `full_name`, `role_id`, `must_change_password` | → `roles(role_id)` | Login accounts |
| **user_preferences** | `pref_id` PK, `user_email` UNIQUE, `dark_mode` | → `users(email)` CASCADE | Per-user settings |
| **employees** | `employee_id` PK, `first_name`, `last_name`, `role_id`, `department_id`, `employment_type`, `phone`, `email` UNIQUE, `hire_date`, `status`, `leave_from`, `leave_until`, `salary`, `emergency_contact` | → `roles(role_id)`, → `departments(department_id)` | Staff records |
| **patients** | `patient_id` PK, `first_name`, `last_name`, `sex`, `date_of_birth`, `phone`, `email`, `emergency_contact`, `blood_type`, `discount_type_id`, `status`, `notes` | → `discount_types(discount_id)` ON DELETE SET NULL | Patient records |
| **patient_conditions** | `condition_id` PK, `patient_id`, `condition_name` | → `patients(patient_id)` CASCADE | Patient–condition mapping |

### 3.3 Transaction Tables

| Table | Key Columns | Foreign Keys | Purpose |
|-------|------------|--------------|---------|
| **appointments** | `appointment_id` PK, `patient_id`, `doctor_id`, `service_id`, `appointment_date`, `appointment_time`, `status`, `cancellation_reason`, `reschedule_reason` | → `patients`, → `employees`, → `services` | Appointment scheduling |
| **queue_entries** | `queue_id` PK, `patient_id`, `doctor_id`, `appointment_id`, `queue_time`, `purpose`, `status` | → `patients`, → `employees`, → `appointments` | Daily clinical queue |
| **invoices** | `invoice_id` PK, `patient_id`, `appointment_id`, `method_id`, `discount_percent`, `total_amount`, `amount_paid`, `status` | → `patients`, → `appointments`, → `payment_methods` | Billing records |
| **invoice_items** | `item_id` PK, `invoice_id`, `service_id`, `quantity`, `unit_price`, `subtotal` | → `invoices` CASCADE, → `services` | Line items per invoice |
| **activity_log** | `log_id` PK, `user_email`, `user_role`, `action`, `record_type`, `record_detail`, `created_at` | — | Full audit trail |
| **leave_requests** | `request_id` PK, `employee_id`, `leave_from`, `leave_until`, `reason`, `status`, `hr_note`, `hr_decided_by` | → `employees(employee_id)` | Leave request workflow |
| **notifications** | `notification_id` PK, `employee_id`, `message`, `is_read`, `created_at` | → `employees(employee_id)` | In-app notifications |

### 3.4 Indexes

| Index | Table | Column(s) |
|-------|-------|-----------|
| `idx_appointments_date` | appointments | appointment_date |
| `idx_appointments_doctor` | appointments | doctor_id |
| `idx_appointments_patient` | appointments | patient_id |
| `idx_appointments_status` | appointments | status |
| `idx_invoices_patient` | invoices | patient_id |
| `idx_invoices_status` | invoices | status |
| `idx_invoices_appointment` | invoices | appointment_id |
| `idx_queue_date` | queue_entries | created_at |
| `idx_queue_appointment` (UNIQUE) | queue_entries | (appointment_id, created_at) |
| `idx_patients_status` | patients | status |
| `idx_employees_role` | employees | role_id |
| `idx_employees_dept` | employees | department_id |
| `idx_employees_status` | employees | status |
| `idx_activity_log_date` | activity_log | created_at |
| `idx_activity_log_user` | activity_log | user_email |
| `idx_leave_requests_employee` | leave_requests | employee_id |
| `idx_leave_requests_status` | leave_requests | status |
| `idx_notifications_employee` | notifications | employee_id |
| `idx_notifications_read` | notifications | is_read |

### 3.5 Views

| View | Joins | Purpose |
|------|-------|---------|
| **vw_employees** | employees ↔ roles ↔ departments | Employees with role_name + department_name |
| **vw_patients** | patients LEFT JOIN patient_conditions (GROUP_CONCAT) | Patients with conditions as comma-separated string + computed age |
| **vw_appointments** | appointments ↔ patients ↔ employees ↔ services | Full appointment details with formatted time |
| **vw_queue** | queue_entries ↔ patients ↔ employees | Queue with patient/doctor names |
| **vw_invoices** | invoices ↔ patients ↔ payment_methods ↔ invoice_items ↔ services | Full invoice detail with line items |
| **vw_doctor_performance** | employees ↔ roles ↔ appointments ↔ services | Aggregated stats per doctor |
| **vw_monthly_revenue** | appointments ↔ services (Completed only) | Revenue by month |
| **vw_today_appointments** | appointments ↔ patients ↔ employees ↔ services | Today's schedule |
| **vw_top_services** | services LEFT JOIN appointments | Service usage frequency + revenue |

---

## 4. Backend Architecture — backend/

### 4.1 Inheritance Chain

```
DatabaseBase                    ← base.py (DB connection, query helpers, activity log)
    ├── AuthMixin               ← auth.py
    ├── EmployeeMixin           ← employees.py
    ├── PatientMixin            ← patients.py
    ├── AppointmentMixin        ← appointments.py
    ├── ClinicalMixin           ← clinical.py
    ├── DashboardMixin          ← dashboard.py
    ├── AnalyticsMixin          ← analytics.py
    ├── SettingsMixin           ← settings.py
    └── SearchMixin             ← search.py
            │
            ▼
        AuthBackend             ← __init__.py (diamond mixin merge)
```

A single `AuthBackend()` instance is created in `App.__init__()` and passed to every UI page.

### 4.2 DatabaseBase (backend/base.py)

- **DB_CONFIG**: localhost, root, no password, database `carecrud_db`, `use_pure=True`
- **Connection management**: lazy `_get_connection()`, auto-reconnects if disconnected
- **Auto-migration** (`_ensure_schema`): On init, creates `discount_types` table and adds `discount_type_id` column to patients if missing
- **Query helpers**:
  - `fetch(sql, params, one)` — SELECT returning list of dicts or single dict
  - `exec(sql, params)` — INSERT/UPDATE/DELETE with auto-commit; returns lastrowid or rowcount
  - `exec_many(queries)` — multiple writes in one transaction with rollback on failure
- **Common lookups**: `_get_employee_name()`, `_lookup_patient_id()`, `_lookup_role_id()`
- **Activity logging**: `log_activity(action, record_type, detail)` writes to `activity_log`

### 4.3 AuthMixin (backend/auth.py)

| Method | Purpose |
|--------|---------|
| `login(email, password)` | Authenticate; returns (success, role, full_name, message, must_change_password) |
| `clear_must_change_password(email)` | Reset forced-change flag |
| `update_own_password(email, current_pw, new_pw)` | User self-service password change |
| `force_change_password(email, new_pw)` | Set new password + clear flag (first login) |
| `get_user_full_name(email)` | Lookup display name |
| `get_all_roles()` | List role name strings |
| `get_all_user_accounts()` | List all users (Admin) |
| `admin_create_user_account(...)` | Create user with must_change_password=1 |
| `admin_reset_password(user_id, new_pw)` | Reset + force change on next login |
| `admin_delete_user_account(user_id)` | Delete user account |

### 4.4 EmployeeMixin (backend/employees.py)

| Category | Methods |
|----------|---------|
| **CRUD** | `get_employees()`, `get_employees_detailed()`, `add_employee()`, `update_employee()`, `delete_employee()` |
| **HR Data** | `get_leave_employees()`, `get_hr_stats()`, `get_payroll_summary()`, `get_employment_type_counts()` |
| **Performance** | `get_employee_performance()`, `get_employee_appointments()`, `get_employee_stats()`, `get_department_counts()` |
| **Leave Requests** | `submit_leave_request()`, `get_pending_leave_requests()`, `get_all_leave_requests()`, `get_my_leave_requests()`, `approve_leave_request()`, `decline_leave_request()`, `auto_expire_leaves()` |
| **Notifications** | `get_unread_notifications()`, `mark_notifications_read()` |
| **Helpers** | `_split_name()`, `_lookup_dept_id()`, `check_duplicate_phone()`, `get_employee_id_by_email()` |

### 4.5 PatientMixin (backend/patients.py)

| Method | Purpose |
|--------|---------|
| `get_patients()` | Full patient list with conditions, discount type, age |
| `get_patient_full_profile(patient_id)` | Complete profile with appointment history, invoices, conditions |
| `add_patient(data)` | Create patient + save conditions + assign discount type |
| `update_patient(patient_id, data)` | Update patient + conditions + discount type |
| `delete_patient(patient_id)` | Cascade delete all related records |
| `merge_patients(keep_id, remove_id)` | Merge two patient records |
| `get_patients_for_doctor(email)` | Patients with appointments for a specific doctor |
| `get_active_patients()` | Active patients for dropdowns |

### 4.6 AppointmentMixin (backend/appointments.py)

| Method | Purpose |
|--------|---------|
| `get_appointments(doctor_email)` | All/filtered appointments with details |
| `get_appointments_for_doctor(email)` | Doctor-scoped appointment view |
| `get_doctors()` | Active doctors for dropdowns |
| `get_services_list(active_only)` | Services for scheduling |
| `check_appointment_conflict(...)` | Conflict detection within ±29 min window |
| `_validate_appointment_date(date_str)` | No past dates, no Sundays, max 6 months out |
| `add_appointment(data)` | Create with validation + optional auto-queue for today |
| `update_appointment(id, data)` | Update with conflict re-check |

### 4.7 ClinicalMixin (backend/clinical.py)

| Category | Methods |
|----------|---------|
| **Queue Ops** | `get_queue_entries()`, `get_queue_stats()`, `update_queue_entry()`, `sync_today_appointments_to_queue()`, `call_next_queue(doctor_id)` |
| **Queue ↔ Appointment Sync** | `complete_appointment_from_queue()`, `cancel_appointment_from_queue()` |
| **Invoice Generation** | `create_invoice_from_queue(queue_id)` — auto-creates invoice with patient discount |
| **Invoice Ops** | `get_invoices()`, `add_invoice(data)`, `add_payment(invoice_id, amount, method_id)`, `void_invoice()`, `get_invoice_detail()` |
| **Billing Helpers** | `get_today_completed_appointments_for_patient()`, `get_payment_methods()`, `get_avg_consultation_minutes()` |
| **Service Mgmt** | `add_service()`, `update_service_full()`, `bulk_update_prices()`, `get_service_usage_counts()`, `get_service_categories()` |

### 4.8 DashboardMixin (backend/dashboard.py)

| Method | Returns |
|--------|---------|
| `get_dashboard_summary()` | active_patients, new_patients_week, today_appts, today_revenue, total_revenue, active_staff |
| `get_upcoming_appointments(limit)` | Next N confirmed/pending appointments |
| `get_patient_stats_monthly(months)` | Visit counts per month (filled to include current month) |

### 4.9 AnalyticsMixin (backend/analytics.py)

| Method | Purpose |
|--------|---------|
| `_fill_months()` | Static helper — ensures continuous month series, fills gaps with zeros |
| `get_monthly_revenue(months)` | Revenue by month from paid/partial invoices |
| `get_doctor_performance()` | All doctors' appointment counts + revenue |
| `get_doctor_own_stats(email)` | Individual doctor stats + monthly breakdown |
| `get_top_services()` | Service usage ranking |
| `get_appointment_status_counts()` | Distribution by status |
| `get_patient_condition_counts()` | Most common conditions |
| `get_patient_demographics()` | Age group distribution (0–17, 18–35, 36–50, 51–65, 65+) |
| `get_revenue_by_department()` | Revenue by department |
| `get_active_doctor_count()` | Active doctor headcount |
| `get_monthly_appointment_stats(months)` | Monthly visits/completed/cancelled |
| `get_patient_retention(months)` | New vs. returning patients per month |
| `get_cancellation_rate_trend(months)` | Cancellation rate over time |
| `get_summary_stats(from, to)` | Period KPIs (revenue, appointments, patients, avg/day) |
| `get_period_comparison()` | Current vs. previous month deltas (%) |

### 4.10 SettingsMixin (backend/settings.py)

| Category | Methods |
|----------|---------|
| **DB Overview** | `get_table_counts()` — row counts for 15 tables |
| **Cleanup** | `cleanup_completed_appointments(before_date)`, `cleanup_cancelled_appointments()`, `cleanup_inactive_patients()`, `truncate_table(table_name)` (whitelist enforced) |
| **Standard Conditions** | `get_standard_conditions()`, `add_standard_condition()`, `delete_standard_condition()` |
| **Discount Types** | `get_discount_types()`, `add_discount_type()`, `update_discount_type()`, `delete_discount_type()`, `get_patient_discount_percent()` |

### 4.11 SearchMixin (backend/search.py)

| Method | Purpose |
|--------|---------|
| `global_search(query, include_employees)` | LIKE search across patients, appointments, and optionally employees |

---

## 5. UI Architecture — ui/

### 5.1 Window Hierarchy

```
App
 ├── AuthWindow (login)
 │    └── _ForcePasswordChangeDialog (modal)
 └── MainWindow (post-login)
      ├── Sidebar (nav buttons, user card, logout)
      ├── Top Bar (page title, global search bar)
      └── QStackedWidget (8 pages)
           ├── [0] DashboardPage
           ├── [1] PatientsPage
           ├── [2] AppointmentsPage
           ├── [3] ClinicalPage (Clinical & POS)
           ├── [4] AnalyticsPage (Data Analytics)
           ├── [5] EmployeesPage / HREmployeesPage
           ├── [6] ActivityLogPage
           └── [7] SettingsPage
```

### 5.2 Role Access Map

| Page | Admin | Doctor | HR | Cashier | Receptionist |
|------|:-----:|:------:|:--:|:-------:|:------------:|
| Dashboard | ✓ | ✓ | ✓ | ✓ | ✓ |
| Patients | ✓ | ✓ | — | ✓ | ✓ |
| Appointments | ✓ | ✓ | — | ✓ | ✓ |
| Clinical & POS | ✓ | ✓ | — | ✓ | ✓ |
| Data Analytics | ✓ | ✓ | — | — | — |
| Employees | ✓ | — | ✓ | — | — |
| Activity Log | ✓ | — | ✓ | — | — |
| Settings | ✓ | ✓ | ✓ | ✓ | ✓ |

**Employee page variant**: Admin and HR see `HREmployeesPage` (with salary, leave management, payroll summary). Other roles see basic `EmployeesPage`.

**Settings variant**: Non-Admin roles see only the Profile/Password Change section. Admin sees full DB cleanup, condition management, discount type management, and user account management.

### 5.3 Page Details

| Page | File | Key Features |
|------|------|-------------|
| **DashboardPage** | ui/shared/dashboard_page.py | KPI cards (patients, appointments, revenue, staff), upcoming appointments table, role-specific quick-action shortcuts |
| **PatientsPage** | ui/shared/patients_page.py | Patient CRUD, search/filter, full profile view, patient merge. Doctor role: view-only (no delete) |
| **AppointmentsPage** | ui/shared/appointments_page.py | Calendar date-tab view, scheduling, conflict detection, status management (Confirm/Cancel with reason), doctor-scoped filtering |
| **ClinicalPage** | ui/shared/clinical_page.py | 3-tab layout: Queue Management, Invoices/Billing, Services. Queue sync from today's appointments, call next, auto-invoice on completion, receipt generation |
| **AnalyticsPage** | ui/shared/analytics_page.py | Revenue charts, doctor performance, service usage, demographics, retention, cancellation trends, period comparison, individual doctor stats |
| **EmployeesPage** | ui/shared/employees_page.py | Basic staff directory and employee management |
| **HREmployeesPage** | ui/shared/hr_employees_page.py | Full HR suite: salary data, leave request approval/decline with notes, payroll summary, employment type breakdown |
| **ActivityLogPage** | ui/shared/activity_log_page.py | Audit trail viewer with filters (user, action, type, date range, role) |
| **SettingsPage** | ui/shared/settings_page.py | Profile/password change (all roles), DB table counts, cleanup tools, standard conditions CRUD, discount types CRUD, user account management (Admin only) |

### 5.4 Dialog Files

| File | Purpose |
|------|---------|
| ui/shared/patient_dialogs.py | Add/Edit patient dialogs |
| ui/shared/appointment_dialog.py | Add/Edit appointment dialog |
| ui/shared/clinical_dialogs.py | Invoice creation, payment, queue management dialogs |
| ui/shared/employee_dialogs.py | Add/Edit employee dialogs |
| ui/shared/hr_employee_dialogs.py | HR-specific employee dialogs with salary/leave fields |
| ui/shared/chart_widgets.py | Custom QPainter-based chart widgets for analytics |

### 5.5 Styling

| File | Purpose |
|------|---------|
| ui/styles.py | Python string constants `MAIN_STYLE`, `AUTH_STYLE`, `set_active_palette()` |
| ui/styles/auth.qss | QSS stylesheet for the login window |
| ui/styles/main.qss | QSS stylesheet for the main application window |

---

## 6. Authentication Flow

```
1.  AuthWindow displayed
2.  User enters email + password
3.  AuthMixin.login() called:
     a. Validates inputs
     b. Queries users table joined with roles
     c. Compares password
     d. Sets current user context via set_current_user()
     e. Logs "Login" activity
     f. Returns (success, role, full_name, message, must_change_password)
4.  If must_change_password == True:
     → _ForcePasswordChangeDialog shown (modal)
     → User must set new password
     → If cancelled → login aborted
5.  login_success signal emitted → App._on_login()
6.  MainWindow created with (email, role, full_name)
7.  Sidebar nav buttons filtered by _ROLE_ACCESS[role]
```

Admin-created accounts always set `must_change_password=1`, forcing a password change on first login.

---

## 7. Clinical Workflow — Patient Flow

```
                    ┌──────────────┐
                    │ Appointment  │  Created by Receptionist/Admin/Cashier
                    │  (Confirmed) │  via Appointments page
                    └──────┬───────┘
                           │
          sync_today_appointments_to_queue()
          (auto on ClinicalPage load or manual refresh)
                           │
                    ┌──────▼───────┐
                    │ Queue Entry  │  Status: "Waiting"
                    │  (Today)     │  Linked to appointment_id
                    └──────┬───────┘
                           │
              call_next_queue(doctor_id)
              (doctor clicks "Call Next")
                           │
                    ┌──────▼───────┐
                    │ Queue Entry  │  Status: "In Progress"
                    │  (Consult)   │
                    └──────┬───────┘
                           │
              Queue marked "Completed"
              → create_invoice_from_queue(queue_id)
                           │
              ┌────────────▼──────────────┐
              │  Invoice (Unpaid)          │
              │  • Applies patient discount│
              │  • Creates invoice_items   │
              │  • Marks appointment       │
              │    "Completed"             │
              └────────────┬──────────────┘
                           │
              add_payment(invoice_id, amount, method_id)
              (Cashier collects payment)
                           │
              ┌────────────▼──────────────┐
              │  Invoice (Paid/Partial)   │
              │  • Tracks partial payments │
              │  • Payment method recorded │
              │  • Receipt generated       │
              └───────────────────────────┘
```

**Queue sync**: `sync_today_appointments_to_queue()` finds today's Confirmed appointments not yet in queue and inserts them as Waiting. A UNIQUE index on `(appointment_id, created_at)` prevents duplicates.

**Discount application**: Auto-created invoices check `patients.discount_type_id` → look up `discount_types.discount_percent` → apply to service price. Discounts are always DB-enforced.

**Queue cancellation**: Cancelling a queue entry also updates the linked appointment to Cancelled status via `cancel_appointment_from_queue()`.

---

## 8. Role Permissions Detail

### Admin
- **Full access** to all 8 pages
- User account management: create/delete accounts, reset passwords
- Full employee management with salary and leave data (HREmployeesPage)
- Settings: DB cleanup tools, truncate tables, manage standard conditions, manage discount types
- Activity log: full audit trail visibility
- Data analytics: all reports and charts

### Doctor
- **Dashboard, Patients, Appointments, Clinical & POS, Data Analytics, Settings**
- Patient list may be scoped to own patients
- Appointments filtered to own schedule
- Analytics includes personal stats (`get_doctor_own_stats`)
- Patients page: view-only (no delete capability)
- Can submit leave requests; receives notifications for decisions

### HR
- **Dashboard, Employees, Activity Log, Settings**
- Enhanced employee page with salary, payroll summary, employment type breakdown
- Leave request approval/decline with notes
- Approving leave auto-cancels conflicting appointments
- Cannot access patients, appointments, or clinical pages

### Cashier
- **Dashboard, Patients, Appointments, Clinical & POS, Settings**
- Primary billing role — processes payments on invoices
- Can create manual invoices
- Dashboard quick actions: Appointments, Clinical Queue (no New Patient or Analytics)
- No access to analytics, employees, or activity log

### Receptionist
- **Dashboard, Patients, Appointments, Clinical & POS, Settings**
- Primary scheduling role — creates/manages appointments
- Manages patient registration
- Dashboard quick actions: all except Analytics
- No access to analytics, employees, or activity log

---

## 9. Key Features

### 9.1 Leave Management System
- Employees submit leave requests with date range + reason
- HR/Admin approve or decline with notes
- On approval: employee status → "On Leave", `leave_from`/`leave_until` updated, notification sent, conflicting appointments auto-cancelled
- On decline: notification sent with HR's note
- `auto_expire_leaves()` runs every 5 minutes — when leave period ends, status reverts to "Active"
- Non-HR employees get popup notifications every 15 seconds for leave decision updates

### 9.2 Discount System (Philippine Law Compliance)
- Pre-configured: Senior Citizen (20%, RA 9994), PWD (20%, RA 10754), Pregnant (configurable)
- Admin can CRUD discount types in Settings
- Each patient assigned a `discount_type_id`
- Discounts enforced from DB — `add_invoice()` re-reads from `discount_types`, ignoring UI-supplied values
- Auto-applied during queue-to-invoice generation

### 9.3 Analytics & Reporting
- Monthly revenue trends (from invoices)
- Doctor performance rankings (appointments, completions, revenue)
- Individual doctor stats with monthly breakdown
- Top services by usage
- Appointment status distribution
- Patient demographics (age groups: 0–17, 18–35, 36–50, 51–65, 65+)
- Patient condition frequency
- Revenue by department
- Patient retention (new vs. returning)
- Cancellation rate trend
- Period-over-period comparison (current vs. previous month with delta %)
- Summary KPIs with optional date range filter
- All monthly data uses start-of-month boundaries and fills missing months with zeros

### 9.4 Global Search
- Available in the top bar of MainWindow
- Searches patients (by name, phone, email), appointments (by patient name), and employees (name, email — Admin/HR only)
- Results shown in a modal dialog with categorized tables
- Minimum 2-character query required

### 9.5 Activity Audit Log
- Every significant action logged: Login, Created, Edited, Deleted, Voided
- Fields: user_email, user_role, action, record_type, record_detail, timestamp
- Filterable by user, action type, record type, date range, roles
- Accessible to Admin and HR only

### 9.6 Data Cleanup Tools (Settings — Admin only)
- Cleanup completed appointments before a given date (cascades to invoices, invoice items, queue)
- Cleanup all cancelled appointments
- Cleanup inactive patients (cascades all related records)
- Truncate specific tables (whitelist: queue_entries, invoice_items, invoices, appointments, patient_conditions, activity_log)
- Table row counts dashboard showing all 15 tables

### 9.7 Patient Management
- Full CRUD with blood type, sex, DOB (age auto-computed), emergency contact
- Multiple medical conditions per patient (from `standard_conditions` vocabulary)
- Discount type assignment
- Active/Inactive status management
- Patient merge capability (consolidates two records into one)
- Full profile view with appointment history and invoice history

### 9.8 Appointment Scheduling
- Doctor assignment from active doctor list
- Service selection with pricing
- Time conflict detection (±29 minute window per doctor)
- Date validation: no past dates, no Sundays, max 6 months ahead
- Status workflow: Pending → Confirmed → Completed/Cancelled
- Cancellation reason and reschedule reason tracking
- Auto-insert to today's queue when a Confirmed appointment is created for today
- Average consultation time computed from DB (last 30 days of completed queue entries)

### 9.9 Notification System
- Push-style notifications for non-HR/Admin employees
- Checked every 15 seconds via QTimer
- Used for leave request decisions (approved/declined)
- Tracked in `notifications` table with `is_read` status
- Displayed as QMessageBox popups

---

## 10. Architectural Diagram

```
┌─────────────────────────────────────────────────────┐
│                    main.py (App)                     │
│  QApplication ← Fusion style, light palette          │
│  Global exception hook                               │
├──────────────┬──────────────────────────────────────┤
│  AuthWindow  │          MainWindow                   │
│  (login)     │  ┌─────────┬─────────────────────┐   │
│              │  │ Sidebar  │  QStackedWidget      │   │
│              │  │ (nav)    │  8 pages             │   │
│              │  └─────────┴─────────────────────┘   │
├──────────────┴──────────────────────────────────────┤
│                  AuthBackend                         │
│  (Single instance, passed to all pages)              │
│  ┌────────────────────────────────────────────────┐ │
│  │ DatabaseBase  ← connection, fetch/exec/log     │ │
│  │ + AuthMixin   ← login, accounts                │ │
│  │ + EmployeeMixin ← staff, leave, notifications  │ │
│  │ + PatientMixin  ← patient CRUD, merge          │ │
│  │ + AppointmentMixin ← scheduling, conflicts     │ │
│  │ + ClinicalMixin ← queue, invoices, services    │ │
│  │ + DashboardMixin ← KPIs, upcoming              │ │
│  │ + AnalyticsMixin ← charts, trends, comparisons │ │
│  │ + SettingsMixin  ← cleanup, conditions, discnt  │ │
│  │ + SearchMixin   ← global search                │ │
│  └────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────┤
│              MySQL / MariaDB (carecrud_db)            │
│  6 lookup tables, 5 main tables, 6 transaction tbls  │
│  9 views, 19 indexes                                 │
└─────────────────────────────────────────────────────┘
```

---

## 11. File Structure

```
CareCRUDV1/
├── main.py                          Application entry point
├── requirements.txt                 Python dependencies
├── backend/
│   ├── __init__.py                  AuthBackend (mixin composition)
│   ├── base.py                      DatabaseBase (connection, helpers)
│   ├── auth.py                      AuthMixin (login, accounts)
│   ├── employees.py                 EmployeeMixin (staff, leave, notifications)
│   ├── patients.py                  PatientMixin (CRUD, merge, profiles)
│   ├── appointments.py              AppointmentMixin (scheduling, conflicts)
│   ├── clinical.py                  ClinicalMixin (queue, invoices, services)
│   ├── dashboard.py                 DashboardMixin (KPIs, summaries)
│   ├── analytics.py                 AnalyticsMixin (reports, charts, trends)
│   ├── settings.py                  SettingsMixin (cleanup, conditions, discounts)
│   └── search.py                    SearchMixin (global search)
├── database/
│   ├── carecrud.sql                 Full schema DDL
│   ├── sample_data.sql              Sample data for testing
│   └── drop_all_data.sql            Data wipe script
└── ui/
    ├── __init__.py
    ├── auth_window.py               Login + forced password change
    ├── main_window.py               Main window, sidebar, role routing
    ├── reports.py                    Report utilities
    ├── styles.py                    Style constants
    ├── styles/
    │   ├── auth.qss                 Login window stylesheet
    │   └── main.qss                 Main window stylesheet
    └── shared/
        ├── dashboard_page.py        Dashboard with KPIs and shortcuts
        ├── patients_page.py         Patient records management
        ├── appointments_page.py     Appointment scheduling
        ├── clinical_page.py         Clinical queue + billing + services
        ├── analytics_page.py        Data analytics and charts
        ├── employees_page.py        Basic employee directory
        ├── hr_employees_page.py     HR employee management
        ├── activity_log_page.py     Audit trail viewer
        ├── settings_page.py         System settings
        ├── patient_dialogs.py       Patient add/edit dialogs
        ├── appointment_dialog.py    Appointment add/edit dialog
        ├── clinical_dialogs.py      Billing and queue dialogs
        ├── employee_dialogs.py      Employee add/edit dialogs
        ├── hr_employee_dialogs.py   HR employee dialogs
        └── chart_widgets.py         Custom chart painting widgets
```
