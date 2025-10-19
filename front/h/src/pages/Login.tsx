import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { useLocation, useNavigate, Link } from "react-router-dom";
import "../styles/login.css";

type AuthResponse = { jwt: string };
type LocationState = { loginPrefill?: string };

function RosatomLogo() {
  return (
    <svg
      className="login-logo"
      width="55"
      height="55"
      viewBox="0 0 55 55"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M31.6809 31.3749C29.5497 33.7434 25.9105 33.9298 23.5501 31.7928C21.1889 29.6557 20.9997 26.0018 23.1267 23.6329C25.257 21.2641 28.8988 21.0797 31.2592 23.2163C33.6196 25.3534 33.808 29.0062 31.6809 31.3749Z" fill="#F5F6F8"/>
      <path d="M10.9213 5.53012C7.15468 8.38103 4.14466 12.185 2.24707 16.5848C4.52423 17.1481 11.3421 19.3747 14.4701 27.8498C15.411 27.5421 17.4391 26.356 18.8462 21.7766C20.7331 15.6456 24.3126 9.74861 28.9546 7.76849C24.3256 3.17276 18.2266 2.09062 10.9213 5.53012Z" fill="#F5F6F8"/>
      <path d="M48.5084 9.96332C48.5089 9.9628 48.5093 9.96227 48.5097 9.96175C43.4839 3.8763 35.895 0 27.404 0C21.2164 0 15.5079 2.05848 10.9211 5.53022C21.0629 0.755224 28.8791 4.69432 33.6657 14.6509C41.2899 16.0231 46.4679 12.2162 48.5084 9.96332Z" fill="#F5F6F8"/>
      <path d="M16.6888 52.8072C21.0323 54.6554 25.8198 55.3695 30.5654 54.8189C29.9129 52.5581 28.4254 45.5191 34.1747 38.563C33.4389 37.8991 31.4012 36.7295 26.746 37.7962C20.5119 39.2218 13.6334 39.0592 9.60373 36.0148C7.95243 42.3358 10.0681 48.1777 16.6888 52.8072Z" fill="#F5F6F8"/>
      <path d="M1.72081 17.9224C1.72015 17.9223 1.71948 17.9222 1.71883 17.9221C-1.01963 25.3329 -0.570173 33.8667 3.67536 41.2466C6.76916 46.6244 11.3997 50.5566 16.689 52.8072C7.49762 46.3802 6.98867 37.6173 13.1873 28.4789C10.5593 21.1663 4.68511 18.5695 1.72081 17.9224Z" fill="#F5F6F8"/>
      <path d="M54.6022 24.1559C54.0254 19.4569 52.2478 14.9388 49.3998 11.0896C47.7752 12.7871 42.4448 17.5994 33.5674 16.0806C33.3625 17.0521 33.372 19.4078 36.6201 22.9205C40.9673 27.626 44.2663 33.6855 43.654 38.7101C49.9343 36.9847 53.9176 32.225 54.6022 24.1559Z" fill="#F5F6F8"/>
      <path d="M31.983 54.6074C31.9832 54.6081 31.9835 54.6087 31.9837 54.6093C39.748 53.284 46.8874 48.6264 51.1329 41.2466C54.2267 35.8688 55.3046 29.8781 54.6021 24.1558C53.6518 35.3577 46.3445 40.1815 35.3593 39.3633C30.3631 45.3037 31.0592 51.7075 31.983 54.6074Z" fill="#F5F6F8"/>
    </svg>
  );
}

export default function Login() {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const state = location.state as LocationState | null;
    if (state?.loginPrefill) setLogin(state.loginPrefill);
  }, [location.state]);

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = { login: login.trim(), password };
      const { data } = await axios.put<AuthResponse>(
        "http://localhost:8080/auth",
        payload,
        { headers: { "Content-Type": "application/json" } }
      );
      if (!data?.jwt) throw new Error("Не получили JWT от сервера");
      localStorage.setItem("token", data.jwt);
      navigate("/chat", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const msg =
          (err.response?.data as any)?.message ??
          `Ошибка авторизации${err.response?.status ? ` (${err.response.status})` : ""}`;
        setError(msg);
        console.error("Ошибка авторизации:", err.response?.data ?? err.message);
      } else if (err instanceof Error) setError(err.message);
      else setError("Произошла неизвестная ошибка");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="login-wrapper">
      <aside className="login-decor" aria-hidden="true">
        <div className="login-brand">
          <RosatomLogo />
          <div className="login-brand__text">
            <span className="login-brand__title">РОСАТОМ</span>
            <span className="login-brand__subtitle">Чат поддержки</span>
          </div>
        </div>
      </aside>

      <div className="login-content">
        <form onSubmit={onSubmit} className="login-form">
          <h1 className="login-heading">Авторизация</h1>

          {error && <div className="login-error">{error}</div>}

          <label className="login-field">
            <span className="sr-only">Логин</span>
            <input
              type="text"
              name="login"
              placeholder="Логин"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              autoComplete="username"
              required
              disabled={loading}
            />
          </label>

          <label className="login-field">
            <span className="sr-only">Пароль</span>
            <input
              type="password"
              name="password"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              disabled={loading}
            />
          </label>

          <div className="login-forgot">Забыл пароль?</div>

          <button type="submit" disabled={loading}>
            {loading ? "Входим..." : "Войти"}
          </button>

          {/* Меню-переключатель как на странице регистрации */}
          <div className="login-tabs">
            <Link to="/auth/login" className="tab-link active">Вход</Link>
            <Link to="/auth/register" className="tab-link">Регистрация</Link>
          </div>
        </form>
      </div>
    </section>
  );
}
