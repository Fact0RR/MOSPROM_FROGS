import { useState, type ReactNode } from "react";

type Props = {
  onSend: (msg: string) => void;
  disabled?: boolean;
  placeholder?: string;
  /** Контент справа внутри инпута (например, VoiceRecorder) */
  children?: ReactNode;

  /**
   * Когда true — основная красная кнопка выполняет override-действие
   * (например, stopAndUpload для голосовой записи).
   */
  overrideActive?: boolean;
  /** Обработчик override-действия основной кнопки */
  onOverridePrimary?: () => void;
  /** Блокировка основной кнопки при активном override */
  overrideDisabled?: boolean;
};

export default function ChatInput({
  onSend,
  disabled,
  placeholder = "Введите сообщение...",
  children,
  overrideActive = false,
  onOverridePrimary,
  overrideDisabled = false,
}: Props) {
  const [value, setValue] = useState("");

  function submit() {
    const v = value.trim();
    if (!v || disabled) return;
    onSend(v);
    setValue("");
  }

  const buttonDisabled = overrideActive
    ? overrideDisabled
    : disabled || !value.trim();

  function onPrimaryClick() {
    if (overrideActive) {
      onOverridePrimary?.();
    } else {
      submit();
    }
  }

  return (
    <div className="chat-input">
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !overrideActive) submit();
        }}
        placeholder={placeholder}
        disabled={disabled}
        aria-label="Сообщение"
      />

      {/* Доп. элементы справа внутри инпута (микрофон и пр.) */}
      <div className="chat-input__addon-right" aria-hidden={false}>
        {children}
      </div>

      <button
        type="button"
        onClick={onPrimaryClick}
        disabled={buttonDisabled}
        aria-label={overrideActive ? "Остановить запись и отправить" : "Отправить"}
        title={overrideActive ? "Остановить запись и отправить" : "Отправить"}
      />
    </div>
  );
}

