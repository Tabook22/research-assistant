/**
 * Arabic / English script detection for bilingual voice input.
 * Used to pick the correct Web Speech API language code.
 */

export type VoiceLang = "en" | "ar";
export type VoiceLangMode = "auto" | "en" | "ar";
export type ScriptDetection = VoiceLang | "mixed" | "unknown";

const ARABIC_LETTER_RE = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/g;
const LATIN_LETTER_RE = /[A-Za-z]/g;

/** Count Arabic vs Latin letters and decide dominant language of the text. */
export function detectScriptLanguage(text: string): ScriptDetection {
  if (!text || !text.trim()) return "unknown";

  const arabic = (text.match(ARABIC_LETTER_RE) || []).length;
  const latin = (text.match(LATIN_LETTER_RE) || []).length;
  const total = arabic + latin;

  if (total < 2) return "unknown";

  const arRatio = arabic / total;
  const enRatio = latin / total;

  // Clear bilingual mix in the same string
  if (arRatio >= 0.35 && enRatio >= 0.35) return "mixed";
  if (arabic > 0 && arRatio >= 0.4) return "ar";
  if (latin > 0 && enRatio >= 0.55) return "en";
  if (arabic > latin) return "ar";
  if (latin > arabic) return "en";
  return "unknown";
}

/** BCP-47 tag for the browser SpeechRecognition API. */
export function toSpeechBcp47(lang: VoiceLang): string {
  // ar-SA is widely available; engines still accept Modern Standard / dialectal Arabic speech.
  return lang === "ar" ? "ar-SA" : "en-US";
}

export function speechLangLabel(lang: VoiceLang): string {
  return lang === "ar" ? "العربية (Arabic)" : "English";
}

/**
 * Resolve which recognition language to use.
 * - Fixed mode (en/ar): always that language
 * - Auto: prefer script of existing field text, else project writing language
 */
export function resolveVoiceLang(
  mode: VoiceLangMode,
  projectWritingLang?: string | null,
  existingText?: string
): VoiceLang {
  if (mode === "en") return "en";
  if (mode === "ar") return "ar";

  const fromText = detectScriptLanguage(existingText || "");
  if (fromText === "ar" || fromText === "en") return fromText;

  const code = (projectWritingLang || "en").toLowerCase();
  if (code.startsWith("ar")) return "ar";
  return "en";
}

/**
 * If Auto mode hears text that is clearly the other language, switch recognition.
 * Returns null when no switch is needed.
 */
export function shouldSwitchRecognitionLang(
  mode: VoiceLangMode,
  current: VoiceLang,
  transcript: string
): VoiceLang | null {
  if (mode !== "auto") return null;
  const detected = detectScriptLanguage(transcript);
  if (detected === "ar" && current !== "ar") return "ar";
  if (detected === "en" && current !== "en") return "en";
  return null;
}

/** Text direction for UI based on dominant script. */
export function textDirection(text: string, fallbackLang?: VoiceLang): "rtl" | "ltr" {
  const d = detectScriptLanguage(text);
  if (d === "ar") return "rtl";
  if (d === "en") return "ltr";
  if (d === "mixed") {
    // Prefer RTL if any substantial Arabic is present
    const arabic = (text.match(ARABIC_LETTER_RE) || []).length;
    return arabic > 0 ? "rtl" : "ltr";
  }
  return fallbackLang === "ar" ? "rtl" : "ltr";
}
