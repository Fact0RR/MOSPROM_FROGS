import { useEffect, useState } from "react";

function getCurrentTheme(): "light" | "dark" {
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "dark" ? "dark" : "light";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(getCurrentTheme());

  useEffect(() => {
    const current = getCurrentTheme();
    if (current !== theme) setTheme(current);
    // keep in sync if other parts change it
    const observer = new MutationObserver(() => {
      const t = getCurrentTheme();
      setTheme(t);
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  const toggle = () => {
    const next = theme === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch {}
    setTheme(next);
  };

  return (
    <button className="secondary" onClick={toggle} title="Переключить тему">
      {theme === "dark" ? "🌙" : "☀️"}
    </button>
  );
}


