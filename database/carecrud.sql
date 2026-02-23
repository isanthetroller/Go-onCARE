-- ============================================================
-- CareCRUD Database Schema  –  MySQL / MariaDB (XAMPP)
-- Normalized to Third Normal Form (3NF)
-- ============================================================

CREATE DATABASE IF NOT EXISTS carecrud_db;
USE carecrud_db;


-- ────────────────────────────────────────────────────────────
-- LOOKUP / REFERENCE TABLES
-- ────────────────────────────────────────────────────────────

-- Departments (eliminates transitive dependency from employees)
CREATE TABLE departments (
    department_id   INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

-- Roles (eliminates transitive dependency from employees)
CREATE TABLE roles (
    role_id   INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE
);

-- Services offered by the hospital
CREATE TABLE services (
    service_id   INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    price        DECIMAL(10, 2) NOT NULL DEFAULT 0.00
);

-- Payment methods (eliminates repeating string values in invoices)
CREATE TABLE payment_methods (
    method_id   INT AUTO_INCREMENT PRIMARY KEY,
    method_name VARCHAR(50) NOT NULL UNIQUE
);


-- ────────────────────────────────────────────────────────────
-- CORE ENTITY TABLES
-- ────────────────────────────────────────────────────────────

-- User accounts (for login)
CREATE TABLE users (
    user_id    INT AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    full_name  VARCHAR(100) NOT NULL,
    role_id    INT          NOT NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Employees / Staff
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

    FOREIGN KEY (role_id)       REFERENCES roles(role_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- Patients
CREATE TABLE patients (
    patient_id    INT AUTO_INCREMENT PRIMARY KEY,
    first_name    VARCHAR(50)  NOT NULL,
    last_name     VARCHAR(50)  NOT NULL,
    sex           ENUM('Male', 'Female') NOT NULL,
    date_of_birth DATE,
    phone         VARCHAR(20),
    email         VARCHAR(150),
    status        ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
    notes         TEXT,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Patient medical conditions (3NF: multi-valued attribute separated)
CREATE TABLE patient_conditions (
    condition_id   INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT          NOT NULL,
    condition_name VARCHAR(100) NOT NULL,

    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ON DELETE CASCADE
);


-- ────────────────────────────────────────────────────────────
-- TRANSACTIONAL TABLES
-- ────────────────────────────────────────────────────────────

-- Appointments
CREATE TABLE appointments (
    appointment_id   INT AUTO_INCREMENT PRIMARY KEY,
    patient_id       INT  NOT NULL,
    doctor_id        INT  NOT NULL,
    service_id       INT  NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status           ENUM('Pending', 'Confirmed', 'Cancelled', 'Completed') NOT NULL DEFAULT 'Pending',
    notes            TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES employees(employee_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- Patient queue (clinical workflow)
CREATE TABLE queue_entries (
    queue_id       INT AUTO_INCREMENT PRIMARY KEY,
    patient_id     INT  NOT NULL,
    doctor_id      INT  NOT NULL,
    appointment_id INT,
    queue_time     TIME NOT NULL,
    purpose        VARCHAR(100),
    status         ENUM('Waiting', 'In Progress', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Waiting',
    created_at     DATE NOT NULL DEFAULT (CURRENT_DATE),

    FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id)      REFERENCES employees(employee_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id)
);

-- Invoices (billing header)
CREATE TABLE invoices (
    invoice_id       INT AUTO_INCREMENT PRIMARY KEY,
    patient_id       INT  NOT NULL,
    appointment_id   INT,
    method_id        INT,
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    total_amount     DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    amount_paid      DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    status           ENUM('Paid', 'Unpaid', 'Partial') NOT NULL DEFAULT 'Unpaid',
    notes            TEXT,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)     REFERENCES patients(patient_id),
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
    FOREIGN KEY (method_id)      REFERENCES payment_methods(method_id)
);

-- Invoice line items (3NF: each item is its own row)
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


-- ────────────────────────────────────────────────────────────
-- INDEXES FOR PERFORMANCE
-- ────────────────────────────────────────────────────────────

CREATE INDEX idx_appointments_date     ON appointments(appointment_date);
CREATE INDEX idx_appointments_doctor   ON appointments(doctor_id);
CREATE INDEX idx_appointments_patient  ON appointments(patient_id);
CREATE INDEX idx_appointments_status   ON appointments(status);
CREATE INDEX idx_invoices_patient      ON invoices(patient_id);
CREATE INDEX idx_invoices_status       ON invoices(status);
CREATE INDEX idx_queue_date            ON queue_entries(created_at);
CREATE INDEX idx_patients_status       ON patients(status);
CREATE INDEX idx_employees_role        ON employees(role_id);
CREATE INDEX idx_employees_dept        ON employees(department_id);
CREATE INDEX idx_employees_status      ON employees(status);


-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Lookup data
INSERT INTO departments (department_name) VALUES
    ('General Medicine'),
    ('Cardiology'),
    ('Dentistry'),
    ('Pediatrics'),
    ('Laboratory'),
    ('Front Desk'),
    ('Management'),
    ('Pharmacy');

INSERT INTO roles (role_name) VALUES
    ('Doctor'),
    ('Nurse'),
    ('Receptionist'),
    ('Lab Tech'),
    ('Admin'),
    ('Pharmacist');

INSERT INTO services (service_name, price) VALUES
    ('General Checkup',          800.00),
    ('Follow-up Visit',          500.00),
    ('Lab Tests – CBC',         1200.00),
    ('Lab Tests – Urinalysis',   600.00),
    ('Dental Cleaning',         2500.00),
    ('X-Ray',                   1500.00),
    ('ECG',                     1000.00),
    ('Physical Therapy Session', 1800.00),
    ('Consultation',             500.00),
    ('Blood Work',              1200.00),
    ('Lab Results Review',       300.00),
    ('X-Ray Review',             800.00),
    ('Physical Exam',           1000.00);

INSERT INTO payment_methods (method_name) VALUES
    ('Cash'),
    ('Credit Card'),
    ('GCash'),
    ('Maya'),
    ('Insurance');

-- Default user accounts (one per role for testing)
-- Passwords are plain-text for development; hash in production
INSERT INTO users (email, password, full_name, role_id) VALUES
    ('admin@carecrud.com',         'admin123',     'Carlo Santos',  5),
    ('ana.reyes@carecrud.com',     'doctor123',    'Ana Reyes',     1),
    ('sofia.reyes@carecrud.com',   'nurse123',     'Sofia Reyes',   2),
    ('james.cruz@carecrud.com',    'reception123', 'James Cruz',    3);

-- Employees
INSERT INTO employees (first_name, last_name, role_id, department_id, employment_type, phone, email, hire_date, status) VALUES
    ('Ana',    'Reyes',   1, 2, 'Full-time', '09171234567', 'ana.reyes@carecrud.com',    '2020-06-15', 'Active'),
    ('Mark',   'Tan',     1, 1, 'Full-time', '09179876543', 'mark.tan@carecrud.com',     '2019-03-10', 'Active'),
    ('Lisa',   'Lim',     1, 3, 'Part-time', '09171112233', 'lisa.lim@carecrud.com',     '2021-01-20', 'Active'),
    ('Pedro',  'Santos',  1, 4, 'Full-time', '09172223344', 'pedro.santos@carecrud.com', '2018-09-01', 'Inactive'),
    ('Sofia',  'Reyes',   2, 2, 'Full-time', '09174445566', 'sofia.reyes@carecrud.com',  '2022-04-12', 'Active'),
    ('James',  'Cruz',    3, 6, 'Full-time', '09177778899', 'james.cruz@carecrud.com',   '2021-07-01', 'Active'),
    ('Maria',  'Garcia',  4, 5, 'Full-time', '09173334455', 'maria.garcia@carecrud.com', '2020-11-15', 'On Leave'),
    ('Carlo',  'Santos',  5, 7, 'Full-time', '09176667788', 'carlo.santos@carecrud.com', '2019-01-05', 'Active');

-- Patients
INSERT INTO patients (first_name, last_name, sex, date_of_birth, phone, email, status) VALUES
    ('Maria',  'Santos',      'Female', '1994-05-12', '09171234567', 'maria@email.com',   'Active'),
    ('Juan',   'Dela Cruz',   'Male',   '1981-08-23', '09179876543', 'juan@email.com',    'Active'),
    ('Ana',    'Reyes',       'Female', '1998-02-14', '09171112233', 'ana@email.com',     'Active'),
    ('Carlos', 'Garcia',      'Male',   '1966-11-30', '09174445566', 'carlos@email.com',  'Inactive'),
    ('Lea',    'Mendoza',     'Female', '1989-07-19', '09177778899', 'lea@email.com',     'Active'),
    ('Roberto','Cruz',        'Male',   '1974-03-08', '09173334455', 'roberto@email.com', 'Active'),
    ('Isabel', 'Tan',         'Female', '1985-12-25', '09176667788', 'isabel@email.com',  'Active'),
    ('Miguel', 'Lim',         'Male',   '1971-09-17', '09172223344', 'miguel@email.com',  'Inactive'),
    ('Rosa',   'Mendoza',     'Female', '1990-06-01', '09175551234', 'rosa@email.com',    'Active'),
    ('Pedro',  'Villanueva',  'Male',   '1988-10-10', '09175559876', 'pedro.v@email.com', 'Active'),
    ('Luis',   'Garcia',      'Male',   '1975-04-22', '09175554321', 'luis@email.com',    'Active'),
    ('Sofia',  'Reyes',       'Female', '1992-01-30', '09175556789', 'sofia.r@email.com', 'Active');

-- Patient conditions (3NF: separated from patient table)
INSERT INTO patient_conditions (patient_id, condition_name) VALUES
    (1, 'Hypertension'),
    (2, 'Diabetes'),
    (3, 'Asthma'),
    (4, 'Heart Disease'),
    (6, 'Hypertension'),
    (7, 'Allergies'),
    (8, 'Arthritis');

-- Appointments
-- doctor_id: 1=Dr. Reyes, 2=Dr. Tan, 3=Dr. Lim, 4=Dr. Santos
-- service_id references services table
INSERT INTO appointments (patient_id, doctor_id, service_id, appointment_date, appointment_time, status) VALUES
    -- Today: Feb 22, 2026
    (1,  1, 1,  '2026-02-22', '09:00:00', 'Confirmed'),
    (2,  2, 2,  '2026-02-22', '09:30:00', 'Confirmed'),
    (3,  1, 11, '2026-02-22', '10:00:00', 'Pending'),
    (4,  3, 5,  '2026-02-22', '10:30:00', 'Confirmed'),
    (5,  2, 9,  '2026-02-22', '11:00:00', 'Pending'),
    -- Tomorrow: Feb 23
    (6,  1, 10, '2026-02-23', '08:30:00', 'Confirmed'),
    (7,  3, 12, '2026-02-23', '09:00:00', 'Pending'),
    (12, 2, 9,  '2026-02-23', '10:00:00', 'Confirmed'),
    -- Feb other days
    (8,  2, 13, '2026-02-24', '10:00:00', 'Confirmed'),
    (9,  1, 1,  '2026-02-18', '09:00:00', 'Completed'),
    (10, 3, 5,  '2026-02-15', '14:00:00', 'Completed'),
    -- January 2026
    (11, 2, 2,  '2026-01-28', '10:00:00', 'Completed'),
    (1,  1, 11, '2026-01-22', '09:30:00', 'Completed'),
    (3,  3, 12, '2026-01-15', '11:00:00', 'Completed'),
    (4,  1, 10, '2026-01-10', '08:30:00', 'Completed'),
    -- December 2025
    (2,  2, 13, '2025-12-18', '09:00:00', 'Completed'),
    (5,  1, 1,  '2025-12-10', '10:30:00', 'Completed'),
    (6,  3, 5,  '2025-12-05', '14:00:00', 'Completed'),
    -- November 2025
    (7,  2, 9,  '2025-11-20', '09:30:00', 'Completed'),
    (8,  1, 2,  '2025-11-12', '10:00:00', 'Completed');

-- Queue entries (today)
INSERT INTO queue_entries (patient_id, doctor_id, appointment_id, queue_time, purpose, status, created_at) VALUES
    (1, 1, 1, '09:00:00', 'General Checkup', 'Waiting',     '2026-02-22'),
    (2, 2, 2, '09:30:00', 'Follow-up Visit',       'In Progress', '2026-02-22'),
    (3, 1, 3, '10:00:00', 'Lab Results Review',    'Waiting',     '2026-02-22'),
    (4, 3, 4, '10:30:00', 'Dental Cleaning',  'Waiting',     '2026-02-22');

-- Invoices
INSERT INTO invoices (patient_id, appointment_id, method_id, discount_percent, total_amount, amount_paid, status) VALUES
    (1, 1,  1, 0.00,  800.00,  800.00, 'Paid'),
    (2, 2,  3, 0.00,  500.00,    0.00, 'Unpaid'),
    (3, 3,  2, 0.00, 1200.00, 1200.00, 'Paid'),
    (4, 4,  5, 0.00, 2500.00, 1000.00, 'Partial');

-- Invoice items
INSERT INTO invoice_items (invoice_id, service_id, quantity, unit_price, subtotal) VALUES
    (1, 1, 1,  800.00,  800.00),
    (2, 2, 1,  500.00,  500.00),
    (3, 3, 1, 1200.00, 1200.00),
    (4, 5, 1, 2500.00, 2500.00);


-- ============================================================
-- VIEWS (JOIN queries for common operations)
-- ============================================================

-- ── Full employee details with role and department names ────
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
    e.notes
FROM employees e
INNER JOIN roles r       ON e.role_id       = r.role_id
INNER JOIN departments d ON e.department_id = d.department_id;


-- ── Full patient details with conditions ───────────────────
CREATE VIEW vw_patients AS
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS full_name,
    p.sex,
    TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
    p.phone,
    p.email,
    COALESCE(GROUP_CONCAT(pc.condition_name SEPARATOR ', '), 'None') AS conditions,
    p.status,
    p.notes
FROM patients p
LEFT JOIN patient_conditions pc ON p.patient_id = pc.patient_id
GROUP BY p.patient_id;


-- ── Appointment list with patient, doctor, and service names
CREATE VIEW vw_appointments AS
SELECT
    a.appointment_id,
    a.appointment_date,
    DATE_FORMAT(a.appointment_time, '%h:%i %p') AS appointment_time,
    CONCAT(p.first_name, ' ', p.last_name)      AS patient_name,
    CONCAT(e.first_name, ' ', e.last_name)       AS doctor_name,
    s.service_name                                AS purpose,
    a.status,
    a.notes
FROM appointments a
INNER JOIN patients  p ON a.patient_id = p.patient_id
INNER JOIN employees e ON a.doctor_id  = e.employee_id
INNER JOIN services  s ON a.service_id = s.service_id;


-- ── Queue with patient and doctor names ────────────────────
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


-- ── Invoice details with patient, payment method, items ────
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


-- ── Doctor performance (appointments + revenue) ───────────
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


-- ── Monthly revenue summary ───────────────────────────────
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


-- ── Today's appointments (quick dashboard query) ──────────
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


-- ── Top services by usage count ───────────────────────────
CREATE VIEW vw_top_services AS
SELECT
    s.service_id,
    s.service_name,
    COUNT(a.appointment_id) AS usage_count,
    SUM(s.price)             AS total_revenue
FROM services s
LEFT JOIN appointments a ON s.service_id = a.service_id
GROUP BY s.service_id, s.service_name
ORDER BY usage_count DESC;


-- ============================================================
-- USEFUL QUERIES (examples for Python connector)
-- ============================================================

-- Get today's appointments
-- SELECT * FROM vw_today_appointments;

-- Get appointments for a specific month/year
-- SELECT * FROM vw_appointments
-- WHERE MONTH(appointment_date) = 2
--   AND YEAR(appointment_date) = 2026
-- ORDER BY appointment_date, appointment_time;

-- Get all active patients with conditions
-- SELECT * FROM vw_patients WHERE status = 'Active';

-- Get all active employees
-- SELECT * FROM vw_employees WHERE status = 'Active';

-- Get unpaid / partial invoices
-- SELECT * FROM vw_invoices WHERE status IN ('Unpaid', 'Partial');

-- Get doctor performance
-- SELECT * FROM vw_doctor_performance ORDER BY revenue_generated DESC;

-- Get appointments filtered by doctor and status
-- SELECT * FROM vw_appointments
-- WHERE doctor_name LIKE '%Reyes%'
--   AND status = 'Confirmed';

-- Dashboard quick stats
-- SELECT
--     (SELECT COUNT(*) FROM patients WHERE status = 'Active') AS total_patients,
--     (SELECT COUNT(*) FROM appointments WHERE appointment_date = CURDATE()) AS today_appointments,
--     (SELECT COALESCE(SUM(amount_paid), 0) FROM invoices WHERE status IN ('Paid', 'Partial')) AS total_revenue;
