export const API_CONFIG = {
    BASE_URL: "http://localhost:8080/api/v1",
    ENDPOINTS: {
        SESSIONS: "/sessions",
        SPEC_OPERATIONS: "/sessions/{sessionId}/spec/operations",
        VALIDATION: "/validation",
        AI_SUGGEST: "/ai/suggest",
        AI_FIX: "/ai/fix",
        MOCK_SERVER: "/mock",
        MOCK_REFRESH: "/mock/{sessionId}/refresh",
        PROXY_REQUEST: "/proxy/request"
    }
};

export const UI_CONFIG = {
    PANELS: {
        NAVIGATION: "navigation",
        DETAIL: "detail",
        INSPECTOR: "inspector"
    },
    TABS: {
        VALIDATION: "validation",
        API_LAB: "apiLab",
        SWAGGER_UI: "swaggerUi"
    },
    THEMES: {
        MONACO_DARK: "vs-dark"
    }
};

export const REQUEST_CONFIG = {
    SERVER_TARGETS: {
        MOCK: "mock",
        CUSTOM: "custom"
    },
    DEFAULT_TIMEOUT: 30000,
    HTTP_METHODS: ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
};

export const MOCK_SERVER_CONFIG = {
    DEFAULT_PORT: 3001,
    HEALTH_CHECK_INTERVAL: 5000
};

export const VALIDATION_CONFIG = {
    AUTO_VALIDATE_DELAY: 500,
    MAX_SUGGESTIONS: 10
};

export const AI_CONFIG = {
    MAX_CONTEXT_LENGTH: 4000,
    SUGGESTION_TIMEOUT: 10000
};