import React from "react";

const BiasBar = ({ stats }) => {
  if (!stats || !stats.by_bias) return null;

  const { left = 0, center = 0, right = 0, unknown = 0 } = stats.by_bias;
  const total = left + center + right + unknown;

  if (total === 0) return null;

  const getPercent = (val) => (val / total) * 100;

  return (
    <div className="bias-bar-container">
      <div className="bias-bar">
        {left > 0 && (
          <div
            className="bias-segment left"
            style={{ width: `${getPercent(left)}%` }}
            title={`Left: ${left}`}
          />
        )}
        {center > 0 && (
          <div
            className="bias-segment center"
            style={{ width: `${getPercent(center)}%` }}
            title={`Center: ${center}`}
          />
        )}
        {right > 0 && (
          <div
            className="bias-segment right"
            style={{ width: `${getPercent(right)}%` }}
            title={`Right: ${right}`}
          />
        )}
        {unknown > 0 && (
          <div
            className="bias-segment unknown"
            style={{ width: `${getPercent(unknown)}%` }}
            title={`Unknown: ${unknown}`}
          />
        )}
      </div>
      <div className="bias-labels">
        <span className="bias-label left">Left ({left})</span>
        <span className="bias-label center">Center ({center})</span>
        <span className="bias-label right">Right ({right})</span>
      </div>
    </div>
  );
};

export default BiasBar;
