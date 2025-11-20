# GitHub OAuth + Database Persistence Implementation Plan

## 📋 Overview
Add GitHub OAuth authentication and PostgreSQL database persistence to enable users to save, version, and manage their OpenAPI specifications.

---

## 🎯 Goals
1. **Authentication**: GitHub OAuth login/logout
2. **Persistence**: Save specifications to PostgreSQL database
3. **Versioning**: Create and manage multiple versions of specs
4. **Project Management**: Organize specs into projects
5. **User Sessions**: Maintain authenticated user sessions

---

## 🏗️ Architecture Changes

### Current Architecture
```
UI (React) → API Gateway (Spring Boot) → AI Service (Python)
                    ↓
                  Redis (sessions)
```

### New Architecture
```
UI (React) → API Gateway (Spring Boot) → AI Service (Python)
                    ↓
          ┌─────────┴─────────┐
          ↓                   ↓
    PostgreSQL           Redis (sessions)
    (persistence)        (temp sessions)
```

---

## 📦 Phase 1: Database Setup & Models

### 1.1 Add Dependencies (pom.xml)
```xml
<!-- PostgreSQL Database -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>

<!-- OAuth2 Client -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-oauth2-client</artifactId>
</dependency>

<!-- Flyway for DB migrations -->
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-core</artifactId>
</dependency>
```

### 1.2 Database Schema Design

**Tables:**

**users**
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    github_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_github_id ON users(github_id);
```

**projects**
```sql
CREATE TABLE projects (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
```

**specifications**
```sql
CREATE TABLE specifications (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version VARCHAR(50) NOT NULL,
    spec_content TEXT NOT NULL,
    spec_format VARCHAR(10) DEFAULT 'json', -- 'json' or 'yaml'
    commit_message TEXT,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by BIGINT REFERENCES users(id),
    UNIQUE(project_id, version)
);

CREATE INDEX idx_specifications_project_id ON specifications(project_id);
CREATE INDEX idx_specifications_current ON specifications(is_current);
```

**validation_snapshots** (optional - for tracking validation history)
```sql
CREATE TABLE validation_snapshots (
    id BIGSERIAL PRIMARY KEY,
    specification_id BIGINT NOT NULL REFERENCES specifications(id) ON DELETE CASCADE,
    errors JSONB,
    suggestions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_snapshots_spec_id ON validation_snapshots(specification_id);
```

### 1.3 JPA Entities

**User.java**
```java
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "github_id", unique = true, nullable = false)
    private String githubId;

    @Column(nullable = false)
    private String username;

    private String email;

    @Column(name = "avatar_url")
    private String avatarUrl;

    @Column(name = "created_at")
    @CreationTimestamp
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    @UpdateTimestamp
    private LocalDateTime updatedAt;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    private List<Project> projects;
}
```

**Project.java**
```java
@Entity
@Table(name = "projects")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Project {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false)
    private String name;

    private String description;

    @Column(name = "is_public")
    private Boolean isPublic = false;

    @Column(name = "created_at")
    @CreationTimestamp
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    @UpdateTimestamp
    private LocalDateTime updatedAt;

    @OneToMany(mappedBy = "project", cascade = CascadeType.ALL)
    private List<Specification> specifications;
}
```

**Specification.java**
```java
@Entity
@Table(name = "specifications")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Specification {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "project_id", nullable = false)
    private Project project;

    @Column(nullable = false)
    private String version;

    @Column(name = "spec_content", columnDefinition = "TEXT", nullable = false)
    private String specContent;

    @Column(name = "spec_format")
    private String specFormat = "json";

    @Column(name = "commit_message", columnDefinition = "TEXT")
    private String commitMessage;

    @Column(name = "is_current")
    private Boolean isCurrent = true;

    @Column(name = "created_at")
    @CreationTimestamp
    private LocalDateTime createdAt;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "created_by")
    private User createdBy;
}
```

---

## 🔐 Phase 2: GitHub OAuth Authentication

### 2.1 GitHub OAuth App Setup

**Manual Steps:**
1. Go to GitHub Settings → Developer settings → OAuth Apps
2. Click "New OAuth App"
3. Fill in:
   - Application name: `SchemaSculpt`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8080/login/oauth2/code/github`
4. Save **Client ID** and **Client Secret**

### 2.2 Spring Security Configuration

**application.properties**
```properties
# Database Configuration
spring.datasource.url=jdbc:postgresql://localhost:5432/schemasculpt
spring.datasource.username=postgres
spring.datasource.password=your_password
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=false

# Flyway Migration
spring.flyway.enabled=true
spring.flyway.baseline-on-migrate=true

# OAuth2 GitHub Configuration
spring.security.oauth2.client.registration.github.client-id=${GITHUB_CLIENT_ID}
spring.security.oauth2.client.registration.github.client-secret=${GITHUB_CLIENT_SECRET}
spring.security.oauth2.client.registration.github.scope=user:email,read:user
spring.security.oauth2.client.provider.github.authorization-uri=https://github.com/login/oauth/authorize
spring.security.oauth2.client.provider.github.token-uri=https://github.com/login/oauth/access_token
spring.security.oauth2.client.provider.github.user-info-uri=https://api.github.com/user

# JWT Configuration (for stateless sessions)
app.jwt.secret=${JWT_SECRET:your-secret-key-change-in-production}
app.jwt.expiration=86400000
```

**SecurityConfig.java**
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .cors(cors -> cors.configurationSource(corsConfigurationSource()))
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                // Public endpoints
                .requestMatchers("/", "/login/**", "/oauth2/**", "/error").permitAll()
                .requestMatchers("/api/v1/auth/**").permitAll()

                // Protected endpoints
                .requestMatchers("/api/v1/projects/**").authenticated()
                .requestMatchers("/api/v1/specifications/**").authenticated()

                // Temporary: keep existing session endpoints public during migration
                .requestMatchers("/api/v1/sessions/**").permitAll()

                .anyRequest().authenticated()
            )
            .oauth2Login(oauth2 -> oauth2
                .loginPage("/login")
                .defaultSuccessUrl("http://localhost:3000/dashboard", true)
                .failureUrl("http://localhost:3000/login?error=true")
                .userInfoEndpoint(userInfo -> userInfo
                    .userService(customOAuth2UserService())
                )
            )
            .logout(logout -> logout
                .logoutSuccessUrl("http://localhost:3000")
                .deleteCookies("JSESSIONID")
            )
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(Arrays.asList("http://localhost:3000"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public CustomOAuth2UserService customOAuth2UserService() {
        return new CustomOAuth2UserService();
    }

    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }
}
```

**CustomOAuth2UserService.java**
```java
@Service
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);

        // Extract GitHub user info
        String githubId = oAuth2User.getAttribute("id").toString();
        String username = oAuth2User.getAttribute("login");
        String email = oAuth2User.getAttribute("email");
        String avatarUrl = oAuth2User.getAttribute("avatar_url");

        // Find or create user
        User user = userRepository.findByGithubId(githubId)
            .orElseGet(() -> {
                User newUser = new User();
                newUser.setGithubId(githubId);
                newUser.setUsername(username);
                newUser.setEmail(email);
                newUser.setAvatarUrl(avatarUrl);
                return userRepository.save(newUser);
            });

        // Create custom principal with user ID
        return new CustomOAuth2User(oAuth2User, user);
    }
}
```

**JwtTokenProvider.java**
```java
@Component
public class JwtTokenProvider {

    @Value("${app.jwt.secret}")
    private String jwtSecret;

    @Value("${app.jwt.expiration}")
    private long jwtExpirationMs;

    public String generateToken(User user) {
        return Jwts.builder()
            .setSubject(user.getGithubId())
            .claim("userId", user.getId())
            .claim("username", user.getUsername())
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + jwtExpirationMs))
            .signWith(SignatureAlgorithm.HS512, jwtSecret)
            .compact();
    }

    public Long getUserIdFromToken(String token) {
        Claims claims = Jwts.parser()
            .setSigningKey(jwtSecret)
            .parseClaimsJws(token)
            .getBody();
        return claims.get("userId", Long.class);
    }

    public boolean validateToken(String token) {
        try {
            Jwts.parser().setSigningKey(jwtSecret).parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
```

### 2.3 Authentication Controllers

**AuthController.java**
```java
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired
    private UserRepository userRepository;

    @GetMapping("/me")
    public ResponseEntity<UserDTO> getCurrentUser(@AuthenticationPrincipal CustomOAuth2User principal) {
        if (principal == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        User user = userRepository.findById(principal.getUserId())
            .orElseThrow(() -> new RuntimeException("User not found"));

        return ResponseEntity.ok(new UserDTO(user));
    }

    @PostMapping("/token")
    public ResponseEntity<TokenResponse> getToken(@AuthenticationPrincipal CustomOAuth2User principal) {
        User user = userRepository.findById(principal.getUserId())
            .orElseThrow(() -> new RuntimeException("User not found"));

        String token = tokenProvider.generateToken(user);
        return ResponseEntity.ok(new TokenResponse(token, user.getUsername(), user.getAvatarUrl()));
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(HttpServletRequest request) {
        // Clear any server-side session if exists
        request.getSession().invalidate();
        return ResponseEntity.ok().build();
    }
}
```

---

## 💾 Phase 3: Project & Specification Management

### 3.1 Repositories

**UserRepository.java**
```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByGithubId(String githubId);
}
```

**ProjectRepository.java**
```java
public interface ProjectRepository extends JpaRepository<Project, Long> {
    List<Project> findByUserId(Long userId);
    Optional<Project> findByUserIdAndName(Long userId, String name);
    List<Project> findByIsPublicTrue();
}
```

**SpecificationRepository.java**
```java
public interface SpecificationRepository extends JpaRepository<Specification, Long> {
    List<Specification> findByProjectIdOrderByCreatedAtDesc(Long projectId);
    Optional<Specification> findByProjectIdAndVersion(Long projectId, String version);
    Optional<Specification> findByProjectIdAndIsCurrentTrue(Long projectId);
}
```

### 3.2 Service Layer

**ProjectService.java**
```java
@Service
public class ProjectService {

    @Autowired
    private ProjectRepository projectRepository;

    @Autowired
    private SpecificationRepository specificationRepository;

    public Project createProject(Long userId, CreateProjectRequest request) {
        Project project = new Project();
        project.setUser(new User(userId)); // Simplified
        project.setName(request.getName());
        project.setDescription(request.getDescription());
        project.setIsPublic(request.getIsPublic());
        return projectRepository.save(project);
    }

    public List<Project> getUserProjects(Long userId) {
        return projectRepository.findByUserId(userId);
    }

    public Project getProject(Long projectId, Long userId) {
        Project project = projectRepository.findById(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("Project not found"));

        if (!project.getUser().getId().equals(userId) && !project.getIsPublic()) {
            throw new UnauthorizedException("Access denied");
        }

        return project;
    }

    public void deleteProject(Long projectId, Long userId) {
        Project project = getProject(projectId, userId);
        if (!project.getUser().getId().equals(userId)) {
            throw new UnauthorizedException("Cannot delete other user's project");
        }
        projectRepository.delete(project);
    }
}
```

**SpecificationService.java**
```java
@Service
public class SpecificationService {

    @Autowired
    private SpecificationRepository specificationRepository;

    @Autowired
    private ProjectRepository projectRepository;

    public Specification saveSpecification(Long projectId, Long userId, SaveSpecRequest request) {
        Project project = projectRepository.findById(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("Project not found"));

        if (!project.getUser().getId().equals(userId)) {
            throw new UnauthorizedException("Access denied");
        }

        // Mark current version as not current
        specificationRepository.findByProjectIdAndIsCurrentTrue(projectId)
            .ifPresent(current -> {
                current.setIsCurrent(false);
                specificationRepository.save(current);
            });

        // Create new version
        Specification spec = new Specification();
        spec.setProject(project);
        spec.setVersion(generateVersion(projectId));
        spec.setSpecContent(request.getSpecContent());
        spec.setSpecFormat(request.getSpecFormat());
        spec.setCommitMessage(request.getCommitMessage());
        spec.setIsCurrent(true);
        spec.setCreatedBy(new User(userId));

        return specificationRepository.save(spec);
    }

    public List<Specification> getProjectVersions(Long projectId, Long userId) {
        // Verify access
        Project project = projectRepository.findById(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("Project not found"));

        if (!project.getUser().getId().equals(userId) && !project.getIsPublic()) {
            throw new UnauthorizedException("Access denied");
        }

        return specificationRepository.findByProjectIdOrderByCreatedAtDesc(projectId);
    }

    public Specification getCurrentSpecification(Long projectId, Long userId) {
        // Verify access
        Project project = projectRepository.findById(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("Project not found"));

        if (!project.getUser().getId().equals(userId) && !project.getIsPublic()) {
            throw new UnauthorizedException("Access denied");
        }

        return specificationRepository.findByProjectIdAndIsCurrentTrue(projectId)
            .orElseThrow(() -> new ResourceNotFoundException("No current specification"));
    }

    private String generateVersion(Long projectId) {
        long count = specificationRepository.countByProjectId(projectId);
        return "v" + (count + 1);
    }
}
```

### 3.3 REST Controllers

**ProjectController.java**
```java
@RestController
@RequestMapping("/api/v1/projects")
public class ProjectController {

    @Autowired
    private ProjectService projectService;

    @GetMapping
    public ResponseEntity<List<ProjectDTO>> getMyProjects(@AuthenticationPrincipal CustomOAuth2User user) {
        List<Project> projects = projectService.getUserProjects(user.getUserId());
        return ResponseEntity.ok(projects.stream().map(ProjectDTO::new).collect(Collectors.toList()));
    }

    @PostMapping
    public ResponseEntity<ProjectDTO> createProject(
            @AuthenticationPrincipal CustomOAuth2User user,
            @RequestBody CreateProjectRequest request) {
        Project project = projectService.createProject(user.getUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).body(new ProjectDTO(project));
    }

    @GetMapping("/{projectId}")
    public ResponseEntity<ProjectDTO> getProject(
            @PathVariable Long projectId,
            @AuthenticationPrincipal CustomOAuth2User user) {
        Project project = projectService.getProject(projectId, user.getUserId());
        return ResponseEntity.ok(new ProjectDTO(project));
    }

    @DeleteMapping("/{projectId}")
    public ResponseEntity<Void> deleteProject(
            @PathVariable Long projectId,
            @AuthenticationPrincipal CustomOAuth2User user) {
        projectService.deleteProject(projectId, user.getUserId());
        return ResponseEntity.noContent().build();
    }
}
```

**SpecificationController.java** (Updated)
```java
@RestController
@RequestMapping("/api/v1/projects/{projectId}/specifications")
public class SpecificationManagementController {

    @Autowired
    private SpecificationService specificationService;

    @GetMapping
    public ResponseEntity<List<SpecificationDTO>> getVersions(
            @PathVariable Long projectId,
            @AuthenticationPrincipal CustomOAuth2User user) {
        List<Specification> specs = specificationService.getProjectVersions(projectId, user.getUserId());
        return ResponseEntity.ok(specs.stream().map(SpecificationDTO::new).collect(Collectors.toList()));
    }

    @GetMapping("/current")
    public ResponseEntity<SpecificationDTO> getCurrent(
            @PathVariable Long projectId,
            @AuthenticationPrincipal CustomOAuth2User user) {
        Specification spec = specificationService.getCurrentSpecification(projectId, user.getUserId());
        return ResponseEntity.ok(new SpecificationDTO(spec));
    }

    @PostMapping
    public ResponseEntity<SpecificationDTO> saveVersion(
            @PathVariable Long projectId,
            @AuthenticationPrincipal CustomOAuth2User user,
            @RequestBody SaveSpecRequest request) {
        Specification spec = specificationService.saveSpecification(projectId, user.getUserId(), request);
        return ResponseEntity.status(HttpStatus.CREATED).body(new SpecificationDTO(spec));
    }

    @GetMapping("/{version}")
    public ResponseEntity<SpecificationDTO> getVersion(
            @PathVariable Long projectId,
            @PathVariable String version,
            @AuthenticationPrincipal CustomOAuth2User user) {
        // Implementation
    }
}
```

---

## 🎨 Phase 4: Frontend Integration

### 4.1 New React Components

**LoginPage.js**
```jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
    const navigate = useNavigate();

    const handleGitHubLogin = () => {
        window.location.href = 'http://localhost:8080/oauth2/authorization/github';
    };

    useEffect(() => {
        // Check if user is already logged in
        const token = localStorage.getItem('authToken');
        if (token) {
            navigate('/dashboard');
        }
    }, [navigate]);

    return (
        <div className="login-container">
            <h1>SchemaSculpt</h1>
            <p>OpenAPI Specification Editor with AI</p>
            <button onClick={handleGitHubLogin} className="github-login-btn">
                <GithubIcon /> Sign in with GitHub
            </button>
        </div>
    );
}
```

**OAuth2RedirectHandler.js**
```jsx
import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';

function OAuth2RedirectHandler() {
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        // Extract token from URL or get from backend
        const getToken = async () => {
            try {
                const response = await axios.post('http://localhost:8080/api/v1/auth/token', {}, {
                    withCredentials: true
                });

                const { token, username, avatarUrl } = response.data;

                // Store in localStorage
                localStorage.setItem('authToken', token);
                localStorage.setItem('username', username);
                localStorage.setItem('avatarUrl', avatarUrl);

                navigate('/dashboard');
            } catch (error) {
                console.error('Failed to get token:', error);
                navigate('/login?error=true');
            }
        };

        getToken();
    }, [navigate, location]);

    return <div>Loading...</div>;
}
```

**ProjectsPage.js**
```jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProjects, createProject } from '../api/projectService';

function ProjectsPage() {
    const [projects, setProjects] = useState([]);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        loadProjects();
    }, []);

    const loadProjects = async () => {
        const data = await getProjects();
        setProjects(data);
    };

    const handleCreateProject = async (projectData) => {
        await createProject(projectData);
        loadProjects();
        setShowCreateModal(false);
    };

    const handleOpenProject = (projectId) => {
        navigate(`/editor/${projectId}`);
    };

    return (
        <div className="projects-page">
            <header>
                <h1>My Projects</h1>
                <button onClick={() => setShowCreateModal(true)}>
                    + New Project
                </button>
            </header>

            <div className="projects-grid">
                {projects.map(project => (
                    <ProjectCard
                        key={project.id}
                        project={project}
                        onOpen={() => handleOpenProject(project.id)}
                    />
                ))}
            </div>

            {showCreateModal && (
                <CreateProjectModal
                    onClose={() => setShowCreateModal(false)}
                    onCreate={handleCreateProject}
                />
            )}
        </div>
    );
}
```

### 4.2 API Service Updates

**authService.js**
```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v1';

export const getCurrentUser = async () => {
    const token = localStorage.getItem('authToken');
    const response = await axios.get(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
};

export const logout = async () => {
    const token = localStorage.getItem('authToken');
    await axios.post(`${API_BASE}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` }
    });
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    localStorage.removeItem('avatarUrl');
};
```

**projectService.js**
```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8080/api/v1';

const getAuthHeaders = () => ({
    Authorization: `Bearer ${localStorage.getItem('authToken')}`
});

export const getProjects = async () => {
    const response = await axios.get(`${API_BASE}/projects`, {
        headers: getAuthHeaders()
    });
    return response.data;
};

export const createProject = async (projectData) => {
    const response = await axios.post(`${API_BASE}/projects`, projectData, {
        headers: getAuthHeaders()
    });
    return response.data;
};

export const getProjectSpec = async (projectId) => {
    const response = await axios.get(
        `${API_BASE}/projects/${projectId}/specifications/current`,
        { headers: getAuthHeaders() }
    );
    return response.data;
};

export const saveSpecVersion = async (projectId, specData) => {
    const response = await axios.post(
        `${API_BASE}/projects/${projectId}/specifications`,
        specData,
        { headers: getAuthHeaders() }
    );
    return response.data;
};

export const getSpecVersions = async (projectId) => {
    const response = await axios.get(
        `${API_BASE}/projects/${projectId}/specifications`,
        { headers: getAuthHeaders() }
    );
    return response.data;
};
```

### 4.3 Updated App Routing

**App.js**
```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import OAuth2RedirectHandler from './components/OAuth2RedirectHandler';
import ProjectsPage from './pages/ProjectsPage';
import EditorPage from './pages/EditorPage';
import PrivateRoute from './components/PrivateRoute';

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/oauth2/redirect" element={<OAuth2RedirectHandler />} />

                <Route path="/dashboard" element={
                    <PrivateRoute>
                        <ProjectsPage />
                    </PrivateRoute>
                } />

                <Route path="/editor/:projectId" element={
                    <PrivateRoute>
                        <EditorPage />
                    </PrivateRoute>
                } />

                <Route path="/" element={<Navigate to="/dashboard" />} />
            </Routes>
        </BrowserRouter>
    );
}
```

**PrivateRoute.js**
```jsx
import { Navigate } from 'react-router-dom';

function PrivateRoute({ children }) {
    const token = localStorage.getItem('authToken');

    if (!token) {
        return <Navigate to="/login" />;
    }

    return children;
}
```

---

## 🚀 Phase 5: Migration Strategy

### 5.1 Backward Compatibility

**Hybrid Session Management** (During Migration):
- Keep existing Redis sessions for anonymous users
- Use JWT + Database for authenticated users
- Gradual migration path

**SessionService.java** (Updated)
```java
@Service
public class SessionService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private SpecificationService specificationService;

    public String createSession(String specText) {
        // For anonymous users - use Redis (existing behavior)
        String sessionId = UUID.randomUUID().toString();
        // ... existing Redis logic
        return sessionId;
    }

    public String createSessionForProject(Long projectId, Long userId) {
        // For authenticated users - load from database
        Specification spec = specificationService.getCurrentSpecification(projectId, userId);

        // Create temporary session for editing
        String sessionId = "project-" + projectId;
        // ... store in Redis with project metadata
        return sessionId;
    }
}
```

### 5.2 Data Migration Script

For existing users (if any):
```sql
-- Copy anonymous sessions to a backup table
CREATE TABLE anonymous_sessions_backup AS
SELECT * FROM redis_sessions WHERE created_at > NOW() - INTERVAL '7 days';
```

---

## 📝 Phase 6: Implementation Checklist

### Backend Tasks

- [ ] **Database Setup**
  - [ ] Install PostgreSQL
  - [ ] Create database `schemasculpt`
  - [ ] Add JPA, PostgreSQL, OAuth2 dependencies
  - [ ] Configure application.properties

- [ ] **Database Schema**
  - [ ] Create Flyway migration scripts
  - [ ] Create tables: users, projects, specifications, validation_snapshots
  - [ ] Create JPA entities
  - [ ] Create repositories

- [ ] **GitHub OAuth**
  - [ ] Register GitHub OAuth App
  - [ ] Configure Spring Security
  - [ ] Implement CustomOAuth2UserService
  - [ ] Create JWT token provider

- [ ] **API Endpoints**
  - [ ] AuthController (/api/v1/auth)
  - [ ] ProjectController (/api/v1/projects)
  - [ ] SpecificationManagementController (/api/v1/projects/{id}/specifications)
  - [ ] Update existing SessionController for hybrid support

- [ ] **Service Layer**
  - [ ] ProjectService
  - [ ] SpecificationService
  - [ ] UserService
  - [ ] Update SessionService for hybrid mode

### Frontend Tasks

- [ ] **Authentication UI**
  - [ ] LoginPage component
  - [ ] OAuth2RedirectHandler
  - [ ] PrivateRoute wrapper
  - [ ] authService API

- [ ] **Project Management UI**
  - [ ] ProjectsPage (dashboard)
  - [ ] CreateProjectModal
  - [ ] ProjectCard component
  - [ ] projectService API

- [ ] **Editor Integration**
  - [ ] Update EditorPage to load from projects
  - [ ] Add "Save Version" button
  - [ ] Version history panel
  - [ ] Commit message input

- [ ] **Navigation**
  - [ ] Update routing (React Router)
  - [ ] Add user menu (logout, profile)
  - [ ] Breadcrumbs for navigation

### Testing & Deployment

- [ ] **Testing**
  - [ ] Test OAuth flow
  - [ ] Test project CRUD
  - [ ] Test spec versioning
  - [ ] Test unauthorized access

- [ ] **Environment Setup**
  - [ ] Production PostgreSQL setup
  - [ ] Environment variables for secrets
  - [ ] GitHub OAuth production app

- [ ] **Documentation**
  - [ ] API documentation updates
  - [ ] User guide for projects/versions
  - [ ] Deployment guide

---

## 🔒 Security Considerations

1. **HTTPS Required**: Use HTTPS in production for OAuth
2. **Secret Management**: Store secrets in environment variables, not code
3. **CORS**: Restrict to specific domains in production
4. **SQL Injection**: Use parameterized queries (JPA handles this)
5. **XSS Protection**: Sanitize user inputs
6. **Rate Limiting**: Add rate limiting to prevent abuse
7. **Token Expiration**: Implement token refresh mechanism

---

## 📊 Database Indexes for Performance

```sql
-- Additional indexes for performance
CREATE INDEX idx_specifications_created_at ON specifications(created_at DESC);
CREATE INDEX idx_specifications_composite ON specifications(project_id, is_current, created_at DESC);
CREATE INDEX idx_projects_composite ON projects(user_id, created_at DESC);
```

---

## 🎯 Success Metrics

After implementation:
- ✅ Users can login with GitHub
- ✅ Users can create multiple projects
- ✅ Each project can have multiple spec versions
- ✅ Users can revert to previous versions
- ✅ Anonymous editing still works (backward compatible)
- ✅ All existing features work with authentication

---

## 📦 Estimated Timeline

- **Phase 1** (Database Setup): 2-3 days
- **Phase 2** (OAuth): 2-3 days
- **Phase 3** (Backend APIs): 3-4 days
- **Phase 4** (Frontend): 3-4 days
- **Phase 5** (Migration): 1-2 days
- **Phase 6** (Testing): 2-3 days

**Total: 13-19 days** (about 2-3 weeks)

---

## 🚦 Next Steps

1. **Immediate**: Set up PostgreSQL database
2. **Set up GitHub OAuth App**
3. **Start with Phase 1**: Database schema & entities
4. **Implement incrementally**: Test each phase before moving forward

Would you like to start implementing any specific phase?
