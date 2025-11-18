import React from "react";
import { Link } from "react-router-dom";
import BiasBar from "./BiasBar";

const formatSource = (source) => {
  const map = {
    ansa: "ANSA",
    la_repubblica: "La Repubblica",
    il_giornale: "Il Giornale",
  };
  return map[source] || source;
};

const StoryCard = ({ story }) => {
  const { id, title, stats } = story;
  const dateStr = stats.last_published_at
    ? new Date(stats.last_published_at).toLocaleDateString("it-IT", {
        day: "numeric",
        month: "short",
      })
    : "N/A";

  return (
    <div className="story-card">
      <div className="story-header">
        <h3 className="story-title">
          <Link to={`/story/${id}`}>{title}</Link>
        </h3>
        <span className="story-date">{dateStr}</span>
      </div>

      <div className="story-stats">
        <span className="article-count">{stats.total_articles} articoli</span>
        <div className="source-badges">
          {Object.entries(stats.by_source).map(([source, count]) => (
            <span key={source} className="source-badge">
              {formatSource(source)}: {count}
            </span>
          ))}
        </div>
      </div>

      <BiasBar stats={stats} />

      <Link to={`/story/${id}`} className="view-story-btn">
        Vedi copertura completa
      </Link>
    </div>
  );
};

export default StoryCard;
