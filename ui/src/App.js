import SpecEditor from './features/editor/Editor';
import bannerLogo from './assets/banner-logo.png';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={bannerLogo} className="App-logo" alt="SchemaSculpt Logo" />
        <div className="header-text">
          <h1>SchemaSculpt</h1>
          <p className="tagline">Your AI Co-pilot for Flawless APIs</p>
        </div>
      </header>
      <main className="App-main">
        <SpecEditor />
      </main>
    </div>
  );
}

export default App;