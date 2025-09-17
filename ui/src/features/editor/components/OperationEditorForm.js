import React, { useState, useEffect } from "react";
import { useSpecStore } from "../../../store/specStore";

function OperationEditorForm({ endpoint }) {
  const [formData, setFormData] = useState({ summary: "", description: "" });

  // Get the update action from the store
  const updateOperationDetails = useSpecStore(
    (state) => state.updateOperationDetails
  );

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

  const handleSave = () => {
    // Call the action from the store, passing the necessary data
    updateOperationDetails(endpoint, formData);
  };

  if (!endpoint) {
    // This part should now be handled by the DetailPanel's logic
    return null;
  }

  return (
    <div className="operation-editor-form">
      <div className="panel-header">
        Edit: {endpoint.method} {endpoint.path}
      </div>
      <div className="panel-content">
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
    </div>
  );
}

export default OperationEditorForm;
