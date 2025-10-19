// VoiceRecorder.tsx
import { forwardRef, useImperativeHandle, useRef, useState } from "react";

export type VoiceUploadResult = {
  question: string;
  voice_url?: string;
};

export type VoiceRecorderHandle = {
  isRecording: () => boolean;
  stop: () => void;
  upload: () => void;
  stopAndUpload: () => void;
};

type Props = {
  onResult: (res: VoiceUploadResult) => void;
  onUploadingChange?: (v: boolean) => void;
  onUnauthorized?: () => void;
  onError?: (msg: string) => void;
  onRecordingChange?: (v: boolean) => void;
  onLocalUrl?: (url: string) => void;
};

const VoiceRecorder = forwardRef<VoiceRecorderHandle, Props>(function VoiceRecorder(
  { onResult, onUploadingChange, onUnauthorized, onError, onRecordingChange, onLocalUrl }: Props,
  ref
) {
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const blobRef = useRef<Blob | null>(null);
  const uploadingRef = useRef(false);
  const localUrlRef = useRef<string | null>(null);

  function revokeLocalUrl() {
    if (localUrlRef.current) {
      try {
        URL.revokeObjectURL(localUrlRef.current);
      } catch {
        /* noop */
      }
      localUrlRef.current = null;
    }
  }

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
    [recording]
  );

  async function startRecording() {
    try {
      revokeLocalUrl();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mr;
      chunksRef.current = [];
      blobRef.current = null;

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      mr.onstop = () => {
        const finalBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        blobRef.current = finalBlob;
        const url = URL.createObjectURL(finalBlob);
        localUrlRef.current = url;
        onLocalUrl?.(url);
        onRecordingChange?.(false);

        try {
          stream.getTracks().forEach((track) => track.stop());
        } catch {
          /* noop */
        }
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
    } catch {
      /* noop */
    }
    setRecording(false);
  }

  async function uploadRecording() {
    try {
      if (uploadingRef.current) return;
      const readyBlob = blobRef.current;
      if (!readyBlob) {
        onError?.("Нет записанного файла для отправки");
        return;
      }

      uploadingRef.current = true;
      onUploadingChange?.(true);

      const file = new File([readyBlob], "voice.webm", { type: "audio/webm" });
      const formData = new FormData();
      formData.append("voice", file);

      const token = localStorage.getItem("token") ?? "";
      const headers: HeadersInit = token
        ? { Authorization: `Bearer ${token}`, Accept: "application/json" }
        : { Accept: "application/json" };

      const res = await fetch(`http://localhost:8080/voice`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (res.status === 401 || res.status === 403) {
        onUnauthorized?.();
        return;
      }
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
          text?.trim()
            ? `Не удалось распознать голос: ${text}`
            : "Не удалось распознать голос"
        );
      }

      let data: any;
      try {
        data = await res.json();
      } catch {
        throw new Error("Сервер вернул некорректный JSON при распознавании голоса");
      }

      onResult({
        question: String(data?.question ?? ""),
        voice_url: typeof data?.voice_url === "string" ? data.voice_url : undefined,
      });
    } catch (err: any) {
      onError?.(err?.message ?? "Ошибка распознавания");
    } finally {
      uploadingRef.current = false;
      onUploadingChange?.(false);
    }
  }

  return (
    <div className="flex items-center justify-center p-2">
      {!recording ? (
        <button
          type="button"
          className="w-8 h-8 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors"
          onClick={startRecording}
          title="Начать запись"
          aria-label="Начать запись"
        >
          <svg
            width="18"
            height="23"
            viewBox="0 0 18 23"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M8.625 0.046875C9.9055 0.046875 11.1336 0.555488 12.0391 1.46094C12.9445 2.36639 13.4531 3.5945 13.4531 4.875V10.875L13.4473 11.1143C13.3868 12.3071 12.8857 13.4385 12.0371 14.2871C11.132 15.1922 9.90504 15.7016 8.625 15.7031L8.38574 15.6973C7.19285 15.6368 6.06147 15.1357 5.21289 14.2871C4.30776 13.382 3.79836 12.155 3.79688 10.875V4.875C3.79688 3.5945 4.30549 2.36639 5.21094 1.46094C6.11639 0.555488 7.3445 0.046875 8.625 0.046875ZM8.625 2.20312C7.91637 2.20312 7.23643 2.48428 6.73535 2.98535C6.23428 3.48643 5.95312 4.16637 5.95312 4.875V10.875C5.95312 11.5836 6.23428 12.2636 6.73535 12.7646C7.23643 13.2657 7.91637 13.5469 8.625 13.5469C9.33363 13.5469 10.0136 13.2657 10.5146 12.7646C11.0157 12.2636 11.2969 11.5836 11.2969 10.875V4.875C11.2969 4.16637 11.0157 3.48643 10.5146 2.98535C10.0136 2.48428 9.33363 2.20312 8.625 2.20312ZM7.54688 19.3857L7.50586 19.3809C5.4435 19.1067 3.55051 18.0925 2.17871 16.5283C0.807068 14.9641 0.0495254 12.9554 0.046875 10.875C0.046875 10.5891 0.160117 10.3145 0.362305 10.1123C0.564492 9.91012 0.839064 9.79688 1.125 9.79688C1.41094 9.79688 1.68551 9.91012 1.8877 10.1123C2.08988 10.3145 2.20312 10.5891 2.20312 10.875C2.20312 12.5782 2.87965 14.2117 4.08398 15.416C5.28832 16.6203 6.92181 17.2969 8.625 17.2969C10.3282 17.2969 11.9617 16.6203 13.166 15.416C14.3704 14.2117 15.0469 12.5782 15.0469 10.875C15.0469 10.5891 15.1601 10.3145 15.3623 10.1123C15.5645 9.91012 15.8391 9.79688 16.125 9.79688C16.4109 9.79688 16.6855 9.91012 16.8877 10.1123C17.0899 10.3145 17.2031 10.5891 17.2031 10.875L17.1934 11.2637C17.103 13.2045 16.3573 15.0618 15.0713 16.5283C13.6995 18.0925 11.8065 19.1067 9.74414 19.3809L9.70312 19.3857V21.375C9.70312 21.6609 9.58988 21.9355 9.3877 22.1377C9.18551 22.3399 8.91094 22.4531 8.625 22.4531C8.33906 22.4531 8.06449 22.3399 7.8623 22.1377C7.66012 21.9355 7.54688 21.6609 7.54688 21.375V19.3857Z"
              fill="currentColor"
              stroke="currentColor"
              strokeWidth="0.09375"
            />
          </svg>
        </button>
      ) : (
        <button
          type="button"
          className="w-8 h-8 flex items-center justify-center text-red-600 hover:text-red-700 transition-colors"
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
