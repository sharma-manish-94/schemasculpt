import React, { useState, useCallback, useRef, useEffect } from "react";
import { RedocStandalone } from "redoc";
import PropTypes from "prop-types";
import SpecDownloadButton from "./SpecDownloadButton";
import "./RedocViewer.css";

/**
 * RedocViewer - Enhanced API documentation viewer using Redoc
 *
 * Features:
 * - Beautiful, readable API documentation
 * - Search functionality
 * - Deep linking support
 * - Custom theme matching SchemaSculpt
 * - JSON/YAML download buttons
 * - Custom branding
 */

// Redoc theme configuration matching SchemaSculpt's light theme
const redocTheme = {
  spacing: {
    unit: 5,
    sectionHorizontal: ({ spacing }) => spacing.unit * 8,
    sectionVertical: ({ spacing }) => spacing.unit * 8,
  },
  breakpoints: {
    small: "50rem",
    medium: "85rem",
    large: "105rem",
  },
  colors: {
    tonalOffset: 0.3,
    primary: {
      main: "#0066cc",
      light: "#e6f2ff",
      dark: "#004080",
      contrastText: "#ffffff",
    },
    success: {
      main: "#10b981",
      light: "#d1fae5",
      dark: "#059669",
      contrastText: "#ffffff",
    },
    warning: {
      main: "#f59e0b",
      light: "#fef3c7",
      dark: "#d97706",
      contrastText: "#ffffff",
    },
    error: {
      main: "#ef4444",
      light: "#fee2e2",
      dark: "#dc2626",
      contrastText: "#ffffff",
    },
    text: {
      primary: "#334155",
      secondary: "#64748b",
    },
    border: {
      dark: "#e2e8f0",
      light: "#f1f5f9",
    },
    responses: {
      success: {
        color: "#10b981",
        backgroundColor: "#d1fae5",
      },
      error: {
        color: "#ef4444",
        backgroundColor: "#fee2e2",
      },
      redirect: {
        color: "#3b82f6",
        backgroundColor: "#dbeafe",
      },
      info: {
        color: "#64748b",
        backgroundColor: "#f1f5f9",
      },
    },
    http: {
      get: "#3b82f6",
      post: "#00a86b",
      put: "#f59e0b",
      options: "#64748b",
      patch: "#8b5cf6",
      delete: "#ef4444",
      basic: "#94a3b8",
      link: "#0066cc",
      head: "#64748b",
    },
  },
  schema: {
    nestedBackground: "#f8fafc",
    linesColor: "#e2e8f0",
    defaultDetailsWidth: "75%",
    typeNameColor: "#0066cc",
    typeTitleColor: "#334155",
    requireLabelColor: "#ef4444",
  },
  typography: {
    fontSize: "14px",
    lineHeight: "1.6",
    fontWeightRegular: "400",
    fontWeightBold: "600",
    fontWeightLight: "300",
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
    smoothing: "antialiased",
    optimizeSpeed: true,
    headings: {
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
      fontWeight: "600",
      lineHeight: "1.4em",
    },
    code: {
      fontSize: "13px",
      fontFamily:
        '"SF Mono", "Monaco", "Consolas", "Liberation Mono", "Courier New", monospace',
      fontWeight: "400",
      color: "#1d4ed8",
      backgroundColor: "#f1f5f9",
      wrap: false,
    },
    links: {
      color: "#0066cc",
      visited: "#004080",
      hover: "#0052a3",
    },
  },
  sidebar: {
    backgroundColor: "#ffffff",
    width: "260px",
    textColor: "#334155",
    activeTextColor: "#0066cc",
    groupItems: {
      textTransform: "uppercase",
    },
    level1Items: {
      textTransform: "none",
    },
    arrow: {
      size: "1.5em",
      color: "#64748b",
    },
  },
  rightPanel: {
    backgroundColor: "#1e293b",
    width: "40%",
    textColor: "#f8fafc",
  },
  codeBlock: {
    backgroundColor: "#1e293b",
  },
};

// Redoc options configuration
const redocOptions = {
  scrollYOffset: 50,
  hideDownloadButton: true,
  hideHostname: false,
  expandResponses: "200,201",
  requiredPropsFirst: true,
  sortPropsAlphabetically: false,
  showExtensions: true,
  hideSingleRequestSampleTab: true,
  menuToggle: true,
  pathInMiddlePanel: true,
  jsonSampleExpandLevel: 2,
  disableSearch: false,
  nativeScrollbars: true,
  noAutoAuth: false,
  theme: redocTheme,
};

function RedocViewer({ spec, isLoading, selectedOperation }) {
  const [redocError, setRedocError] = useState(null);
  const [isRedocReady, setIsRedocReady] = useState(false);
  const redocContainerRef = useRef(null);

  // Handle Redoc rendering errors
  const handleRedocError = useCallback((error) => {
    console.error("Redoc rendering error:", error);
    setRedocError({
      title: "Documentation Rendering Error",
      message: error.message || "Failed to render API documentation",
    });
  }, []);

  // Reset state when spec changes
  useEffect(() => {
    if (spec && !isLoading) {
      setIsRedocReady(false);
      setRedocError(null);
    }
  }, [spec, isLoading]);

  // Scroll to operation when ready (deep linking support)
  useEffect(() => {
    if (selectedOperation && isRedocReady && redocContainerRef.current) {
      // Construct operation ID (Redoc format)
      const pathSlug = selectedOperation.path
        .replace(/\//g, "-")
        .replace(/[{}]/g, "");
      const operationId = `operation/${pathSlug}/${selectedOperation.method.toLowerCase()}`;

      // Attempt to scroll to operation
      setTimeout(() => {
        const operationElement = redocContainerRef.current?.querySelector(
          `[id="${operationId}"]`,
        );
        if (operationElement) {
          operationElement.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        }
      }, 100);
    }
  }, [selectedOperation, isRedocReady]);

  // Get CSS class for HTTP method badge
  const getMethodClass = (method) => {
    return method ? method.toLowerCase() : "";
  };

  // Render operation badge in header
  const renderOperationBadge = () => {
    if (!selectedOperation) return null;
    return (
      <span
        className={`operation-badge ${getMethodClass(selectedOperation.method)}`}
      >
        {selectedOperation.method}
      </span>
    );
  };

  // Sanitize filename for download
  const getDownloadFilename = () => {
    if (!selectedOperation) {
      // Full spec view - use spec title or default
      const title = spec.info?.title || "api";
      return title
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^a-z0-9-]/g, "");
    }

    // Single operation view - use method and path
    const methodPart = selectedOperation.method
      ? selectedOperation.method.toLowerCase()
      : "operation";
    const pathPart = selectedOperation.path
      ? selectedOperation.path.replace(/\//g, "-").replace(/[{}]/g, "")
      : "spec";

    return `${methodPart}${pathPart}`;
  };

  // Error state
  if (redocError) {
    return (
      <div className="redoc-viewer-container">
        <div className="redoc-error">
          <div className="redoc-error-title">{redocError.title}</div>
          <div className="redoc-error-message">{redocError.message}</div>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="redoc-viewer-container">
        <div className="redoc-loading">
          <div className="redoc-loading-spinner"></div>
          Loading documentation...
        </div>
      </div>
    );
  }

  // No spec state
  if (!spec || !spec.paths) {
    return (
      <div className="redoc-viewer-container">
        <div className="panel-content-placeholder">
          Select an operation to view documentation
        </div>
      </div>
    );
  }

  // Determine if this is single-operation or full-spec view
  const viewMode = selectedOperation ? "single-operation" : "full-spec";
  const specTitle = spec.info?.title || "API Documentation";

  // Main render
  return (
    <div
      className={`redoc-viewer-container ${viewMode}`}
      ref={redocContainerRef}
    >
      <div className="redoc-header-controls">
        <div className="redoc-header-title">
          {renderOperationBadge()}
          {selectedOperation ? (
            <span>{selectedOperation.path}</span>
          ) : (
            <span>{specTitle}</span>
          )}
        </div>
        <SpecDownloadButton spec={spec} filename={getDownloadFilename()} />
      </div>

      <div className="redoc-viewer-wrapper">
        <RedocStandalone
          spec={spec}
          options={redocOptions}
          onLoaded={() => {
            setIsRedocReady(true);
          }}
        />
      </div>
    </div>
  );
}

RedocViewer.propTypes = {
  spec: PropTypes.object,
  isLoading: PropTypes.bool,
  selectedOperation: PropTypes.shape({
    path: PropTypes.string,
    method: PropTypes.string,
  }),
};

RedocViewer.defaultProps = {
  isLoading: false,
  selectedOperation: null,
};

export default RedocViewer;
