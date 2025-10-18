import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import ChatInput from "../components/ChatInput";
import VoiceRecorder, {
  type VoiceUploadResult,
  type VoiceRecorderHandle,
} from "../components/VoiceRecorder";
import axios from "axios";
import "../styles/chat.css";

const API_BASE = "http://localhost:8080";

type HistoryItem = {
  id?: number;
  question: string;
  answer: string;
  answer_id?: number;
  created_at?: string;
};

export default function Chat() {
  const navigate = useNavigate();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [liked, setLiked] = useState<Record<number, boolean>>({});
  const [isRecording, setIsRecording] = useState(false);
  const [pendingVoice, setPendingVoice] = useState(false); // есть готовая, но неотправленная запись
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const voiceRef = useRef<VoiceRecorderHandle | null>(null);

  useEffect(() => {
    if (!getToken()) navigate("/auth/login", { replace: true });
  }, [navigate]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError("");
      try {
        const { data } = await axios.get<HistoryItem[]>(
          `${API_BASE}/history`,
          { headers: authHeaders() }
        );
        if (!cancelled) {
          const items: HistoryItem[] = Array.isArray(data)
            ? data.map((x: any) => ({
                id: x?.id,
                question: String(x?.question ?? ""),
                answer: String(x?.answer ?? ""),
                answer_id:
                  typeof x?.answer_id === "number" ? x.answer_id : undefined,
                created_at: x?.created_at,
              }))
            : [];
          setHistory(items);
        }
      } catch (err: any) {
        if (!cancelled) handleHttpError(err, navigate, setError);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, sending]);

  async function handleSend(message: string, voice_url?: string) {
    const question = message.trim();
    if (!question && !voice_url) return; // хотя бы что-то одно

    // создаём временную запись в истории
    setHistory((prev) => [
      ...prev,
      { question: question || "Голосовое сообщение", answer: "", created_at: new Date().toISOString() },
    ]);

    setSending(true);
    setError("");

    try {
      const payload: any = { question };
      if (voice_url) payload.voice_url = voice_url; // новый необязательный параметр

      const { data } = await axios.post<{ answer: string; answer_id?: number }>(
        `${API_BASE}/message`,
        payload,
        { headers: authHeaders() }
      );

      // обновляем последнюю незаполненную по этому вопросу запись
      setHistory((prev) => {
        const copy = [...prev];
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].answer === "") {
            copy[i] = {
              ...copy[i],
              answer: String((data as any)?.answer ?? ""),
              answer_id:
                typeof (data as any)?.answer_id === "number"
                  ? (data as any).answer_id
                  : copy[i].answer_id,
            };
            break;
          }
        }
        return copy;
      });
    } catch (err: any) {
      // убрать только последний незавершённый элемент
      setHistory((prev) => {
        const copy = [...prev];
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].answer === "") { copy.splice(i, 1); break; }
        }
        return copy;
      });
      handleHttpError(err, navigate, setError);
    } finally {
      setSending(false);
    }
  }

  async function clearHistory() {
    setError("");
    try {
      await axios.delete(`${API_BASE}/clear`, { headers: authHeaders() });
      setHistory([]);
      setLiked({});
    } catch (err: any) {
      handleHttpError(err, navigate, setError);
    }
  }

  async function likeAnswer(answer_id?: number) {
    if (!answer_id || liked[answer_id]) return;
    setError("");
    try {
      await axios.put(
        `${API_BASE}/like`,
        { answer_id, like: true },
        { headers: authHeaders() }
      );
      setLiked((prev) => ({ ...prev, [answer_id]: true }));
    } catch (err: any) {
      handleHttpError(err, navigate, setError);
    }
  }

  // Новый поток: результат загрузки голоса теперь содержит voice_url,
  // а сам ответ получаем отдельным запросом на /message
  async function handleVoiceResult(res: VoiceUploadResult) {
    const question = (res.question || "").trim();
    const voice_url = res.voice_url || "";

    setPendingVoice(false);

    await handleSend(question || "Голосовое сообщение", voice_url);
  }

  function handleVoiceUnauthorized() {
    localStorage.removeItem("token");
    navigate("/auth/login", { replace: true });
  }

  return (
    <section className="chat-container">
      <Header onClear={clearHistory} />
      {error && <div className="chat-error">{error}</div>}

      <div className="chat-messages" aria-live="polite">
        {loading && history.length === 0 ? (
          <div className="chat-empty">Загрузка истории…</div>
        ) : history.length === 0 ? (
          <div className="chat-empty">Сообщений пока нет</div>
        ) : (
          history.map((item, idx) => (
            <div key={`${item.id ?? idx}-wrap`}>
              <div className="msg user">
                <div className="meta">
                  <span className="role">Вы</span>
                  <span className="time">{formatTime(item.created_at)}</span>
                </div>
                <div className="text">{item.question}</div>
              </div>

              {item.answer !== "" && (
                <div className="msg bot">
                  <div className="meta">
                    <span className="role">Бот</span>
                    <div className="meta-actions">
                      <button
                        className="icon"
                        title="Нравится"
                        onClick={() => likeAnswer(item.answer_id)}
                        disabled={!item.answer_id || !!liked[item.answer_id]}
                      >
                        {liked[item.answer_id ?? -1] ? "✅" : "👍"}
                      </button>
                    </div>
                  </div>
                  <div className="text">{item.answer}</div>
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Инпут: если идёт запись — кнопка останавливает.
          Если запись остановлена (есть blob) — кнопка отправляет голос. */}
      <ChatInput
        onSend={(msg) => handleSend(msg)}
        disabled={sending}
        overrideActive={isRecording || pendingVoice}
        onOverridePrimary={() => {
          if (isRecording) {
            // Только стоп — без отправки
            voiceRef.current?.stop();
            // после onstop VoiceRecorder вызовет onRecordingChange(false)
            // и мы активируем кнопку отправки
          } else if (pendingVoice) {
            // Отправляем записанный голос
            voiceRef.current?.upload();
          }
        }}
        overrideDisabled={sending} // пока идёт аплоад — блокируем кнопку
      >
        <div className="voice-btn-wrapper">
          <VoiceRecorder
            ref={voiceRef}
            onResult={handleVoiceResult}
            onUploadingChange={(v) => {
              setSending(v);
              if (v) setPendingVoice(false); // во время отправки скрываем состояние ожидания
            }}
            onUnauthorized={handleVoiceUnauthorized}
            onError={(msg) => setError(msg)}
            onRecordingChange={(rec) => {
              setIsRecording(rec);
              if (!rec) {
                // Запись только что остановили — можно нажать "Отправить"
                setPendingVoice(true);
              } else {
                setPendingVoice(false);
              }
            }}
          />
        </div>
      </ChatInput>
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
  setError: (msg: string) => void
) {
  const status = err?.response?.status;
  if (status === 401 || status === 403) {
    localStorage.removeItem("token");
    navigate("/auth/login", { replace: true });
    return;
  }
  const msg =
    err?.response?.data?.message ??
    err?.message ??
    "Ошибка сети. Попробуйте позже.";
  setError(msg);
  console.error("HTTP error:", err);
}

function formatTime(ts?: string) {
  try {
    const d = ts ? new Date(ts) : new Date();
    return d.toLocaleTimeString();
  } catch {
    return "";
  }
}
