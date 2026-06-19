import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import LanguageSwitcher from "../components/LanguageSwitcher";

export default function Login() {
  const { login } = useAuth();
  const { t } = useTranslation();
  const nav = useNavigate();
  const [email, setEmail] = useState("ava.chen@student.example.edu");
  const [password, setPassword] = useState("student123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      nav("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 4 }}>
          <LanguageSwitcher />
        </div>
        <h1>LMS<span style={{ color: "var(--primary)" }}> Bridge</span></h1>
        <p className="muted" style={{ marginTop: 0 }}>{t("login.subtitle")}</p>
        <form onSubmit={submit}>
          <div className="field">
            <label>{t("login.email")}</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
          </div>
          <div className="field">
            <label>{t("login.password")}</label>
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
          </div>
          <button className="btn" style={{ width: "100%" }} disabled={busy}>
            {busy ? t("login.signingIn") : t("common.signIn")}
          </button>
          {error && <div className="error">{error}</div>}
        </form>
        <div className="demo-creds">
          <strong>Demo accounts</strong><br />
          Student: ava.chen@student.example.edu / student123<br />
          Instructor: instructor@example.edu / instructor123
        </div>
      </div>
    </div>
  );
}
