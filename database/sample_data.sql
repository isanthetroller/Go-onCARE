-- ============================================================
-- CareCRUD V2 Sample Data  –  MySQL / MariaDB (XAMPP)
-- Run after carecrud.sql schema to populate rich test data
-- Includes all V2 columns (blood_type, emergency_contact,
--   service categories, cancellation reasons, etc.)
-- ============================================================

USE carecrud_db;

-- Clear existing data (child tables first, then parents)
DELETE FROM invoice_items;
DELETE FROM invoices;
DELETE FROM queue_entries;
DELETE FROM appointments;
DELETE FROM patient_conditions;
DELETE FROM patients;
DELETE FROM employees;
DELETE FROM users;
DELETE FROM user_preferences;
DELETE FROM activity_log;
DELETE FROM standard_conditions;
DELETE FROM payment_methods;
DELETE FROM services;
DELETE FROM roles;
DELETE FROM departments;


-- ────────────────────────────────────────────────────────────
-- LOOKUP / REFERENCE DATA
-- ────────────────────────────────────────────────────────────

INSERT INTO departments (department_id, department_name) VALUES
    (1, 'General Medicine'),
    (2, 'Cardiology'),
    (3, 'Dentistry'),
    (4, 'Pediatrics'),
    (5, 'Laboratory'),
    (6, 'Front Desk'),
    (7, 'Management'),
    (8, 'Pharmacy');

INSERT INTO roles (role_id, role_name) VALUES
    (1, 'Doctor'),
    (2, 'Cashier'),
    (3, 'Receptionist'),
    (4, 'Lab Tech'),
    (5, 'Admin'),
    (6, 'Pharmacist');

INSERT INTO services (service_id, service_name, price, category, is_active) VALUES
    (1,  'General Checkup',          800.00,  'Consultation', 1),
    (2,  'Follow-up Visit',          500.00,  'Consultation', 1),
    (3,  'Lab Tests – CBC',         1200.00,  'Lab',          1),
    (4,  'Lab Tests – Urinalysis',   600.00,  'Lab',          1),
    (5,  'Dental Cleaning',         2500.00,  'Dental',       1),
    (6,  'X-Ray',                   1500.00,  'Imaging',      1),
    (7,  'ECG',                     1000.00,  'Imaging',      1),
    (8,  'Physical Therapy Session', 1800.00, 'Therapy',      1),
    (9,  'Consultation',             500.00,  'Consultation', 1),
    (10, 'Blood Work',              1200.00,  'Lab',          1),
    (11, 'Lab Results Review',       300.00,  'Lab',          1),
    (12, 'X-Ray Review',             800.00,  'Imaging',      1),
    (13, 'Physical Exam',           1000.00,  'Consultation', 1);

INSERT INTO payment_methods (method_id, method_name) VALUES
    (1, 'Cash'),
    (2, 'Credit Card'),
    (3, 'GCash'),
    (4, 'Maya'),
    (5, 'Insurance');

INSERT INTO standard_conditions (condition_name) VALUES
    ('Hypertension'), ('Diabetes'), ('Asthma'), ('Heart Disease'),
    ('Allergies'), ('Arthritis'), ('COPD'), ('Obesity'),
    ('Thyroid Disorder'), ('Anemia'), ('Kidney Disease'),
    ('Depression'), ('Anxiety'), ('Migraine'), ('Epilepsy'),
    ('Cancer'), ('Stroke'), ('HIV/AIDS'), ('Tuberculosis'),
    ('Hepatitis'), ('None');


-- ────────────────────────────────────────────────────────────
-- USER ACCOUNTS
-- ────────────────────────────────────────────────────────────

INSERT INTO users (email, password, full_name, role_id) VALUES
    ('admin@carecrud.com',         'admin123',     'Carlo Santos',  5),
    ('ana.reyes@carecrud.com',     'doctor123',    'Ana Reyes',     1),
    ('mark.tan@carecrud.com',      'doctor123',    'Mark Tan',      1),
    ('lisa.lim@carecrud.com',      'doctor123',    'Lisa Lim',      1),
    ('sofia.reyes@carecrud.com',   'cashier123',   'Sofia Reyes',   2),
    ('james.cruz@carecrud.com',    'reception123', 'James Cruz',    3);


-- ────────────────────────────────────────────────────────────
-- USER PREFERENCES (V2)
-- ────────────────────────────────────────────────────────────

INSERT INTO user_preferences (user_email, dark_mode) VALUES
    ('admin@carecrud.com', 0);


-- ────────────────────────────────────────────────────────────
-- EMPLOYEES (V2: with leave_from / leave_until)
-- ────────────────────────────────────────────────────────────

INSERT INTO employees (employee_id, first_name, last_name, role_id, department_id, employment_type, phone, email, hire_date, status, leave_from, leave_until) VALUES
    (1, 'Ana',    'Reyes',   1, 2, 'Full-time', '09171234567', 'ana.reyes@carecrud.com',    '2020-06-15', 'Active',   NULL,         NULL),
    (2, 'Mark',   'Tan',     1, 1, 'Full-time', '09179876543', 'mark.tan@carecrud.com',     '2019-03-10', 'Active',   NULL,         NULL),
    (3, 'Lisa',   'Lim',     1, 3, 'Part-time', '09171112233', 'lisa.lim@carecrud.com',     '2021-01-20', 'Active',   NULL,         NULL),
    (4, 'Pedro',  'Santos',  1, 4, 'Full-time', '09172223344', 'pedro.santos@carecrud.com', '2018-09-01', 'Inactive', NULL,         NULL),
    (5, 'Sofia',  'Reyes',   2, 2, 'Full-time', '09174445566', 'sofia.reyes@carecrud.com',  '2022-04-12', 'Active',   NULL,         NULL),
    (6, 'James',  'Cruz',    3, 6, 'Full-time', '09177778899', 'james.cruz@carecrud.com',   '2021-07-01', 'Active',   NULL,         NULL),
    (7, 'Maria',  'Garcia',  4, 5, 'Full-time', '09173334455', 'maria.garcia@carecrud.com', '2020-11-15', 'On Leave', '2026-02-20', '2026-03-05'),
    (8, 'Carlo',  'Santos',  5, 7, 'Full-time', '09176667788', 'carlo.santos@carecrud.com', '2019-01-05', 'Active',   NULL,         NULL);


-- ────────────────────────────────────────────────────────────
-- PATIENTS  (20 patients, V2 fields: emergency_contact, blood_type)
-- ────────────────────────────────────────────────────────────

INSERT INTO patients (patient_id, first_name, last_name, sex, date_of_birth, phone, email, emergency_contact, blood_type, status) VALUES
    (1,  'Maria',    'Santos',      'Female', '1994-05-12', '09171234567', 'maria@email.com',      'Juan Santos – 09171234568',       'O+',      'Active'),
    (2,  'Juan',     'Dela Cruz',   'Male',   '1981-08-23', '09179876543', 'juan@email.com',       'Rosa Dela Cruz – 09179876544',    'A+',      'Active'),
    (3,  'Ana',      'Reyes',       'Female', '1998-02-14', '09171112233', 'ana@email.com',        '',                                 'B+',      'Active'),
    (4,  'Carlos',   'Garcia',      'Male',   '1966-11-30', '09174445566', 'carlos@email.com',     'Elena Garcia – 09174445567',      'AB+',     'Active'),
    (5,  'Lea',      'Mendoza',     'Female', '1989-07-19', '09177778899', 'lea@email.com',        'Roberto Mendoza – 09177778800',   'O-',      'Active'),
    (6,  'Roberto',  'Cruz',        'Male',   '1974-03-08', '09173334455', 'roberto@email.com',    'Maria Cruz – 09173334456',        'A-',      'Active'),
    (7,  'Isabel',   'Tan',         'Female', '1985-12-25', '09176667788', 'isabel@email.com',     '',                                 'Unknown', 'Active'),
    (8,  'Miguel',   'Lim',         'Male',   '1971-09-17', '09172223344', 'miguel@email.com',     '',                                 'B-',      'Inactive'),
    (9,  'Rosa',     'Mendoza',     'Female', '1990-06-01', '09175551234', 'rosa@email.com',       '',                                 'O+',      'Active'),
    (10, 'Pedro',    'Villanueva',  'Male',   '1988-10-10', '09175559876', 'pedro.v@email.com',    '',                                 'A+',      'Active'),
    (11, 'Luis',     'Garcia',      'Male',   '1975-04-22', '09175554321', 'luis@email.com',       '',                                 'Unknown', 'Active'),
    (12, 'Sofia',    'Reyes',       'Female', '1992-01-30', '09175556789', 'sofia.r@email.com',    '',                                 'AB-',     'Active'),
    (13, 'Elena',    'Bautista',    'Female', '2010-03-15', '09175550001', 'elena.b@email.com',    'Marco Bautista – 09175550010',    'O+',      'Active'),
    (14, 'Marco',    'Ramos',       'Male',   '2015-07-22', '09175550002', 'marco.r@email.com',    'Diana Ramos – 09175550020',       'A+',      'Active'),
    (15, 'Camille',  'Torres',      'Female', '1955-11-03', '09175550003', 'camille.t@email.com',  'Antonio Torres – 09175550030',    'B+',      'Active'),
    (16, 'Antonio',  'Flores',      'Male',   '1948-06-18', '09175550004', 'antonio.f@email.com',  '',                                 'AB+',     'Active'),
    (17, 'Patricia', 'Navarro',     'Female', '2005-09-28', '09175550005', 'patricia.n@email.com', '',                                 'O-',      'Active'),
    (18, 'Gabriel',  'Luna',        'Male',   '1960-02-14', '09175550006', 'gabriel.l@email.com',  'Isabel Luna – 09175550060',       'A-',      'Active'),
    (19, 'Diana',    'Castro',      'Female', '2000-12-05', '09175550007', 'diana.c@email.com',    '',                                 'B-',      'Active'),
    (20, 'Rafael',   'Aquino',      'Male',   '1995-08-30', '09175550008', 'rafael.a@email.com',   '',                                 'Unknown', 'Inactive');


-- ────────────────────────────────────────────────────────────
-- PATIENT CONDITIONS
-- ────────────────────────────────────────────────────────────

INSERT INTO patient_conditions (patient_id, condition_name) VALUES
    (1,  'Hypertension'),
    (2,  'Diabetes'),
    (2,  'Hypertension'),
    (3,  'Asthma'),
    (4,  'Heart Disease'),
    (5,  'Allergies'),
    (6,  'Hypertension'),
    (7,  'Allergies'),
    (8,  'Arthritis'),
    (9,  'Diabetes'),
    (10, 'Asthma'),
    (11, 'Heart Disease'),
    (15, 'Hypertension'),
    (16, 'Heart Disease'),
    (16, 'Diabetes'),
    (18, 'Arthritis');


-- ────────────────────────────────────────────────────────────
-- APPOINTMENTS  (spread across 6 months for analytics)
-- V2: includes cancellation_reason on cancelled rows
-- doctor_id: 1=Dr. Reyes, 2=Dr. Tan, 3=Dr. Lim, 4=Dr. Santos
-- ────────────────────────────────────────────────────────────

INSERT INTO appointments (appointment_id, patient_id, doctor_id, service_id, appointment_date, appointment_time, status, cancellation_reason) VALUES
    -- ── September 2025 ──
    (1,  1,  1, 1,  '2025-09-02', '09:00:00', 'Completed', NULL),
    (2,  2,  2, 2,  '2025-09-05', '10:00:00', 'Completed', NULL),
    (3,  3,  1, 9,  '2025-09-08', '09:30:00', 'Completed', NULL),
    (4,  5,  3, 5,  '2025-09-10', '14:00:00', 'Completed', NULL),
    (5,  6,  2, 6,  '2025-09-12', '11:00:00', 'Completed', NULL),
    (6,  7,  1, 3,  '2025-09-15', '09:00:00', 'Completed', NULL),
    (7,  9,  3, 7,  '2025-09-18', '10:30:00', 'Completed', NULL),
    (8,  10, 2, 8,  '2025-09-22', '14:00:00', 'Completed', NULL),
    (9,  4,  1, 1,  '2025-09-25', '09:00:00', 'Cancelled', 'Patient no-show'),
    (10, 11, 2, 13, '2025-09-28', '11:00:00', 'Completed', NULL),

    -- ── October 2025 ──
    (11, 1,  1, 11, '2025-10-01', '09:30:00', 'Completed', NULL),
    (12, 3,  2, 2,  '2025-10-03', '10:00:00', 'Completed', NULL),
    (13, 5,  1, 1,  '2025-10-06', '09:00:00', 'Completed', NULL),
    (14, 6,  3, 12, '2025-10-08', '14:00:00', 'Completed', NULL),
    (15, 7,  2, 9,  '2025-10-10', '11:00:00', 'Completed', NULL),
    (16, 9,  1, 3,  '2025-10-13', '09:00:00', 'Completed', NULL),
    (17, 10, 3, 5,  '2025-10-15', '14:30:00', 'Completed', NULL),
    (18, 12, 2, 6,  '2025-10-17', '10:00:00', 'Completed', NULL),
    (19, 2,  1, 10, '2025-10-20', '09:30:00', 'Completed', NULL),
    (20, 11, 2, 7,  '2025-10-22', '11:00:00', 'Completed', NULL),
    (21, 4,  3, 1,  '2025-10-25', '14:00:00', 'Cancelled', 'Doctor unavailable'),
    (22, 15, 1, 13, '2025-10-28', '09:00:00', 'Completed', NULL),

    -- ── November 2025 ──
    (23, 1,  2, 2,  '2025-11-03', '10:00:00', 'Completed', NULL),
    (24, 3,  1, 1,  '2025-11-05', '09:00:00', 'Completed', NULL),
    (25, 5,  3, 7,  '2025-11-07', '14:00:00', 'Completed', NULL),
    (26, 7,  2, 9,  '2025-11-10', '10:30:00', 'Completed', NULL),
    (27, 6,  1, 6,  '2025-11-12', '09:00:00', 'Completed', NULL),
    (28, 9,  3, 5,  '2025-11-14', '14:30:00', 'Completed', NULL),
    (29, 10, 2, 8,  '2025-11-17', '10:00:00', 'Completed', NULL),
    (30, 12, 1, 3,  '2025-11-19', '09:30:00', 'Completed', NULL),
    (31, 2,  2, 13, '2025-11-21', '11:00:00', 'Completed', NULL),
    (32, 16, 1, 10, '2025-11-24', '09:00:00', 'Completed', NULL),
    (33, 13, 3, 1,  '2025-11-26', '14:00:00', 'Completed', NULL),
    (34, 4,  2, 2,  '2025-11-28', '10:00:00', 'Cancelled', 'Patient requested cancellation'),

    -- ── December 2025 ──
    (35, 1,  1, 1,  '2025-12-01', '09:00:00', 'Completed', NULL),
    (36, 3,  2, 6,  '2025-12-03', '10:00:00', 'Completed', NULL),
    (37, 5,  1, 9,  '2025-12-05', '09:30:00', 'Completed', NULL),
    (38, 6,  3, 5,  '2025-12-08', '14:00:00', 'Completed', NULL),
    (39, 7,  2, 3,  '2025-12-10', '10:30:00', 'Completed', NULL),
    (40, 9,  1, 11, '2025-12-12', '09:00:00', 'Completed', NULL),
    (41, 10, 3, 12, '2025-12-15', '14:30:00', 'Completed', NULL),
    (42, 11, 2, 7,  '2025-12-17', '11:00:00', 'Completed', NULL),
    (43, 14, 1, 1,  '2025-12-19', '09:00:00', 'Completed', NULL),
    (44, 15, 3, 8,  '2025-12-22', '14:00:00', 'Completed', NULL),
    (45, 2,  2, 2,  '2025-12-24', '10:00:00', 'Cancelled', 'Holiday conflict'),

    -- ── January 2026 ──
    (46, 1,  1, 10, '2026-01-06', '09:00:00', 'Completed', NULL),
    (47, 3,  2, 9,  '2026-01-08', '10:00:00', 'Completed', NULL),
    (48, 5,  3, 5,  '2026-01-10', '14:00:00', 'Completed', NULL),
    (49, 6,  1, 1,  '2026-01-13', '09:30:00', 'Completed', NULL),
    (50, 7,  2, 3,  '2026-01-15', '10:30:00', 'Completed', NULL),
    (51, 9,  1, 6,  '2026-01-17', '09:00:00', 'Completed', NULL),
    (52, 10, 3, 7,  '2026-01-20', '14:00:00', 'Completed', NULL),
    (53, 12, 2, 8,  '2026-01-22', '10:00:00', 'Completed', NULL),
    (54, 11, 1, 13, '2026-01-24', '09:00:00', 'Completed', NULL),
    (55, 16, 3, 12, '2026-01-27', '14:30:00', 'Completed', NULL),
    (56, 2,  2, 2,  '2026-01-29', '10:00:00', 'Completed', NULL),
    (57, 17, 1, 1,  '2026-01-31', '09:00:00', 'Completed', NULL),
    (58, 4,  3, 9,  '2026-01-14', '14:00:00', 'Cancelled', 'Schedule conflict'),

    -- ── February 2026 ──
    (59, 1,  1, 1,  '2026-02-03', '09:00:00', 'Completed', NULL),
    (60, 3,  2, 2,  '2026-02-05', '10:00:00', 'Completed', NULL),
    (61, 5,  1, 9,  '2026-02-07', '09:30:00', 'Completed', NULL),
    (62, 6,  3, 5,  '2026-02-10', '14:00:00', 'Completed', NULL),
    (63, 7,  2, 6,  '2026-02-12', '10:30:00', 'Completed', NULL),
    (64, 9,  1, 3,  '2026-02-14', '09:00:00', 'Completed', NULL),
    (65, 10, 3, 7,  '2026-02-17', '14:00:00', 'Completed', NULL),
    (66, 12, 2, 8,  '2026-02-19', '10:00:00', 'Completed', NULL),
    (67, 2,  1, 10, '2026-02-21', '09:30:00', 'Completed', NULL),
    (68, 11, 2, 13, '2026-02-21', '11:00:00', 'Completed', NULL),
    -- Today (Feb 25, 2026)
    (69, 1,  1, 1,  '2026-02-25', '09:00:00', 'Confirmed', NULL),
    (70, 2,  2, 2,  '2026-02-25', '09:30:00', 'Confirmed', NULL),
    (71, 3,  1, 11, '2026-02-25', '10:00:00', 'Pending',   NULL),
    (72, 4,  3, 5,  '2026-02-25', '10:30:00', 'Confirmed', NULL),
    (73, 5,  2, 9,  '2026-02-25', '11:00:00', 'Pending',   NULL),
    -- Tomorrow
    (74, 6,  1, 10, '2026-02-26', '08:30:00', 'Confirmed', NULL),
    (75, 7,  3, 12, '2026-02-26', '09:00:00', 'Pending',   NULL),
    (76, 12, 2, 9,  '2026-02-26', '10:00:00', 'Confirmed', NULL),
    -- Later this week
    (77, 15, 1, 1,  '2026-02-27', '09:00:00', 'Confirmed', NULL),
    (78, 16, 2, 7,  '2026-02-27', '10:00:00', 'Pending',   NULL),
    (79, 19, 3, 5,  '2026-02-28', '14:00:00', 'Confirmed', NULL),
    -- Cancelled this month
    (80, 18, 1, 9,  '2026-02-20', '09:00:00', 'Cancelled', 'Patient feeling better');


-- ────────────────────────────────────────────────────────────
-- QUEUE ENTRIES  (today)
-- ────────────────────────────────────────────────────────────

INSERT INTO queue_entries (patient_id, doctor_id, appointment_id, queue_time, purpose, status, created_at) VALUES
    (1, 1, 69, '09:00:00', 'General Checkup',    'Waiting',     '2026-02-25'),
    (2, 2, 70, '09:30:00', 'Follow-up Visit',    'In Progress', '2026-02-25'),
    (3, 1, 71, '10:00:00', 'Lab Results Review',  'Waiting',     '2026-02-25'),
    (4, 3, 72, '10:30:00', 'Dental Cleaning',     'Waiting',     '2026-02-25');


-- ────────────────────────────────────────────────────────────
-- INVOICES  (tied to completed appointments)
-- ────────────────────────────────────────────────────────────

INSERT INTO invoices (invoice_id, patient_id, appointment_id, method_id, discount_percent, total_amount, amount_paid, status, created_at) VALUES
    -- Sep 2025
    (1,  1,  1,  1, 0.00,   800.00,   800.00, 'Paid',    '2025-09-02 09:30:00'),
    (2,  2,  2,  3, 0.00,   500.00,   500.00, 'Paid',    '2025-09-05 10:30:00'),
    (3,  3,  3,  2, 0.00,   500.00,   500.00, 'Paid',    '2025-09-08 10:00:00'),
    (4,  5,  4,  5, 0.00,  2500.00,  2500.00, 'Paid',    '2025-09-10 14:30:00'),
    (5,  6,  5,  1, 0.00,  1500.00,  1500.00, 'Paid',    '2025-09-12 11:30:00'),
    (6,  7,  6,  2, 0.00,  1200.00,  1200.00, 'Paid',    '2025-09-15 09:30:00'),
    (7,  9,  7,  4, 0.00,  1000.00,  1000.00, 'Paid',    '2025-09-18 11:00:00'),
    (8,  10, 8,  1, 0.00,  1800.00,  1800.00, 'Paid',    '2025-09-22 14:30:00'),
    (9,  11, 10, 3, 0.00,  1000.00,  1000.00, 'Paid',    '2025-09-28 11:30:00'),
    -- Oct 2025
    (10, 1,  11, 1, 0.00,   300.00,   300.00, 'Paid',    '2025-10-01 10:00:00'),
    (11, 3,  12, 3, 0.00,   500.00,   500.00, 'Paid',    '2025-10-03 10:30:00'),
    (12, 5,  13, 2, 0.00,   800.00,   800.00, 'Paid',    '2025-10-06 09:30:00'),
    (13, 6,  14, 1, 0.00,   800.00,   800.00, 'Paid',    '2025-10-08 14:30:00'),
    (14, 7,  15, 5, 0.00,   500.00,   500.00, 'Paid',    '2025-10-10 11:30:00'),
    (15, 9,  16, 4, 0.00,  1200.00,  1200.00, 'Paid',    '2025-10-13 09:30:00'),
    (16, 10, 17, 1, 0.00,  2500.00,  2500.00, 'Paid',    '2025-10-15 15:00:00'),
    (17, 12, 18, 2, 0.00,  1500.00,  1500.00, 'Paid',    '2025-10-17 10:30:00'),
    (18, 2,  19, 3, 0.00,  1200.00,  1200.00, 'Paid',    '2025-10-20 10:00:00'),
    (19, 11, 20, 1, 0.00,  1000.00,  1000.00, 'Paid',    '2025-10-22 11:30:00'),
    (20, 15, 22, 5, 0.00,  1000.00,  1000.00, 'Paid',    '2025-10-28 09:30:00'),
    -- Nov 2025
    (21, 1,  23, 1, 0.00,   500.00,   500.00, 'Paid',    '2025-11-03 10:30:00'),
    (22, 3,  24, 2, 0.00,   800.00,   800.00, 'Paid',    '2025-11-05 09:30:00'),
    (23, 5,  25, 5, 0.00,  1000.00,  1000.00, 'Paid',    '2025-11-07 14:30:00'),
    (24, 7,  26, 3, 0.00,   500.00,   500.00, 'Paid',    '2025-11-10 11:00:00'),
    (25, 6,  27, 1, 0.00,  1500.00,  1500.00, 'Paid',    '2025-11-12 09:30:00'),
    (26, 9,  28, 4, 0.00,  2500.00,  2500.00, 'Paid',    '2025-11-14 15:00:00'),
    (27, 10, 29, 2, 0.00,  1800.00,  1800.00, 'Paid',    '2025-11-17 10:30:00'),
    (28, 12, 30, 1, 0.00,  1200.00,  1200.00, 'Paid',    '2025-11-19 10:00:00'),
    (29, 2,  31, 3, 0.00,  1000.00,  1000.00, 'Paid',    '2025-11-21 11:30:00'),
    (30, 16, 32, 5, 0.00,  1200.00,  1200.00, 'Paid',    '2025-11-24 09:30:00'),
    (31, 13, 33, 1, 0.00,   800.00,   800.00, 'Paid',    '2025-11-26 14:30:00'),
    -- Dec 2025
    (32, 1,  35, 1, 0.00,   800.00,   800.00, 'Paid',    '2025-12-01 09:30:00'),
    (33, 3,  36, 3, 0.00,  1500.00,  1500.00, 'Paid',    '2025-12-03 10:30:00'),
    (34, 5,  37, 2, 0.00,   500.00,   500.00, 'Paid',    '2025-12-05 10:00:00'),
    (35, 6,  38, 5, 0.00,  2500.00,  2500.00, 'Paid',    '2025-12-08 14:30:00'),
    (36, 7,  39, 4, 0.00,  1200.00,  1200.00, 'Paid',    '2025-12-10 11:00:00'),
    (37, 9,  40, 1, 0.00,   300.00,   300.00, 'Paid',    '2025-12-12 09:30:00'),
    (38, 10, 41, 2, 0.00,   800.00,   800.00, 'Paid',    '2025-12-15 15:00:00'),
    (39, 11, 42, 3, 0.00,  1000.00,  1000.00, 'Paid',    '2025-12-17 11:30:00'),
    (40, 14, 43, 1, 0.00,   800.00,   800.00, 'Paid',    '2025-12-19 09:30:00'),
    (41, 15, 44, 5, 0.00,  1800.00,  1800.00, 'Paid',    '2025-12-22 14:30:00'),
    -- Jan 2026
    (42, 1,  46, 1, 0.00,  1200.00,  1200.00, 'Paid',    '2026-01-06 09:30:00'),
    (43, 3,  47, 3, 0.00,   500.00,   500.00, 'Paid',    '2026-01-08 10:30:00'),
    (44, 5,  48, 5, 0.00,  2500.00,  2500.00, 'Paid',    '2026-01-10 14:30:00'),
    (45, 6,  49, 1, 0.00,   800.00,   800.00, 'Paid',    '2026-01-13 10:00:00'),
    (46, 7,  50, 2, 0.00,  1200.00,  1200.00, 'Paid',    '2026-01-15 11:00:00'),
    (47, 9,  51, 1, 0.00,  1500.00,  1500.00, 'Paid',    '2026-01-17 09:30:00'),
    (48, 10, 52, 4, 0.00,  1000.00,  1000.00, 'Paid',    '2026-01-20 14:30:00'),
    (49, 12, 53, 2, 0.00,  1800.00,  1800.00, 'Paid',    '2026-01-22 10:30:00'),
    (50, 11, 54, 3, 0.00,  1000.00,  1000.00, 'Paid',    '2026-01-24 09:30:00'),
    (51, 16, 55, 5, 0.00,   800.00,   800.00, 'Paid',    '2026-01-27 15:00:00'),
    (52, 2,  56, 1, 0.00,   500.00,   500.00, 'Paid',    '2026-01-29 10:30:00'),
    (53, 17, 57, 4, 0.00,   800.00,   800.00, 'Paid',    '2026-01-31 09:30:00'),
    -- Feb 2026 (completed so far)
    (54, 1,  59, 1, 0.00,   800.00,   800.00, 'Paid',    '2026-02-03 09:30:00'),
    (55, 3,  60, 3, 0.00,   500.00,   500.00, 'Paid',    '2026-02-05 10:30:00'),
    (56, 5,  61, 2, 0.00,   500.00,   500.00, 'Paid',    '2026-02-07 10:00:00'),
    (57, 6,  62, 5, 0.00,  2500.00,  2500.00, 'Paid',    '2026-02-10 14:30:00'),
    (58, 7,  63, 4, 0.00,  1500.00,  1500.00, 'Paid',    '2026-02-12 11:00:00'),
    (59, 9,  64, 1, 0.00,  1200.00,  1200.00, 'Paid',    '2026-02-14 09:30:00'),
    (60, 10, 65, 2, 0.00,  1000.00,  1000.00, 'Paid',    '2026-02-17 14:30:00'),
    (61, 12, 66, 3, 0.00,  1800.00,  1800.00, 'Paid',    '2026-02-19 10:30:00'),
    (62, 2,  67, 1, 0.00,  1200.00,  1200.00, 'Paid',    '2026-02-21 10:00:00'),
    (63, 11, 68, 5, 0.00,  1000.00,  1000.00, 'Paid',    '2026-02-21 11:30:00'),
    -- Today's invoices (unpaid / partial)
    (64, 1,  69, 1, 0.00,   800.00,   800.00, 'Paid',    '2026-02-25 09:30:00'),
    (65, 2,  70, NULL, 0.00, 500.00,    0.00, 'Unpaid',  '2026-02-25 10:00:00'),
    (66, 4,  72, 5, 0.00,  2500.00,  1000.00, 'Partial', '2026-02-25 11:00:00');


-- ────────────────────────────────────────────────────────────
-- INVOICE ITEMS
-- ────────────────────────────────────────────────────────────

INSERT INTO invoice_items (invoice_id, service_id, quantity, unit_price, subtotal) VALUES
    (1,  1,  1,  800.00,   800.00),
    (2,  2,  1,  500.00,   500.00),
    (3,  9,  1,  500.00,   500.00),
    (4,  5,  1,  2500.00,  2500.00),
    (5,  6,  1,  1500.00,  1500.00),
    (6,  3,  1,  1200.00,  1200.00),
    (7,  7,  1,  1000.00,  1000.00),
    (8,  8,  1,  1800.00,  1800.00),
    (9,  13, 1,  1000.00,  1000.00),
    (10, 11, 1,   300.00,   300.00),
    (11, 2,  1,   500.00,   500.00),
    (12, 1,  1,   800.00,   800.00),
    (13, 12, 1,   800.00,   800.00),
    (14, 9,  1,   500.00,   500.00),
    (15, 3,  1,  1200.00,  1200.00),
    (16, 5,  1,  2500.00,  2500.00),
    (17, 6,  1,  1500.00,  1500.00),
    (18, 10, 1,  1200.00,  1200.00),
    (19, 7,  1,  1000.00,  1000.00),
    (20, 13, 1,  1000.00,  1000.00),
    (21, 2,  1,   500.00,   500.00),
    (22, 1,  1,   800.00,   800.00),
    (23, 7,  1,  1000.00,  1000.00),
    (24, 9,  1,   500.00,   500.00),
    (25, 6,  1,  1500.00,  1500.00),
    (26, 5,  1,  2500.00,  2500.00),
    (27, 8,  1,  1800.00,  1800.00),
    (28, 3,  1,  1200.00,  1200.00),
    (29, 13, 1,  1000.00,  1000.00),
    (30, 10, 1,  1200.00,  1200.00),
    (31, 1,  1,   800.00,   800.00),
    (32, 1,  1,   800.00,   800.00),
    (33, 6,  1,  1500.00,  1500.00),
    (34, 9,  1,   500.00,   500.00),
    (35, 5,  1,  2500.00,  2500.00),
    (36, 3,  1,  1200.00,  1200.00),
    (37, 11, 1,   300.00,   300.00),
    (38, 12, 1,   800.00,   800.00),
    (39, 7,  1,  1000.00,  1000.00),
    (40, 1,  1,   800.00,   800.00),
    (41, 8,  1,  1800.00,  1800.00),
    (42, 10, 1,  1200.00,  1200.00),
    (43, 9,  1,   500.00,   500.00),
    (44, 5,  1,  2500.00,  2500.00),
    (45, 1,  1,   800.00,   800.00),
    (46, 3,  1,  1200.00,  1200.00),
    (47, 6,  1,  1500.00,  1500.00),
    (48, 7,  1,  1000.00,  1000.00),
    (49, 8,  1,  1800.00,  1800.00),
    (50, 13, 1,  1000.00,  1000.00),
    (51, 12, 1,   800.00,   800.00),
    (52, 2,  1,   500.00,   500.00),
    (53, 1,  1,   800.00,   800.00),
    (54, 1,  1,   800.00,   800.00),
    (55, 2,  1,   500.00,   500.00),
    (56, 9,  1,   500.00,   500.00),
    (57, 5,  1,  2500.00,  2500.00),
    (58, 6,  1,  1500.00,  1500.00),
    (59, 3,  1,  1200.00,  1200.00),
    (60, 7,  1,  1000.00,  1000.00),
    (61, 8,  1,  1800.00,  1800.00),
    (62, 10, 1,  1200.00,  1200.00),
    (63, 13, 1,  1000.00,  1000.00),
    (64, 1,  1,   800.00,   800.00),
    (65, 2,  1,   500.00,   500.00),
    (66, 5,  1,  2500.00,  2500.00);


-- ────────────────────────────────────────────────────────────
-- ACTIVITY LOG  (seed a few entries)
-- ────────────────────────────────────────────────────────────

INSERT INTO activity_log (user_email, user_role, action, record_type, record_detail, created_at) VALUES
    ('admin@carecrud.com',     'Admin',  'Login',   'User',        'Carlo Santos logged in',               '2026-02-25 08:00:00'),
    ('admin@carecrud.com',     'Admin',  'Created', 'Patient',     'Added patient Diana Castro (ID 19)',   '2026-02-24 09:15:00'),
    ('ana.reyes@carecrud.com', 'Doctor', 'Login',   'User',        'Ana Reyes logged in',                  '2026-02-25 08:30:00'),
    ('ana.reyes@carecrud.com', 'Doctor', 'Edited',  'Appointment', 'Updated appointment #69 status',       '2026-02-25 09:05:00'),
    ('james.cruz@carecrud.com','Receptionist','Created','Appointment','Created appointment #79 for Diana Castro','2026-02-24 14:00:00');
