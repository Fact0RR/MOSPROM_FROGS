import { Outlet, NavLink } from "react-router-dom";
import "./AuthLayout.css";

export default function AuthLayout() {
  return (
    <section>
      <h2>Аккаунт</h2>
      <div className="tabs">
        <NavLink 
          to="/auth/login" 
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Вход
        </NavLink>
        <NavLink 
          to="/auth/register" 
          className={({ isActive }) => isActive ? "active" : ""}
        >
          Регистрация
        </NavLink>
      </div>
      <div className="card">
        <Outlet />
      </div>
    </section>
  );
}