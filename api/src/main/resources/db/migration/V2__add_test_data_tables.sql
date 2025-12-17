-- V2__add_test_data_tables.sql
-- Add tables for persisting generated test cases and mock data

-- Create operation_test_cases table
-- Stores generated test cases for specific API operations
CREATE TABLE operation_test_cases
(
    id                BIGSERIAL PRIMARY KEY,
    project_id        BIGINT       NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    specification_id  BIGINT       REFERENCES specifications (id) ON DELETE SET NULL,

    -- Operation identification
    path              VARCHAR(500) NOT NULL,
    method            VARCHAR(10)  NOT NULL,
    operation_summary TEXT,

    -- Test case data
    test_cases        JSONB        NOT NULL,
    include_ai_tests  BOOLEAN               DEFAULT TRUE,
    total_tests       INTEGER      NOT NULL DEFAULT 0,

    -- Metadata
    spec_hash         VARCHAR(64)  NOT NULL, -- Hash of the spec to detect changes
    created_at        TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    created_by        BIGINT REFERENCES users (id),

    -- Ensure one entry per project+operation combination
    CONSTRAINT unique_project_operation_tests UNIQUE (project_id, path, method)
);

CREATE INDEX idx_operation_test_cases_project_id ON operation_test_cases (project_id);
CREATE INDEX idx_operation_test_cases_spec_id ON operation_test_cases (specification_id);
CREATE INDEX idx_operation_test_cases_composite ON operation_test_cases (project_id, path, method);
CREATE INDEX idx_operation_test_cases_created_at ON operation_test_cases (created_at DESC);

-- Create operation_mock_data table
-- Stores generated mock data variations for specific API operations
CREATE TABLE operation_mock_data
(
    id               BIGSERIAL PRIMARY KEY,
    project_id       BIGINT       NOT NULL REFERENCES projects (id) ON DELETE CASCADE,
    specification_id BIGINT       REFERENCES specifications (id) ON DELETE SET NULL,

    -- Operation identification
    path             VARCHAR(500) NOT NULL,
    method           VARCHAR(10)  NOT NULL,
    response_code    VARCHAR(10)           DEFAULT '200',

    -- Mock data
    mock_variations  JSONB        NOT NULL,
    variation_count  INTEGER      NOT NULL DEFAULT 3,

    -- Metadata
    spec_hash        VARCHAR(64)  NOT NULL, -- Hash of the spec to detect changes
    created_at       TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP             DEFAULT CURRENT_TIMESTAMP,
    created_by       BIGINT REFERENCES users (id),

    -- Ensure one entry per project+operation+response combination
    CONSTRAINT unique_project_operation_mock UNIQUE (project_id, path, method, response_code)
);

CREATE INDEX idx_operation_mock_data_project_id ON operation_mock_data (project_id);
CREATE INDEX idx_operation_mock_data_spec_id ON operation_mock_data (specification_id);
CREATE INDEX idx_operation_mock_data_composite ON operation_mock_data (project_id, path, method, response_code);
CREATE INDEX idx_operation_mock_data_created_at ON operation_mock_data (created_at DESC);

-- Create test_data_generation_history table (optional - for analytics)
-- Tracks history of test data generation requests
CREATE TABLE test_data_generation_history
(
    id                 BIGSERIAL PRIMARY KEY,
    project_id         BIGINT       NOT NULL REFERENCES projects (id) ON DELETE CASCADE,

    -- Generation details
    data_type          VARCHAR(20)  NOT NULL, -- 'test_cases' or 'mock_data'
    path               VARCHAR(500) NOT NULL,
    method             VARCHAR(10)  NOT NULL,

    -- Result
    success            BOOLEAN      NOT NULL,
    error_message      TEXT,
    generation_time_ms INTEGER,

    -- Cache hit tracking
    cache_hit          BOOLEAN   DEFAULT FALSE,

    -- Metadata
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by         BIGINT REFERENCES users (id)
);

CREATE INDEX idx_test_data_history_project_id ON test_data_generation_history (project_id);
CREATE INDEX idx_test_data_history_created_at ON test_data_generation_history (created_at DESC);
CREATE INDEX idx_test_data_history_composite ON test_data_generation_history (project_id, data_type, created_at DESC);

-- Add comments for documentation
COMMENT
ON TABLE operation_test_cases IS 'Persisted test cases generated for API operations';
COMMENT
ON TABLE operation_mock_data IS 'Persisted mock data variations generated for API operations';
COMMENT
ON TABLE test_data_generation_history IS 'History of test data generation requests for analytics';

COMMENT
ON COLUMN operation_test_cases.spec_hash IS 'SHA-256 hash of the specification to detect when regeneration is needed';
COMMENT
ON COLUMN operation_test_cases.test_cases IS 'JSONB containing all generated test cases (happy path, sad path, edge cases, AI tests)';
COMMENT
ON COLUMN operation_mock_data.spec_hash IS 'SHA-256 hash of the specification to detect when regeneration is needed';
COMMENT
ON COLUMN operation_mock_data.mock_variations IS 'JSONB array containing generated mock data variations';
COMMENT
ON COLUMN test_data_generation_history.cache_hit IS 'Whether this request was served from cache (DB or in-memory)';
