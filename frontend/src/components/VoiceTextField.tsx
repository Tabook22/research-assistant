import { useCallback, useEffect, useId, useRef, useState, type TextareaHTMLAttributes } from "react";
import { useSpeechToText } from "../hooks/useSpeechToText";
import { useI18n } from "../i18n/I18nContext";
import {
  type VoiceLang,
  type VoiceLangMode,
  speechLangLabel,
  textDirection,
} from "../lib/languageDetect";

type Props = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "value" | "onChange"> & {
  value: string;
  onChange: (value: string) => void;
  language?: string | null;
  compact?: boolean;
  label?: string;
};

const MODE_STORAGE_KEY = "rg_voice_lang_mode";

function loadMode(): VoiceLangMode {
  try {
    const v = localStorage.getItem(MODE_STORAGE_KEY);
    if (v === "en" || v === "ar" || v === "auto") return v;
  } catch {
    /* ignore */
  }
  return "auto";
}

export default function VoiceTextField({
  value,
  onChange,
  language,
  compact,
  label,
  className,
  disabled,
  placeholder,
  ...rest
}: Props) {
  const { t } = useI18n();
  const generatedId = useId();
  const fieldId = rest.id || generatedId;
  const [mode, setMode] = useState<VoiceLangMode>(() => loadMode());
  const [resolvedNote, setResolvedNote] = useState<string | null>(null);
  const valueRef = useRef(value);
  valueRef.current = value;

  const stableAppend = useCallback(
    (payload: { text: string; lang: VoiceLang }) => {
      const piece = payload.text.trim();
      if (!piece) return;
      const current = valueRef.current;
      const next = current ? `${current.trimEnd()} ${piece}` : piece;
      valueRef.current = next;
      onChange(next);
    },
    [onChange]
  );

  const onLanguageResolved = useCallback(
    (lang: VoiceLang, reason: string) => {
      if (reason === "auto-script-detect") {
        setResolvedNote(lang === "ar" ? t("voice.detectedAr") : t("voice.detectedEn"));
      } else if (reason === "auto-fallback-no-result") {
        setResolvedNote(lang === "ar" ? t("voice.switchAr") : t("voice.switchEn"));
      } else if (reason === "auto-initial" || reason === "manual" || reason === "user-select") {
        setResolvedNote(lang === "ar" ? t("voice.recAr") : t("voice.recEn"));
      }
    },
    [t]
  );

  const {
    supported,
    listening,
    interim,
    error,
    activeLang,
    toggle,
    stop,
    setLanguage,
    clearError,
  } = useSpeechToText({
    mode,
    projectWritingLang: language,
    existingText: value,
    onFinalTranscript: stableAppend,
    onLanguageResolved,
  });

  useEffect(() => {
    if (disabled && listening) stop();
  }, [disabled, listening, stop]);

  useEffect(() => {
    try {
      localStorage.setItem(MODE_STORAGE_KEY, mode);
    } catch {
      /* ignore */
    }
  }, [mode]);

  const selectMode = (next: VoiceLangMode) => {
    setMode(next);
    clearError();
    if (next === "en") setLanguage("en", listening);
    else if (next === "ar") setLanguage("ar", listening);
  };

  const dir = textDirection(value || interim, activeLang);

  const displayPlaceholder =
    listening && interim
      ? activeLang === "ar"
        ? `جاري الاستماع… ${interim}`
        : `Listening… ${interim}`
      : placeholder || (activeLang === "ar" ? t("voice.placeholderAr") : t("voice.placeholder"));

  return (
    <div
      className={`voice-field ${compact ? "voice-field-compact" : ""} ${className || ""}`}
      data-voice-lang={activeLang}
    >
      <div className="voice-field-toolbar">
        {label ? <label htmlFor={fieldId} className="voice-field-label">{label}</label> : <span />}
        {supported && (
          <div className="voice-controls">
            <div className="voice-lang-modes" role="group" aria-label="Voice language">
              <button
                type="button"
                className={`voice-lang-btn ${mode === "auto" ? "active" : ""}`}
                onClick={() => selectMode("auto")}
                disabled={disabled}
                title={t("voice.hint")}
              >
                {t("voice.auto")}
              </button>
              <button
                type="button"
                className={`voice-lang-btn ${mode === "en" ? "active" : ""}`}
                onClick={() => selectMode("en")}
                disabled={disabled}
                title={t("common.english")}
              >
                {t("voice.en")}
              </button>
              <button
                type="button"
                className={`voice-lang-btn ${mode === "ar" ? "active" : ""}`}
                onClick={() => selectMode("ar")}
                disabled={disabled}
                title={t("common.arabic")}
              >
                {t("voice.ar")}
              </button>
            </div>
            <button
              type="button"
              className={`btn voice-mic ${listening ? "listening" : ""}`}
              onClick={() => {
                clearError();
                setResolvedNote(null);
                toggle();
              }}
              disabled={disabled}
              title={
                listening
                  ? t("voice.stop")
                  : `${t("voice.voice")} (${speechLangLabel(activeLang)}). ${mode}`
              }
              aria-pressed={listening}
              aria-label={listening ? t("voice.stop") : t("voice.voice")}
            >
              <span className="voice-mic-icon" aria-hidden>
                {listening ? "■" : "🎤"}
              </span>
              <span className="voice-mic-text">
                {listening ? t("voice.stop") : t("voice.voice")}
              </span>
            </button>
          </div>
        )}
        {!supported && (
          <span className="muted voice-unsupported" title={t("voice.unsupportedHint")}>
            {t("voice.typeOnly")}
          </span>
        )}
      </div>

      <textarea
        id={fieldId}
        aria-label={label || placeholder}
        {...rest}
        dir={dir}
        lang={activeLang === "ar" ? "ar" : "en"}
        value={value}
        disabled={disabled}
        placeholder={displayPlaceholder}
        onChange={(e) => onChange(e.target.value)}
        className={listening ? "voice-listening" : undefined}
      />

      {listening && (
        <div className="voice-status listening-status" role="status">
          <span className="voice-pulse" />
          <span>
            {activeLang === "ar" ? t("voice.listeningAr") : t("voice.listeningEn")}
            {mode === "auto" ? ` · ${t("voice.autoMode")}` : ""}
          </span>
          {interim ? (
            <em className="voice-interim" dir={textDirection(interim, activeLang)}>
              {" "}
              “{interim}”
            </em>
          ) : null}
        </div>
      )}

      {resolvedNote && !error && (
        <div className="voice-status voice-resolved" role="status">
          {resolvedNote}
        </div>
      )}

      {error && (
        <div className="voice-status voice-error" role="alert">
          {error}
        </div>
      )}

      {!supported && !compact && (
        <p className="muted voice-hint">{t("voice.unsupportedHint")}</p>
      )}
      {supported && !compact && !listening && (
        <p className="muted voice-hint">{t("voice.hint")}</p>
      )}
    </div>
  );
}
