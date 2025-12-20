/**
 * Repository Service - API client for repository operations
 *
 * Provides methods to connect to and browse repositories via MCP integration.
 */

import axios from "axios";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8080/api/v1";

/**
 * Connect to a repository provider (GitHub, GitLab, etc.)
 *
 * @param {string} sessionId - Session ID
 * @param {string} provider - Provider name (github, gitlab)
 * @param {string} accessToken - OAuth access token
 * @returns {Promise<{success: boolean, message: string, provider: string}>}
 */
export const connectRepository = async (sessionId, provider, accessToken) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/repository/connect`,
      {
        provider,
        accessToken,
      },
      {
        headers: {
          "X-Session-ID": sessionId,
          "Content-Type": "application/json",
        },
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Error connecting to repository:", error);
    return {
      success: false,
      error:
        error.response?.data?.message ||
        error.message ||
        "Failed to connect to repository",
    };
  }
};

/**
 * Disconnect from repository provider
 *
 * @param {string} sessionId - Session ID
 * @returns {Promise<{success: boolean}>}
 */
export const disconnectRepository = async (sessionId) => {
  try {
    await axios.post(
      `${API_BASE_URL}/repository/disconnect`,
      {},
      {
        headers: {
          "X-Session-ID": sessionId,
        },
      },
    );

    return { success: true };
  } catch (error) {
    console.error("Error disconnecting from repository:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * Browse repository tree at a specific path
 *
 * @param {string} sessionId - Session ID
 * @param {Object} params - Browse parameters
 * @param {string} params.owner - Repository owner
 * @param {string} params.repo - Repository name
 * @param {string} params.path - Path in repository (default: "")
 * @param {string} params.branch - Branch name (optional)
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const browseTree = async (
  sessionId,
  { owner, repo, path = "", branch = null },
) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/repository/browse`,
      {
        owner,
        repo,
        path,
        branch,
      },
      {
        headers: {
          "X-Session-ID": sessionId,
          "Content-Type": "application/json",
        },
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Error browsing repository tree:", error);
    return {
      success: false,
      error:
        error.response?.data?.message ||
        error.message ||
        "Failed to browse repository",
    };
  }
};

/**
 * Read file content from repository
 *
 * @param {string} sessionId - Session ID
 * @param {Object} params - File parameters
 * @param {string} params.owner - Repository owner
 * @param {string} params.repo - Repository name
 * @param {string} params.path - File path
 * @param {string} params.ref - Git reference (branch, tag, commit) (optional)
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const readFile = async (
  sessionId,
  { owner, repo, path, ref = null },
) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/repository/file`,
      {
        owner,
        repo,
        path,
        ref,
      },
      {
        headers: {
          "X-Session-ID": sessionId,
          "Content-Type": "application/json",
        },
      },
    );

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Error reading file:", error);
    return {
      success: false,
      error:
        error.response?.data?.message || error.message || "Failed to read file",
    };
  }
};

/**
 * Get repository connection status for session
 *
 * @param {string} sessionId - Session ID
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const getConnectionStatus = async (sessionId) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/repository/status`, {
      headers: {
        "X-Session-ID": sessionId,
      },
    });

    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error("Error getting connection status:", error);
    return {
      success: false,
      error: error.response?.data?.message || error.message,
    };
  }
};

/**
 * GitHub OAuth - Get authorization URL
 *
 * @param {string} clientId - GitHub OAuth App Client ID
 * @param {string} redirectUri - Redirect URI after authorization
 * @param {Array<string>} scopes - OAuth scopes (default: ['repo'])
 * @returns {string} Authorization URL
 */
export const getGitHubAuthUrl = (clientId, redirectUri, scopes = ["repo"]) => {
  const scopeString = scopes.join(" ");
  const state = Math.random().toString(36).substring(7); // Random state for CSRF protection

  // Store state in sessionStorage for verification
  sessionStorage.setItem("github_oauth_state", state);

  return `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(
    redirectUri,
  )}&scope=${encodeURIComponent(scopeString)}&state=${state}`;
};

/**
 * Verify GitHub OAuth state
 *
 * @param {string} state - State parameter from OAuth callback
 * @returns {boolean} True if state is valid
 */
export const verifyGitHubOAuthState = (state) => {
  const storedState = sessionStorage.getItem("github_oauth_state");
  sessionStorage.removeItem("github_oauth_state");
  return storedState === state;
};

/**
 * Parse repository URL to extract owner and repo name
 *
 * @param {string} url - Repository URL (e.g., https://github.com/owner/repo)
 * @returns {{owner: string, name: string} | null}
 */
export const parseRepositoryUrl = (url) => {
  try {
    const match = url.match(/github\.com\/([^\/]+)\/([^\/]+)/);
    if (match) {
      const owner = match[1];
      const name = match[2].replace(/\.git$/, ""); // Remove .git suffix if present
      return {
        owner: owner,
        name: name,
        fullName: `${owner}/${name}`,
      };
    }
    return null;
  } catch (error) {
    console.error("Error parsing repository URL:", error);
    return null;
  }
};
