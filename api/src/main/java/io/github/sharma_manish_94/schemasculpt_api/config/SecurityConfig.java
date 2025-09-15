package io.github.sharma_manish_94.schemasculpt_api.config;


import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
                .authorizeHttpRequests(authz -> authz
                        // Allow public access to all API and WebSocket endpoints
                        .requestMatchers("/api/**", "/ws/**").permitAll()
                        // Require authentication for any other request
                        .anyRequest().authenticated()
                )
                .httpBasic(withDefaults()); // Or use another authentication method

        // For stateless APIs, you might disable CSRF. For development, this is often simpler.
        http.csrf(csrf -> csrf.disable());

        return http.build();
    }
}
