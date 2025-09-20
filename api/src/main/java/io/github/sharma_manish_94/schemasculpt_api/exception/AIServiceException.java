package io.github.sharma_manish_94.schemasculpt_api.exception;

/**
 * Exception thrown when AI service operations fail.
 */
public class AIServiceException extends SchemaSculptException {

    private static final String ERROR_CODE = "AI_SERVICE_ERROR";

    public AIServiceException(String message) {
        super(ERROR_CODE, message);
    }

    public AIServiceException(String message, Throwable cause) {
        super(ERROR_CODE, message, cause);
    }
}