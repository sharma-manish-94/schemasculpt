/**
 * RepositoryPanel - Main container for repository integration
 *
 * Combines GitHubConnect and RepositoryBrowser, handles spec loading.
 */

import React, { useState } from "react";
import { useSpecStore } from "../../../store/specStore";
import GitHubConnect from "./GitHubConnect";
import RepositoryBrowser from "./RepositoryBrowser";
import "./RepositoryPanel.css";

const LocalRepoConnector = () => {
  const {
    projectId,
    linkLocalRepository,
    isLinkingLocalRepo,
    linkLocalRepoError,
    localRepositoryPath,
  } = useSpecStore();

  const [path, setPath] = useState("");

  const handleLinkRepository = async () => {
    if (!path || !projectId) return;
    const result = await linkLocalRepository(projectId, path);
    if (result.success) {
      alert(
        "Successfully linked repository! Indexing will begin in the background.",
      );
    }
  };

  return (
    <div className="local-repo-connector">
      <div className="divider">
        <span>OR</span>
      </div>
      <h4>Connect a Local Repository</h4>
      {localRepositoryPath ? (
        <div>
          <p className="linked-path">
            <strong>Linked Path:</strong> <code>{localRepositoryPath}</code>
          </p>
          <p className="help-text">
            To change the path, enter a new one below and re-link.
          </p>
        </div>
      ) : (
        <p className="help-text">
          Enter the absolute local path to your source code repository to enable
          Code-Aware Analysis.
        </p>
      )}
      <div className="input-group">
        <input
          type="text"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          placeholder="/Users/yourname/Documents/Github/my-project"
          disabled={isLinkingLocalRepo}
          aria-label="Local repository path"
        />
        <button
          onClick={handleLinkRepository}
          disabled={isLinkingLocalRepo || !path}
        >
          {isLinkingLocalRepo ? "Linking..." : "Link & Index"}
        </button>
      </div>
      {linkLocalRepoError && (
        <p className="error-message">{linkLocalRepoError}</p>
      )}
    </div>
  );
};

const RepositoryPanel = ({ onClose }) => {
  const {
    sessionId,
    projectId, // Ensure projectId is available
    isConnected,
    currentRepo,
    loadSpecFromRepository,
    setSpecText,
    isReadingFile,
    fileError,
  } = useSpecStore();

  const [repoInfo, setRepoInfo] = useState(null);
  const [loadingSpec, setLoadingSpec] = useState(false);
  const [loadError, setLoadError] = useState(null);

  const handleConnected = (repo) => {
    if (repo) {
      setRepoInfo(repo);
    }
  };

  const handleFileSelect = async (file) => {
    if (!file || file.type !== "file") return;

    if (!file.isOpenApiSpec) {
      const confirmLoad = window.confirm(
        `${file.name} may not be an OpenAPI specification. Load it anyway?`,
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
        null,
      );

      if (result.success) {
        setSpecText(result.content);
        alert(`Successfully loaded ${file.name}`);
        if (onClose) {
          onClose();
        }
      } else {
        setLoadError(result.error || "Failed to load file");
      }
    } catch (error) {
      console.error("Error loading spec:", error);
      setLoadError(error.message || "An unexpected error occurred");
    } finally {
      setLoadingSpec(false);
    }
  };

  return (
    <div className="repository-panel">
      <div className="panel-header">
        <h2>Repository Integration</h2>
        {onClose && (
          <button onClick={onClose} className="close-button" aria-label="Close">
            ×
          </button>
        )}
      </div>

      <div className="panel-content">
        <GitHubConnect onConnected={handleConnected} />

        <LocalRepoConnector />

        {isConnected && (
          <div className="browser-section">
            <h4>Browse GitHub Repository</h4>
            {repoInfo || currentRepo ? (
              <RepositoryBrowser
                repoInfo={repoInfo || currentRepo}
                onFileSelect={handleFileSelect}
              />
            ) : (
              <div className="prompt-message">
                <p>Enter a GitHub repository URL above to get started.</p>
              </div>
            )}
          </div>
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
            <button
              onClick={() => setLoadError(null)}
              className="dismiss-error"
            >
              ×
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default RepositoryPanel;
