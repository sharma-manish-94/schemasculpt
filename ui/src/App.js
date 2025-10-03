import SpecEditor from "./features/editor/SpecEditor";
import bannerLogo from "./assets/banner-logo.png";
import { Link } from "react-router-dom";
import "./App.css";

function App() {
  return (
    <div className="app-container">
      {" "}
      {/* Use this new wrapper */}
      <header className="App-header">
        <div className="header-left">
          <img src={bannerLogo} className="App-logo" alt="SchemaSculpt Logo" />
          <div className="header-text">
            <h1>SchemaSculpt</h1>
            <p className="tagline">Your AI Co-pilot for Flawless APIs</p>
          </div>
        </div>
        <div className="header-right">
          <a
            href="https://github.com/your-username"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
          <a href="mailto:your.email@example.com">Contact</a>
          <Link to="/about">About</Link>
        </div>
      </header>
      <main className="App-main">
        <SpecEditor />
      </main>
    </div>
  );
}

export default App;
