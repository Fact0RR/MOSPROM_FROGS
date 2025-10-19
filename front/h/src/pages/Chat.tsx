// Chat.tsx
import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";
import ChatInput from "../components/ChatInput";
import VoiceRecorder, {
  type VoiceUploadResult,
  type VoiceRecorderHandle,
} from "../components/VoiceRecorder";
import axios from "axios";
import "../styles/chat.css";

const API_BASE = "http://localhost:8080";
const CHAT_NAME_OVERRIDES_KEY = "chatNameOverrides";

type HistoryItem = {
  id?: number;
  question: string;          // текст вопроса (или расшифровка голоса)
  answer: string;
  answer_id?: number;
  created_at?: string;
  rating?: number;
  voice_url?: string;        // (опц.) серверный URL на аудио
  transcript?: string;       // (опц.) отдельное поле для расшифровки
  local_url?: string;        // 👈 локальный blob: URL, чтобы сразу проигрывать
};

type ChatSummary = {
  chat_id: number;
  name: string;
};

export default function Chat() {
  const navigate = useNavigate();
  const { id } = useParams<{ id?: string }>();
  const chatId = id && /^\d+$/.test(id) ? Number(id) : null;

  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [chatsLoading, setChatsLoading] = useState(true);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [ratings, setRatings] = useState<Record<number, number>>({});
  const [isRecording, setIsRecording] = useState(false);
  const [pendingVoice, setPendingVoice] = useState(false);

  // сюда положим последний локальный blob: URL из VoiceRecorder
  const lastLocalAudioUrlRef = useRef<string | undefined>(undefined);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const voiceRef = useRef<VoiceRecorderHandle | null>(null);

  useEffect(() => {
    if (!getToken()) navigate("/auth/login", { replace: true });
  }, [navigate]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setChatsLoading(true);
      try {
        const { data } = await axios.get<ChatSummary[]>(
          `${API_BASE}/chats`,
          { headers: authHeaders() }
        );
        if (cancelled) return;
        const overrides = readChatNameOverrides();
        const items: ChatSummary[] = Array.isArray(data)
          ? data
              .map((x: any) => {
                const chat_id = Number(x?.chat_id);
                const baseName = String(x?.name ?? "");
                const override = overrides[String(chat_id)];
                return {
                  chat_id,
                  name: override && override.trim() ? override : baseName,
                };
              })
              .filter((x) => Number.isInteger(x.chat_id) && x.chat_id > 0)
          : [];
        setChats(items);
      } catch (err: any) {
        if (!cancelled) handleHttpError(err, navigate, setError);
      } finally {
        if (!cancelled) setChatsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  useEffect(() => {
    if (chatsLoading) return;
    if (chats.length === 0) {
      setLoading(false);
      return;
    }
    if (chatId == null || !chats.some((chat) => chat.chat_id === chatId)) {
      navigate(`/chat/${chats[0].chat_id}`, { replace: true });
    }
  }, [chatId, chats, chatsLoading, navigate]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (chatId == null) {
        setHistory([]);
        setLoading(false);
        return;
      }
      if (chatsLoading) return;
      if (chats.length > 0 && !chats.some((chat) => chat.chat_id === chatId)) {
        return;
      }
      setLoading(true);
      setError("");
      try {
        const { data } = await axios.get<HistoryItem[]>(
          `${API_BASE}/history/${chatId}`,
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
                rating:
                  typeof x?.rating === "number"
                    ? Math.max(0, Math.min(5, Math.round(x.rating)))
                    : undefined,
                voice_url:
                  typeof x?.voice_url === "string" ? x.voice_url : undefined,
                transcript:
                  typeof x?.transcript === "string" ? x.transcript : undefined,
                // local_url приходит только локально — из истории бэка его не будет
              }))
            : [];
          setHistory(items);
          const ratingMap: Record<number, number> = {};
          for (const item of items) {
            if (item.answer_id && typeof item.rating === "number") {
              ratingMap[item.answer_id] = item.rating;
            }
          }
          setRatings(ratingMap);
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
  }, [navigate, chatId, chats, chatsLoading]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history, sending]);

  // Обновлено: поддержка local_url (blob:)
  async function handleSend(message: string, voice_url?: string, local_url?: string) {
    if (chatId == null) {
      setError("Чат не найден. Обновите страницу или создайте новый чат.");
      return;
    }
    const question = message.trim();
    if (!question && !voice_url && !local_url) return;

    setHistory((prev) => [
      ...prev,
      {
        question: question || "Голосовое сообщение",
        answer: "",
        created_at: new Date().toISOString(),
        voice_url,
        transcript: question || undefined,
        local_url, // 👈 локальный blob URL для мгновенного прослушивания
      },
    ]);

    setSending(true);
    setError("");

    try {
      const payload: any = { question };
      if (voice_url) payload.voice_url = voice_url;

      const { data } = await axios.post<{ answer: string; answer_id?: number; voice_url?: string }>(
        `${API_BASE}/message/${chatId}`,
        payload,
        { headers: authHeaders() }
      );

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
              // если появился серверный URL, можно сохранить как запасной
              voice_url:
                typeof (data as any)?.voice_url === "string"
                  ? (data as any).voice_url
                  : copy[i].voice_url,
            };
            break;
          }
        }
        return copy;
      });
    } catch (err: any) {
      setHistory((prev) => {
        const copy = [...prev];
        for (let i = copy.length - 1; i >= 0; i--) {
          if (copy[i].answer === "") {
            // при ошибке убираем добавленное сообщение
            copy.splice(i, 1);
            break;
          }
        }
        return copy;
      });
      handleHttpError(err, navigate, setError);
    } finally {
      setSending(false);
    }
  }

  async function clearHistory() {
    if (chatId == null) {
      setError("Нет доступного чата для очистки.");
      return;
    }
    setError("");
    try {
      await axios.delete(`${API_BASE}/clear/${chatId}`, {
        headers: authHeaders(),
      });
      setHistory([]);
      setRatings({});
    } catch (err: any) {
      handleHttpError(err, navigate, setError);
    }
  }

  async function createChat() {
    setError("");
    const payloadName = `chat${chats.length + 1}`;

    try {
      const { data } = await axios.post<{
        chat_id?: number;
        chatId?: number;
        id?: number;
        name?: string;
      }>(
        `${API_BASE}/chat`,
        { name: payloadName },
        { headers: authHeaders() }
      );

      const rawId =
        (data as any)?.chat_id ??
        (data as any)?.chatId ??
        (data as any)?.id;
      const newChatId = typeof rawId === "number" ? rawId : Number(rawId);
      const newChatName = String((data as any)?.name ?? payloadName);

      if (!Number.isFinite(newChatId) || newChatId <= 0) {
        setError("Не удалось создать чат. Попробуйте ещё раз.");
        return;
      }

      setChats((prev) => {
        if (prev.some((item) => item.chat_id === newChatId)) {
          return prev.map((item) =>
            item.chat_id === newChatId ? { ...item, name: newChatName } : item
          );
        }
        return [...prev, { chat_id: newChatId, name: newChatName }];
      });
      setHistory([]);
      setRatings({});
      navigate(`/chat/${newChatId}`, { replace: true });
    } catch (err: any) {
      handleHttpError(err, navigate, setError);
    }
  }

  function renameChat(targetId: number | string, nextName: string) {
    const numericId =
      typeof targetId === "number" ? targetId : Number(targetId);
    if (!Number.isFinite(numericId) || numericId <= 0) return;
    const trimmed = nextName.trim();
    if (!trimmed) return;

    persistChatNameOverride(numericId, trimmed);
    setChats((prev) =>
      prev.map((chat) =>
        chat.chat_id === numericId ? { ...chat, name: trimmed } : chat
      )
    );
  }

  async function rateAnswer(answer_id?: number, rating?: number) {
    if (!answer_id || chatId == null || typeof rating !== "number") return;
    const bounded = Math.min(5, Math.max(1, Math.round(rating)));
    if (ratings[answer_id] === bounded) return;
    setError("");
    try {
      await axios.put(
        `${API_BASE}/like/${chatId}`,
        { answer_id, rating: bounded },
        { headers: authHeaders() }
      );
      setRatings((prev) => ({ ...prev, [answer_id]: bounded }));
    } catch (err: any) {
      handleHttpError(err, navigate, setError);
    }
  }

  // теперь сюда прокидываем и локальный URL
  async function handleVoiceResult(res: VoiceUploadResult) {
    const question = (res.question || "").trim();
    const voice_url = res.voice_url || "";
    const local_url = lastLocalAudioUrlRef.current; // 👈 берём, что пришло из VoiceRecorder.onLocalUrl
    setPendingVoice(false);
    await handleSend(question || "Голосовое сообщение", voice_url, local_url);
    // после отправки можно очистить ссылку, если хотите
    lastLocalAudioUrlRef.current = undefined;
  }

  function handleVoiceUnauthorized() {
    localStorage.removeItem("token");
    navigate("/auth/login", { replace: true });
  }

  const headerChats = chats.map((chat) => ({
    id: chat.chat_id,
    name: chat.name || `Чат ${chat.chat_id}`,
  }));

  const hasChats = chats.length > 0;
  const chatReady =
    chatId != null &&
    (!hasChats || chats.some((chat) => chat.chat_id === chatId));
  const inputDisabled = sending || !chatReady;

  return (
    <section className="chat-container">
      <Header
        onClear={clearHistory}
        chats={headerChats}
        chatsLoading={chatsLoading}
        activeChatId={chatId}
        onSelectChat={(nextId) => {
          const numericId =
            typeof nextId === "number" ? nextId : Number(nextId);
          if (!Number.isFinite(numericId) || numericId <= 0) return;
          if (numericId === chatId) return;
          navigate(`/chat/${numericId}`);
        }}
        onCreateChat={createChat}
        onRenameChat={renameChat}
      />
      {error && <div className="chat-error">{error}</div>}

      <div className="chat-messages" aria-live="polite">
        {chatsLoading ? (
          <div className="chat-empty">Загрузка чатов…</div>
        ) : !hasChats ? (
          <div className="chat-empty">У вас пока нет чатов</div>
        ) : !chatReady ? (
          <div className="chat-empty">Загрузка чата…</div>
        ) : loading && history.length === 0 ? (
          <div className="chat-empty">Загрузка истории…</div>
        ) : history.length === 0 ? (
          <div className="chat-empty">Сообщений пока нет</div>
        ) : (
          history.map((item, idx) => {
            const answerId = item.answer_id;
            const currentRating =
              typeof answerId === "number" ? ratings[answerId] ?? 0 : 0;

            const transcriptText = item.transcript || item.question;
            const audioSrc = item.local_url || item.voice_url; // 👈 локальный приоритет

            return (
              <div key={`${item.id ?? idx}-wrap`}>
                {/* USER */}
                <div className="message-row user">
                  <div className="message-avatar">YOU</div>
                  <div className="message-column">
                    <div className="message-bubble">
                      {audioSrc ? (
                        <>
                          <audio
                            className="message-audio"
                            controls
                            src={audioSrc}
                            preload="none"
                            aria-label="Воспроизвести голосовое сообщение"
                          />
                          {transcriptText && (
                            <p
                              className="message-transcript"
                              aria-label="Расшифровка"
                            >
                              {transcriptText}
                            </p>
                          )}
                        </>
                      ) : (
                        <p className="message-text">{transcriptText}</p>
                      )}
                      <div className="message-meta">
                        {formatTime(item.created_at)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* BOT */}
                {item.answer !== "" && (
                  <div className="message-row bot">
                    <div className="message-avatar">BOT</div>
                    <div className="message-column">
                      <div className="message-bubble">
                        <p className="message-text">{item.answer}</p>
                        <div className="message-meta">
                          {formatTime(item.created_at)}
                        </div>
                      </div>
                      <div className="message-rating">
                        <div
                          className="rating-stars"
                          role="radiogroup"
                          aria-label="Оценка ответа"
                        >
                          {[1, 2, 3, 4, 5].map((star) => (
                            <button
                              type="button"
                              key={`star-${star}`}
                              className={`rating-star${
                                currentRating >= star ? " active" : ""
                              }`}
                              role="radio"
                              onClick={() => {
                                if (typeof answerId === "number") {
                                  rateAnswer(answerId, star);
                                }
                              }}
                              disabled={!answerId}
                              aria-checked={currentRating === star}
                              aria-label={`Оценить на ${star}`}
                            >
                              ★
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput
        onSend={(msg) => handleSend(msg)}
        disabled={inputDisabled}
        overrideActive={isRecording || pendingVoice}
        onOverridePrimary={() => {
          if (isRecording) {
            voiceRef.current?.stop();
          } else if (pendingVoice && chatReady) {
            voiceRef.current?.upload();
          }
        }}
        overrideDisabled={sending || (!chatReady && !isRecording)}
      >
        <div className="voice-btn-wrapper">
          <VoiceRecorder
            ref={voiceRef}
            onResult={handleVoiceResult}
            onUploadingChange={(v) => {
              setSending(v);
              if (v) setPendingVoice(false);
            }}
            onUnauthorized={handleVoiceUnauthorized}
            onError={(msg) => setError(msg)}
            onRecordingChange={(rec) => {
              setIsRecording(rec);
              setPendingVoice(!rec ? true : false);
            }}
            // 👇 получаем локальный blob: URL сразу после остановки записи
            onLocalUrl={(url) => {
              lastLocalAudioUrlRef.current = url;
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

type ChatNameOverrides = Record<string, string>;

function readChatNameOverrides(): ChatNameOverrides {
  try {
    const raw = localStorage.getItem(CHAT_NAME_OVERRIDES_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object") return parsed;
    return {};
  } catch {
    return {};
  }
}

function persistChatNameOverride(chatId: number, name: string) {
  const overrides = readChatNameOverrides();
  overrides[String(chatId)] = name;
  try {
    localStorage.setItem(CHAT_NAME_OVERRIDES_KEY, JSON.stringify(overrides));
  } catch (err) {
    console.error("Failed to persist chat name override", err);
  }
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
    return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}
