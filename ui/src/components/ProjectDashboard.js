import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { projectAPI } from '../api/projectAPI';
import './ProjectDashboard.css';

function ProjectDashboard({ onSelectProject, onCreateProject }) {
  const { token, user, logout } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    isPublic: false
  });

  useEffect(() => {
    loadProjects();
  }, [token]);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectAPI.getProjects();
      setProjects(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Failed to load projects');
      // 401 handling is now done by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      const created = await projectAPI.createProject(newProject);
      setProjects([created, ...projects]);
      setShowCreateModal(false);
      setNewProject({ name: '', description: '', isPublic: false });

      // Auto-select the newly created project
      if (onSelectProject) {
        onSelectProject(created);
      }
    } catch (err) {
      console.error('Failed to create project:', err);
      alert(err.response?.data?.message || 'Failed to create project');
    }
  };

  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure? This will delete all specifications.')) {
      return;
    }

    try {
      await projectAPI.deleteProject(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
    } catch (err) {
      console.error('Failed to delete project:', err);
      alert('Failed to delete project');
    }
  };

  if (loading) {
    return <div className="dashboard-loading">Loading projects...</div>;
  }

  return (
    <div className="project-dashboard">
      <div className="dashboard-header">
        <div className="user-info">
          {user?.avatarUrl && (
            <img src={user.avatarUrl} alt={user.username} className="user-avatar" />
          )}
          <div>
            <h2>Welcome, {user?.username}</h2>
            <button onClick={logout} className="btn-logout">Logout</button>
          </div>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-create">
          + New Project
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="projects-grid">
        {projects.length === 0 ? (
          <div className="empty-state">
            <h3>No projects yet</h3>
            <p>Create your first project to get started</p>
            <button onClick={() => setShowCreateModal(true)} className="btn-create-large">
              Create Project
            </button>
          </div>
        ) : (
          projects.map(project => (
            <div key={project.id} className="project-card">
              <div className="project-card-header">
                <h3>{project.name}</h3>
                {project.isPublic && <span className="badge-public">Public</span>}
              </div>
              <p className="project-description">{project.description || 'No description'}</p>
              <div className="project-meta">
                <span>{project.specificationCount} version{project.specificationCount !== 1 ? 's' : ''}</span>
                <span>•</span>
                <span>{new Date(project.createdAt).toLocaleDateString()}</span>
              </div>
              <div className="project-actions">
                <button
                  onClick={() => onSelectProject(project)}
                  className="btn-open"
                >
                  Open
                </button>
                <button
                  onClick={() => handleDeleteProject(project.id)}
                  className="btn-delete"
                >
                  Delete
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Create New Project</h2>
            <form onSubmit={handleCreateProject}>
              <div className="form-group">
                <label>Project Name *</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={e => setNewProject({ ...newProject, name: e.target.value })}
                  required
                  placeholder="e.g., Petstore API"
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={newProject.description}
                  onChange={e => setNewProject({ ...newProject, description: e.target.value })}
                  placeholder="Brief description of your API"
                  rows="3"
                />
              </div>
              <div className="form-group-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={newProject.isPublic}
                    onChange={e => setNewProject({ ...newProject, isPublic: e.target.checked })}
                  />
                  Make this project public
                </label>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-cancel">
                  Cancel
                </button>
                <button type="submit" className="btn-submit">
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectDashboard;
