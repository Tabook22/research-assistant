import { useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { useI18n } from "../i18n/I18nContext";

type Props = {
  /** Text to translate (English / mixed analysis content). */
  text: string;
  /** Called with Arabic translation for display (does not save to server). */
  onTranslated: (translated: string, meta?: { message?: string }) => void;
  className?: string;
  compact?: boolean;
};

function hasArabic(s: string): boolean {
  return /[\u0600-\u06FF]/.test(s);
}

/**
 * One-click translate to Arabic for ResearchGuide AI comments / analyses.
 */
export default function TranslateButton({
  text,
  onTranslated,
  className = "",
  compact = false,
}: Props) {
  const { token } = useAuth();
  const { t } = useI18n();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [okNote, setOkNote] = useState<string | null>(null);

  async function run() {
    if (!token || !text?.trim()) {
      setError(t("ws.translateFailed"));
      return;
    }
    setBusy(true);
    setError(null);
    setOkNote(null);
    try {
      const res = await api.translateText(token, text, "ar");
      const out = (res.translated || "").trim();
      if (!out) {
        setError(t("ws.translateFailed"));
        return;
      }
      // Already Arabic / no change
      if (out === text.trim() && hasArabic(text)) {
        setOkNote(res.message || t("ws.translateAlreadyAr"));
        onTranslated(out, { message: res.message });
        return;
      }
      if (out === text.trim() && !hasArabic(out)) {
        setError(res.message || t("ws.translateFailed"));
        return;
      }
      if (!hasArabic(out) && text.length > 20) {
        setError(t("ws.translateFailed"));
        return;
      }
      setOkNote(res.message || t("ws.translateOk"));
      onTranslated(out, { message: res.message });
    } catch (e) {
      setError(e instanceof Error ? e.message : t("ws.translateFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (!text?.trim()) return null;

  return (
    <span className={`translate-btn-wrap ${className}`}>
      <button
        type="button"
        className={`btn btn-primary translate-btn${compact ? " translate-btn--compact" : ""}`}
        disabled={busy}
        onClick={() => void run()}
        title={t("ws.translateHint")}
      >
        {busy ? t("ws.translating") : t("ws.translateToAr")}
      </button>
      {error && (
        <span className="error" style={{ fontSize: "0.75rem", marginInlineStart: 4 }}>
          {error}
        </span>
      )}
      {!error && okNote && (
        <span className="muted" style={{ fontSize: "0.75rem", marginInlineStart: 4 }}>
          {okNote}
        </span>
      )}
    </span>
  );
}
