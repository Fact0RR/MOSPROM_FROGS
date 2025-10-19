import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPortal } from "react-dom";
import ThemeToggle from "./ThemeToggle";
import "../styles/header.css";
import "../styles/drawer.css";

type Chat = { id: number | string; name: string };

type HeaderProps = {
  title?: string;
  subtitle?: string;
  showClear?: boolean;
  onClear?: () => void;
  chats?: Chat[];
  chatsLoading?: boolean;
  activeChatId?: Chat["id"] | null;
  onSelectChat?: (id: Chat["id"]) => void;
  onCreateChat?: () => void;
  onRenameChat?: (id: Chat["id"], nextName: string) => void;
  user?: { name: string; avatarUrl?: string };
};

function Header({
  title = "РОСАТОМ",
  subtitle = "ЧАТ ПОДДЕРЖКИ",
  showClear = true,
  onClear,
  chats = [],
  chatsLoading = false,
  activeChatId = null,
  onSelectChat,
  onCreateChat,
  onRenameChat,
  user = { name: "Иван Иванов", avatarUrl: "" },
}: HeaderProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement | null>(null);
  const navigate = useNavigate();

  // Блокировка скролла при открытии
  useEffect(() => {
    if (!menuOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [menuOpen]);

  // Закрытие по ESC
  useEffect(() => {
    const onEsc = (e: KeyboardEvent) =>
      e.key === "Escape" && setMenuOpen(false);
    document.addEventListener("keydown", onEsc);
    return () => document.removeEventListener("keydown", onEsc);
  }, []);

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) setMenuOpen(false);
  };

  const handleClear = () => onClear?.();
  const handleLogout = () => {
    localStorage.removeItem("token");
    setMenuOpen(false);
    navigate("/auth/login", { replace: true });
  };

  const handleCreateChat = () => {
    if (!onCreateChat) return;
    onCreateChat();
    setMenuOpen(false);
  };

  const handleSelectChat = (chat: Chat) => {
    if (!onSelectChat) return;
    onSelectChat(chat.id);
    setMenuOpen(false);
  };

  const handleRenameChat = (chat: Chat) => {
    if (!onRenameChat) return;
    const currentName = chat.name || "";
    const next = window.prompt("Введите новое название чата", currentName);
    if (next == null) return;
    const trimmed = next.trim();
    if (!trimmed || trimmed === currentName) return;
    onRenameChat(chat.id, trimmed);
  };

  return (
    <header className="chat-header">
      <div className="header-brand" aria-label={`${title}. ${subtitle}`}>
        <div className="brand-logo" aria-hidden="true">
          <svg
            width="55"
            height="55"
            viewBox="0 0 55 55"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M31.6809 31.375C29.5497 33.7434 25.9105 33.9299 23.5501 31.7928C21.1889 29.6558 20.9997 26.0018 23.1267 23.633C25.257 21.2641 28.8988 21.0797 31.2592 23.2163C33.6196 25.3534 33.808 29.0062 31.6809 31.375Z"
              fill="url(#paint0_radial_96_308)"
            />
            <path
              d="M10.9213 5.53015C7.15468 8.38106 4.14466 12.185 2.24707 16.5849C4.52423 17.1481 11.3421 19.3748 14.4701 27.8498C15.411 27.5422 17.4391 26.356 18.8462 21.7767C20.7331 15.6456 24.3126 9.74864 28.9546 7.76853C24.3256 3.1728 18.2266 2.09066 10.9213 5.53015Z"
              fill="url(#paint1_linear_96_308)"
            />
            <path
              d="M48.5084 9.96332C48.5089 9.9628 48.5093 9.96227 48.5097 9.96175C43.4839 3.8763 35.895 0 27.404 0C21.2164 0 15.5079 2.05848 10.9211 5.53022C21.0629 0.755224 28.8791 4.69432 33.6657 14.6509C41.2899 16.0231 46.4679 12.2162 48.5084 9.96332Z"
              fill="url(#paint2_linear_96_308)"
            />
            <path
              d="M16.6888 52.8072C21.0323 54.6554 25.8198 55.3695 30.5654 54.8188C29.9129 52.558 28.4254 45.5191 34.1747 38.5629C33.4389 37.899 31.4012 36.7294 26.746 37.7961C20.5119 39.2217 13.6334 39.0591 9.60373 36.0147C7.95243 42.3358 10.0681 48.1776 16.6888 52.8072Z"
              fill="url(#paint3_linear_96_308)"
            />
            <path
              d="M1.72081 17.9225C1.72015 17.9224 1.71948 17.9223 1.71883 17.9222C-1.01963 25.333 -0.570173 33.8668 3.67536 41.2466C6.76916 46.6245 11.3997 50.5567 16.689 52.8072C7.49762 46.3803 6.98867 37.6174 13.1873 28.479C10.5593 21.1664 4.68511 18.5695 1.72081 17.9225Z"
              fill="url(#paint4_linear_96_308)"
            />
            <path
              d="M54.6022 24.1559C54.0254 19.4568 52.2478 14.9388 49.3998 11.0896C47.7752 12.7871 42.4448 17.5994 33.5674 16.0806C33.3625 17.0521 33.372 19.4078 36.6201 22.9205C40.9673 27.6259 44.2663 33.6855 43.654 38.71C49.9343 36.9847 53.9176 32.225 54.6022 24.1559Z"
              fill="url(#paint5_linear_96_308)"
            />
            <path
              d="M31.983 54.6075C31.9832 54.6081 31.9835 54.6087 31.9837 54.6093C39.748 53.284 46.8874 48.6265 51.1329 41.2466C54.2267 35.8688 55.3046 29.8781 54.6021 24.1558C53.6518 35.3578 46.3445 40.1816 35.3593 39.3634C30.3631 45.3038 31.0592 51.7076 31.983 54.6075Z"
              fill="url(#paint6_linear_96_308)"
            />
            <defs>
              <radialGradient
                id="paint0_radial_96_308"
                cx="0"
                cy="0"
                r="1"
                gradientTransform="matrix(8.10269 -0.0090002 0.00896877 8.13108 25.5743 24.2063)"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </radialGradient>
              <linearGradient
                id="paint1_linear_96_308"
                x1="7.97114"
                y1="23.6145"
                x2="21.6637"
                y2="2.60345"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
              <linearGradient
                id="paint2_linear_96_308"
                x1="13.4097"
                y1="-0.650836"
                x2="47.2904"
                y2="12.9901"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
              <linearGradient
                id="paint3_linear_96_308"
                x1="33.7692"
                y1="46.3284"
                x2="8.78714"
                y2="45.0237"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
              <linearGradient
                id="paint4_linear_96_308"
                x1="10.1107"
                y1="53.735"
                x2="4.99472"
                y2="17.4602"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
              <linearGradient
                id="paint5_linear_96_308"
                x1="40.471"
                y1="12.5507"
                x2="51.8918"
                y2="34.8871"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
              <linearGradient
                id="paint6_linear_96_308"
                x1="58.6925"
                y1="29.4096"
                x2="29.8483"
                y2="51.8665"
                gradientUnits="userSpaceOnUse"
              >
                <stop stopColor="#5F94CC" />
                <stop offset="1" stopColor="#202562" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <div className="brand-divider" aria-hidden="true" />
        <div className="brand-labels">
          <span className="brand-name">{title}</span>
          <span className="brand-subtitle">{subtitle}</span>
        </div>
      </div>

      {/* Бургер */}
      <button
        onClick={() => setMenuOpen((v) => !v)}
        aria-haspopup="dialog"
        aria-expanded={menuOpen}
        aria-label={menuOpen ? "Закрыть панель" : "Открыть панель"}
        className="burger-btn"
      >
        {menuOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M18 6L6 18M6 6l12 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : (
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

      {/* Дровер */}
      {createPortal(
        <div
          aria-hidden={!menuOpen}
          className="drawer-host"
          style={{ pointerEvents: menuOpen ? "auto" : "none" }}
        >
          <div
            className={`drawer-overlay ${menuOpen ? "open" : ""}`}
            onClick={handleOverlayClick}
          />
          <aside
            ref={drawerRef}
            role="dialog"
            aria-modal="true"
            aria-label="Боковое меню"
            className={`drawer ${menuOpen ? "open" : ""}`}
          >
            {/* верхняя панель */}
            <div className="drawer-top">
              <button
                className="icon-btn"
                aria-label="Закрыть"
                onClick={() => setMenuOpen(false)}
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

            {/* Профиль */}
            <div className="profile">
              <div className="avatar">
                {user.avatarUrl ? (
                  <img src={user.avatarUrl} alt={user.name} />
                ) : (
                  <div className="avatar-fallback" />
                )}
              </div>

              <div className="profile-name">{user.name}</div>

              {/* иконка выхода */}
              <button
                className="profile-action"
                aria-label="Выйти"
                title="Выйти"
                onClick={handleLogout}
              >
                <svg
                  width="22"
                  height="21"
                  viewBox="0 0 22 21"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M5.67802 0.965699H8.76487C9.46572 0.965689 10.0441 0.965681 10.517 0.999719C11.0075 1.03502 11.4604 1.11064 11.8935 1.30121C12.8006 1.70033 13.5252 2.42491 13.9243 3.33201C14.1149 3.76513 14.1905 4.21799 14.2258 4.7085C14.2598 5.18139 14.2598 5.7598 14.2598 6.46067V6.49647C14.2598 7.04284 13.8169 7.48576 13.2705 7.48576C12.7242 7.48576 12.2812 7.04284 12.2812 6.49647C12.2812 5.75086 12.2806 5.24396 12.2523 4.85054C12.2247 4.46671 12.1744 4.26786 12.1133 4.12885C11.9135 3.67476 11.5507 3.31203 11.0967 3.11223C10.9576 3.05107 10.7588 3.00082 10.375 2.97319C9.98155 2.94487 9.47465 2.94427 8.72904 2.94427H5.71819C4.88375 2.94427 4.31642 2.94502 3.87762 2.98028C3.45008 3.01464 3.23087 3.07695 3.07782 3.15343C2.69362 3.3454 2.38211 3.6569 2.19014 4.04111C2.11367 4.19416 2.05135 4.41337 2.01699 4.84091C1.98173 5.27971 1.98099 5.84703 1.98099 6.68147V14.9498C1.98099 15.7843 1.98173 16.3516 2.01699 16.7904C2.05135 17.2179 2.11367 17.4371 2.19014 17.5902C2.38211 17.9744 2.69362 18.2859 3.07782 18.4779C3.23087 18.5543 3.45008 18.6167 3.87762 18.651C4.31642 18.6863 4.88375 18.687 5.71819 18.687H8.54403C9.37847 18.687 9.9458 18.6863 10.3846 18.651C10.8121 18.6167 11.0314 18.5543 11.1844 18.4779C11.5686 18.2859 11.8801 17.9744 12.0721 17.5902C12.1486 17.4371 12.2109 17.2179 12.2452 16.7904C12.2805 16.3516 12.2812 15.7843 12.2812 14.9498V14.6267C12.2812 14.0803 12.7242 13.6374 13.2705 13.6374C13.8169 13.6374 14.2598 14.0803 14.2598 14.6267V14.99C14.2598 15.7742 14.2598 16.4214 14.2174 16.9489C14.1734 17.4966 14.079 18.0002 13.842 18.4746C13.4585 19.242 12.8363 19.8643 12.0688 20.2478C11.5945 20.4848 11.0908 20.5792 10.5431 20.6232C10.0156 20.6656 9.3685 20.6656 8.58428 20.6656H5.67794C4.89372 20.6656 4.24657 20.6656 3.71913 20.6232C3.17143 20.5792 2.66776 20.4848 2.19344 20.2478C1.42596 19.8643 0.803704 19.242 0.420217 18.4746C0.183212 18.0002 0.0887886 17.4966 0.0447755 16.9489C0.00238895 16.4214 0.00239903 15.7742 0.0024113 14.99V6.64131C0.00239903 5.85705 0.00238895 5.20988 0.0447755 4.68242C0.0887886 4.13472 0.183212 3.63105 0.420217 3.15673C0.803704 2.38925 1.42596 1.76699 2.19344 1.3835C2.66776 1.1465 3.17143 1.05208 3.71913 1.00806C4.24659 0.965676 4.89377 0.965686 5.67802 0.965699ZM16.6615 6.30747C17.0466 5.91981 17.6729 5.91767 18.0606 6.30269L21.6419 9.85966C21.8289 10.0454 21.9341 10.298 21.9341 10.5616C21.9341 10.8251 21.8289 11.0778 21.6419 11.2635L18.0606 14.8205C17.6729 15.2055 17.0466 15.2033 16.6615 14.8157C16.2765 14.428 16.2787 13.8016 16.6663 13.4166L18.5449 11.5509H7.13111C6.58474 11.5509 6.14182 11.1079 6.14182 10.5616C6.14182 10.0152 6.58474 9.57229 7.13111 9.57229H18.5449L16.6663 7.70652C16.2787 7.3215 16.2765 6.69512 16.6615 6.30747Z"
                    fill="#007AFF"
                  />
                </svg>
              </button>
            </div>

            {/* Разделы меню */}
            <nav className="sections">
              <button
                className="section-item"
                onClick={handleCreateChat}
                disabled={!onCreateChat || chatsLoading}
              >
                Новый чат
              </button>
              <button className="section-item">Статистика</button>

              <div className="section-title">Мои чаты</div>
              <ul className="chat-list">
                {chatsLoading ? (
                  <li className="chat-item disabled">Загрузка…</li>
                ) : chats.length === 0 ? (
                  <li className="chat-item disabled">Чатов пока нет</li>
                ) : (
                  chats.map((c) => (
                    <li
                      key={`${c.id}`}
                      className={`chat-item ${activeChatId === c.id ? "active" : ""}`}
                      onClick={() => handleSelectChat(c)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") handleSelectChat(c);
                      }}
                    >
                      <span className="chat-item__name">{c.name}</span>
                      <button
                        type="button"
                        className="chat-item__edit"
                        aria-label="Переименовать чат"
                        title="Переименовать чат"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRenameChat(c);
                        }}
                        onKeyDown={(e) => e.stopPropagation()}
                      >
                        ✏️
                      </button>
                    </li>
                  ))
                )}
              </ul>
            </nav>

            {/* Слайдер */}
            <div className="divider" />
            <div className="slider-row">
              <ThemeToggle />
            </div>

            {/* Кнопки */}
            <div className="drawer-actions">
              {showClear && (
                <button
                  className="btn secondary"
                  onClick={handleClear}
                  disabled={!onClear}
                >
                  Очистить
                </button>
              )}
            </div>
          </aside>
        </div>,
        document.body
      )}
    </header>
  );
}

export default Header;
