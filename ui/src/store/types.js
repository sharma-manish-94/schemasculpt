export const STORE_ACTIONS = {
    // Core Spec Actions
    SET_SPEC_TEXT: 'setSpecText',
    PARSE_SPEC: 'parseSpec',
    CREATE_SESSION: 'createSession',

    // Navigation Actions
    SET_SELECTED_NAV_ITEM: 'setSelectedNavItem',
    PARSE_ENDPOINTS: 'parseEndpoints',

    // Mock Server Actions
    START_MOCK_SERVER: 'startMockServer',
    REFRESH_MOCK_SERVER: 'refreshMockServer',

    // Request Actions
    SEND_REQUEST: 'sendRequest',
    SET_SERVER_TARGET: 'setServerTarget',
    SET_CUSTOM_SERVER_URL: 'setCustomServerUrl',
    SET_PATH_PARAMS: 'setPathParams',
    SET_REQUEST_BODY: 'setRequestBody',

    // Response Actions
    START_REQUEST: 'startRequest',
    SET_RESPONSE: 'setResponse',

    // Validation Actions
    VALIDATE_SPEC: 'validateSpec',
    SET_VALIDATION_RESULT: 'setValidationResult',
    SET_VALIDATION_LOADING: 'setValidationLoading',
    APPLY_SUGGESTION: 'applySuggestion',

    // AI Actions
    SUGGEST_IMPROVEMENTS: 'suggestImprovements',
    FIX_WITH_AI: 'fixWithAi',
    SET_AI_SUGGESTION: 'setAiSuggestion',
    SET_AI_LOADING: 'setAiLoading',
    SET_AI_INPUT: 'setAiInput'
};

export const LOADING_STATES = {
    IDLE: 'idle',
    LOADING: 'loading',
    SUCCESS: 'success',
    ERROR: 'error'
};

export const ERROR_TYPES = {
    NETWORK_ERROR: 'NETWORK_ERROR',
    VALIDATION_ERROR: 'VALIDATION_ERROR',
    PARSING_ERROR: 'PARSING_ERROR',
    SERVER_ERROR: 'SERVER_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR'
};