import { useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

type AuthResponse = {
  jwt: string;
};

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = { login: email, password };

      const { data } = await axios.put<AuthResponse>(
        "http://localhost:8080/auth",
        payload,
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      if (!data?.jwt) {
        throw new Error("Не получили JWT от сервера");
      }

      // Сохраняем JWT в localStorage
      localStorage.setItem("token", data.jwt);

      navigate("/chat", { replace: true });
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const msg =
          (err.response?.data as any)?.message ??
          `Ошибка авторизации${err.response?.status ? ` (${err.response.status})` : ""}`;
        setError(msg);
        console.error("Ошибка авторизации:", err.response?.data ?? err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Произошла неизвестная ошибка");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="form">
      <h3>Авторизация</h3>

      {error && <div className="error-message" style={{ color: "tomato" }}>{error}</div>}

      <label>
        Email
        <input
          type="text"
          name="email"
          placeholder="you@example.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
          disabled={loading}
        />
      </label>

      <label>
        Пароль
        <input
          type="password"
          name="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
          disabled={loading}
        />
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Входим..." : "Войти"}
      </button>
    </form>
  );
}
