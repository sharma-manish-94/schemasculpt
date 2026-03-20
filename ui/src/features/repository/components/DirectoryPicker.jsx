/**
 * DirectoryPicker - Modal for browsing local filesystem directories.
 * Calls the backend filesystem browse API to navigate directories.
 */
import React, { useCallback, useEffect, useState } from "react";
import { browseLocalFilesystem } from "../../../api/repositoryService";

const DirectoryPicker = ({ onSelect, onClose }) => {
  const [currentPath, setCurrentPath] = useState("");
  const [parentPath, setParentPath] = useState("");
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputPath, setInputPath] = useState("");

  const browse = useCallback(async (path) => {
    setLoading(true);
    setError(null);
    const result = await browseLocalFilesystem(path);
    setLoading(false);
    if (result.success) {
      setCurrentPath(result.data.currentPath);
      setParentPath(result.data.parentPath);
      setEntries(result.data.entries);
      setInputPath(result.data.currentPath);
    } else {
      setError(result.error);
    }
  }, []);

  useEffect(() => {
    browse("");
  }, [browse]);

  const handleEntryClick = (entry) => {
    if (entry.readable === "true") {
      browse(entry.path);
    }
  };

  const handleGoUp = () => {
    if (parentPath) browse(parentPath);
  };

  const handleNavigateInput = (e) => {
    e.preventDefault();
    if (inputPath) browse(inputPath);
  };

  const handleSelect = () => {
    onSelect(currentPath);
    onClose();
  };

  return (
    <div className="dir-picker-overlay" onClick={onClose}>
      <div
        className="dir-picker-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Browse for directory"
      >
        <div className="dir-picker-header">
          <span>Browse for Folder</span>
          <button
            className="dir-picker-close"
            onClick={onClose}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form className="dir-picker-nav" onSubmit={handleNavigateInput}>
          <input
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="/path/to/directory"
            aria-label="Directory path"
          />
          <button type="submit">Go</button>
        </form>

        <div className="dir-picker-body">
          {loading && <div className="dir-picker-loading">Loading...</div>}
          {error && <div className="dir-picker-error">{error}</div>}
          {!loading && (
            <ul className="dir-picker-list">
              {parentPath && (
                <li
                  className="dir-picker-entry dir-picker-up"
                  onClick={handleGoUp}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && handleGoUp()}
                >
                  <span className="dir-icon">📁</span>
                  <span>..</span>
                </li>
              )}
              {entries.map((entry) => (
                <li
                  key={entry.path}
                  className={`dir-picker-entry${entry.readable === "false" ? " unreadable" : ""}`}
                  onClick={() => handleEntryClick(entry)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) =>
                    e.key === "Enter" && handleEntryClick(entry)
                  }
                >
                  <span className="dir-icon">📁</span>
                  <span>{entry.name}</span>
                </li>
              ))}
              {entries.length === 0 && !loading && (
                <li className="dir-picker-empty">No subdirectories found</li>
              )}
            </ul>
          )}
        </div>

        <div className="dir-picker-footer">
          <div className="dir-picker-selected">
            Selected: <code>{currentPath || "—"}</code>
          </div>
          <div className="dir-picker-actions">
            <button className="btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              className="btn-primary"
              onClick={handleSelect}
              disabled={!currentPath}
            >
              Select This Folder
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DirectoryPicker;
