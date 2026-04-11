CREATE DATABASE IF NOT EXISTS fire_training
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE fire_training;

SET time_zone = '+00:00';

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME(6) NULL,
    can_switch_role TINYINT(1) NULL DEFAULT 0,
    original_role VARCHAR(20) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS training_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    training_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    total_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    step_scores JSON NULL,
    video_path VARCHAR(255) NULL,
    duration_seconds DECIMAL(8, 2) NULL,
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    feedback TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT fk_training_records_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_training_records_user_id_created_at (user_id, created_at),
    INDEX idx_training_records_status_created_at (status, created_at)
);

CREATE TABLE IF NOT EXISTS action_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    record_id INT NOT NULL,
    action_name VARCHAR(50) NOT NULL,
    step_index SMALLINT NOT NULL,
    is_correct TINYINT(1) NOT NULL,
    confidence_score DECIMAL(5, 4) NULL,
    action_timestamp DATETIME(6) NOT NULL,
    detail JSON NULL,
    CONSTRAINT fk_action_logs_record_id_training_records
        FOREIGN KEY (record_id) REFERENCES training_records(id)
        ON DELETE CASCADE,
    INDEX idx_action_logs_record_id_step_index (record_id, step_index),
    INDEX idx_action_logs_action_timestamp (action_timestamp)
);

CREATE TABLE IF NOT EXISTS training_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_trainings INT NOT NULL DEFAULT 0,
    completed_trainings INT NOT NULL DEFAULT 0,
    total_training_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    average_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    best_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    last_training_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT uq_training_statistics_user_id UNIQUE (user_id),
    CONSTRAINT fk_training_statistics_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- 管理员操作日志表
CREATE TABLE IF NOT EXISTS admin_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NULL,
    target_id INT NULL,
    details JSON NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_logs_admin_id_users
        FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_admin_logs_admin_id (admin_id),
    INDEX idx_admin_logs_created_at (created_at)
);

-- 视频检测任务表
CREATE TABLE IF NOT EXISTS video_detection_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uploader_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    ai_result JSON NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    CONSTRAINT fk_video_detection_tasks_uploader_id_users
        FOREIGN KEY (uploader_id) REFERENCES users(id),
    INDEX idx_video_detection_tasks_uploader_id (uploader_id),
    INDEX idx_video_detection_tasks_status (status),
    INDEX idx_video_detection_tasks_created_at (created_at)
);
