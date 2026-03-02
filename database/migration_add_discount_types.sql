-- Migration: Add discount_types table and link to patients
-- Run this on an existing carecrud_db to add discount support.

USE carecrud_db;

-- Create discount_types table
CREATE TABLE IF NOT EXISTS discount_types (
    discount_id      INT AUTO_INCREMENT PRIMARY KEY,
    type_name        VARCHAR(100) NOT NULL UNIQUE,
    discount_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    legal_basis      VARCHAR(255) DEFAULT '',
    is_active        TINYINT(1) NOT NULL DEFAULT 1
);

-- Add discount_type_id column to patients (if not exists)
SET @col_exists = (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'carecrud_db' AND TABLE_NAME = 'patients' AND COLUMN_NAME = 'discount_type_id');

SET @sql = IF(@col_exists = 0,
    'ALTER TABLE patients ADD COLUMN discount_type_id INT DEFAULT NULL AFTER blood_type, ADD FOREIGN KEY (discount_type_id) REFERENCES discount_types(discount_id) ON DELETE SET NULL',
    'SELECT 1');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Seed default discount types (based on Philippine law)
INSERT IGNORE INTO discount_types (type_name, discount_percent, legal_basis) VALUES
    ('Senior Citizen', 20.00, 'RA 9994 – Expanded Senior Citizens Act of 2010'),
    ('PWD',            20.00, 'RA 10754 – Act Expanding Benefits and Privileges of Persons with Disability'),
    ('Pregnant',        0.00, 'Courtesy discount – configurable by admin');
