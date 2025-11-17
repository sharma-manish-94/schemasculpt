/**
 * RepositoryPanel - Main container for repository integration
 *
 * Combines GitHubConnect and RepositoryBrowser, handles spec loading.
 */

import React, { useState } from 'react';
import { useSpecStore } from '../../../store/specStore';
import GitHubConnect from './GitHubConnect';
import RepositoryBrowser from './RepositoryBrowser';
import './RepositoryPanel.css';

const RepositoryPanel = ({ onClose }) => {
    const {
        sessionId,
        isConnected,
        currentRepo,
        loadSpecFromRepository,
        setSpecText,
        isReadingFile,
        fileError
    } = useSpecStore();

    const [repoInfo, setRepoInfo] = useState(null);
    const [loadingSpec, setLoadingSpec] = useState(false);
    const [loadError, setLoadError] = useState(null);

    const handleConnected = (repo) => {
        if (repo) {
            // Quick load scenario - user provided repo URL
            setRepoInfo(repo);
        }
    };

    const handleFileSelect = async (file) => {
        if (!file || file.type !== 'file') return;

        if (!file.isOpenApiSpec) {
            const confirmLoad = window.confirm(
                `${file.name} may not be an OpenAPI specification. Load it anyway?`
            );
            if (!confirmLoad) return;
        }

        setLoadingSpec(true);
        setLoadError(null);

        try {
            const result = await loadSpecFromRepository(
                sessionId,
                currentRepo.owner,
                currentRepo.name,
                file.path,
                null
            );

            if (result.success) {
                // Load the content into the editor
                setSpecText(result.content);

                // Show success message
                alert(`Successfully loaded ${file.name}`);

                // Close the panel
                if (onClose) {
                    onClose();
                }
            } else {
                setLoadError(result.error || 'Failed to load file');
            }
        } catch (error) {
            console.error('Error loading spec:', error);
            setLoadError(error.message || 'An unexpected error occurred');
        } finally {
            setLoadingSpec(false);
        }
    };

    return (
        <div className="repository-panel">
            <div className="panel-header">
                <h2>Import from Repository</h2>
                {onClose && (
                    <button onClick={onClose} className="close-button" aria-label="Close">
                        ×
                    </button>
                )}
            </div>

            <div className="panel-content">
                {!isConnected ? (
                    <GitHubConnect onConnected={handleConnected} />
                ) : (
                    <>
                        <GitHubConnect onConnected={handleConnected} />
                        <div className="browser-section">
                            {repoInfo || currentRepo ? (
                                <RepositoryBrowser
                                    repoInfo={repoInfo || currentRepo}
                                    onFileSelect={handleFileSelect}
                                />
                            ) : (
                                <div className="prompt-message">
                                    <p>Enter a repository URL above to get started.</p>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {(loadingSpec || isReadingFile) && (
                    <div className="loading-overlay">
                        <div className="loading-spinner"></div>
                        <p>Loading specification...</p>
                    </div>
                )}

                {(loadError || fileError) && (
                    <div className="error-message">
                        <strong>Error:</strong> {loadError || fileError}
                        <button onClick={() => setLoadError(null)} className="dismiss-error">
                            ×
                        </button>
                    </div>
                )}
            </div>

            <div className="panel-footer">
                <div className="help-text">
                    <strong>Tip:</strong> Connect to GitHub to browse and import OpenAPI specifications from your repositories.
                </div>
            </div>
        </div>
    );
};

export default RepositoryPanel;
