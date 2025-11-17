/**
 * GitHubConnect - Component for connecting to GitHub via OAuth
 *
 * Handles GitHub OAuth flow and connection to repository provider.
 */

import React, { useState, useEffect } from 'react';
import { useSpecStore } from '../../../store/specStore';
import { getGitHubAuthUrl, verifyGitHubOAuthState, parseRepositoryUrl } from '../../../api/repositoryService';
import './GitHubConnect.css';

const GitHubConnect = ({ onConnected }) => {
    const {
        sessionId,
        isConnected,
        provider,
        isConnecting,
        connectionError,
        connectToRepository,
        disconnectFromRepository,
        setAccessToken,
        setOAuthInProgress,
        clearErrors
    } = useSpecStore();

    const [repoUrl, setRepoUrl] = useState('');
    const [manualToken, setManualToken] = useState('');
    const [useManualAuth, setUseManualAuth] = useState(true); // Default to manual auth

    // GitHub OAuth App credentials (these should be in env variables in production)
    const GITHUB_CLIENT_ID = process.env.REACT_APP_GITHUB_CLIENT_ID || 'YOUR_GITHUB_CLIENT_ID';
    const REDIRECT_URI = process.env.REACT_APP_GITHUB_REDIRECT_URI || 'http://localhost:3000/oauth/callback';

    useEffect(() => {
        // Check if we're returning from OAuth callback
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');

        if (code && state) {
            handleOAuthCallback(code, state);
        }
    }, []);

    const handleOAuthCallback = async (code, state) => {
        // Verify state to prevent CSRF
        if (!verifyGitHubOAuthState(state)) {
            console.error('Invalid OAuth state - possible CSRF attack');
            return;
        }

        // In a real app, you would exchange the code for an access token on your backend
        // For now, we'll show a message that the user needs to use manual token
        console.log('OAuth code received:', code);
        setUseManualAuth(true);

        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname);
    };

    const handleOAuthLogin = () => {
        const authUrl = getGitHubAuthUrl(GITHUB_CLIENT_ID, REDIRECT_URI, ['repo']);
        setOAuthInProgress(true);
        window.location.href = authUrl;
    };

    const handleManualConnect = async () => {
        if (!manualToken.trim()) {
            alert('Please enter a GitHub Personal Access Token');
            return;
        }

        if (!sessionId) {
            alert('No active session. Please create a session first.');
            return;
        }

        clearErrors();

        const result = await connectToRepository(sessionId, 'github', manualToken);

        if (result.success) {
            setAccessToken(manualToken);
            if (onConnected) {
                onConnected();
            }
        }
    };

    const handleDisconnect = async () => {
        if (!sessionId) return;

        await disconnectFromRepository(sessionId);
    };

    const handleQuickLoad = async () => {
        if (!repoUrl.trim()) {
            alert('Please enter a repository URL');
            return;
        }

        const parsed = parseRepositoryUrl(repoUrl);
        if (!parsed) {
            alert('Invalid repository URL. Expected format: https://github.com/owner/repo');
            return;
        }

        // First ensure we're connected
        if (!isConnected) {
            if (!manualToken.trim()) {
                alert('Please connect to GitHub first or enter an access token');
                return;
            }
            await handleManualConnect();
        }

        // Navigate to the repository (this will be handled by RepositoryBrowser)
        if (onConnected) {
            onConnected(parsed);
        }
    };

    if (isConnected) {
        return (
            <div className="github-connect connected">
                <div className="connection-status">
                    <span className="status-icon">✓</span>
                    <span className="status-text">Connected to GitHub</span>
                </div>
                <button
                    onClick={handleDisconnect}
                    className="btn btn-secondary"
                    disabled={isConnecting}
                >
                    Disconnect
                </button>
            </div>
        );
    }

    return (
        <div className="github-connect">
            <h3>Connect to GitHub</h3>

            {connectionError && (
                <div className="error-message">
                    <strong>Error:</strong> {connectionError}
                </div>
            )}

            <div className="connect-options">
                <div className="manual-auth-section">
                    <p>
                        Enter your GitHub Personal Access Token.{' '}
                        <a
                            href="https://github.com/settings/tokens/new?scopes=repo&description=SchemaSculpt"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Create one here
                        </a>
                    </p>
                    <div className="form-group">
                        <label htmlFor="github-token">Personal Access Token:</label>
                        <input
                            id="github-token"
                            type="password"
                            value={manualToken}
                            onChange={(e) => setManualToken(e.target.value)}
                            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                            className="form-control"
                            autoFocus
                        />
                    </div>
                    <button
                        onClick={handleManualConnect}
                        className="btn btn-primary"
                        disabled={isConnecting || !manualToken.trim()}
                    >
                        {isConnecting ? 'Connecting...' : 'Connect'}
                    </button>
                </div>
            </div>

            <div className="quick-load-section">
                <h4>Quick Load from URL</h4>
                <p>Or paste a repository URL to quickly load a spec:</p>
                <div className="form-group">
                    <input
                        type="text"
                        value={repoUrl}
                        onChange={(e) => setRepoUrl(e.target.value)}
                        placeholder="https://github.com/owner/repo"
                        className="form-control"
                    />
                </div>
                <button
                    onClick={handleQuickLoad}
                    className="btn btn-secondary"
                    disabled={isConnecting || !repoUrl.trim()}
                >
                    Load Repository
                </button>
            </div>
        </div>
    );
};

export default GitHubConnect;
