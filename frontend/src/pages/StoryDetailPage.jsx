import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import BiasBar from "../components/BiasBar";
import ReactMarkdown from "react-markdown";

const formatSource = (source) => {
  const map = {
    ansa: "ANSA",
    la_repubblica: "La Repubblica",
    il_giornale: "Il Giornale",
  };
  return map[source] || source;
};

const StoryDetailPage = () => {
  const { storyId } = useParams();
  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchStory = async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/story/${storyId}`
        );
        if (!response.ok) {
          throw new Error("Story not found");
        }
        const data = await response.json();
        setStory(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStory();
  }, [storyId]);

  if (loading)
    return (
      <div className="loader-container">
        <div className="pulsar-loader"></div>
        <div className="loader-text">ANALISI IN CORSO...</div>
      </div>
    );
  if (error) return <div className="error">Errore: {error}</div>;
  if (!story) return null;

  // Group articles by source for display
  const articlesBySource = story.articles.reduce((acc, article) => {
    const source = article.source_name || article.source_id;
    if (!acc[source]) acc[source] = [];
    acc[source].push(article);
    return acc;
  }, {});

  return (
    <div className="story-detail-page">
      <Link to="/" className="back-link">
        ← Torna alla ricerca
      </Link>

      <header className="story-detail-header">
        <h1 className="story-detail-title">{story.title}</h1>
        <div className="story-meta">
          <span>Ricerca: "{story.query}"</span>
          <span> • </span>
          <span>{story.stats.total_articles} articoli</span>
        </div>
        <div className="detail-bias-bar">
          <BiasBar stats={story.stats} />
        </div>
      </header>

      {story.analysis && (
        <section className="story-analysis-section">
          <div className="analysis-card">
            <h3 className="analysis-title">🤖 Analisi AI della Copertura</h3>
            <div className="analysis-content">
              <ReactMarkdown>{story.analysis}</ReactMarkdown>
            </div>
          </div>
        </section>
      )}

      <div className="sources-columns">
        {Object.entries(articlesBySource).map(([sourceName, articles]) => (
          <div key={sourceName} className="source-column">
            <h2 className="source-column-title">{formatSource(sourceName)}</h2>
            <div className="articles-list">
              {articles.map((article) => {
                const isLink = !!article.url;
                const CardTag = isLink ? "a" : "div";
                const cardProps = isLink
                  ? {
                      href: article.url,
                      target: "_blank",
                      rel: "noopener noreferrer",
                      className: "article-card detail-card clickable",
                    }
                  : {
                      className: "article-card detail-card",
                    };

                return (
                  <CardTag key={article.id} {...cardProps}>
                    <h4 className="article-title">
                      <span
                        className={`bias-dot ${article.bias || "unknown"}`}
                        title={`Bias Effettivo: ${article.bias}\nFonte: ${
                          article.bias_source
                        }\nArticolo (AI): ${article.bias_article} (${Math.round(
                          (article.bias_confidence || 0) * 100
                        )}%)`}
                      ></span>
                      {article.title}
                    </h4>

                    {article.bias_explanation && (
                      <div
                        className="bias-explanation"
                        style={{
                          fontSize: "0.85rem",
                          color: "rgba(255, 255, 255, 0.5)",
                          marginTop: "0.3rem",
                          marginBottom: "0.5rem",
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.2rem",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "flex-start",
                            gap: "0.4rem",
                            fontStyle: "italic",
                          }}
                        >
                          <span style={{ fontSize: "1rem", lineHeight: 1 }}>
                            🤖
                          </span>
                          <span>{article.bias_explanation}</span>
                        </div>
                        {article.bias_confidence && (
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "0.5rem",
                              marginLeft: "1.4rem",
                            }}
                          >
                            <div
                              style={{
                                flex: 1,
                                height: "4px",
                                background: "rgba(255,255,255,0.1)",
                                borderRadius: "2px",
                                maxWidth: "100px",
                              }}
                            >
                              <div
                                style={{
                                  width: `${article.bias_confidence * 100}%`,
                                  height: "100%",
                                  background:
                                    article.bias_confidence > 0.8
                                      ? "#4ade80"
                                      : article.bias_confidence > 0.5
                                      ? "#facc15"
                                      : "#f87171",
                                  borderRadius: "2px",
                                }}
                              ></div>
                            </div>
                            <span style={{ fontSize: "0.75rem", opacity: 0.7 }}>
                              {Math.round(article.bias_confidence * 100)}%
                              confidence
                            </span>
                          </div>
                        )}
                      </div>
                    )}

                    <p className="article-snippet">{article.snippet}</p>
                    <span className="article-date">
                      {article.published_at
                        ? new Date(article.published_at).toLocaleDateString()
                        : article.raw_date}
                    </span>
                  </CardTag>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default StoryDetailPage;
