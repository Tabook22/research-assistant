import { useCallback, useEffect, useRef, useState } from "react";
import {
  type VoiceLang,
  type VoiceLangMode,
  resolveVoiceLang,
  shouldSwitchRecognitionLang,
  toSpeechBcp47,
} from "../lib/languageDetect";

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: ((ev: Event) => void) | null;
  onend: ((ev: Event) => void) | null;
  onerror: ((ev: Event & { error?: string }) => void) | null;
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null;
};

type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: { transcript: string; confidence?: number };
    };
  };
};

function getRecognitionConstructor(): (new () => SpeechRecognitionLike) | null {
  if (typeof window === "undefined") return null;
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  };
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

export function isSpeechRecognitionSupported(): boolean {
  return getRecognitionConstructor() !== null;
}

export type SpeechFinalPayload = {
  text: string;
  lang: VoiceLang;
  bcp47: string;
};

/**
 * Bilingual speech-to-text (English / Arabic).
 * Recognition language is set explicitly so the engine produces the correct script.
 */
export function useSpeechToText(options: {
  mode: VoiceLangMode;
  projectWritingLang?: string | null;
  existingText?: string;
  onFinalTranscript?: (payload: SpeechFinalPayload) => void;
  onInterimTranscript?: (text: string, lang: VoiceLang) => void;
  onLanguageResolved?: (lang: VoiceLang, reason: string) => void;
}) {
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [supported] = useState(() => isSpeechRecognitionSupported());
  const [activeLang, setActiveLang] = useState<VoiceLang>(() =>
    resolveVoiceLang(options.mode, options.projectWritingLang, options.existingText)
  );

  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const wantListenRef = useRef(false);
  const activeLangRef = useRef(activeLang);
  const modeRef = useRef(options.mode);
  const restartTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silenceSwitchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const gotResultRef = useRef(false);
  const triedAltLangRef = useRef(false);

  const onFinalRef = useRef(options.onFinalTranscript);
  const onInterimRef = useRef(options.onInterimTranscript);
  const onLangRef = useRef(options.onLanguageResolved);

  useEffect(() => {
    onFinalRef.current = options.onFinalTranscript;
    onInterimRef.current = options.onInterimTranscript;
    onLangRef.current = options.onLanguageResolved;
  }, [options.onFinalTranscript, options.onInterimTranscript, options.onLanguageResolved]);

  useEffect(() => {
    modeRef.current = options.mode;
    // When user changes EN/AR/Auto while idle, update active language
    if (!wantListenRef.current) {
      const next = resolveVoiceLang(
        options.mode,
        options.projectWritingLang,
        options.existingText
      );
      activeLangRef.current = next;
      setActiveLang(next);
    }
  }, [options.mode, options.projectWritingLang, options.existingText]);

  const clearTimers = useCallback(() => {
    if (restartTimerRef.current) {
      clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
    if (silenceSwitchTimerRef.current) {
      clearTimeout(silenceSwitchTimerRef.current);
      silenceSwitchTimerRef.current = null;
    }
  }, []);

  const abortRecognition = useCallback(() => {
    const rec = recognitionRef.current;
    recognitionRef.current = null;
    if (rec) {
      try {
        rec.onend = null;
        rec.onstart = null;
        rec.onresult = null;
        rec.onerror = null;
        rec.abort();
      } catch {
        /* ignore */
      }
    }
  }, []);

  const startWithLang = useCallback(
    (lang: VoiceLang, reason: string) => {
      const Ctor = getRecognitionConstructor();
      if (!Ctor) {
        setError(
          "Voice input is not supported in this browser. Use Chrome or Edge, or type instead."
        );
        wantListenRef.current = false;
        setListening(false);
        return;
      }

      abortRecognition();
      activeLangRef.current = lang;
      setActiveLang(lang);
      onLangRef.current?.(lang, reason);

      const recognition = new Ctor();
      const bcp47 = toSpeechBcp47(lang);
      recognition.lang = bcp47;
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setListening(true);
        setError(null);
        // In Auto mode: if no usable result after a few seconds, try the other language once
        if (modeRef.current === "auto" && !triedAltLangRef.current) {
          if (silenceSwitchTimerRef.current) clearTimeout(silenceSwitchTimerRef.current);
          silenceSwitchTimerRef.current = setTimeout(() => {
            if (!wantListenRef.current || gotResultRef.current || triedAltLangRef.current) return;
            triedAltLangRef.current = true;
            const alt: VoiceLang = activeLangRef.current === "ar" ? "en" : "ar";
            startWithLang(alt, "auto-fallback-no-result");
          }, 3500);
        }
      };

      recognition.onerror = (ev) => {
        const code = (ev as { error?: string }).error || "unknown";
        if (code === "aborted") return;
        if (code === "no-speech") return;
        // Terminal failures must not repeatedly reopen the microphone.
        wantListenRef.current = false;
        clearTimers();
        setListening(false);
        if (code === "not-allowed") {
          setError("Microphone permission denied. Allow the mic in your browser settings.");
          wantListenRef.current = false;
          setListening(false);
          return;
        }
        if (code === "network") {
          setError("Speech service network error. Check your connection and try again.");
        } else if (code === "language-not-supported") {
          setError(
            lang === "ar"
              ? "Arabic speech recognition is not available in this browser/OS. Try Chrome, or type in Arabic."
              : "English speech recognition is not available in this browser."
          );
        } else {
          setError(`Voice input error: ${code}`);
        }
      };

      recognition.onresult = (event) => {
        let interimText = "";
        let finalText = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const piece = event.results[i][0]?.transcript || "";
          if (event.results[i].isFinal) {
            finalText += piece;
          } else {
            interimText += piece;
          }
        }

        const combined = `${finalText} ${interimText}`.trim();
        if (combined) {
          gotResultRef.current = true;
        }

        // Auto: switch engine language when transcript script clearly mismatches
        if (combined) {
          const switchTo = shouldSwitchRecognitionLang(
            modeRef.current,
            activeLangRef.current,
            combined
          );
          if (switchTo) {
            // Commit any final text first with the language that produced it
            if (finalText.trim()) {
              onFinalRef.current?.({
                text: finalText.trim(),
                lang: activeLangRef.current,
                bcp47: toSpeechBcp47(activeLangRef.current),
              });
            }
            setInterim("");
            startWithLang(switchTo, "auto-script-detect");
            return;
          }
        }

        if (finalText.trim()) {
          onFinalRef.current?.({
            text: finalText.trim(),
            lang: activeLangRef.current,
            bcp47: toSpeechBcp47(activeLangRef.current),
          });
        }
        setInterim(interimText);
        onInterimRef.current?.(interimText, activeLangRef.current);
      };

      recognition.onend = () => {
        if (!wantListenRef.current) {
          setListening(false);
          setInterim("");
          return;
        }
        // Chrome ends continuous sessions periodically — restart same language
        if (recognitionRef.current === recognition) {
          recognitionRef.current = null;
        }
        restartTimerRef.current = setTimeout(() => {
          if (wantListenRef.current) {
            startWithLang(activeLangRef.current, "session-restart");
          }
        }, 200);
      };

      recognitionRef.current = recognition;
      setListening(true);
      try {
        recognition.start();
      } catch {
        setError("Could not start voice input. Try again.");
        wantListenRef.current = false;
        setListening(false);
      }
    },
    [abortRecognition, clearTimers]
  );

  const stop = useCallback(() => {
    wantListenRef.current = false;
    clearTimers();
    // stop() allows the engine to deliver its final words before onend.
    // abort() is reserved for unmount/language changes, when results must be discarded.
    const recognition = recognitionRef.current;
    if (recognition) {
      try { recognition.stop(); }
      catch { abortRecognition(); setListening(false); setInterim(""); }
    } else { setListening(false); setInterim(""); }
  }, [abortRecognition, clearTimers]);

  const start = useCallback(() => {
    setError(null);
    gotResultRef.current = false;
    triedAltLangRef.current = false;
    wantListenRef.current = true;

    const initial = resolveVoiceLang(
      modeRef.current,
      options.projectWritingLang,
      options.existingText
    );
    startWithLang(
      initial,
      modeRef.current === "auto" ? "auto-initial" : "manual"
    );
  }, [options.existingText, options.projectWritingLang, startWithLang]);

  const toggle = useCallback(() => {
    if (wantListenRef.current || listening) stop();
    else start();
  }, [listening, start, stop]);

  /** Force language while listening (or just set for next start). */
  const setLanguage = useCallback(
    (lang: VoiceLang, restartIfListening = true) => {
      activeLangRef.current = lang;
      setActiveLang(lang);
      onLangRef.current?.(lang, "user-select");
      if (restartIfListening && wantListenRef.current) {
        gotResultRef.current = false;
        triedAltLangRef.current = true; // don't auto-flip away immediately
        startWithLang(lang, "user-select");
      }
    },
    [startWithLang]
  );

  useEffect(() => {
    return () => {
      wantListenRef.current = false;
      clearTimers();
      abortRecognition();
    };
  }, [abortRecognition, clearTimers]);

  return {
    supported,
    listening,
    interim,
    error,
    activeLang,
    activeBcp47: toSpeechBcp47(activeLang),
    start,
    stop,
    toggle,
    setLanguage,
    clearError: () => setError(null),
  };
}

// Back-compat helpers
export function speechLangFromProject(writingLanguage?: string | null): string {
  return toSpeechBcp47(resolveVoiceLang("auto", writingLanguage, ""));
}
