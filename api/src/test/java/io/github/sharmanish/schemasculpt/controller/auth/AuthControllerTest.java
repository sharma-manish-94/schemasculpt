package io.github.sharmanish.schemasculpt.controller.auth;


import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharmanish.schemasculpt.config.JacksonConfig;
import io.github.sharmanish.schemasculpt.config.WebMvcConfig;
import io.github.sharmanish.schemasculpt.entity.User;
import io.github.sharmanish.schemasculpt.repository.UserRepository;
import io.github.sharmanish.schemasculpt.security.CustomOAuth2User;
import io.github.sharmanish.schemasculpt.security.JwtTokenProvider;
import java.util.Collections;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.oauth2.core.user.OAuth2UserAuthority;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

@WebMvcTest(
    controllers = AuthController.class,
    excludeAutoConfiguration = {
        org.springframework.boot.security.oauth2.client.autoconfigure.servlet
            .OAuth2ClientWebSecurityAutoConfiguration.class,
        org.springframework.boot.security.oauth2.client.autoconfigure.OAuth2ClientAutoConfiguration
            .class
    })
@Import({WebMvcConfig.class, JacksonConfig.class, AuthControllerTest.TestConfig.class})
@TestPropertySource(properties = {"app.jwt.expiration=3600000"})
class AuthControllerTest {

  private final long jwtExpirationMs = 3600000;
  @Autowired
  private MockMvc mockMvc;
  @Autowired
  private WebApplicationContext context;

  @Autowired
  @Qualifier("cleanObjectMapper")
  private ObjectMapper cleanObjectMapper;

  @Autowired
  private JwtTokenProvider tokenProvider;

  @Autowired
  private UserRepository userRepository;

  private User user;

  private CustomOAuth2User testPrincipal;

  @BeforeEach
  void setUp() throws JsonProcessingException {
    user = new User();
    user.setId(1L);
    user.setUsername("testuser");
    user.setEmail("test.email.com");
    user.setAvatarUrl("http://example.com/avatar.png");

    Map<String, Object> attributes =
        Map.of(
            "id", user.getId(),
            "login", user.getUsername(),
            "email", user.getEmail());

    testPrincipal =
        new CustomOAuth2User(
            new org.springframework.security.oauth2.core.user.DefaultOAuth2User(
                Collections.singleton(new OAuth2UserAuthority(attributes)), attributes, "login"),
            user);

    this.mockMvc =
        MockMvcBuilders.webAppContextSetup(context)
            .defaultRequest(MockMvcRequestBuilders.get("/").accept(MediaType.APPLICATION_JSON))
            .build();
  }

  @Test
  void whenGetCurrentUserWithValidPrincipal_thenReturnsUserDTO() throws Exception {
    //    when(userRepository.findById(1L)).thenReturn(Optional.of(user));
    //    doAnswer(invocation -> true).when(cleanObjectMapper).canSerialize(any());
    //    mockMvc
    //        .perform(
    //            MockMvcRequestBuilders.get("/api/v1/auth/me")
    //                .with(oauth2Login().oauth2User(testPrincipal))
    //                .accept(MediaType.APPLICATION_JSON)
    //                .contentType(MediaType.APPLICATION_JSON))
    //		    .andDo(result -> System.out.println("Response: " +
    // result.getResponse().getContentAsString()))
    //		    .andDo(result -> System.out.println("Status: " + result.getResponse().getStatus()))
    //		    .andExpect(status().isOk())
    //        .andExpect(content().contentType(MediaType.APPLICATION_JSON))
    //        .andExpect(jsonPath("$.username").value("testuser"))
    //        .andExpect(jsonPath("$.email").value("test.email.com"))
    //        .andExpect(jsonPath("$.avatarUrl").value("http://example.com/avatar.png"));
  }

  @Test
  void getToken() {
  }

  @Test
  void logout() {
  }

  @Test
  void health() {
  }

  @TestConfiguration
  static class TestConfig {
    @Bean
    public JwtTokenProvider jwtTokenProvider() {
      return Mockito.mock(JwtTokenProvider.class);
    }

    @Bean
    public UserRepository userRepository() {
      return Mockito.mock(UserRepository.class);
    }
  }
}
