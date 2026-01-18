package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when a user is not found in the database. Maps to HTTP 404 Not Found.
 */
public final class UserNotFoundException extends ResourceNotFoundException {

  public UserNotFoundException(Long userId) {
    super(ErrorCode.USER_NOT_FOUND, "User not found with ID: " + userId);
  }

  public UserNotFoundException(String githubId) {
    super(ErrorCode.USER_NOT_FOUND, "User not found with GitHub ID: " + githubId);
  }
}
