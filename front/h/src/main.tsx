import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./styles/chat.css";

function applyTheme(theme: "light" | "dark") {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
}

function initTheme() {
  try {
    const saved = localStorage.getItem("theme");
    if (saved === "light" || saved === "dark") {
      applyTheme(saved);
      return;
    }
  } catch {}
  const prefersDark =
    typeof window !== "undefined" &&
    (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  applyTheme(prefersDark ? "dark" : "light");
}

initTheme();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
