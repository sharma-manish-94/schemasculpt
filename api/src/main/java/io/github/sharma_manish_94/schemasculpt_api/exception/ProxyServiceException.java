package io.github.sharma_manish_94.schemasculpt_api.exception;

/**
 * Exception thrown when proxy service operations fail.
 */
public class ProxyServiceException extends SchemaSculptException {

  private static final String ERROR_CODE = "PROXY_SERVICE_ERROR";

  public ProxyServiceException(String message) {
    super(ERROR_CODE, message);
  }

  public ProxyServiceException(String message, Throwable cause) {
    super(ERROR_CODE, message, cause);
  }
}
