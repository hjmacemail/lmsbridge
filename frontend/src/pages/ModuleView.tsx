import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { SessionState, TutorMessage } from "../types";

export default function ModuleView(
  { moduleId: moduleIdProp, onBack }: { moduleId?: number; onBack?: () => void } = {},
) {
  const { id } = useParams();
  const nav = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language;
  const moduleId = moduleIdProp ?? Number(id);
  const goBack = onBack ?? (() => nav(-1));
  const goDashboard = onBack ?? (() => nav("/dashboard"));

  const [session, setSession] = useState<SessionState | null>(null);
  const [messages, setMessages] = useState<TutorMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [complete, setComplete] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.startSession(moduleId, lang)
      .then((s) => {
        setSession(s);
        setMessages(s.messages);
        setComplete(s.status === "completed");
      })
      .catch((e) => setErr((e as Error).message));
  }, [moduleId]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy || complete) return;
    setInput("");
    setBusy(true);
    const nextSeq = messages.length;
    setMessages((m) => [...m, { id: -1, sequence: nextSeq, role: "student", content: text }]);
    try {
      const turn = await api.sendSessionMessage(moduleId, text, lang);
      setMessages((m) => [
        ...m,
        { id: -2, sequence: nextSeq + 1, role: "tutor", content: turn.reply },
      ]);
      if (turn.complete) setComplete(true);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (err) return <div className="container"><div className="card error">{err}</div></div>;
  if (!session) return <div className="container"><p className="muted">{t("tutor.starting")}</p></div>;

  return (
    <div className="container" style={{ maxWidth: 760 }}>
      <button className="btn secondary" onClick={goBack} style={{ marginBottom: 16 }}>
        {t("tutor.back")}
      </button>
      <div className="row">
        <h1 style={{ fontSize: 22 }}>{session.title}</h1>
        <span className={`pill ${complete ? "completed" : "in_progress"}`}>
          {complete ? t("tutor.completed") : t("tutor.inSession")}
        </span>
      </div>
      <p className="muted" style={{ fontSize: 13 }}>
        {t("tutor.intro")}
        {session.grounded_on?.length
          ? " " + t("tutor.groundedIn", { sources: session.grounded_on.join(", ") }) : ""}
      </p>

      <div className="card chat" style={{ marginTop: 12 }}>
        <div className="chat-log">
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              {m.role === "tutor" && <div className="bubble-who">{t("tutor.aiTutor")}</div>}
              <div className="bubble-text">{m.content}</div>
            </div>
          ))}
          {busy && (
            <div className="bubble tutor">
              <div className="bubble-who">{t("tutor.aiTutor")}</div>
              <div className="bubble-text muted">{t("tutor.thinking")}</div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {complete ? (
          <div className="session-done">
            {t("tutor.complete")}
            <div style={{ marginTop: 12 }}>
              <button className="btn" onClick={goDashboard}>{t("tutor.backToDashboard")}</button>
            </div>
          </div>
        ) : (
          <form className="chat-input" onSubmit={send}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(e); }
              }}
              placeholder={t("tutor.placeholder")}
              rows={2}
              disabled={busy}
            />
            <button className="btn" disabled={busy || !input.trim()}>{t("tutor.send")}</button>
          </form>
        )}
      </div>
    </div>
  );
}
