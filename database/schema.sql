-- NYC Council Initiative Reporting System (PIN #102202709162026)
-- MySQL 8.0+ / InnoDB. Contract transcribed from the schema supplied for this project.
-- Do not run against a database containing data: this file creates objects only.

CREATE SCHEMA IF NOT EXISTS council_irs_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE council_irs_db;

CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(36) PRIMARY KEY,
    ein VARCHAR(10) NOT NULL,
    legal_name VARCHAR(255) NOT NULL,
    org_type ENUM('CBO', 'CITY_AGENCY') NOT NULL DEFAULT 'CBO',
    borough VARCHAR(50) NULL,
    status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_org_ein UNIQUE (ein)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS initiatives (
    id VARCHAR(36) PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    fiscal_year INT NOT NULL,
    status ENUM('ACTIVE', 'COMBINED', 'RETIRED') NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_init_fy (fiscal_year)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS initiative_relationships (
    predecessor_id VARCHAR(36) NOT NULL,
    successor_id VARCHAR(36) NOT NULL,
    relationship_type ENUM('RENAMED', 'COMBINED') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (predecessor_id, successor_id, relationship_type),
    CONSTRAINT fk_rel_pred FOREIGN KEY (predecessor_id) REFERENCES initiatives(id) ON DELETE RESTRICT,
    CONSTRAINT fk_rel_succ FOREIGN KEY (successor_id) REFERENCES initiatives(id) ON DELETE RESTRICT,
    CONSTRAINT chk_rel_distinct CHECK (predecessor_id <> successor_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS reporting_cycles (
    id VARCHAR(36) NOT NULL,
    initiative_id VARCHAR(36) NOT NULL,
    cycle_name VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status ENUM('UPCOMING', 'OPEN', 'CLOSED') NOT NULL DEFAULT 'UPCOMING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT uq_cycle_init UNIQUE (initiative_id, id),
    CONSTRAINT uq_cycle_name UNIQUE (initiative_id, cycle_name),
    CONSTRAINT chk_cycle_dates CHECK (start_date <= due_date),
    CONSTRAINT fk_cycle_init FOREIGN KEY (initiative_id) REFERENCES initiatives(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS initiative_organizations (
    initiative_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    awarded_amount DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (initiative_id, organization_id),
    CONSTRAINT fk_io_initiative FOREIGN KEY (initiative_id) REFERENCES initiatives(id) ON DELETE RESTRICT,
    CONSTRAINT fk_io_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS form_templates (
    id VARCHAR(36) PRIMARY KEY,
    initiative_id VARCHAR(36) NOT NULL,
    version INT NOT NULL DEFAULT 1,
    schema_definition JSON NOT NULL,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_form_template_version UNIQUE (initiative_id, version),
    CONSTRAINT fk_form_init FOREIGN KEY (initiative_id) REFERENCES initiatives(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role ENUM('COUNCIL_ADMIN', 'COUNCIL_REVIEWER', 'EXTERNAL_SUBMITTER', 'VIEW_ONLY') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_role (role)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS user_organizations (
    user_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, organization_id),
    CONSTRAINT fk_uo_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_uo_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS submissions (
    id VARCHAR(36) PRIMARY KEY,
    initiative_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    cycle_id VARCHAR(36) NOT NULL,
    template_version INT NOT NULL,
    status ENUM('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'REVISION_REQUESTED', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'DRAFT',
    form_data JSON NOT NULL,
    allocated_budget DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    total_budget DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    is_balanced BOOLEAN NOT NULL DEFAULT FALSE,
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_sub_cycle_init FOREIGN KEY (initiative_id, cycle_id)
        REFERENCES reporting_cycles (initiative_id, id) ON DELETE RESTRICT,
    CONSTRAINT fk_sub_init_org FOREIGN KEY (initiative_id, organization_id)
        REFERENCES initiative_organizations (initiative_id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_sub_form_template FOREIGN KEY (initiative_id, template_version)
        REFERENCES form_templates (initiative_id, version) ON DELETE RESTRICT,
    CONSTRAINT uq_sub_id_template UNIQUE (id, template_version),
    CONSTRAINT fk_sub_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT uq_sub_instance UNIQUE (initiative_id, organization_id, cycle_id),
    INDEX idx_sub_triage (is_balanced, status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS budget_line_items (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL,
    line_number INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    description VARCHAR(500) NULL,
    budgeted_amount DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    actual_amount DECIMAL(14, 2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_line_item UNIQUE (submission_id, line_number),
    CONSTRAINT chk_line_number CHECK (line_number BETWEEN 1 AND 100),
    CONSTRAINT fk_line_item_sub FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS submission_versions (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL,
    version_number INT NOT NULL,
    template_version INT NOT NULL,
    form_snapshot JSON NOT NULL,
    budget_snapshot JSON NOT NULL,
    submitted_by VARCHAR(36) NOT NULL,
    reviewer_notes TEXT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sub_ver UNIQUE (submission_id, version_number),
    CONSTRAINT fk_ver_sub_template FOREIGN KEY (submission_id, template_version)
        REFERENCES submissions (id, template_version) ON DELETE RESTRICT,
    CONSTRAINT fk_ver_user FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS attachments (
    id VARCHAR(36) PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL,
    bucket_name VARCHAR(100) NOT NULL,
    object_key VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    content_type VARCHAR(150) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    checksum_sha256 CHAR(64) NULL,
    uploaded_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_attachment_location UNIQUE (bucket_name, object_key),
    CONSTRAINT fk_att_sub FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE RESTRICT,
    CONSTRAINT fk_att_user FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT chk_att_size CHECK (file_size_bytes > 0 AND file_size_bytes <= 26214400)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    submission_id VARCHAR(36) NOT NULL,
    action VARCHAR(100) NOT NULL,
    actor_id VARCHAR(36) NOT NULL,
    actor_role VARCHAR(50) NOT NULL,
    state_diff JSON NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_sub (submission_id),
    INDEX idx_audit_time (created_at),
    CONSTRAINT fk_audit_sub FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

DELIMITER //

CREATE TRIGGER trg_prevent_published_template_update
BEFORE UPDATE ON form_templates
FOR EACH ROW
BEGIN
    IF OLD.is_published = TRUE AND NEW.is_published = TRUE AND OLD.schema_definition <> NEW.schema_definition THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Policy violation: Cannot modify a published form template schema. Provision a new template version.';
    END IF;
END;
//

CREATE TRIGGER trg_audit_logs_no_update
BEFORE UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Policy violation: Audit logs are immutable and cannot be updated.';
END;
//

CREATE TRIGGER trg_audit_logs_no_delete
BEFORE DELETE ON audit_logs
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Policy violation: Audit logs are retained in perpetuity and cannot be deleted.';
END;
//

CREATE TRIGGER trg_submission_versions_immutable
BEFORE UPDATE ON submission_versions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Policy violation: Historical submission snapshots are immutable.';
END;
//

CREATE TRIGGER trg_submission_versions_no_delete
BEFORE DELETE ON submission_versions
FOR EACH ROW
BEGIN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Policy violation: Historical submission versions cannot be deleted.';
END;
//

CREATE TRIGGER trg_single_primary_user_org_insert
BEFORE INSERT ON user_organizations
FOR EACH ROW
BEGIN
    IF NEW.is_primary = TRUE AND (SELECT COUNT(*) FROM user_organizations WHERE user_id = NEW.user_id AND is_primary = TRUE) > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Constraint violation: User can only have one primary organization.';
    END IF;
END;
//

CREATE TRIGGER trg_single_primary_user_org_update
BEFORE UPDATE ON user_organizations
FOR EACH ROW
BEGIN
    IF NEW.is_primary = TRUE AND OLD.is_primary = FALSE AND (SELECT COUNT(*) FROM user_organizations WHERE user_id = NEW.user_id AND is_primary = TRUE) > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Constraint violation: User can only have one primary organization.';
    END IF;
END;
//

DELIMITER ;
