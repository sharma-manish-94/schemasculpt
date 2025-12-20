import React from "react";
import yaml from "js-yaml";
import PropTypes from "prop-types";

/**
 * SpecDownloadButton - Provides download buttons for OpenAPI spec in JSON/YAML formats
 *
 * @param {Object} spec - The OpenAPI specification object to download
 * @param {string} filename - Base filename (without extension) for the downloaded file
 */
function SpecDownloadButton({ spec, filename = "openapi-spec" }) {
  const downloadAsJSON = () => {
    try {
      const jsonString = JSON.stringify(spec, null, 2);
      const blob = new Blob([jsonString], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${filename}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download JSON:", error);
    }
  };

  const downloadAsYAML = () => {
    try {
      const yamlString = yaml.dump(spec, { indent: 2, noRefs: true });
      const blob = new Blob([yamlString], { type: "application/x-yaml" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${filename}.yaml`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download YAML:", error);
    }
  };

  return (
    <div className="spec-download-buttons">
      <button
        onClick={downloadAsJSON}
        className="download-btn download-json"
        title="Download as JSON"
      >
        <span className="download-icon">↓</span> JSON
      </button>
      <button
        onClick={downloadAsYAML}
        className="download-btn download-yaml"
        title="Download as YAML"
      >
        <span className="download-icon">↓</span> YAML
      </button>
    </div>
  );
}

SpecDownloadButton.propTypes = {
  spec: PropTypes.object.isRequired,
  filename: PropTypes.string,
};

export default SpecDownloadButton;
