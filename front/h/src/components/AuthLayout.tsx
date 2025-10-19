import { Outlet, NavLink, useLocation } from "react-router-dom";
import "./AuthLayout.css";

export default function AuthLayout() {
  const location = useLocation();
  const normalizedPath = location.pathname.replace(/\/+$/, "");
  const isLogin = normalizedPath === "/auth/login";

  if (isLogin) {
    return <Outlet />;
  }

  return (
    <section>
      <h2>Аккаунт</h2>
      <div className="tabs">
        <NavLink to="/auth/login" className={({ isActive }) => (isActive ? "active" : "")}>
          Вход
        </NavLink>
        <NavLink to="/auth/register" className={({ isActive }) => (isActive ? "active" : "")}>
          Регистрация
        </NavLink>
      </div>
      <div className="card">
        <Outlet />
      </div>
    </section>
  );
}
