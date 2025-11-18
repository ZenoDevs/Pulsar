import { useState } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import StoryDetailPage from "./pages/StoryDetailPage";
import "./App.css";

function App() {
  // Lifted state for persistence
  const [query, setQuery] = useState("");
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);

  return (
    <Router>
      <div className="app-container">
        <header className="header">
          <h1>Pulsar</h1>
          <p>Narrative Intelligence per le news italiane</p>
        </header>
        <Routes>
          <Route
            path="/"
            element={
              <SearchPage
                query={query}
                setQuery={setQuery}
                stories={stories}
                setStories={setStories}
                loading={loading}
                setLoading={setLoading}
                error={error}
                setError={setError}
                searched={searched}
                setSearched={setSearched}
              />
            }
          />
          <Route path="/story/:storyId" element={<StoryDetailPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
