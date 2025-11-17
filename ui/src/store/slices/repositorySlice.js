/**
 * Repository Slice - Zustand state management for repository operations
 *
 * Manages connection to repository providers, browsing, and file operations.
 */

import {
    connectRepository,
    disconnectRepository,
    browseTree,
    readFile,
    getConnectionStatus
} from '../../api/repositoryService';

export const createRepositorySlice = (set, get) => ({
    // --- STATE ---

    // Connection state
    isConnected: false,
    provider: null,  // 'github', 'gitlab', etc.
    connectionError: null,
    isConnecting: false,

    // Repository browsing
    currentRepo: null,  // { owner, name, fullName, defaultBranch, ... }
    currentPath: '',
    currentBranch: null,
    files: [],  // Current directory contents
    isBrowsing: false,
    browseError: null,

    // File reading
    currentFile: null,  // { path, content, size, ... }
    isReadingFile: false,
    fileError: null,

    // OAuth state
    oauthInProgress: false,
    accessToken: null,

    // --- ACTIONS ---

    /**
     * Connect to a repository provider
     */
    connectToRepository: async (sessionId, provider, accessToken) => {
        set({ isConnecting: true, connectionError: null });

        const result = await connectRepository(sessionId, provider, accessToken);

        if (result.success) {
            set({
                isConnected: true,
                provider: provider,
                accessToken: accessToken,
                isConnecting: false,
                connectionError: null
            });
        } else {
            set({
                isConnected: false,
                connectionError: result.error,
                isConnecting: false
            });
        }

        return result;
    },

    /**
     * Disconnect from repository provider
     */
    disconnectFromRepository: async (sessionId) => {
        set({ isConnecting: true });

        const result = await disconnectRepository(sessionId);

        if (result.success) {
            set({
                isConnected: false,
                provider: null,
                accessToken: null,
                currentRepo: null,
                currentPath: '',
                files: [],
                currentFile: null,
                isConnecting: false
            });
        } else {
            set({ isConnecting: false });
        }

        return result;
    },

    /**
     * Browse repository tree
     */
    browseRepositoryTree: async (sessionId, owner, repo, path = '', branch = null) => {
        set({ isBrowsing: true, browseError: null });

        const result = await browseTree(sessionId, { owner, repo, path, branch });

        if (result.success) {
            set({
                files: result.data.files || [],
                currentPath: path,
                currentBranch: branch || result.data.branch,
                isBrowsing: false,
                browseError: null
            });

            // Update current repo info if not set
            if (!get().currentRepo || get().currentRepo.name !== repo) {
                set({
                    currentRepo: {
                        owner,
                        name: repo,
                        fullName: `${owner}/${repo}`
                    }
                });
            }
        } else {
            set({
                browseError: result.error,
                isBrowsing: false,
                files: []
            });
        }

        return result;
    },

    /**
     * Read file from repository
     */
    readRepositoryFile: async (sessionId, owner, repo, path, ref = null) => {
        set({ isReadingFile: true, fileError: null });

        const result = await readFile(sessionId, { owner, repo, path, ref });

        if (result.success) {
            set({
                currentFile: result.data,
                isReadingFile: false,
                fileError: null
            });
        } else {
            set({
                currentFile: null,
                fileError: result.error,
                isReadingFile: false
            });
        }

        return result;
    },

    /**
     * Set current repository
     */
    setCurrentRepository: (repoInfo) => set({ currentRepo: repoInfo }),

    /**
     * Navigate to parent directory
     */
    navigateToParent: async (sessionId) => {
        const { currentRepo, currentPath, currentBranch } = get();

        if (!currentRepo || !currentPath) return;

        // Calculate parent path
        const pathParts = currentPath.split('/').filter(p => p);
        pathParts.pop();
        const parentPath = pathParts.join('/');

        return get().browseRepositoryTree(
            sessionId,
            currentRepo.owner,
            currentRepo.name,
            parentPath,
            currentBranch
        );
    },

    /**
     * Navigate to directory
     */
    navigateToDirectory: async (sessionId, dirPath) => {
        const { currentRepo, currentBranch } = get();

        if (!currentRepo) return;

        return get().browseRepositoryTree(
            sessionId,
            currentRepo.owner,
            currentRepo.name,
            dirPath,
            currentBranch
        );
    },

    /**
     * Load spec file into editor
     */
    loadSpecFromRepository: async (sessionId, owner, repo, path, ref = null) => {
        const result = await get().readRepositoryFile(sessionId, owner, repo, path, ref);

        if (result.success) {
            // Return the file content to be loaded into the editor
            return {
                success: true,
                content: result.data.content,
                path: result.data.path
            };
        }

        return result;
    },

    /**
     * Filter files to show only OpenAPI specs
     */
    getOpenApiSpecs: () => {
        const { files } = get();
        return files.filter(file =>
            file.type === 'file' && file.isOpenApiSpec
        );
    },

    /**
     * Check connection status
     */
    checkConnectionStatus: async (sessionId) => {
        const result = await getConnectionStatus(sessionId);

        if (result.success && result.data.success) {
            set({
                isConnected: true,
                provider: result.data.provider
            });
        } else {
            set({
                isConnected: false,
                provider: null
            });
        }

        return result;
    },

    /**
     * Set OAuth state
     */
    setOAuthInProgress: (inProgress) => set({ oauthInProgress: inProgress }),

    /**
     * Set access token
     */
    setAccessToken: (token) => set({ accessToken: token }),

    /**
     * Clear errors
     */
    clearErrors: () => set({
        connectionError: null,
        browseError: null,
        fileError: null
    }),

    /**
     * Reset repository state
     */
    resetRepositoryState: () => set({
        isConnected: false,
        provider: null,
        connectionError: null,
        isConnecting: false,
        currentRepo: null,
        currentPath: '',
        currentBranch: null,
        files: [],
        isBrowsing: false,
        browseError: null,
        currentFile: null,
        isReadingFile: false,
        fileError: null,
        oauthInProgress: false,
        accessToken: null
    })
});
