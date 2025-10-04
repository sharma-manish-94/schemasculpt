package io.github.sharma_manish_94.schemasculpt_api.security;

import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import io.github.sharma_manish_94.schemasculpt_api.repository.UserRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Custom OAuth2 User Service that creates or updates users from GitHub OAuth
 */
@Service
@Slf4j
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;

    public CustomOAuth2UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        try {
            return processOAuth2User(oAuth2User);
        } catch (Exception ex) {
            log.error("Error processing OAuth2 user", ex);
            throw new OAuth2AuthenticationException(ex.getMessage());
        }
    }

    @Transactional
    private OAuth2User processOAuth2User(OAuth2User oAuth2User) {
        // Extract GitHub user info with null safety
        Object idObj = oAuth2User.getAttribute("id");
        if (idObj == null) {
            throw new OAuth2AuthenticationException(
                new OAuth2Error("missing_user_id", "GitHub user ID not found", null));
        }
        String githubId = idObj.toString();

        String username = oAuth2User.getAttribute("login");
        if (username == null || username.isBlank()) {
            throw new OAuth2AuthenticationException(
                new OAuth2Error("missing_username", "GitHub username not found", null));
        }

        String email = oAuth2User.getAttribute("email");  // Can be null
        String avatarUrl = oAuth2User.getAttribute("avatar_url");  // Can be null

        log.info("Processing OAuth2 user: {} (GitHub ID: {})", username, githubId);

        // Find or create user
        User user = userRepository.findByGithubId(githubId)
            .map(existingUser -> {
                // Update existing user
                log.info("User found, updating: {}", existingUser.getId());
                existingUser.setUsername(username);
                existingUser.setEmail(email);
                existingUser.setAvatarUrl(avatarUrl);
                return userRepository.save(existingUser);
            })
            .orElseGet(() -> {
                // Create new user
                log.info("Creating new user: {}", username);
                User newUser = new User();
                newUser.setGithubId(githubId);
                newUser.setUsername(username);
                newUser.setEmail(email);
                newUser.setAvatarUrl(avatarUrl);
                return userRepository.save(newUser);
            });

        log.info("User processed successfully: {}", user.getId());

        return new CustomOAuth2User(oAuth2User, user);
    }
}
