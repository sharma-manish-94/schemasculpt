import React from "react";
import PropTypes from "prop-types";

function LoadingSpinner({
  size = "medium",
  text = "Loading...",
  centered = false,
  className = "",
}) {
  const sizeClasses = {
    small: "spinner-small",
    medium: "spinner-medium",
    large: "spinner-large",
  };

  const containerClass = centered
    ? "loading-container centered"
    : "loading-container";
  const spinnerClass = `loading-spinner ${sizeClasses[size]} ${className}`;

  return (
    <div className={containerClass}>
      <div className={spinnerClass}>⟳</div>
      {text && <div className="loading-text">{text}</div>}
    </div>
  );
}

LoadingSpinner.propTypes = {
  size: PropTypes.oneOf(["small", "medium", "large"]),
  text: PropTypes.string,
  centered: PropTypes.bool,
  className: PropTypes.string,
};

export default LoadingSpinner;
