import { useI18n } from "../i18n/I18nContext";

/** Top-menu control: switch entire UI between English and Arabic. */
export default function LanguageSwitcher({ compact = false }: { compact?: boolean }) {
  const { lang, setLang, t } = useI18n();

  return (
    <div
      className={`lang-switcher ${compact ? "lang-switcher-compact" : ""}`}
      role="group"
      aria-label={t("lang.switchTo")}
      title={t("lang.switchTo")}
    >
      <button
        type="button"
        className={`lang-btn ${lang === "en" ? "active" : ""}`}
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
      >
        EN
      </button>
      <button
        type="button"
        className={`lang-btn ${lang === "ar" ? "active" : ""}`}
        onClick={() => setLang("ar")}
        aria-pressed={lang === "ar"}
      >
        ع
      </button>
    </div>
  );
}
