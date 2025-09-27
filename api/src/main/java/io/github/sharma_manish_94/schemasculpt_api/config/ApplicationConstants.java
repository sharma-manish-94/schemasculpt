package io.github.sharma_manish_94.schemasculpt_api.config;

import java.time.Duration;

/**
 * Application-wide constants.
 */
public final class ApplicationConstants {

    // Session Management
    public static final Duration DEFAULT_SESSION_TTL = Duration.ofHours(1);
    public static final String SESSION_KEY_PREFIX = "schemasculpt:session:";

    // Error Messages
    public static final String SESSION_NOT_FOUND_MESSAGE = "Session not found";
    public static final String INVALID_SPEC_MESSAGE = "Invalid specification provided";
    public static final String SPEC_PARSING_FAILED_MESSAGE = "Failed to parse specification";
    public static final String EMPTY_SPEC_MESSAGE = "Specification content cannot be empty";

    // API Paths
    public static final String API_V1_BASE = "/api/v1";
    public static final String SESSIONS_PATH = "/sessions";
    public static final String MOCK_PATH = "/mock";
    public static final String PROXY_PATH = "/proxy";

    // Default Values
    public static final String DEFAULT_AI_SERVICE_URL = "http://localhost:8000";
    public static final int DEFAULT_SESSION_TIMEOUT_SECONDS = 30;

    // Validation Constants
    public static final int MAX_SPEC_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
    public static final int MIN_SESSION_ID_LENGTH = 10;
    public static final int MAX_SESSION_ID_LENGTH = 100;
    public static final String AGENT_NAME = "agent_name";
    public static final String STATUS = "status";
    public static final String LAST_UPDATED = "last_updated";
    public static final String UNKNOWN = "unknown";
    public static final String MESSAGE = "message";
    public static final String TIMESTAMP = "timestamp";

    private ApplicationConstants() {
        // Private constructor to prevent instantiation
    }
}