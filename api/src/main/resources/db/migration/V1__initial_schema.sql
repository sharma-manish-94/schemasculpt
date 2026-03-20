-- V1__initial_schema.sql
-- Initial database schema for SchemaSculpt

-- Create users table
CREATE TABLE users
(
    id         BIGSERIAL PRIMARY KEY,
    github_id  VARCHAR(255) UNIQUE NOT NULL,
    username   VARCHAR(255)        NOT NULL,
    email      VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_github_id ON users (github_id);
CREATE INDEX idx_users_username ON users (username);

-- Create projects table
CREATE TABLE projects
(
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    is_public   BOOLEAN   DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_project_name UNIQUE (user_id, name)
);

CREATE INDEX idx_projects_user_id ON projects (user_id);
CREATE INDEX idx_projects_created_at ON projects (created_at DESC);
CREATE INDEX idx_projects_is_public ON projects (is_public);

-- Create specifications table
CREATE TABLE specifications
(
    id             BIGSERIAL PRIMARY KEY,
    project_id     BIGINT      NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    version        VARCHAR(50) NOT NULL,
    spec_content   TEXT        NOT NULL,
    spec_format    VARCHAR(10) DEFAULT 'json',
    commit_message TEXT,
    is_current     BOOLEAN     DEFAULT TRUE,
    created_at     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    created_by     BIGINT REFERENCES users (id),
    CONSTRAINT unique_project_version UNIQUE (project_id, version)
);

CREATE INDEX idx_specifications_project_id ON specifications (project_id);
CREATE INDEX idx_specifications_current ON specifications (is_current);
CREATE INDEX idx_specifications_created_at ON specifications (created_at DESC);
CREATE INDEX idx_specifications_composite ON specifications (project_id, is_current, created_at DESC);

-- Create validation_snapshots table (optional - for tracking validation history)
CREATE TABLE validation_snapshots
(
    id               BIGSERIAL PRIMARY KEY,
    specification_id BIGINT NOT NULL REFERENCES specifications (id) ON DELETE CASCADE,
    errors           JSONB,
    suggestions      JSONB,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_snapshots_spec_id ON validation_snapshots (specification_id);
CREATE INDEX idx_validation_snapshots_created_at ON validation_snapshots (created_at DESC);

-- Add comments for documentation
COMMENT
ON TABLE users IS 'GitHub authenticated users';
COMMENT
ON TABLE projects IS 'User projects containing OpenAPI specifications';
COMMENT
ON TABLE specifications IS 'Versioned OpenAPI specification content';
COMMENT
ON TABLE validation_snapshots IS 'Historical validation results for specifications';

COMMENT
ON COLUMN specifications.is_current IS 'Indicates the current/active version of the specification';
COMMENT
ON COLUMN specifications.spec_format IS 'Format of the spec: json or yaml';
