package io.github.sharma_manish_94.schemasculpt_api.exception;

/**
 * Exception thrown when a session cannot be found.
 */
public class SessionNotFoundException extends SchemaSculptException {

    private static final String ERROR_CODE = "SESSION_NOT_FOUND";

    public SessionNotFoundException(String sessionId) {
        super(ERROR_CODE, "Session not found: " + sessionId);
    }

    public SessionNotFoundException(String sessionId, Throwable cause) {
        super(ERROR_CODE, "Session not found: " + sessionId, cause);
    }
}
