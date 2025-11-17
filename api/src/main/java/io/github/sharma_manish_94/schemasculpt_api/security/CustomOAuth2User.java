package io.github.sharma_manish_94.schemasculpt_api.security;

import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.core.user.OAuth2User;

/** Custom OAuth2User that includes our User entity */
public class CustomOAuth2User implements OAuth2User {

  private final OAuth2User oauth2User;
  private final User user;

  public CustomOAuth2User(OAuth2User oauth2User, User user) {
    this.oauth2User = oauth2User;
    this.user = user;
  }

  @Override
  public Map<String, Object> getAttributes() {
    return oauth2User != null ? oauth2User.getAttributes() : Map.of();
  }

  @Override
  public Collection<? extends GrantedAuthority> getAuthorities() {
    return oauth2User != null ? oauth2User.getAuthorities() : List.of();
  }

  @Override
  public String getName() {
    return user.getUsername();
  }

  public Long getUserId() {
    return user.getId();
  }

  public User getUser() {
    return user;
  }

  public String getUsername() {
    return user.getUsername();
  }

  public String getEmail() {
    return user.getEmail();
  }

  public String getAvatarUrl() {
    return user.getAvatarUrl();
  }
}
