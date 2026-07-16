import React from "react";

export default function ErrorMessage({ message, onClose }) {
  if (!message) return null;
  return (
    <div className="error-banner">
      <span className="error-icon">⚠️</span>
      <span className="error-text">{message}</span>
      {onClose && <button className="error-close-btn" onClick={onClose}>&times;</button>}
    </div>
  );
}