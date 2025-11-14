package io.github.sharma_manish_94.schemasculpt_api.dto.auth;

import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import java.time.LocalDateTime;

public record UserDTO(
    Long id,
    String githubId,
    String username,
    String email,
    String avatarUrl,
    LocalDateTime createdAt) {
  public UserDTO(User user) {
    this(
        user.getId(),
        user.getGithubId(),
        user.getUsername(),
        user.getEmail(),
        user.getAvatarUrl(),
        user.getCreatedAt());
  }
}
