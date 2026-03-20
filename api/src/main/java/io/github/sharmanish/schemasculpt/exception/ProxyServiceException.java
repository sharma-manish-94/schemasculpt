package io.github.sharmanish.schemasculpt.exception;

/** Exception thrown when proxy service operations fail. Maps to HTTP 502 Bad Gateway. */
public final class ProxyServiceException extends ServiceException {

  public ProxyServiceException(String message) {
    super(ErrorCode.PROXY_SERVICE_ERROR, message);
  }

  public ProxyServiceException(String message, Throwable cause) {
    super(ErrorCode.PROXY_SERVICE_ERROR, message, cause);
  }
}
