package io.github.sharma_manish_94.schemasculpt_api.controller.auth;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.when;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.sharma_manish_94.schemasculpt_api.config.JacksonConfig;
import io.github.sharma_manish_94.schemasculpt_api.config.WebMvcConfig;
import io.github.sharma_manish_94.schemasculpt_api.entity.User;
import io.github.sharma_manish_94.schemasculpt_api.repository.UserRepository;
import io.github.sharma_manish_94.schemasculpt_api.security.CustomOAuth2User;
import io.github.sharma_manish_94.schemasculpt_api.security.JwtTokenProvider;
import java.util.Collections;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.security.oauth2.core.user.OAuth2UserAuthority;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockMvcRequestBuilders;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

@WebMvcTest(AuthController.class)
@Import({WebMvcConfig.class, JacksonConfig.class})
@TestPropertySource(properties = {"app.jwt.expiration=3600000"})
class AuthControllerTest {
  @Autowired private MockMvc mockMvc;
  @Autowired private WebApplicationContext context;

  @Qualifier("cleanObjectMapper")
  private ObjectMapper cleanObjectMapper;

  @MockBean private JwtTokenProvider tokenProvider;

  @MockBean private UserRepository userRepository;

  private User user;

  private CustomOAuth2User testPrincipal;

  private final long jwtExpirationMs = 3600000;

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

    ObjectMapper realMapper = new ObjectMapper();
    // Forward all common serialization methods to the real mapper
    when(cleanObjectMapper.getSerializerProvider()).thenReturn(realMapper.getSerializerProvider());
    when(cleanObjectMapper.getSerializationConfig())
        .thenReturn(realMapper.getSerializationConfig());
    doReturn(realMapper.getFactory()).when(cleanObjectMapper).getFactory();
    doAnswer(invocation -> realMapper.writeValueAsString(invocation.getArgument(0)))
        .when(cleanObjectMapper)
        .writeValueAsString(any());

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
  void getToken() {}

  @Test
  void logout() {}

  @Test
  void health() {}
}
