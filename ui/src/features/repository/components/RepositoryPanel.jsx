/**
 * RepositoryPanel - Main container for repository integration
 *
 * Combines GitHubConnect and RepositoryBrowser, handles spec loading.
 */

import React, { useState } from "react";
import { useSpecStore } from "../../../store/specStore";
import GitHubConnect from "./GitHubConnect";
import RepositoryBrowser from "./RepositoryBrowser";
import DirectoryPicker from "./DirectoryPicker";
import "./RepositoryPanel.css";

const LocalRepoConnector = () => {
  const {
    sessionId,
    localRepositoryPath,
    isLinkingLocalRepo,
    linkLocalRepoError,
  } = useSpecStore();

  const [path, setPath] = useState("");
  const [showPicker, setShowPicker] = useState(false);
  const [status, setStatus] = useState(null); // null | "success" | "error"
  const [statusMsg, setStatusMsg] = useState("");

  const handleLinkRepository = async () => {
    if (!path) return;
    if (!sessionId) {
      setStatus("error");
      setStatusMsg("No active session. Please refresh the page and try again.");
      return;
    }

    setStatus(null);
    setStatusMsg("");

    const { linkLocalRepositoryBySession, getRepoMindHealth } =
      await import("../../../api/repositoryService");

    // Check RepoMind availability in parallel with linking
    const [result, health] = await Promise.all([
      linkLocalRepositoryBySession(sessionId, path),
      getRepoMindHealth(),
    ]);

    if (result.success) {
      useSpecStore.setState({ localRepositoryPath: path });
      const repoName = result.data?.repoName || path;
      if (health.available) {
        setStatus("success");
        setStatusMsg(
          `Repository "${repoName}" linked! Indexing started in the background. ` +
            `Now, select an endpoint from the "API Structure" panel to view its implementation and contract integrity.`,
        );
      } else {
        setStatus("warning");
        setStatusMsg(
          `Repository path saved, but RepoMind is not running — indexing skipped. ` +
            `Start RepoMind to enable code intelligence (REPOMIND_ENABLED=true).`,
        );
      }
    } else {
      setStatus("error");
      setStatusMsg(result.error || "Failed to link repository.");
    }
  };

  const handleDirectorySelected = (selectedPath) => {
    setPath(selectedPath);
  };

  return (
    <div className="local-repo-connector">
      <div className="local-repo-divider">
        <span>OR</span>
      </div>

      <div className="local-repo-card">
        <h3 className="local-repo-title">💻 Connect a Local Repository</h3>

        {localRepositoryPath ? (
          <div className="local-repo-linked">
            <span className="local-repo-linked-icon">✅</span>
            <div>
              <div className="local-repo-linked-label">Currently linked</div>
              <code className="local-repo-linked-path">
                {localRepositoryPath}
              </code>
            </div>
          </div>
        ) : (
          <p className="local-repo-description">
            Select your local source code repository to enable{" "}
            <strong>Code-Aware Analysis</strong> — AI that understands your
            actual implementation.
          </p>
        )}

        <div className="local-repo-section">
          <label className="local-repo-label" htmlFor="local-repo-path">
            Repository Path
          </label>
          <div className="local-repo-input-row">
            <input
              id="local-repo-path"
              type="text"
              className="form-control"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/home/user/projects/my-api"
              disabled={isLinkingLocalRepo}
              aria-label="Local repository path"
            />
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setShowPicker(true)}
              disabled={isLinkingLocalRepo}
              title="Browse for folder"
            >
              📂 Browse
            </button>
          </div>
          <button
            type="button"
            className="btn btn-primary local-repo-link-btn"
            onClick={handleLinkRepository}
            disabled={isLinkingLocalRepo || !path}
          >
            {isLinkingLocalRepo ? "Linking…" : "🔗 Link & Index"}
          </button>
        </div>

        {status === "success" && (
          <div className="local-repo-status local-repo-status--success">
            ✅ {statusMsg}
          </div>
        )}
        {status === "warning" && (
          <div className="local-repo-status local-repo-status--warning">
            ⚠️ {statusMsg}
          </div>
        )}
        {(status === "error" || linkLocalRepoError) && (
          <div className="local-repo-status local-repo-status--error">
            ❌ {statusMsg || linkLocalRepoError}
          </div>
        )}
      </div>

      {showPicker && (
        <DirectoryPicker
          onSelect={handleDirectorySelected}
          onClose={() => setShowPicker(false)}
        />
      )}
    </div>
  );
};

const RepositoryPanel = ({ onClose }) => {
  const {
    sessionId,
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
