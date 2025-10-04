import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import SpecEditor from "./features/editor/SpecEditor";
import ProjectDashboard from "./components/ProjectDashboard";
import bannerLogo from "./assets/banner-logo.png";
import "./App.css";

function App() {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, loading, navigate]);

  if (loading) {
    return (
      <div className="app-container">
        <div style={{ padding: '4rem', textAlign: 'center' }}>
          Loading...
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect to login
  }

  return (
    <div className="app-container">
      <header className="App-header">
        <div className="header-left">
          <img src={bannerLogo} className="App-logo" alt="SchemaSculpt Logo" />
          <div className="header-text">
            <h1>SchemaSculpt</h1>
            <p className="tagline">Your AI Co-pilot for Flawless APIs</p>
          </div>
        </div>
        {selectedProject && (
          <div className="header-center">
            <span className="current-project">{selectedProject.name}</span>
            <button
              onClick={() => setSelectedProject(null)}
              className="btn-back-to-projects"
            >
              ← Back to Projects
            </button>
          </div>
        )}
      </header>
      <main className="App-main">
        {selectedProject ? (
          <SpecEditor project={selectedProject} />
        ) : (
          <ProjectDashboard onSelectProject={setSelectedProject} />
        )}
      </main>
    </div>
  );
}

export default App;
