import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { SessionState, TutorMessage } from "../types";

function estMin(steps: number) { return Math.max(3, Math.round((steps || 4) * 1.5)); }
function confKey(s: number) {
  return s < 0.4 ? "tutor.confLow" : s < 0.75 ? "tutor.confMedium" : "tutor.confHigh";
}

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

  async function submit(text: string) {
    const val = text.trim();
    if (!val || busy || complete) return;
    setInput("");
    setBusy(true);
    const nextSeq = messages.length;
    setMessages((m) => [...m, { id: -1, sequence: nextSeq, role: "student", content: val }]);
    try {
      const turn = await api.sendSessionMessage(moduleId, val, lang);
      setMessages((m) => [...m, { id: -2, sequence: nextSeq + 1, role: "tutor", content: turn.reply }]);
      if (turn.complete) setComplete(true);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (err) return <div className="container"><div className="card error">{err}</div></div>;
  if (!session) return <div className="container"><p className="muted">{t("tutor.starting")}</p></div>;

  const concept = session.concept_name || session.title;
  const goal = session.goal || t("tutor.goalFallback", { concept });
  const minutes = estMin(session.objectives?.length || 0);
  const ev = session.evidence;
  const hasEvidence = !!ev && !!(ev.chosen || ev.misconception || ev.question);
  const answered = messages.some((m) => m.role === "student");

  const Chip = ({ label }: { label: string }) => (
    <button type="button" onClick={() => submit(label)} disabled={busy}
      style={{
        border: "1px solid var(--line, #e2e2ea)", background: "#fff", color: "var(--ink,#333)",
        borderRadius: 999, padding: "6px 13px", fontSize: 13, cursor: busy ? "default" : "pointer",
        opacity: busy ? 0.5 : 1,
      }}>{label}</button>
  );

  return (
    <div className="container" style={{ maxWidth: 760 }}>
      <button className="btn secondary" onClick={goBack} style={{ marginBottom: 16 }}>
        {t("tutor.back")}
      </button>

      <div className="row" style={{ alignItems: "center" }}>
        <h1 style={{ fontSize: 22 }}>{session.title}</h1>
        {complete ? (
          <span className="pill completed">{t("tutor.completed")}</span>
        ) : (
          <span style={{
            display: "inline-flex", alignItems: "center", gap: 7, fontSize: 12.5, fontWeight: 600,
            color: "#1E7A43", background: "#E5F5EC", padding: "3px 11px", borderRadius: 999,
          }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#2F9D5B" }} />
            {t("tutor.activeStatus")}
          </span>
        )}
      </div>

      {/* Persistent goal banner */}
      <div className="card" style={{
        marginTop: 10, padding: "12px 16px", background: "#EEF0FB", border: "1px solid #D5DAF3",
        display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap",
      }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase",
            color: "#4A4F9E" }}>🎯 {t("tutor.goalLabel")}</div>
          <div style={{ fontSize: 14.5, color: "#23264D", marginTop: 2 }}>{goal}</div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flex: "none" }}>
          <span style={{ fontSize: 12.5, color: "#4A4F9E", background: "#fff", border: "1px solid #D5DAF3",
            borderRadius: 999, padding: "4px 11px", whiteSpace: "nowrap" }}>
            ⏱ {t("tutor.estTime", { min: minutes })}</span>
          {session.mastery_score != null && (
            <span style={{ fontSize: 12.5, color: "#4A4F9E", background: "#fff",
              border: "1px solid #D5DAF3", borderRadius: 999, padding: "4px 11px", whiteSpace: "nowrap" }}>
              {t("tutor.confidenceLabel")}: {t(confKey(session.mastery_score))}</span>
          )}
        </div>
      </div>

      {/* Why you're here — the specific missed answer */}
      {hasEvidence && (
        <div className="card" style={{
          marginTop: 10, padding: "12px 16px", background: "#FBEDDC", border: "1px solid #EAD3AE",
        }}>
          <div style={{ fontSize: 11.5, fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase",
            color: "#8A5312" }}>⚠ {t("tutor.whyCard")}</div>
          {ev!.question && (
            <div style={{ fontSize: 13.5, color: "#5C3A0E", margin: "6px 0", fontStyle: "italic" }}>
              “{ev!.question}”</div>
          )}
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", fontSize: 14, marginTop: 4 }}>
            {ev!.chosen != null && ev!.chosen !== "" && (
              <span style={{ color: "#8A5312" }}>{t("tutor.youAnswered")}:{" "}
                <strong>{ev!.chosen}</strong></span>
            )}
            {ev!.correct != null && ev!.correct !== "" && (
              <span style={{ color: "#1E7A43" }}>{t("tutor.correctAnswer")}:{" "}
                <strong>{ev!.correct}</strong></span>
            )}
          </div>
          {ev!.misconception && (
            <div style={{ fontSize: 13.5, color: "#5C3A0E", marginTop: 6 }}>
              {t("tutor.misconceptionLead")} {ev!.misconception}</div>
          )}
        </div>
      )}

      <p className="muted" style={{ fontSize: 12.5, marginTop: 10 }}>
        {t("tutor.planLabel")}: {t("tutor.planSteps")}
        {session.grounded_on?.length
          ? " · " + t("tutor.groundedIn", { sources: session.grounded_on.join(", ") }) : ""}
      </p>

      <div className="card chat" style={{ marginTop: 8 }}>
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
          <>
            {!answered && (
              <div style={{ padding: "10px 4px 0" }}>
                <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>{t("tutor.quickTitle")}</div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  <Chip label={t("tutor.quickUnsure")} />
                  <Chip label={t("tutor.quickGuessed")} />
                  <Chip label={t("tutor.quickWalk")} />
                </div>
              </div>
            )}

            <form className="chat-input" onSubmit={(e) => { e.preventDefault(); submit(input); }}>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(input); }
                }}
                placeholder={t("tutor.placeholder")}
                rows={2}
                disabled={busy}
              />
              <button className="btn" disabled={busy || !input.trim()}>{t("tutor.send")}</button>
            </form>
            <div className="muted" style={{ fontSize: 12, padding: "0 4px 8px" }}>{t("tutor.inputHint")}</div>

            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center",
              padding: "0 4px 10px" }}>
              <span className="muted" style={{ fontSize: 12 }}>{t("tutor.stuckTitle")}</span>
              <Chip label={t("tutor.stuckHint")} />
              <Chip label={t("tutor.stuckDifferently")} />
              <Chip label={t("tutor.stuckExample")} />
              <Chip label={t("tutor.stuckLost")} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
