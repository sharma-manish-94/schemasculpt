package io.github.sharma_manish_94.schemasculpt_api.exception;

/**
 * Base exception class for SchemaSculpt application.
 * All custom exceptions should extend this class.
 */
public abstract class SchemaSculptException extends RuntimeException {

    private final String errorCode;

    protected SchemaSculptException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }

    protected SchemaSculptException(String errorCode, String message, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}