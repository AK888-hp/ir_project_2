// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app.jsx";
import "./index.css";   // keep this so global styles load

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
