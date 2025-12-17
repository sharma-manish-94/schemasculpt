package io.github.sharmanish.schemasculpt.exception;

/**
 * Exception thrown when a user is not found in the database
 */
public class UserNotFoundException extends SchemaSculptException {

  public UserNotFoundException(Long userId) {
    super("USER_NOT_FOUND", "User not found with ID: " + userId);
  }

  public UserNotFoundException(String githubId) {
    super("USER_NOT_FOUND", "User not found with GitHub ID: " + githubId);
  }
}
