import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import ChatInput from "../components/ChatInput";
import "../styles/chat.css";

const API_BASE = "http://localhost:8080";

type SupportApiMessage = {
  id?: number;
  message?: string;
  user_uuid?: string;
  chat_id?: number;
  create_date?: string;
};

type SupportMessage = {
  id?: number | string;
  message: string;
  user_uuid?: string;
  create_date?: string;
  sender: "me" | "remote" | "unknown";
};

type WsStatus = "idle" | "connecting" | "open" | "closed" | "error";

export default function SupportHistory() {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();

  const [joinId, setJoinId] = useState("");
  const [messages, setMessages] = useState<SupportMessage[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [wsStatus, setWsStatus] = useState<WsStatus>("idle");
  const [wsAttempt, setWsAttempt] = useState(0);
  const [error, setError] = useState("");
  const [selfUuid, setSelfUuid] = useState<string>();
  const [canSubscribe, setCanSubscribe] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const keyRef = useRef(0);

  const hasParam = typeof id === "string";
  const chatId = hasParam && /^\d+$/.test(id) ? Number(id) : null;
  const showJoinView = !hasParam || chatId == null;
  const joinValidationError = hasParam && chatId == null;

  useEffect(() => {
    if (!getToken()) {
      navigate("/auth/login", { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    if (chatId == null) {
      setMessages([]);
      setWsStatus("idle");
      setSelfUuid(undefined);
      setCanSubscribe(false);
      return;
    }

    let cancelled = false;
    setLoadingHistory(true);
    setError("");
    setMessages([]);
    setCanSubscribe(false);

    axios
      .get<SupportApiMessage[]>(`${API_BASE}/support_history/${chatId}`, {
        headers: authHeaders(),
      })
      .then(({ data }) => {
        if (cancelled) return;
        const items = Array.isArray(data)
          ? data
              .filter((item) => typeof item?.message === "string")
              .map<SupportMessage>((item) => ({
                id: item?.id ?? `history-${++keyRef.current}`,
                message: String(item?.message ?? ""),
                user_uuid: typeof item?.user_uuid === "string" ? item.user_uuid : undefined,
                create_date: typeof item?.create_date === "string" ? item.create_date : undefined,
                sender: "unknown",
              }))
          : [];
        setMessages(items);
        setCanSubscribe(true);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = handleHttpError(err, navigate, (msg) => setError(msg));
        if (status !== 401) {
          setCanSubscribe(false);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chatId, navigate]);

  useEffect(() => {
    if (chatId == null || !canSubscribe) return;
    const token = getToken();
    if (!token) {
      navigate("/auth/login", { replace: true });
      return;
    }

    setWsStatus("connecting");
    setError("");

    const ws = new WebSocket(buildWsUrl(API_BASE, chatId, token));
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus("open");
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload?.type === "connection_established" && typeof payload?.uuid === "string") {
          setSelfUuid(payload.uuid);
          return;
        }

        if (typeof payload?.message === "string") {
          setMessages((prev) => [
            ...prev,
            {
              id: `ws-${++keyRef.current}`,
              message: payload.message,
              sender: "remote",
              create_date: new Date().toISOString(),
            },
          ]);
        }
      } catch (err) {
        console.warn("Failed to parse WebSocket payload", err);
      }
    };

    ws.onerror = () => {
      setWsStatus("error");
      setError((prev) => prev || "Не удалось установить соединение с чатом");
    };

    ws.onclose = () => {
      setWsStatus((prev) => (prev === "error" ? prev : "closed"));
      wsRef.current = null;
    };

    return () => {
      wsRef.current = null;
      ws.close();
    };
  }, [chatId, wsAttempt, navigate, canSubscribe]);

  useEffect(() => {
    if (!messages.length) return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const wsStatusLabel = useMemo(() => {
    switch (wsStatus) {
      case "open":
        return "В сети";
      case "connecting":
        return "Подключение…";
      case "error":
        return "Ошибка соединения";
      case "closed":
        return "Соединение закрыто";
      default:
        return "Нет соединения";
    }
  }, [wsStatus]);

  if (showJoinView) {
    return (
      <section className="chat-container">
        <header>
          <h2>Подключение к чату поддержки</h2>
        </header>

        <div className="chat-messages">
          <form
            onSubmit={(event) => {
              event.preventDefault();
              const trimmed = joinId.trim();
              if (!trimmed) {
                setError("Введите идентификатор чата");
                return;
              }
              if (!/^\d+$/.test(trimmed)) {
                setError("ID может содержать только цифры");
                return;
              }
              setError("");
              navigate(`/support_history/${trimmed}`);
            }}
            className="message-column"
            style={{ maxWidth: 360, margin: "40px auto", gap: "16px" }}
          >
            <label className="message-column" style={{ gap: "8px" }}>
              <span>Введите ID чата, чтобы присоединиться</span>
              <input
                type="text"
                inputMode="numeric"
                value={joinId}
                onChange={(e) => {
                  setJoinId(e.target.value);
                  if (error) setError("");
                }}
                placeholder="Например, 1"
                style={{
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border: "1px solid #e2e8f0",
                  fontSize: "15px",
                }}
              />
            </label>
            <button
              type="submit"
              style={{
                padding: "12px 16px",
                borderRadius: "10px",
                background: "#2563eb",
                color: "#fff",
                border: "none",
                fontSize: "15px",
                cursor: "pointer",
              }}
            >
              Подключиться
            </button>
            {(error || joinValidationError) && (
              <div className="chat-error" role="alert" style={{ borderRadius: "10px" }}>
                {joinValidationError ? "Некорректный идентификатор чата" : error}
              </div>
            )}
          </form>
        </div>
      </section>
    );
  }

  function handleSend(message: string) {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setError("Соединение с чатом еще не установлено");
      return;
    }

    const payload = message.trim();
    if (!payload) return;

    try {
      ws.send(JSON.stringify({ message: payload }));

      setMessages((prev) => [
        ...prev,
        {
          id: `local-${++keyRef.current}`,
          message: payload,
          user_uuid: selfUuid,
          create_date: new Date().toISOString(),
          sender: "me",
        },
      ]);
      setError("");
    } catch (err) {
      console.error("Failed to send WS message", err);
      setError("Не удалось отправить сообщение");
    }
  }

  return (
    <section className="chat-container">
      <header>
        <h2>Чат #{chatId}</h2>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <span style={{ fontSize: 14, color: wsStatus === "error" ? "#ef4444" : "#475569" }}>
            {wsStatusLabel}
          </span>
          <button
            type="button"
            onClick={() => setWsAttempt((prev) => prev + 1)}
            disabled={wsStatus === "connecting"}
            style={{
              padding: "6px 12px",
              borderRadius: "8px",
              border: "1px solid #334155",
              background: "transparent",
              color: "#334155",
              cursor: wsStatus === "connecting" ? "not-allowed" : "pointer",
            }}
          >
            Обновить соединение
          </button>
        </div>
      </header>

      {error && (
        <div className="chat-error" role="alert">
          {error}
        </div>
      )}

      <div className="chat-messages" aria-live="polite">
        {loadingHistory ? (
          <div className="chat-empty">Загружаем историю…</div>
        ) : !canSubscribe ? (
          <div className="chat-empty">
            Нет доступа к истории этого чата. Проверьте правильность ID или права пользователя.
          </div>
        ) : messages.length === 0 ? (
          <div className="chat-empty">Сообщений пока нет</div>
        ) : (
          messages.map((msg, idx) => {
            const key = msg.id ?? `msg-${idx}`;
            const isMine =
              msg.sender === "me" ||
              (selfUuid && typeof msg.user_uuid === "string" && msg.user_uuid === selfUuid);
            const avatarLabel = isMine
              ? "Вы"
              : typeof msg.user_uuid === "string"
              ? shortenUuid(msg.user_uuid)
              : "Гость";

            return (
              <div
                className={`message-row ${isMine ? "user" : "bot"}`}
                key={key}
              >
                <div className="message-avatar" aria-hidden="true">
                  {avatarLabel}
                </div>
                <div className="message-column">
                  <div className="message-bubble">
                    <p className="message-text">{msg.message}</p>
                    <div className="message-meta">
                      <span>{avatarLabel}</span>
                      <time dateTime={msg.create_date}>
                        {formatTime(msg.create_date)}
                      </time>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput
        onSend={handleSend}
        disabled={!canSubscribe || wsStatus !== "open"}
        placeholder="Напишите сообщение поддержки…"
      />
    </section>
  );
}

function getToken() {
  return localStorage.getItem("token");
}

function authHeaders() {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function handleHttpError(
  err: any,
  navigate: (path: string, opts?: { replace?: boolean }) => void,
  setMessage: (msg: string) => void,
) {
  const status = err?.response?.status;
  if (status === 401) {
    localStorage.removeItem("token");
    navigate("/auth/login", { replace: true });
    return status;
  }
  const msg =
    err?.response?.data?.message ??
    err?.response?.data?.error ??
    err?.message ??
    "Не удалось получить историю чата поддержки";
  setMessage(msg);
  console.error("Support API request failed", err);
  return status;
}

function buildWsUrl(base: string, chatId: number, token: string) {
  const url = new URL(`/support/${chatId}`, base);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.searchParams.set("token", token);
  return url.toString();
}

function formatTime(input?: string) {
  if (!input) return "";
  try {
    return new Date(input).toLocaleTimeString();
  } catch {
    return "";
  }
}

function shortenUuid(uuid: string) {
  if (uuid.length <= 8) return uuid;
  return `${uuid.slice(0, 4)}…${uuid.slice(-4)}`;
}
