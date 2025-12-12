package io.github.sharma_manish_94.schemasculpt_api.controller.auth;

import io.github.sharma_manish_94.schemasculpt_api.dto.auth.TokenResponse;
import io.github.sharma_manish_94.schemasculpt_api.dto.auth.UserDTO;
import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import io.github.sharma_manish_94.schemasculpt_api.exception.UserNotFoundException;
import io.github.sharma_manish_94.schemasculpt_api.repository.UserRepository;
import io.github.sharma_manish_94.schemasculpt_api.security.CustomOAuth2User;
import io.github.sharma_manish_94.schemasculpt_api.security.JwtTokenProvider;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Authentication Controller for OAuth2 and JWT
 */
@RestController
@RequestMapping("/api/v1/auth")
@Slf4j
public class AuthController {

  private final JwtTokenProvider tokenProvider;
  private final UserRepository userRepository;
  private final long jwtExpirationMs;

  public AuthController(
      JwtTokenProvider tokenProvider,
      UserRepository userRepository,
      @Value("${app.jwt.expiration}") long jwtExpirationMs) {
    this.tokenProvider = tokenProvider;
    this.userRepository = userRepository;
    this.jwtExpirationMs = jwtExpirationMs;
  }

  /**
   * Get current authenticated user
   */
  @GetMapping("/me")
  public ResponseEntity<UserDTO> getCurrentUser(
      @AuthenticationPrincipal CustomOAuth2User principal) {
    if (principal == null) {
      log.warn("No authenticated user found");
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    User user =
        userRepository
            .findById(principal.getUserId())
            .orElseThrow(() -> new UserNotFoundException(principal.getUserId()));

    log.info("Returning current user: {}", user.getUsername());
    return ResponseEntity.ok(new UserDTO(user));
  }

  /**
   * Generate JWT token after OAuth2 login Frontend calls this after OAuth redirect to get JWT token
   */
  @PostMapping("/token")
  public ResponseEntity<TokenResponse> getToken(
      @AuthenticationPrincipal CustomOAuth2User principal) {
    if (principal == null) {
      log.warn("No authenticated user for token generation");
      return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    User user =
        userRepository
            .findById(principal.getUserId())
            .orElseThrow(() -> new UserNotFoundException(principal.getUserId()));

    String token = tokenProvider.generateToken(user);

    log.info("Generated JWT token for user: {}", user.getUsername());

    TokenResponse response =
        new TokenResponse(
            token,
            "Bearer",
            jwtExpirationMs / 1000, // Convert to seconds
            user.getId(),
            user.getUsername(),
            user.getEmail(),
            user.getAvatarUrl());

    return ResponseEntity.ok(response);
  }

  /**
   * Logout endpoint
   */
  @PostMapping("/logout")
  public ResponseEntity<Void> logout(HttpServletRequest request) {
    // JWT tokens are stateless, so just clear session if exists
    if (request.getSession(false) != null) {
      request.getSession().invalidate();
    }

    log.info("User logged out");
    return ResponseEntity.ok().build();
  }

  /**
   * Health check endpoint (public)
   */
  @GetMapping("/health")
  public ResponseEntity<String> health() {
    return ResponseEntity.ok("Authentication service is running");
  }
}
