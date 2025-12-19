package io.github.sharmanish.schemasculpt.security;

import io.github.sharmanish.schemasculpt.repository.UserRepository;
import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.csrf.CookieCsrfTokenRepository;
import org.springframework.security.web.csrf.CsrfTokenRepository;
import org.springframework.security.web.server.csrf.CookieServerCsrfTokenRepository;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

/**
 * Security Configuration for OAuth2 and JWT
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

  private final CustomOAuth2UserService customOAuth2UserService;
  @Value("${app.cors.allowed-origins}")
  private String allowedOrigins;
  @Value("${app.frontend.url}")
  private String frontendUrl;

  public SecurityConfig(CustomOAuth2UserService customOAuth2UserService) {
    this.customOAuth2UserService = customOAuth2UserService;
  }

  @Bean
  public SecurityFilterChain securityFilterChain(
      HttpSecurity http,
      JwtAuthenticationFilter jwtAuthenticationFilter) {
    http.cors(cors -> cors.configurationSource(corsConfigurationSource()))
        .csrf(csrf -> csrf
            .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            .ignoringRequestMatchers("/ws/**", "/api/v1/auth/**", "/api/v1/sessions/**",
                "/api/v1/explanations/**", "/api/v1/repository/**", "/proxy/**"))
        .sessionManagement(
            session -> session.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
        .authorizeHttpRequests(
            auth ->
                auth
                    // Public endpoints
                    .requestMatchers("/", "/error", "/favicon.ico")
                    .permitAll()
                    .requestMatchers("/login/**")
                    .permitAll()
                    .requestMatchers("/oauth2/**")
                    .permitAll()
                    .requestMatchers("/api/v1/auth/**")
                    .permitAll()
                    .requestMatchers("/actuator/**")
                    .permitAll()

                    // Protected endpoints
                    .requestMatchers("/api/v1/projects/**")
                    .authenticated()
                    .requestMatchers("/api/v1/specifications/**")
                    .authenticated()

                    // Temporary: keep existing session endpoints public during migration
                    .requestMatchers("/api/v1/sessions/**")
                    .permitAll()
                    .requestMatchers("/api/v1/explanations/**")
                    .permitAll()
                    .requestMatchers("/api/v1/repository/**")
                    .permitAll()
                    .requestMatchers("/proxy/**")
                    .permitAll()
                    .requestMatchers("/ws/**")
                    .permitAll()

                    // All other endpoints require authentication
                    .anyRequest()
                    .authenticated())
        .oauth2Login(
            oauth2 ->
                oauth2
                    .loginPage("/oauth2/authorization/github")
                    .defaultSuccessUrl(frontendUrl + "/oauth2/redirect", true)
                    .failureUrl(frontendUrl + "/login?error=true")
                    .userInfoEndpoint(userInfo -> userInfo.userService(customOAuth2UserService)))
        .logout(logout -> logout.logoutSuccessUrl(frontendUrl).deleteCookies("JSESSIONID"))
        .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

    return http.build();
  }

  @Bean
  public CorsConfigurationSource corsConfigurationSource() {
    CorsConfiguration configuration = new CorsConfiguration();

    // Parse allowed origins from application.properties
    List<String> origins = Arrays.asList(allowedOrigins.split(","));
    configuration.setAllowedOrigins(origins);

    configuration.setAllowedMethods(
        Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));
    configuration.setAllowedHeaders(List.of("*"));
    configuration.setAllowCredentials(true);
    configuration.setMaxAge(3600L);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/**", configuration);
    return source;
  }

  @Bean
  public JwtAuthenticationFilter jwtAuthenticationFilter(
      JwtTokenProvider tokenProvider,
      UserRepository userRepository
  ) {
    return new JwtAuthenticationFilter(tokenProvider, userRepository);
  }
}
