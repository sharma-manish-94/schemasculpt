import SpecEditor from './features/editor/Editor';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>SchemaSculpt</h1>
      </header>
      <main className="App-main">
        <SpecEditor />
      </main>
    </div>
  );
}

export default App;