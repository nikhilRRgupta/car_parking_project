-- ============================================================================
-- Smart Vehicle Parking Management System - Database Schema (MySQL 8.0+)
-- ============================================================================

CREATE DATABASE IF NOT EXISTS smart_parking_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_parking_db;

-- 1. USERS & ROLES TABLE
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'attendant', 'customer') DEFAULT 'customer' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_email (email),
    INDEX idx_user_role (role)
) ENGINE=InnoDB;

-- 2. VEHICLES TABLE
CREATE TABLE IF NOT EXISTS vehicles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type ENUM('2-wheeler', '4-wheeler', 'ev') NOT NULL,
    model_name VARCHAR(100) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_plate (plate_number)
) ENGINE=InnoDB;

-- 3. PRICING RULES TABLE
CREATE TABLE IF NOT EXISTS pricing_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_type ENUM('2-wheeler', '4-wheeler', 'ev') UNIQUE NOT NULL,
    base_hours INT DEFAULT 4 NOT NULL,
    base_rate DECIMAL(10, 2) NOT NULL,
    hourly_rate_after_base DECIMAL(10, 2) NOT NULL,
    grace_period_minutes INT DEFAULT 15 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. PARKING SLOTS TABLE
CREATE TABLE IF NOT EXISTS parking_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot_number VARCHAR(20) UNIQUE NOT NULL,
    floor_zone VARCHAR(50) NOT NULL,
    vehicle_type ENUM('2-wheeler', '4-wheeler', 'ev') NOT NULL,
    is_ev BOOLEAN DEFAULT FALSE NOT NULL,
    status ENUM('AVAILABLE', 'RESERVED', 'OCCUPIED', 'MAINTENANCE') DEFAULT 'AVAILABLE' NOT NULL,
    current_booking_id INT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_slot_status (status),
    INDEX idx_slot_type (vehicle_type)
) ENGINE=InnoDB;

-- 5. BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_code VARCHAR(32) UNIQUE NOT NULL,
    user_id INT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    vehicle_type ENUM('2-wheeler', '4-wheeler', 'ev') NOT NULL,
    slot_id INT NOT NULL,
    customer_name VARCHAR(120) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(120) NOT NULL,
    expected_start_time DATETIME NOT NULL,
    expected_end_time DATETIME NOT NULL,
    base_hours INT DEFAULT 4 NOT NULL,
    base_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('PENDING_PAYMENT', 'CONFIRMED', 'ACTIVE', 'COMPLETED', 'CANCELLED', 'EXPIRED') DEFAULT 'PENDING_PAYMENT' NOT NULL,
    qr_token VARCHAR(255) NOT NULL,
    expires_at DATETIME NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (slot_id) REFERENCES parking_slots(id) ON DELETE RESTRICT,
    INDEX idx_booking_code (booking_code),
    INDEX idx_booking_status (status),
    INDEX idx_booking_vehicle (vehicle_number)
) ENGINE=InnoDB;

-- 6. PARKING SESSIONS TABLE (Active / Completed Stays)
CREATE TABLE IF NOT EXISTS parking_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT UNIQUE NOT NULL,
    slot_id INT NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    entry_time DATETIME NOT NULL,
    exit_time DATETIME NULL,
    total_duration_minutes INT DEFAULT 0,
    prepaid_amount DECIMAL(10, 2) NOT NULL,
    extra_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    status ENUM('IN_PROGRESS', 'COMPLETED') DEFAULT 'IN_PROGRESS' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (slot_id) REFERENCES parking_slots(id) ON DELETE RESTRICT,
    INDEX idx_session_status (status),
    INDEX idx_session_vehicle (vehicle_number)
) ENGINE=InnoDB;

-- 7. PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    booking_id INT NOT NULL,
    session_id INT NULL,
    payment_type ENUM('PREPAID', 'EXIT_OVERSTAY') NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method ENUM('CARD', 'UPI', 'NET_BANKING', 'CASH_KIOSK') NOT NULL,
    transaction_ref VARCHAR(64) UNIQUE NOT NULL,
    gateway_status ENUM('SUCCESS', 'FAILED', 'PENDING') DEFAULT 'SUCCESS' NOT NULL,
    payment_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES parking_sessions(id) ON DELETE SET NULL,
    INDEX idx_tx_ref (transaction_ref)
) ENGINE=InnoDB;

-- 8. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    booking_id INT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    notification_type ENUM('INFO', 'WARNING', 'ALERT', 'SUCCESS') DEFAULT 'INFO' NOT NULL,
    channel ENUM('IN_APP', 'SMS', 'EMAIL') DEFAULT 'IN_APP' NOT NULL,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
    INDEX idx_user_notif (user_id, is_read)
) ENGINE=InnoDB;

-- 9. BARRIER AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS barrier_audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    gate_type ENUM('ENTRY', 'EXIT') NOT NULL,
    vehicle_number VARCHAR(20) NOT NULL,
    booking_code VARCHAR(32) NULL,
    action ENUM('OPEN', 'DENY', 'MANUAL_OVERRIDE') NOT NULL,
    reason VARCHAR(255) NOT NULL,
    operator_name VARCHAR(100) DEFAULT 'System Automated' NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_time (timestamp),
    INDEX idx_audit_gate (gate_type)
) ENGINE=InnoDB;
