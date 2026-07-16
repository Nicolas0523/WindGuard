import React from "react";

export default function LoadingSpinner({ message = "Loading..." }) {
  return (
    <div className="spinner-overlay">
      <div className="spinner"></div>
      <p className="spinner-message">{message}</p>
    </div>
  );
}