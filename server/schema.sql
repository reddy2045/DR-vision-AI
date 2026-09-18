CREATE TABLE IF NOT EXISTS api_users (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(80) NOT NULL DEFAULT 'PHC Worker',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS api_patients (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL DEFAULT '',
    patient_id VARCHAR(20) NOT NULL UNIQUE,
    age TINYINT UNSIGNED NOT NULL,
    gender ENUM('M', 'F', 'O') NOT NULL,
    diabetes_duration DECIMAL(4,1) NOT NULL DEFAULT 0,
    hba1c DECIMAL(4,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS api_screenings (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    patient_id BIGINT UNSIGNED NOT NULL,
    eye_side ENUM('OD', 'OS') NOT NULL DEFAULT 'OD',
    fundus_path VARCHAR(500) NOT NULL,
    gradcam_path VARCHAR(500) NULL,
    predicted_class VARCHAR(30) NOT NULL,
    dr_level TINYINT UNSIGNED NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    referable BOOLEAN NOT NULL,
    low_confidence BOOLEAN NOT NULL,
    quality_passed BOOLEAN NOT NULL,
    quality_metrics JSON NOT NULL,
    quality_message VARCHAR(255) NOT NULL,
    referral_urgency ENUM('routine', 'priority', 'urgent') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_api_screenings_patient FOREIGN KEY (patient_id) REFERENCES api_patients(id) ON DELETE CASCADE,
    INDEX idx_api_screenings_patient_created (patient_id, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;