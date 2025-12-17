package io.github.sharmanish.schemasculpt.dto.auth;

public record TokenResponse(
    String token,
    String tokenType,
    Long expiresIn,
    Long userId,
    String username,
    String email,
    String avatarUrl) {
  public TokenResponse(String token, Long userId, String username, String email, String avatarUrl) {
    this(token, "Bearer", 86400L, userId, username, email, avatarUrl);
  }
}
