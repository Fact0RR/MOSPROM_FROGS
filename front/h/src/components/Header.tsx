import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import ThemeToggle from "./ThemeToggle";

type HeaderProps = {
  title?: string;
  showLogout?: boolean;
  showClear?: boolean;
  onClear?: () => void;
};

function Header({
  title = "Чат",
  showLogout = true,
  showClear = true,
  onClear,
}: HeaderProps) {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/auth/login", { replace: true });
  };

  // Блокируем скролл body, закрываем по Esc
  useEffect(() => {
    if (menuOpen) {
      const prev = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = prev;
      };
    }
  }, [menuOpen]);

  useEffect(() => {
    const onEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, []);

  // Клик по фону
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) setMenuOpen(false);
  };

  return (
    <header
      className="chat-header"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 12,
        padding: "12px 16px",
        borderBottom: "1px solid var(--border, #e5e7eb)",
        position: "relative",
      }}
    >
      <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>{title}</h2>

      {/* Бургер-кнопка */}
      <button
        ref={buttonRef}
        onClick={() => setMenuOpen((v) => !v)}
        aria-haspopup="dialog"
        aria-expanded={menuOpen}
        aria-label={menuOpen ? "Закрыть панель" : "Открыть панель"}
        className="burger-btn"
        style={{
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          width: 40,
          height: 40,
          borderRadius: 8,
          border: "1px solid var(--border, #e5e7eb)",
          background: "var(--bg, #fff)",
          cursor: "pointer",
        }}
      >
        {menuOpen ? (
          // Иконка закрытия (X)
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M18 6L6 18M6 6l12 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          // Иконка бургера
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M4 6h16M4 12h16M4 18h16"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        )}
      </button>

      {/* Правый дровер + оверлей через портал */}
      {createPortal(
        <div
          aria-hidden={!menuOpen}
          style={{
            pointerEvents: menuOpen ? "auto" : "none",
          }}
        >
          {/* Оверлей */}
          <div
            onClick={handleOverlayClick}
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0,0,0,0.35)",
              opacity: menuOpen ? 1 : 0,
              transition: "opacity 200ms ease",
              zIndex: 999, // ниже панели
            }}
          />
          {/* Панель */}
          <aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Меню действий"
            style={{
              position: "fixed",
              top: 0,
              right: 0,
              height: "100vh",
              width: "min(92vw, 360px)",
              background: "var(--bg, #fff)",
              borderLeft: "1px solid var(--border, #e5e7eb)",
              boxShadow:
                "0 10px 40px rgba(0,0,0,.18), 0 2px 8px rgba(0,0,0,.08)",
              transform: menuOpen ? "translateX(0)" : "translateX(100%)",
              transition: "transform 260ms cubic-bezier(.2,.8,.2,1)",
              zIndex: 1000,
              display: "flex",
              flexDirection: "column",
            }}
          >
            {/* Шапка панели */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "14px 16px",
                borderBottom: "1px solid var(--border, #e5e7eb)",
              }}
            >
              <div style={{ fontWeight: 600 }}>Меню</div>
              <button
                onClick={() => setMenuOpen(false)}
                aria-label="Закрыть"
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  border: "1px solid var(--border, #e5e7eb)",
                  background: "var(--bg, #fff)",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  cursor: "pointer",
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M18 6L6 18M6 6l12 12"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            </div>

            {/* Контент панели */}
            <div style={{ padding: 16, display: "grid", gap: 12 }}>
              <div
                style={{
                  paddingBottom: 12,
                  borderBottom: "1px solid var(--border, #e5e7eb)",
                }}
              >
                <ThemeToggle />
              </div>

              {showClear && (
                <button
                  className="secondary"
                  onClick={onClear}
                  disabled={!onClear}
                  style={{
                    padding: "12px",
                    borderRadius: 10,
                    border: "1px solid var(--border, #e5e7eb)",
                    background: "var(--muted, #f9fafb)",
                    cursor: onClear ? "pointer" : "not-allowed",
                    opacity: onClear ? 1 : 0.6,
                    textAlign: "left",
                  }}
                >
                  Очистить
                </button>
              )}

              {showLogout && (
                <button
                  className="danger"
                  onClick={handleLogout}
                  style={{
                    padding: "12px",
                    borderRadius: 10,
                    border: "1px solid #ef4444",
                    background: "#fee2e2",
                    color: "#b91c1c",
                    textAlign: "left",
                    cursor: "pointer",
                  }}
                >
                  Выйти
                </button>
              )}
            </div>
          </aside>
        </div>,
        // В портал — в body (без доп. настроек)
        document.body
      )}
    </header>
  );
}

export default Header;
