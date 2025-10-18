import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

export default function Dashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
     
      navigate("/auth/login");
    }
  }, [navigate]);

  function logout() {
    localStorage.removeItem("token");
    navigate("/auth/login");
  }

  return (
    <section>
      <h2>Добро пожаловать</h2>
      <p>Вы успешно авторизованы!</p>
      <button onClick={logout}>Выйти</button>
    </section>
  );
}
