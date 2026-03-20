package io.github.sharmanish.schemasculpt.security;

import io.github.sharmanish.schemasculpt.entity.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.UnsupportedJwtException;
import io.jsonwebtoken.security.Keys;
import java.util.Base64;
import java.util.Date;
import javax.crypto.SecretKey;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/** JWT Token Provider for generating and validating JWT tokens. */
@Component
@Slf4j
public class JwtTokenProvider {

  @Value("${app.jwt.secret}")
  private String jwtSecret;

  @Value("${app.jwt.expiration}")
  private long jwtExpirationMs;

  /**
   * Generate a JWT token for the given user.
   *
   * @param user the user to generate a token for
   * @return the generated JWT token string
   */
  public String generateToken(User user) {
    Date now = new Date();
    Date expiryDate = new Date(now.getTime() + jwtExpirationMs);

    return Jwts.builder()
        .setSubject(user.getGithubId())
        .claim("userId", user.getId())
        .claim("username", user.getUsername())
        .claim("email", user.getEmail())
        .claim("avatarUrl", user.getAvatarUrl())
        .setIssuedAt(now)
        .setExpiration(expiryDate)
        .signWith(getSigningKey(), SignatureAlgorithm.HS512)
        .compact();
  }

  private SecretKey getSigningKey() {
    byte[] keyBytes = Base64.getDecoder().decode(jwtSecret);
    return Keys.hmacShaKeyFor(keyBytes);
  }

  /**
   * Extract the user ID from a JWT token.
   *
   * @param token the JWT token
   * @return the user ID
   */
  public Long getUserIdFromToken(String token) {
    Claims claims =
        Jwts.parser().verifyWith(getSigningKey()).build().parseSignedClaims(token).getPayload();

    return claims.get("userId", Long.class);
  }

  /**
   * Extract the username from a JWT token.
   *
   * @param token the JWT token
   * @return the username
   */
  public String getUsernameFromToken(String token) {
    Claims claims =
        Jwts.parser().verifyWith(getSigningKey()).build().parseSignedClaims(token).getPayload();

    return claims.get("username", String.class);
  }

  /**
   * Validate a JWT token.
   *
   * @param authToken the JWT token to validate
   * @return true if the token is valid, false otherwise
   */
  public boolean validateToken(String authToken) {
    try {
      Jwts.parser().verifyWith(getSigningKey()).build().parseSignedClaims(authToken);
      return true;
    } catch (SecurityException _) {
      log.error("Invalid JWT signature");
    } catch (MalformedJwtException _) {
      log.error("Invalid JWT token");
    } catch (ExpiredJwtException _) {
      log.error("Expired JWT token");
    } catch (UnsupportedJwtException _) {
      log.error("Unsupported JWT token");
    } catch (IllegalArgumentException _) {
      log.error("JWT claims string is empty");
    }
    return false;
  }
}
