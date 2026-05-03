import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

// Sprint 22 — migrated from .js → .tsx. Strict-mode entry point.
// Type assertion is safe because <div id="root" /> is hard-coded in
// public/index.html.
const rootElement = document.getElementById("root") as HTMLElement;
const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
