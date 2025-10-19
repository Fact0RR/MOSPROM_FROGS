import { useEffect, useState } from "react";
import "../styles/themetoggle.css";

function getCurrentTheme(): "light" | "dark" {
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "dark" ? "dark" : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(getCurrentTheme());

  useEffect(() => {
    const current = getCurrentTheme();
    if (current !== theme) setTheme(current);

    const observer = new MutationObserver(() => {
      setTheme(getCurrentTheme());
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch {}
    setTheme(next);
  };

  const isOn = theme === "dark";

  return (
    <label
      className={`theme-switch ${isOn ? "is-on" : ""}`}
      title="Переключить тему"
    >
      <input
        type="checkbox"
        role="switch"
        aria-label="Переключить тему"
        checked={isOn}
        onChange={toggle}
      />
      <span className="track">
        <span className="thumb" />
      </span>
    </label>
  );
}
