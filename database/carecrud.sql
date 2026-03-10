
DROP DATABASE IF EXISTS carecrud_db;
CREATE DATABASE carecrud_db;
USE carecrud_db;


-- ────────────────────────────────────────────────────────────
-- LOOKUP TABLES
-- ────────────────────────────────────────────────────────────

-- Departments
CREATE TABLE departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

-- Roles
CREATE TABLE roles (
    role_id   INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Services offered by the hospital
CREATE TABLE services (
    service_id   INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    price        DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    category     VARCHAR(60) DEFAULT 'General',
    is_active    TINYINT(1) NOT NULL DEFAULT 1
);

-- Payment methods
CREATE TABLE payment_methods (
    method_id   INT AUTO_INCREMENT PRIMARY KEY,
    method_name VARCHAR(50) NOT NULL UNIQUE
);

-- Standard conditions list
CREATE TABLE standard_conditions (
    condition_id   INT AUTO_INCREMENT PRIMARY KEY,
    condition_name VARCHAR(100) NOT NULL UNIQUE
);

-- Discount types (PWD, Senior Citizen, etc.)
CREATE TABLE discount_types (
    discount_id      INT AUTO_INCREMENT PRIMARY KEY,
    type_name        VARCHAR(100) NOT NULL UNIQUE,
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    legal_basis      VARCHAR(255) DEFAULT '',
    is_active        TINYINT(1) NOT NULL DEFAULT 1
);


-- ────────────────────────────────────────────────────────────
-- MAIN TABLES
-- ────────────────────────────────────────────────────────────

-- User accounts
CREATE TABLE users (
    user_id              INT AUTO_INCREMENT PRIMARY KEY,
    email                VARCHAR(150) NOT NULL UNIQUE,
    password             VARCHAR(255) NOT NULL,
    full_name            VARCHAR(100) NOT NULL,
    role_id              INT          NOT NULL,
    must_change_password TINYINT(1)   NOT NULL DEFAULT 0,
    created_at           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- User preferences (dark mode etc)
CREATE TABLE user_preferences (
    pref_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(150) NOT NULL UNIQUE,
    dark_mode  TINYINT(1) NOT NULL DEFAULT 0,
    FOREIGN KEY (user_email) REFERENCES users(email)
        ON UPDATE CASCADE ON DELETE CASCADE
);

-- Employees
CREATE TABLE employees (
    employee_id     INT AUTO_INCREMENT PRIMARY KEY,
    first_name      VARCHAR(50)  NOT NULL,
    last_name       VARCHAR(50)  NOT NULL,
    role_id         INT          NOT NULL,
    department_id   INT          NOT NULL,
    employment_type ENUM('Full-time', 'Part-time', 'Contract') NOT NULL DEFAULT 'Full-time',
    phone           VARCHAR(20),
    email           VARCHAR(150) UNIQUE,
    hire_date       DATE         NOT NULL,
    status          ENUM('Active', 'On Leave', 'Inactive') NOT NULL DEFAULT 'Active',
    notes           TEXT,
    leave_from         DATE DEFAULT NULL,
    leave_until        DATE DEFAULT NULL,
    salary             DECIMAL(10, 2) DEFAULT NULL,
    emergency_contact  VARCHAR(200) DEFAULT '',

    FOREIGN KEY (role_id)       REFERENCES roles(role_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- Patients
CREATE TABLE patients (
    patient_id        INT AUTO_INCREMENT PRIMARY KEY,
    first_name        VARCHAR(50)  NOT NULL,
    last_name         VARCHAR(50)  NOT NULL,
    sex               ENUM('Male', 'Female') NOT NULL,
    date_of_birth     DATE,
    phone             VARCHAR(20),
    email             VARCHAR(150),
    address           VARCHAR(300) DEFAULT '',
    civil_status      ENUM('Single', 'Married', 'Widowed', 'Separated') DEFAULT 'Single',
    emergency_contact VARCHAR(200) DEFAULT '',
    blood_type        ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-','Unknown') DEFAULT 'Unknown',
    discount_type_id  INT DEFAULT NULL,
    status            ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
    notes             TEXT,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (discount_type_id) REFERENCES discount_types(discount_id)
        ON DELETE SET NULL
);

-- Patient conditions (separate table so one patient can have multiple)
CREATE TABLE patient_conditions (
    condition_id   INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT          NOT NULL,
    condition_name VARCHAR(100) NOT NULL,

    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ON DELETE CASCADE
);


-- ────────────────────────────────────────────────────────────
-- TRANSACTION TABLES
-- ────────────────────────────────────────────────────────────

-- Appointments
CREATE TABLE appointments (
    appointment_id     INT AUTO_INCREMENT PRIMARY KEY,
    patient_id         INT  NOT NULL,
    doctor_id          INT  NOT NULL,
    service_id         INT  NOT NULL,
    appointment_date   DATE NOT NULL,
    appointment_time   TIME NOT NULL,
    status             ENUM('Pending', 'Confirmed', 'Cancelled', 'Completed') NOT NULL DEFAULT 'Pending',
    notes              TEXT,
    cancellation_reason TEXT,
    reschedule_reason  TEXT,
    reminder_sent      TINYINT(1) NOT NULL DEFAULT 0,
    recurring_parent_id INT DEFAULT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES employees(employee_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- Doctor availability schedules
CREATE TABLE doctor_schedules (
    schedule_id  INT AUTO_INCREMENT PRIMARY KEY,
    doctor_id    INT NOT NULL,
    day_of_week  ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    FOREIGN KEY (doctor_id) REFERENCES employees(employee_id) ON DELETE CASCADE,
    UNIQUE KEY uq_doctor_day (doctor_id, day_of_week)
);

-- Patient queue (for clinical workflow)
CREATE TABLE queue_entries (
    queue_id        INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT  NOT NULL,
    doctor_id       INT  NOT NULL,
    appointment_id  INT,
    queue_time      TIME NOT NULL,
    purpose         VARCHAR(100),
    blood_pressure  VARCHAR(20)  DEFAULT NULL,
    height_cm       DECIMAL(5,1) DEFAULT NULL,
    weight_kg       DECIMAL(5,1) DEFAULT NULL,
    temperature     DECIMAL(4,1) DEFAULT NULL,
    nurse_notes     TEXT DEFAULT NULL,
    status          ENUM('Waiting', 'Triaged', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Waiting',
    created_at      DATE NOT NULL DEFAULT (CURRENT_DATE),
    updated_at      DATETIME DEFAULT NULL,

    FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)      REFERENCES employees(employee_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- Invoices
CREATE TABLE invoices (
    invoice_id       INT AUTO_INCREMENT PRIMARY KEY,
    patient_id       INT  NOT NULL,
    appointment_id   INT,
    method_id        INT,
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    total_amount     DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount_paid      DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status           ENUM('Paid', 'Unpaid', 'Partial', 'Voided') NOT NULL DEFAULT 'Unpaid',
    notes            TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
    FOREIGN KEY (method_id)      REFERENCES payment_methods(method_id)
);

-- Invoice line items (each service on an invoice gets its own row)
CREATE TABLE invoice_items (
    item_id    INT AUTO_INCREMENT PRIMARY KEY,
    invoice_id INT NOT NULL,
    service_id INT NOT NULL,
    quantity   INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal   DECIMAL(10, 2) NOT NULL,

    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
        ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- Activity log
CREATE TABLE activity_log (
    log_id        INT AUTO_INCREMENT PRIMARY KEY,
    user_email    VARCHAR(150) NOT NULL,
    user_role     VARCHAR(50)  NOT NULL,
    action        VARCHAR(50)  NOT NULL,
    record_type   VARCHAR(50)  NOT NULL,
    record_detail TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Leave requests
CREATE TABLE leave_requests (
    request_id     INT AUTO_INCREMENT PRIMARY KEY,
    employee_id    INT NOT NULL,
    leave_from     DATE NOT NULL,
    leave_until    DATE NOT NULL,
    reason         TEXT NOT NULL,
    status         ENUM('Pending','Approved','Declined') NOT NULL DEFAULT 'Pending',
    hr_note        TEXT DEFAULT NULL,
    hr_decided_by  INT DEFAULT NULL,
    decided_at     DATETIME DEFAULT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
    FOREIGN KEY (hr_decided_by) REFERENCES employees(employee_id)
);

-- Notifications
CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    message         TEXT NOT NULL,
    is_read         TINYINT(1) NOT NULL DEFAULT 0,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);


-- ────────────────────────────────────────────────────────────
-- INDEXES
-- ────────────────────────────────────────────────────────────

CREATE INDEX idx_appointments_date     ON appointments(appointment_date);
CREATE INDEX idx_appointments_doctor   ON appointments(doctor_id);
CREATE INDEX idx_appointments_patient  ON appointments(patient_id);
CREATE INDEX idx_appointments_status   ON appointments(status);
CREATE INDEX idx_invoices_patient      ON invoices(patient_id);
CREATE INDEX idx_invoices_status       ON invoices(status);
CREATE INDEX idx_invoices_appointment  ON invoices(appointment_id);
CREATE INDEX idx_queue_date            ON queue_entries(created_at);
CREATE UNIQUE INDEX idx_queue_appointment ON queue_entries(appointment_id, created_at);
CREATE INDEX idx_doctor_schedules_doc  ON doctor_schedules(doctor_id);
CREATE INDEX idx_patients_status       ON patients(status);
CREATE INDEX idx_employees_role        ON employees(role_id);
CREATE INDEX idx_employees_dept        ON employees(department_id);
CREATE INDEX idx_employees_status      ON employees(status);
CREATE INDEX idx_activity_log_date     ON activity_log(created_at);
CREATE INDEX idx_activity_log_user     ON activity_log(user_email);
CREATE INDEX idx_leave_requests_employee ON leave_requests(employee_id);
CREATE INDEX idx_leave_requests_status   ON leave_requests(status);
CREATE INDEX idx_notifications_employee  ON notifications(employee_id);
CREATE INDEX idx_notifications_read      ON notifications(is_read);


-- ============================================================
-- SEED DATA
-- ============================================================

INSERT INTO departments (department_name) VALUES
    ('General Medicine'),
    ('Cardiology'),
    ('Dentistry'),
    ('Pediatrics'),
    ('Laboratory'),
    ('Front Desk'),
    ('Management'),
    ('Pharmacy'),
    ('Human Resources');

INSERT INTO roles (role_name) VALUES
    ('Doctor'),
    ('Nurse'),
    ('Receptionist'),
    ('Admin'),
    ('HR');

INSERT INTO services (service_name, price, category, is_active) VALUES
    ('General Checkup',          800.00,  'Consultation', 1),
    ('Follow-up Visit',          500.00,  'Consultation', 1),
    ('Lab Tests – CBC',         1200.00,  'Lab',          1),
    ('Lab Tests – Urinalysis',   600.00,  'Lab',          1),
    ('Dental Cleaning',         2500.00,  'Dental',       1),
    ('X-Ray',                   1500.00,  'Imaging',      1),
    ('ECG',                     1000.00,  'Imaging',      1),
    ('Physical Therapy Session', 1800.00, 'Therapy',      1),
    ('Consultation',             500.00,  'Consultation', 1),
    ('Blood Work',              1200.00,  'Lab',          1),
    ('Lab Results Review',       300.00,  'Lab',          1),
    ('X-Ray Review',             800.00,  'Imaging',      1),
    ('Physical Exam',           1000.00,  'Consultation', 1);

INSERT INTO payment_methods (method_name) VALUES
    ('Cash'),
    ('Credit Card'),
    ('GCash'),
    ('Maya'),
    ('Insurance');

INSERT INTO standard_conditions (condition_name) VALUES
    ('Hypertension'), ('Diabetes'), ('Asthma'), ('Heart Disease'),
    ('Allergies'), ('Arthritis'), ('COPD'), ('Obesity'),
    ('Thyroid Disorder'), ('Anemia'), ('Kidney Disease'),
    ('Depression'), ('Anxiety'), ('Migraine'), ('Epilepsy'),
    ('Cancer'), ('Stroke'), ('HIV/AIDS'), ('Tuberculosis'),
    ('Hepatitis'), ('None');

-- Default discount types (based on Philippine law)
INSERT INTO discount_types (type_name, discount_percent, legal_basis) VALUES
    ('Senior Citizen', 20.00, 'RA 9994 – Expanded Senior Citizens Act of 2010'),
    ('PWD',            20.00, 'RA 10754 – Act Expanding Benefits and Privileges of Persons with Disability'),
    ('Pregnant',        0.00, 'Courtesy discount – configurable by admin');

-- Default user accounts (one per role for testing)
INSERT INTO users (email, password, full_name, role_id) VALUES
    ('admin@carecrud.com',         'admin123',     'Carlo Santos',  4),
    ('ana.reyes@carecrud.com',     'doctor123',    'Ana Reyes',     1),
    ('sofia.reyes@carecrud.com',   'nurse123',     'Sofia Reyes',   2),
    ('james.cruz@carecrud.com',    'reception123', 'James Cruz',    3),
    ('hr@carecrud.com',            'hr123',        'Elena Ramos',   5);

-- Default employees
INSERT INTO employees (first_name, last_name, role_id, department_id, employment_type, phone, email, hire_date, status, salary) VALUES
    ('Ana',    'Reyes',   1, 2, 'Full-time', '09171234567', 'ana.reyes@carecrud.com',    '2020-06-15', 'Active',   55000.00),
    ('Mark',   'Tan',     1, 1, 'Full-time', '09179876543', 'mark.tan@carecrud.com',     '2019-03-10', 'Active',   60000.00),
    ('Lisa',   'Lim',     1, 3, 'Part-time', '09171112233', 'lisa.lim@carecrud.com',     '2021-01-20', 'Active',   35000.00),
    ('Pedro',  'Santos',  1, 4, 'Full-time', '09172223344', 'pedro.santos@carecrud.com', '2018-09-01', 'Inactive', 50000.00),
    ('Sofia',  'Reyes',   2, 2, 'Full-time', '09174445566', 'sofia.reyes@carecrud.com',  '2022-04-12', 'Active',   28000.00),
    ('James',  'Cruz',    3, 6, 'Full-time', '09177778899', 'james.cruz@carecrud.com',   '2021-07-01', 'Active',   25000.00),
    ('Carlo',  'Santos',  4, 7, 'Full-time', '09176667788', 'carlo.santos@carecrud.com', '2019-01-05', 'Active',   70000.00),
    ('Elena',  'Ramos',   5, 9, 'Full-time', '09178889900', 'hr@carecrud.com',           '2020-01-15', 'Active',   45000.00);

-- Default doctor schedules
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time) VALUES
    (1, 'Monday',    '08:00:00', '17:00:00'),
    (1, 'Tuesday',   '08:00:00', '17:00:00'),
    (1, 'Wednesday', '08:00:00', '17:00:00'),
    (1, 'Thursday',  '08:00:00', '17:00:00'),
    (1, 'Friday',    '08:00:00', '17:00:00'),
    (2, 'Monday',    '09:00:00', '18:00:00'),
    (2, 'Wednesday', '09:00:00', '18:00:00'),
    (2, 'Friday',    '09:00:00', '18:00:00'),
    (3, 'Tuesday',   '08:00:00', '12:00:00'),
    (3, 'Thursday',  '08:00:00', '12:00:00'),
    (3, 'Saturday',  '08:00:00', '12:00:00');


-- ============================================================
-- VIEWS
-- ============================================================

-- Employees with role + department names
CREATE VIEW vw_employees AS
SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS full_name,
    r.role_name,
    d.department_name,
    e.employment_type,
    e.phone,
    e.email,
    e.hire_date,
    e.status,
    e.notes,
    e.leave_from,
    e.leave_until,
    e.salary,
    e.emergency_contact
FROM employees e
INNER JOIN roles r       ON e.role_id       = r.role_id
INNER JOIN departments d ON e.department_id = d.department_id;


-- Patients with their conditions────
CREATE VIEW vw_patients AS
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS full_name,
    p.sex,
    TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
    p.phone,
    p.email,
    p.address,
    p.civil_status,
    p.emergency_contact,
    p.blood_type,
    COALESCE(GROUP_CONCAT(pc.condition_name SEPARATOR ', '), 'None') AS conditions,
    p.status,
    p.notes
FROM patients p
LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
GROUP BY p.patient_id;


-- Appointments with patient, doctor, service names
CREATE VIEW vw_appointments AS
SELECT
    a.appointment_id,
    a.appointment_date,
    DATE_FORMAT(a.appointment_time, '%h:%i %p') AS appointment_time,
    CONCAT(p.first_name, ' ', p.last_name)      AS patient_name,
    CONCAT(e.first_name, ' ', e.last_name)       AS doctor_name,
    s.service_name                                AS purpose,
    a.status,
    a.notes,
    a.cancellation_reason,
    a.reschedule_reason,
    a.reminder_sent
FROM appointments a
INNER JOIN patients  p ON a.patient_id = p.patient_id
INNER JOIN employees e ON a.doctor_id  = e.employee_id
INNER JOIN services  s ON a.service_id = s.service_id;


-- Queue with patient + doctor names────
CREATE VIEW vw_queue AS
SELECT
    q.queue_id,
    DATE_FORMAT(q.queue_time, '%h:%i %p') AS queue_time,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    CONCAT(e.first_name, ' ', e.last_name) AS doctor_name,
    q.purpose,
    q.status,
    q.created_at
FROM queue_entries q
INNER JOIN patients  p ON q.patient_id = p.patient_id
INNER JOIN employees e ON q.doctor_id  = e.employee_id;


-- Invoice details joined with patient, payment method, items
CREATE VIEW vw_invoices AS
SELECT
    i.invoice_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    s.service_name,
    ii.quantity,
    ii.unit_price,
    ii.subtotal,
    pm.method_name AS payment_method,
    i.discount_percent,
    i.total_amount,
    i.amount_paid,
    i.status,
    i.notes,
    i.created_at
FROM invoices i
INNER JOIN patients        p  ON i.patient_id = p.patient_id
LEFT  JOIN payment_methods pm ON i.method_id  = pm.method_id
INNER JOIN invoice_items   ii ON i.invoice_id = ii.invoice_id
INNER JOIN services        s  ON ii.service_id = s.service_id;


-- Doctor performance stats──
CREATE VIEW vw_doctor_performance AS
SELECT
    e.employee_id,
    CONCAT(e.first_name, ' ', e.last_name) AS doctor_name,
    COUNT(a.appointment_id)                              AS total_appointments,
    SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) AS completed,
    COALESCE(SUM(CASE WHEN a.status = 'Completed' THEN s.price ELSE 0 END), 0) AS revenue_generated
FROM employees e
INNER JOIN roles r ON e.role_id = r.role_id
LEFT  JOIN appointments a ON e.employee_id = a.doctor_id
LEFT  JOIN services     s ON a.service_id  = s.service_id
WHERE r.role_name = 'Doctor'
GROUP BY e.employee_id;


-- Monthly revenue────────
CREATE VIEW vw_monthly_revenue AS
SELECT
    DATE_FORMAT(a.appointment_date, '%M %Y') AS month_label,
    DATE_FORMAT(a.appointment_date, '%Y-%m') AS sort_key,
    COUNT(a.appointment_id)                  AS appointment_count,
    SUM(s.price)                             AS total_revenue
FROM appointments a
INNER JOIN services s ON a.service_id = s.service_id
WHERE a.status = 'Completed'
GROUP BY sort_key, month_label
ORDER BY sort_key DESC;


-- Today's appointments for dashboard──
CREATE VIEW vw_today_appointments AS
SELECT
    DATE_FORMAT(a.appointment_time, '%h:%i %p') AS time_slot,
    CONCAT(p.first_name, ' ', p.last_name)       AS patient_name,
    CONCAT(e.first_name, ' ', e.last_name)        AS doctor_name,
    s.service_name                                 AS purpose,
    a.status
FROM appointments a
INNER JOIN patients  p ON a.patient_id = p.patient_id
INNER JOIN employees e ON a.doctor_id  = e.employee_id
INNER JOIN services  s ON a.service_id = s.service_id
WHERE a.appointment_date = CURDATE()
ORDER BY a.appointment_time;


-- Top services by how often they're used────────
CREATE VIEW vw_top_services AS
SELECT
    s.service_id,
    s.service_name,
    s.category,
    s.is_active,
    COUNT(a.appointment_id) AS usage_count,
    SUM(s.price)             AS total_revenue
FROM services s
LEFT JOIN appointments a ON s.service_id = a.service_id
GROUP BY s.service_id, s.service_name, s.category, s.is_active
ORDER BY usage_count DESC;
