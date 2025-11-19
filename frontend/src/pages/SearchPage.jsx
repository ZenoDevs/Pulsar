import React from "react";
import StoryCard from "../components/StoryCard";

const SearchPage = ({
  query,
  setQuery,
  stories,
  setStories,
  loading,
  setLoading,
  error,
  setError,
  searched,
  setSearched,
}) => {
  const [statusMessage, setStatusMessage] = React.useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setStories([]);
    setSearched(true);
    setStatusMessage("Avvio ricerca...");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: query }),
      });

      if (!response.ok) {
        throw new Error("Network response was not ok");
      }

      const data = await response.json();
      const jobId = data.job_id;

      // Polling logic
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch(
            `http://127.0.0.1:8000/api/search/status/${jobId}`
          );
          if (!statusRes.ok) throw new Error("Errore status");

          const statusData = await statusRes.json();
          setStatusMessage(statusData.message || "Elaborazione...");

          if (statusData.status === "completed") {
            clearInterval(pollInterval);
            setStories(statusData.stories);
            setLoading(false);
            setStatusMessage("");
          } else if (statusData.status === "failed") {
            clearInterval(pollInterval);
            setError("La ricerca è fallita.");
            setLoading(false);
            setStatusMessage("");
          }
        } catch (err) {
          clearInterval(pollInterval);
          setError("Errore di comunicazione col server.");
          setLoading(false);
          console.error(err);
        }
      }, 1000);
    } catch (err) {
      setError(
        "Errore durante la ricerca. Assicurati che il backend sia attivo."
      );
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="search-page">
      <section className="search-section">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="Cerca un argomento (es. manovra, AI, immigrazione)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? "..." : "Cerca"}
          </button>
        </form>
        {loading && (
          <div className="loader-container" style={{ height: "40vh" }}>
            <div className="pulsar-loader"></div>
            <div className="loader-text">{statusMessage}</div>
          </div>
        )}
        {error && <p className="error-message">{error}</p>}
      </section>

      <main className="stories-list">
        {stories.length > 0 ? (
          <div className="stories-grid">
            {stories.map((story) => (
              <StoryCard key={story.id} story={story} />
            ))}
          </div>
        ) : (
          searched &&
          !loading &&
          !error && (
            <p className="no-results">
              Nessuna storia trovata per questa ricerca.
            </p>
          )
        )}
      </main>
    </div>
  );
};

export default SearchPage;
