import { forwardRef, useImperativeHandle, useRef, useState } from "react";

export type VoiceUploadResult = {
  question: string;
  voice_url?: string; // новый ответ от /voice
};

export type VoiceRecorderHandle = {
  /** Идёт ли сейчас запись */
  isRecording: () => boolean;
  /** Остановить запись */
  stop: () => void;
  /** Загрузить записанный файл */
  upload: () => void;
  /** Остановить запись (если идёт) и загрузить результат */
  stopAndUpload: () => void;
};

type Props = {
  onResult: (res: VoiceUploadResult) => void;
  onUploadingChange?: (v: boolean) => void;
  onUnauthorized?: () => void;
  onError?: (msg: string) => void;
  /** Уведомляем родителя, что запись началась/закончилась */
  onRecordingChange?: (v: boolean) => void;
};

/**
 * VoiceRecorder:
 * - две иконки: 🎤(старт) и ⏹(стоп)
 * - при стоп — просто останавливает запись
 * - загрузка происходит только по вызову upload() или stopAndUpload()
 * - НОВОЕ: /voice теперь возвращает { question, voice_url }, а не answer
 */
const VoiceRecorder = forwardRef<VoiceRecorderHandle, Props>(function VoiceRecorder(
  { onResult, onUploadingChange, onUnauthorized, onError, onRecordingChange }: Props,
  ref
) {
  const [recording, setRecording] = useState(false);
  const [blob, setBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useImperativeHandle(
    ref,
    () => ({
      isRecording: () => recording,
      stop: () => stopRecording(),
      upload: () => uploadRecording(),
      stopAndUpload: () => {
        stopRecording();
        uploadRecording();
      },
    }),
    [recording, blob]
  );

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mr;
      chunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const finalBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        setBlob(finalBlob);
      };

      mr.start();
      setRecording(true);
      onRecordingChange?.(true);
    } catch (err: any) {
      onError?.(err?.message ?? "Доступ к микрофону отклонён");
    }
  }

  function stopRecording() {
    if (!recording) return;
    try {
      mediaRecorderRef.current?.stop();
    } catch {}
    setRecording(false);
    onRecordingChange?.(false);
  }

  async function uploadRecording() {
    if (!blob) {
      onError?.("Нет записанного файла для отправки");
      return;
    }

    try {
      onUploadingChange?.(true);

      const file = new File([blob], "voice.webm", { type: "audio/webm" });
      const formData = new FormData();
      formData.append("voice", file); // ключ: voice

      const token = localStorage.getItem("token") ?? "";
      const res = await fetch(`http://localhost:8080/voice`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });

      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.();
        return;
      }
      if (!res.ok) throw new Error("Не удалось распознать голос");

      const data = await res.json();
      // ожидаем как минимум voice_url, question может быть моковый
      onResult({
        question: String(data?.question ?? ""),
        voice_url: typeof data?.voice_url === "string" ? data.voice_url : undefined,
      });

      setBlob(null); // очищаем файл после успешной отправки
    } catch (err: any) {
      onError?.(err?.message ?? "Ошибка распознавания");
    } finally {
      onUploadingChange?.(false);
    }
  }

  return (
    <div className="flex items-center justify-center p-2">
      {!recording ? (
        <button
          type="button"
          className="group relative w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 ease-in-out flex items-center justify-center text-xl"
          onClick={startRecording}
          title="Начать запись"
          aria-label="Начать запись"
        >
          🎤
        </button>
      ) : (
        <button
          type="button"
          className="group relative w-12 h-12 bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white rounded-full shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 ease-in-out flex items-center justify-center text-xl animate-pulse"
          onClick={stopRecording}
          title="Остановить запись"
          aria-label="Остановить запись"
        >
          ⏹
        </button>
      )}
    </div>
  );
});

export default VoiceRecorder;
