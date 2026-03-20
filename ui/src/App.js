import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import SpecEditor from "./features/editor/SpecEditor";
import ProjectDashboard from "./components/ProjectDashboard";
import CommandPalette from "./components/CommandPalette";
import useKeyboardShortcuts from "./hooks/useKeyboardShortcuts";
import bannerLogo from "./assets/banner-logo.png";
import "./App.css";

// Define available commands
const getCommands = (handlers) => [
  {
    id: "save",
    label: "Save Specification",
    icon: "💾",
    shortcut: "Cmd+S",
    category: "Actions",
    keywords: ["save", "write", "store"],
    action: handlers.onSave,
  },
  {
    id: "validate",
    label: "Validate Specification",
    icon: "✓",
    shortcut: "Cmd+Shift+V",
    category: "Actions",
    keywords: ["validate", "check", "lint"],
    action: handlers.onValidate,
  },
  {
    id: "security",
    label: "Run Security Analysis",
    icon: "🔐",
    shortcut: "Cmd+Shift+A",
    category: "Security",
    keywords: ["security", "audit", "scan"],
    action: handlers.onSecurityAnalysis,
  },
  {
    id: "tab-validation",
    label: "Go to Validation",
    icon: "✓",
    shortcut: "Cmd+1",
    category: "Navigation",
    keywords: ["validation", "errors", "tab"],
    action: () => handlers.onSwitchTab("validation"),
  },
  {
    id: "tab-explorer",
    label: "Go to API Explorer",
    icon: "🔍",
    shortcut: "Cmd+2",
    category: "Navigation",
    keywords: ["explorer", "swagger", "tab"],
    action: () => handlers.onSwitchTab("api_explorer"),
  },
  {
    id: "tab-ai",
    label: "Go to AI Features",
    icon: "🤖",
    shortcut: "Cmd+3",
    category: "Navigation",
    keywords: ["ai", "assistant", "tab"],
    action: () => handlers.onSwitchTab("ai_features"),
  },
  {
    id: "tab-repo",
    label: "Go to Repository",
    icon: "📁",
    shortcut: "Cmd+4",
    category: "Navigation",
    keywords: ["repository", "git", "tab"],
    action: () => handlers.onSwitchTab("repository"),
  },
  {
    id: "tab-impl",
    label: "Go to Implementation",
    icon: "⚡",
    shortcut: "Cmd+5",
    category: "Navigation",
    keywords: ["implementation", "code", "tab"],
    action: () => handlers.onSwitchTab("implementation"),
  },
  {
    id: "back",
    label: "Back to Projects",
    icon: "←",
    category: "Navigation",
    keywords: ["back", "projects", "home"],
    action: handlers.onBackToProjects,
  },
];

function App() {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const [selectedProject, setSelectedProject] = useState(null);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, loading, navigate]);

  // Command handlers (these will be connected to actual functionality)
  const commandHandlers = {
    onSave: useCallback(() => {
      // Dispatch save event that SpecEditor can listen to
      window.dispatchEvent(new CustomEvent("schemasculpt:save"));
    }, []),
    onValidate: useCallback(() => {
      window.dispatchEvent(new CustomEvent("schemasculpt:validate"));
    }, []),
    onSecurityAnalysis: useCallback(() => {
      window.dispatchEvent(new CustomEvent("schemasculpt:security-analysis"));
    }, []),
    onSwitchTab: useCallback((tabId) => {
      window.dispatchEvent(
        new CustomEvent("schemasculpt:switch-tab", { detail: { tabId } }),
      );
    }, []),
    onBackToProjects: useCallback(() => {
      setSelectedProject(null);
    }, []),
  };

  const commands = getCommands(commandHandlers);

  // Keyboard shortcuts
  useKeyboardShortcuts(
    [
      {
        key: "k",
        modifier: true,
        callback: () => setIsCommandPaletteOpen(true),
      },
      { key: "s", modifier: true, callback: commandHandlers.onSave },
      {
        key: "v",
        modifier: true,
        shift: true,
        callback: commandHandlers.onValidate,
      },
      {
        key: "a",
        modifier: true,
        shift: true,
        callback: commandHandlers.onSecurityAnalysis,
      },
      {
        key: "1",
        modifier: true,
        callback: () => commandHandlers.onSwitchTab("validation"),
      },
      {
        key: "2",
        modifier: true,
        callback: () => commandHandlers.onSwitchTab("api_explorer"),
      },
      {
        key: "3",
        modifier: true,
        callback: () => commandHandlers.onSwitchTab("ai_features"),
      },
      {
        key: "4",
        modifier: true,
        callback: () => commandHandlers.onSwitchTab("repository"),
      },
      {
        key: "5",
        modifier: true,
        callback: () => commandHandlers.onSwitchTab("implementation"),
      },
    ],
    [commandHandlers],
  );

  const handleExecuteCommand = (command) => {
    if (command.action) {
      command.action();
    }
  };

  if (loading) {
    return (
      <div className="app-container">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
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
        <div className="header-right">
          <button
            className="btn-command-palette"
            onClick={() => setIsCommandPaletteOpen(true)}
            title="Command Palette (Cmd+K)"
          >
            <span>⌘K</span>
          </button>
        </div>
      </header>
      <main className="App-main">
        {selectedProject ? (
          <SpecEditor project={selectedProject} />
        ) : (
          <ProjectDashboard onSelectProject={setSelectedProject} />
        )}
      </main>

      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        commands={commands}
        onExecute={handleExecuteCommand}
      />
    </div>
  );
}

export default App;
