import axios from "axios";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";

export default function Register() {
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [agree, setAgree] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");

    if (!agree) {
      setError("Подтвердите согласие с условиями.");
      return;
    }

    if (password.length < 3) {
      setError("Пароль должен содержать минимум 3 символа");
      return;
    }

    setLoading(true);

    try {
      const payload = {
        login: name,
        password: password,
      };

      const response = await axios.post(
        "http://localhost:8080/reg",
        payload,
        {
          headers: { "Content-Type": "application/json" },
        }
      );

      console.log("Успешная регистрация:", response.data);

      // После регистрации отправляем пользователя на логин
      navigate("/auth/login", {
        replace: true,
        state: { registered: true, loginPrefill: name },
      });

      // Сбросим поля (на случай, если пользователь вернётся назад)
      setName("");
      setPassword("");
      setAgree(false);
    } catch (err: any) {
      console.error("Ошибка регистрации:", err);

      if (axios.isAxiosError(err)) {
        if (err.response) {
          setError(
            (err.response.data as any)?.message ||
              `Ошибка ${err.response.status}`
          );
        } else if (err.request) {
          setError("Сервер не отвечает. Проверьте подключение.");
        } else {
          setError("Произошла ошибка при отправке запроса");
        }
      } else {
        setError("Произошла неизвестная ошибка");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="form">
      <h3>Регистрация</h3>

      {error && <div className="error-message" style={{ color: "tomato" }}>{error}</div>}

      <label>
        Имя
        <input
          type="text"
          placeholder="Иван Иванов"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          disabled={loading}
        />
      </label>

      <label>
        Пароль
        <input
          type="password"
          placeholder="Минимум 3 символа"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={3}
          disabled={loading}
        />
      </label>

      <label className="checkbox">
        <input
          type="checkbox"
          checked={agree}
          onChange={(e) => setAgree(e.target.checked)}
          disabled={loading}
        />
        <span>Я согласен с условиями сервиса</span>
      </label>

      <button type="submit" disabled={loading}>
        {loading ? "Регистрация..." : "Зарегистрироваться"}
      </button>
    </form>
  );
}
