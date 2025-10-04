# SchemaSculpt API - Bruno Collection

This Bruno collection provides comprehensive API testing for SchemaSculpt.

## Setup

1. **Install Bruno**: https://www.usebruno.com/downloads
2. **Open Collection**: Open this folder in Bruno
3. **Select Environment**: Choose "local" environment

## Authentication Flow

### Option 1: Browser OAuth (Recommended)

1. Open `http://localhost:8080/oauth2/authorization/github` in your browser
2. Login with GitHub
3. After redirect, open browser console (F12)
4. Run: `localStorage.getItem('token')`
5. Copy the token
6. In Bruno, set the `token` environment variable to the copied value

### Option 2: Manual Token Extraction

If you already logged in via the frontend:

1. Open the frontend (http://localhost:3000)
2. Open browser console (F12)
3. Run: `localStorage.getItem('token')`
4. Copy the token
5. In Bruno, paste it into the `token` environment variable

## API Flow

### 1. Authentication
- **Health Check**: Verify auth service is running
- **Get Current User**: Verify token works

### 2. Projects
- **Create Project**: Creates a new project (saves ID to env)
- **List Projects**: View all your projects
- **Get Project**: View specific project details
- **Update Project**: Modify project details
- **Delete Project**: Remove project and all specs

### 3. Specifications
- **Save Specification**: Create new version (saves version to env)
- **Get Current**: Get latest version
- **List All Versions**: See version history
- **Get Specific Version**: View specific version
- **Revert to Version**: Restore previous version

## Environment Variables

The collection uses these environment variables:

- `baseUrl`: Backend API URL (default: http://localhost:8080)
- `frontendUrl`: Frontend URL (default: http://localhost:3000)
- `token`: JWT authentication token (set after login)
- `projectId`: Current project ID (auto-set after creating project)
- `specificationVersion`: Current spec version (auto-set after saving spec)

## Scripts

Some requests include post-response scripts that automatically save values to environment variables:

- Creating a project saves `projectId`
- Saving a specification saves `specificationVersion`
- Getting a token saves `token`

## Testing Workflow

1. **Authenticate**: Run "Get Current User" to verify token
2. **Create Project**: Run "Create Project" (saves projectId)
3. **Save Spec**: Run "Save Specification" (saves version)
4. **Test Versions**: Run version management endpoints
5. **Cleanup**: Run "Delete Project" when done

## Notes

- All project and specification endpoints require authentication
- Projects are user-specific (you can only access your own)
- Specification versions are auto-numbered (v1, v2, v3...)
- Reverting creates a new version with old content
- Deleting a project deletes all its specifications
