import React, { useState, useEffect } from "react";
import { useSpecStore } from "../../../store/specStore";
import {
  getSessionSpec,
  updateOperation,
} from "../../../api/validationService";

function OperationEditorForm({ endpoint }) {
  const [formData, setFormData] = useState({ summary: "", description: "" });
  const setSpecText = useSpecStore((state) => state.setSpecText);
  const sessionId = useSpecStore((state) => state.sessionId);
  useEffect(() => {
    if (endpoint?.details) {
      setFormData({
        summary: endpoint.details.summary || "",
        description: endpoint.details.description || "",
      });
    }
  }, [endpoint]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    if (!sessionId || !endpoint) {
      return;
    }
    const updateRequest = {
      path: endpoint.path,
      method: endpoint.method,
      summary: formData.summary,
      description: formData.description,
    };

    const result = await updateOperation(sessionId, updateRequest);
    if (result.success) {
      const specResult = await getSessionSpec(sessionId);
      if (specResult.success) {
        setSpecText(specResult.data);
      }
      alert("Operation updated successfully!");
    } else {
      alert(`Error: ${result.error}`);
    }
  };

  if (!endpoint) {
    return <p className="no-errors">Select an endpoint to edit its details.</p>;
  }

  return (
    <div className="operation-editor-form">
      <h4>
        Edit: {endpoint.method} {endpoint.path}
      </h4>
      <div className="form-group">
        <label htmlFor="summary">Summary</label>
        <input
          type="text"
          id="summary"
          name="summary"
          className="text-input"
          value={formData.summary}
          onChange={handleChange}
        />
      </div>
      <div className="form-group">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          name="description"
          className="text-input"
          rows="4"
          value={formData.description}
          onChange={handleChange}
        />
      </div>
      <button className="send-request-button" onClick={handleSave}>
        Save Changes
      </button>
    </div>
  );
}

export default OperationEditorForm;
