-- ============================================================
-- CareCRUD V2 – Drop All Data (keep schema intact)
-- Clears all transactional data. Keeps the admin account
-- and lookup tables (roles, departments, services, payment methods,
-- standard_conditions).
-- ============================================================

USE carecrud_db;

-- Delete in child-to-parent order so FK constraints are satisfied
DELETE FROM invoice_items;
DELETE FROM invoices;
DELETE FROM queue_entries;
DELETE FROM appointments;
DELETE FROM patient_conditions;
DELETE FROM patients;
DELETE FROM employees;
DELETE FROM activity_log;
DELETE FROM user_preferences;

-- Keep the admin account (role_id = 5), delete everyone else
DELETE FROM users WHERE role_id != 5;

-- After running this, all transactional and V2 audit data is cleared.
-- The admin account, lookup tables, and standard_conditions remain intact.
