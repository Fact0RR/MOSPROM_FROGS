import { Navigate, Route, Routes } from "react-router-dom";
import AuthLayout from "./components/AuthLayout";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Chat from "./pages/Chat";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/auth/login" replace />} />

          
          <Route path="/chat" element={<Chat />} />

         
          <Route path="/auth" element={<AuthLayout />}>
            <Route path="login" element={<Login />} />
            <Route path="register" element={<Register />} />
          </Route>

          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  );
}

function NotFound() {
  return (
    <section className="text-center py-16">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Страница не найдена</h2>
      <p className="text-gray-600">Вернитесь на <a href="/" className="text-blue-600 hover:text-blue-800 underline">главную</a>.</p>
    </section>
  );
}
