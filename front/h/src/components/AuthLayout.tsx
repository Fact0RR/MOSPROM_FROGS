import { Outlet } from "react-router-dom";

export default function AuthLayout() {
  // просто выводим дочерние страницы без шапки и вкладок
  return <Outlet />;
}
