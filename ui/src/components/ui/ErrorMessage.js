import React from "react";
import PropTypes from "prop-types";
import { ERROR_TYPES } from "../../store/types";

function ErrorMessage({
  error,
  onRetry,
  onDismiss,
  showDetails = false,
  className = "",
}) {
  if (!error) return null;

  const getErrorIcon = (type) => {
    switch (type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return "📡";
      case ERROR_TYPES.TIMEOUT_ERROR:
        return "⏱️";
      case ERROR_TYPES.SERVER_ERROR:
        return "🔧";
      case ERROR_TYPES.VALIDATION_ERROR:
        return "⚠️";
      default:
        return "❌";
    }
  };

  const getErrorClass = (type) => {
    const baseClass = "error-message";
    switch (type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return `${baseClass} error-network`;
      case ERROR_TYPES.TIMEOUT_ERROR:
        return `${baseClass} error-timeout`;
      case ERROR_TYPES.SERVER_ERROR:
        return `${baseClass} error-server`;
      case ERROR_TYPES.VALIDATION_ERROR:
        return `${baseClass} error-validation`;
      default:
        return `${baseClass} error-general`;
    }
  };

  const errorClass = `${getErrorClass(error.type)} ${className}`;

  return (
    <div className={errorClass}>
      <div className="error-content">
        <span className="error-icon">{getErrorIcon(error.type)}</span>
        <div className="error-details">
          <div className="error-message-text">
            {error.message || "An unexpected error occurred"}
          </div>
          {showDetails && error.statusCode && (
            <div className="error-status">Status Code: {error.statusCode}</div>
          )}
        </div>
      </div>
      <div className="error-actions">
        {onRetry && (
          <button className="error-retry-btn" onClick={onRetry} type="button">
            Retry
          </button>
        )}
        {onDismiss && (
          <button
            className="error-dismiss-btn"
            onClick={onDismiss}
            type="button"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

ErrorMessage.propTypes = {
  error: PropTypes.shape({
    message: PropTypes.string,
    type: PropTypes.string,
    statusCode: PropTypes.number,
  }),
  onRetry: PropTypes.func,
  onDismiss: PropTypes.func,
  showDetails: PropTypes.bool,
  className: PropTypes.string,
};

export default ErrorMessage;
