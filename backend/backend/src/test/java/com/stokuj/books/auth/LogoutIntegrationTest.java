package com.stokuj.books.auth;

import com.stokuj.books.user.User;
import com.stokuj.books.user.UserRepository;
import com.stokuj.books.user.UserRole;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.web.servlet.MockMvc;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;

@SpringBootTest
@AutoConfigureMockMvc
class LogoutIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    private Long testUserId;

    @BeforeEach
    void setUp() {
        User testUser = new User();
        testUser.setEmail("testuser@example.com");
        testUser.setUsername("testuser");
        testUser.setPassword(passwordEncoder.encode("password"));
        testUser.setRole(UserRole.USER);
        testUser.setEnabled(true);
        testUser.setProfilePublic(true);
        testUserId = userRepository.save(testUser).getId();
    }

    @AfterEach
    void tearDown() {
        if (testUserId != null) {
            userRepository.deleteById(testUserId);
        }
    }

    @Test
    void shouldReturnJson200OnLogoutWhenAuthenticated() throws Exception {
        mockMvc.perform(post("/api/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"email\":\"testuser@example.com\",\"password\":\"password\"}"))
                .andExpect(result -> assertThat(result.getResponse().getStatus()).isEqualTo(200));

        MockHttpServletResponse logoutResponse = mockMvc.perform(
                        post("/api/auth/logout")
                                .contentType(MediaType.APPLICATION_JSON))
                .andReturn()
                .getResponse();

        assertThat(logoutResponse.getStatus()).isEqualTo(200);
        assertThat(logoutResponse.getContentAsString()).isEqualTo("{\"message\":\"Logged out successfully\"}");

        String meBody = mockMvc.perform(get("/api/auth/me"))
                .andReturn()
                .getResponse()
                .getContentAsString();

        assertThat(meBody).contains("\"authenticated\":false");
    }

    @Test
    void shouldReturnJson200OnLogoutWhenUnauthenticated() throws Exception {
        MockHttpServletResponse logoutResponse = mockMvc.perform(
                        post("/api/auth/logout")
                                .contentType(MediaType.APPLICATION_JSON))
                .andReturn()
                .getResponse();

        assertThat(logoutResponse.getStatus()).isEqualTo(200);
        assertThat(logoutResponse.getContentAsString()).isEqualTo("{\"message\":\"Logged out successfully\"}");
    }
}
