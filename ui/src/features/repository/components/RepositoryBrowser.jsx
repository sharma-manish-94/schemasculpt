/**
 * RepositoryBrowser - Component for browsing repository files
 *
 * Displays repository tree structure and allows navigation and file selection.
 */

import React, { useEffect, useState } from 'react';
import { useSpecStore } from '../../../store/specStore';
import './RepositoryBrowser.css';

const RepositoryBrowser = ({ repoInfo, onFileSelect }) => {
    const {
        sessionId,
        files,
        currentPath,
        currentRepo,
        isBrowsing,
        browseError,
        browseRepositoryTree,
        navigateToParent,
        navigateToDirectory,
        setCurrentRepository
    } = useSpecStore();

    const [showOnlySpecs, setShowOnlySpecs] = useState(false);

    useEffect(() => {
        if (repoInfo && sessionId) {
            // Set current repository
            setCurrentRepository(repoInfo);

            // Load root directory
            browseRepositoryTree(
                sessionId,
                repoInfo.owner,
                repoInfo.name,
                '',
                null
            );
        }
    }, [repoInfo, sessionId]);

    const handleFileClick = async (file) => {
        if (file.type === 'dir') {
            // Navigate into directory
            await navigateToDirectory(sessionId, file.path);
        } else {
            // Select file
            if (onFileSelect) {
                onFileSelect(file);
            }
        }
    };

    const handleParentClick = async () => {
        if (currentPath) {
            await navigateToParent(sessionId);
        }
    };

    const getDisplayFiles = () => {
        if (!files) return [];

        if (showOnlySpecs) {
            return files.filter(f => f.type === 'file' && f.isOpenApiSpec);
        }

        return files;
    };

    const displayFiles = getDisplayFiles();
    const openApiSpecCount = files?.filter(f => f.isOpenApiSpec).length || 0;

    if (!currentRepo) {
        return (
            <div className="repository-browser">
                <div className="empty-state">
                    <p>Select a repository to browse</p>
                </div>
            </div>
        );
    }

    return (
        <div className="repository-browser">
            <div className="browser-header">
                <div className="repo-info">
                    <h3>{currentRepo.fullName || `${currentRepo.owner}/${currentRepo.name}`}</h3>
                    {currentPath && (
                        <div className="current-path">
                            <span className="path-label">Path:</span>
                            <span className="path-value">/{currentPath}</span>
                        </div>
                    )}
                </div>

                <div className="browser-controls">
                    <label className="filter-toggle">
                        <input
                            type="checkbox"
                            checked={showOnlySpecs}
                            onChange={(e) => setShowOnlySpecs(e.target.checked)}
                        />
                        <span>Show only OpenAPI specs ({openApiSpecCount})</span>
                    </label>
                </div>
            </div>

            {browseError && (
                <div className="error-message">
                    <strong>Error:</strong> {browseError}
                </div>
            )}

            {isBrowsing ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading files...</p>
                </div>
            ) : (
                <div className="file-list">
                    {currentPath && (
                        <div className="file-item parent-dir" onClick={handleParentClick}>
                            <span className="file-icon">📁</span>
                            <span className="file-name">..</span>
                        </div>
                    )}

                    {displayFiles.length === 0 ? (
                        <div className="empty-state">
                            <p>
                                {showOnlySpecs
                                    ? 'No OpenAPI specification files found in this directory'
                                    : 'No files found in this directory'}
                            </p>
                        </div>
                    ) : (
                        displayFiles.map((file) => (
                            <div
                                key={file.path}
                                className={`file-item ${file.type} ${file.isOpenApiSpec ? 'openapi-spec' : ''}`}
                                onClick={() => handleFileClick(file)}
                                title={file.path}
                            >
                                <span className="file-icon">
                                    {file.type === 'dir' ? '📁' : file.isOpenApiSpec ? '📄' : '📝'}
                                </span>
                                <span className="file-name">{file.name}</span>
                                {file.isOpenApiSpec && (
                                    <span className="spec-badge">OpenAPI</span>
                                )}
                                {file.size && file.type === 'file' && (
                                    <span className="file-size">{formatFileSize(file.size)}</span>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};

/**
 * Format file size in human-readable format
 */
const formatFileSize = (bytes) => {
    if (!bytes) return '';

    const kb = bytes / 1024;
    if (kb < 1024) {
        return `${kb.toFixed(1)} KB`;
    }

    const mb = kb / 1024;
    return `${mb.toFixed(1)} MB`;
};

export default RepositoryBrowser;
