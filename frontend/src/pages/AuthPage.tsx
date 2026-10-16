import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";
import Icon from "../components/Icon";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useI18n } from "../i18n/I18nContext";
import type { UiLang } from "../i18n/translations";

export default function AuthPage() {
  const { token, loading, login, register } = useAuth();
  const { t, lang, setLang } = useI18n();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [prefLang, setPrefLang] = useState<UiLang>(lang);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const ar = lang === "ar";
  const copy = (en: string, arabic: string) => ar ? arabic : en;

  if (token && !loading) return <Navigate to="/" replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      if (mode === "login") await login(email.trim(), password);
      else {
        await register(email.trim(), password, fullName.trim(), prefLang);
        setLang(prefLang === "ar" ? "ar" : "en");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t("auth.failed"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <section className="auth-story">
        <div className="brand"><div className="brand-mark"><Icon name="book" /></div><span>ResearchGuide <small>AI</small></span></div>
        <div className="auth-story-content"><div className="eyebrow">{copy("YOUR CURIOSITY. A CLEARER PATH.", "فضولك العلمي. طريق أوضح.")}</div>
          <h1>{copy("Big ideas start", "الأفكار الكبيرة تبدأ")}<br /><em>{copy("with a question.", "بسؤال.")}</em></h1>
          <p>{copy("A thoughtful workspace to shape your ideas, connect the evidence, and move your research forward with confidence.", "مساحة عمل متكاملة لتطوير أفكارك وربط الأدلة والمضي ببحثك بثقة.")}</p>
          <div className="auth-journey"><div><Icon name="spark" />{copy("Turn curiosity into a clear research plan", "حوّل فضولك إلى خطة بحث واضحة")}</div><div><Icon name="book" />{copy("Keep your evidence and ideas connected", "اربط الأدلة بأفكارك البحثية")}</div><div><Icon name="shield" />{copy("Stay the author. Stay in control.", "أنت المؤلف وصاحب القرار.")}</div></div>
        </div>
        <div className="auth-story-footer"><Icon name="shield" size={17} />{copy("Built around research integrity, guided by you.", "مصمم حول النزاهة العلمية، بتوجيه منك.")}</div>
      </section>
      <section className="auth-form-side">
        <div className="auth-lang-bar"><LanguageSwitcher /></div>
        <div className="card auth-card stack">
        <div><h2>{mode === "login" ? copy("Welcome back.", "أهلاً بعودتك.") : copy("Make room for your next idea.", "امنح فكرتك القادمة مساحة.")}</h2><p className="muted auth-subtitle">{mode === "login" ? copy("Your next discovery is waiting. Let’s get started.", "اكتشافك القادم بانتظارك. لنبدأ.") : copy("Create your account and start your research journey.", "أنشئ حسابك وابدأ رحلتك البحثية.")}</p></div>
        <div className="tabs">
          <button
            type="button"
            className={`tab ${mode === "login" ? "active" : ""}`}
            aria-pressed={mode === "login"}
            disabled={busy}
            onClick={() => { setMode("login"); setError(null); }}
          >
            {t("auth.signIn")}
          </button>
          <button
            type="button"
            className={`tab ${mode === "register" ? "active" : ""}`}
            aria-pressed={mode === "register"}
            disabled={busy}
            onClick={() => { setMode("register"); setError(null); }}
          >
            {t("auth.createAccount")}
          </button>
        </div>
        <form className="stack" onSubmit={onSubmit}>
          {mode === "register" && (
            <>
              <div className="field">
                <label htmlFor="full-name">{t("auth.fullName")}</label>
                <input id="full-name" autoComplete="name" disabled={busy} maxLength={255} value={fullName} onChange={(e) => setFullName(e.target.value)} required />
              </div>
              <div className="field">
                <label htmlFor="preferred-language">{t("auth.preferredLanguage")}</label>
                <select id="preferred-language" disabled={busy}
                  value={prefLang}
                  onChange={(e) => setPrefLang(e.target.value === "ar" ? "ar" : "en")}
                >
                  <option value="en">{t("common.english")}</option>
                  <option value="ar">{t("common.arabic")}</option>
                </select>
              </div>
            </>
          )}
          <div className="field">
            <label htmlFor="email">{t("auth.email")}</label>
            <input
              id="email" type="email" autoComplete="email" placeholder="you@university.edu" disabled={busy}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="password">{t("auth.password")}</label>
            <div className="password-control">
            <input
              id="password" type={showPassword ? "text" : "password"} autoComplete={mode === "login" ? "current-password" : "new-password"} disabled={busy} aria-describedby={mode === "register" ? "password-hint" : undefined}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={mode === "register" ? 8 : undefined}
              required
            /><button type="button" aria-pressed={showPassword} onClick={() => setShowPassword((v) => !v)}>{showPassword ? copy("Hide", "إخفاء") : copy("Show", "إظهار")}</button></div>
            {mode === "register" && <small id="password-hint" className="field-hint">{copy("Use at least 8 characters.", "استخدم ٨ أحرف على الأقل.")}</small>}
          </div>
          {error && <div role="alert" className="error">{error}</div>}
          <button className="btn btn-primary" disabled={busy || loading} type="submit">
            {busy
              ? t("common.pleaseWait")
              : mode === "login"
                ? t("auth.signIn")
                : t("auth.createAccount")}
          </button>
        </form>
        <p className="auth-fineprint">{copy("A little guidance. A lot of possibility.", "قليل من الإرشاد. آفاق واسعة من الإمكانات.")}</p>
      </div>
      <footer>ResearchGuide AI · {copy("A thoughtful space for meaningful research", "مساحة للتفكير المتأني والبحث الهادف")}</footer>
      </section>
    </div>
  );
}
