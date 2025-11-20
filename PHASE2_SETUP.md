# Phase 2: GitHub OAuth Setup - COMPLETED ✅

## What We've Implemented

### Security Infrastructure
- ✅ `CustomOAuth2User` - Custom principal with User entity
- ✅ `CustomOAuth2UserService` - OAuth2 user processing and database sync
- ✅ `JwtTokenProvider` - JWT token generation and validation
- ✅ `JwtAuthenticationFilter` - JWT token authentication filter
- ✅ `SecurityConfig` - Spring Security configuration
- ✅ `AuthController` - Authentication REST endpoints

### DTOs
- ✅ `TokenResponse` - JWT token response
- ✅ `UserDTO` - User data transfer object

---

## 🚀 Setup Instructions

### Step 1: Configure GitHub OAuth Credentials

1. **Create `.env` file** from template:
   ```bash
   cd api
   cp .env.template .env
   ```

2. **Edit `.env`** and add your GitHub OAuth credentials:
   ```bash
   GITHUB_CLIENT_ID=your_actual_client_id
   GITHUB_CLIENT_SECRET=your_actual_client_secret
   JWT_SECRET=$(openssl rand -base64 32)
   DB_PASSWORD=postgres
   ```

3. **Load environment variables** (choose one method):

   **Method A: Export in terminal** (temporary)
   ```bash
   export $(cat .env | xargs)
   ```

   **Method B: Use direnv** (automatic, recommended)
   ```bash
   # Install direnv
   # Ubuntu/Debian
   sudo apt install direnv

   # macOS
   brew install direnv

   # Add to ~/.bashrc or ~/.zshrc
   eval "$(direnv hook bash)"  # or zsh

   # Allow directory
   direnv allow .
   ```

   **Method C: IDE Configuration**
   - IntelliJ IDEA: Run > Edit Configurations > Environment Variables
   - VS Code: Add to launch.json

---

### Step 2: Test the Setup

1. **Build the application**:
   ```bash
   ./mvnw clean compile
   ```

2. **Start Spring Boot**:
   ```bash
   ./mvnw spring-boot:run
   ```

3. **Check logs** for:
   ```
   ✅ Flyway migration successful
   ✅ SecurityConfig loaded
   ✅ OAuth2 client configured
   ✅ Application started on port 8080
   ```

4. **Test health endpoint**:
   ```bash
   curl http://localhost:8080/api/v1/auth/health
   # Expected: "Authentication service is running"
   ```

---

## 🔐 OAuth Flow

### How it Works:

```
1. User clicks "Login with GitHub" in React app
   ↓
2. Redirected to: http://localhost:8080/oauth2/authorization/github
   ↓
3. GitHub OAuth login page
   ↓
4. User authorizes app
   ↓
5. GitHub redirects to: http://localhost:8080/login/oauth2/code/github
   ↓
6. CustomOAuth2UserService:
   - Fetches user from GitHub
   - Creates/updates user in database
   - Creates CustomOAuth2User principal
   ↓
7. Redirected to: http://localhost:3000/oauth2/redirect
   ↓
8. Frontend calls: POST /api/v1/auth/token
   ↓
9. Backend generates JWT token
   ↓
10. Frontend stores token in localStorage
   ↓
11. Frontend uses token for all API calls:
    Header: Authorization: Bearer <token>
```

---

## 📡 API Endpoints

### Public Endpoints
```
GET  /api/v1/auth/health          - Health check
POST /api/v1/auth/logout          - Logout (clears session)
GET  /oauth2/authorization/github - Start OAuth flow
```

### Protected Endpoints (Require JWT Token)
```
GET  /api/v1/auth/me    - Get current user info
POST /api/v1/auth/token - Generate JWT token (after OAuth)
```

### Example API Calls

**1. Get current user (with JWT)**:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8080/api/v1/auth/me
```

**Response:**
```json
{
  "id": 1,
  "githubId": "12345678",
  "username": "yourname",
  "email": "you@example.com",
  "avatarUrl": "https://avatars.githubusercontent.com/u/12345678",
  "createdAt": "2025-10-04T18:30:00"
}
```

**2. Generate JWT token** (called by frontend after OAuth):
```bash
# This endpoint requires OAuth2 session
# Frontend calls this automatically after OAuth redirect
curl -X POST http://localhost:8080/api/v1/auth/token \
  -H "Cookie: JSESSIONID=..." \
  -c cookies.txt
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzUxMiJ9...",
  "tokenType": "Bearer",
  "expiresIn": 86400,
  "userId": 1,
  "username": "yourname",
  "email": "you@example.com",
  "avatarUrl": "https://..."
}
```

---

## 🧪 Manual Testing

### Test 1: Start OAuth Flow
```bash
# Open in browser:
http://localhost:8080/oauth2/authorization/github

# Should redirect to GitHub login
# After login, redirects to http://localhost:3000/oauth2/redirect
```

### Test 2: Check Database
```bash
psql -U postgres -d schemasculpt

# Check if user was created
SELECT * FROM users;

# Expected output: Your GitHub user info
```

---

## ⚙️ Security Configuration Details

### CORS Settings
- Allowed Origins: `http://localhost:3000`, `http://localhost:3001`
- Allowed Methods: `GET, POST, PUT, DELETE, OPTIONS, PATCH`
- Credentials: Enabled

### Session Management
- Strategy: `STATELESS` (JWT-based)
- No server-side sessions (except during OAuth flow)

### Protected Routes
- `/api/v1/projects/**` - Requires authentication
- `/api/v1/specifications/**` - Requires authentication

### Public Routes (Backward Compatible)
- `/api/v1/sessions/**` - Public (for migration period)
- `/api/v1/explanations/**` - Public
- `/proxy/**` - Public

---

## 🐛 Troubleshooting

### Issue 1: OAuth redirect fails
**Error**: `redirect_uri_mismatch`

**Solution**: Check GitHub OAuth App settings:
- Authorization callback URL must be: `http://localhost:8080/login/oauth2/code/github`

### Issue 2: JWT token invalid
**Error**: `Invalid JWT signature`

**Solution**: Check JWT secret:
```bash
# Make sure JWT_SECRET is set and consistent
echo $JWT_SECRET

# Restart Spring Boot after changing it
```

### Issue 3: User not created in database
**Check logs**:
```bash
# Look for:
Creating new user: username
User processed successfully: 1
```

**Check database**:
```sql
SELECT * FROM users ORDER BY id DESC LIMIT 1;
```

### Issue 4: CORS errors
**Error**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**: Check `application.properties`:
```properties
app.cors.allowed-origins=http://localhost:3000,http://localhost:3001
```

---

## ✅ Validation Checklist

Before moving to Phase 3, verify:

- [ ] `.env` file created with GitHub credentials
- [ ] Environment variables loaded
- [ ] Spring Boot starts without errors
- [ ] Can access health endpoint
- [ ] OAuth flow redirects to GitHub
- [ ] After GitHub login, user created in database
- [ ] JWT token generated successfully
- [ ] Protected endpoints require authentication
- [ ] Public endpoints still work

---

## 📊 Database Changes

Check users table:
```sql
-- Connect to database
psql -U postgres -d schemasculpt

-- View users
SELECT id, github_id, username, email, created_at FROM users;

-- Example output:
--  id | github_id | username  |     email        |      created_at
-- ----+-----------+-----------+------------------+---------------------
--   1 | 12345678  | yourname  | you@example.com  | 2025-10-04 18:30:00
```

---

## 🎯 Next Steps: Phase 3

Once authentication is working, we'll implement:
1. **Project Management** - Create, list, delete projects
2. **Specification Management** - Save and version specs
3. **Service Layer** - Business logic for projects/specs
4. **REST Controllers** - API endpoints for projects

All of these will be **protected by JWT authentication**!

---

## 📝 Files Created in Phase 2

**Security:**
- `security/CustomOAuth2User.java`
- `security/CustomOAuth2UserService.java`
- `security/JwtTokenProvider.java`
- `security/JwtAuthenticationFilter.java`
- `security/SecurityConfig.java`

**DTOs:**
- `dto/auth/TokenResponse.java`
- `dto/auth/UserDTO.java`

**Controllers:**
- `controller/auth/AuthController.java`

**Config:**
- `.env.template`
- Updated `.gitignore`

**Total:** 9 new files

---

Ready to test! 🚀

Once you verify authentication works, we'll move to **Phase 3: Project & Specification Management**.
