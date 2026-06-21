import { useEffect, useState } from "react";
import {
  sageApi, saveToken, clearToken, loadToken,
  type SageAuth, type SageClassSummary, type SagePostItem,
  type SagePostDetail, type SageInsights,
} from "../api/client";

type View = "auth" | "classes" | "board" | "thread" | "insights";
const USER_KEY = "sage_user";

function loadUser(): SageAuth | null {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as SageAuth) : null;
}
function persist(a: SageAuth) {
  saveToken({ access_token: a.access_token, token_type: a.token_type,
    role: a.role, user_id: a.user_id, full_name: a.full_name } as Parameters<typeof saveToken>[0]);
  sessionStorage.setItem(USER_KEY, JSON.stringify(a));
}

const wrap: React.CSSProperties = { maxWidth: 820, margin: "0 auto", padding: "0 16px 48px" };
const ink = "#3a2d6d";

export default function SageApp() {
  const [user, setUser] = useState<SageAuth | null>(loadUser());
  const [view, setView] = useState<View>(loadToken() && loadUser() ? "classes" : "auth");
  const [cls, setCls] = useState<SageClassSummary | null>(null);
  const [postId, setPostId] = useState<number | null>(null);

  function onAuth(a: SageAuth) { persist(a); setUser(a); setView("classes"); }
  function signOut() { clearToken(); sessionStorage.removeItem(USER_KEY); setUser(null); setView("auth"); }
  function openClass(c: SageClassSummary) { setCls(c); setView("board"); }
  function openPost(id: number) { setPostId(id); setView("thread"); }

  return (
    <div style={{ minHeight: "100vh", background: "#faf9ff" }}>
      <header style={{ background: ink, color: "#fff", padding: "14px 0", marginBottom: 24 }}>
        <div style={{ ...wrap, display: "flex", justifyContent: "space-between",
          alignItems: "center", paddingBottom: 0 }}>
          <div style={{ cursor: "pointer", fontWeight: 800, fontSize: 20, letterSpacing: -0.4 }}
            onClick={() => setView(user ? "classes" : "auth")}>
            Sage <span style={{ opacity: 0.7, fontWeight: 400, fontSize: 13 }}>· by LMS Bridge</span>
          </div>
          {user && (
            <div style={{ fontSize: 13, display: "flex", gap: 14, alignItems: "center" }}>
              <span style={{ opacity: 0.85 }}>{user.full_name}</span>
              <button className="btn" style={{ padding: "4px 12px" }} onClick={signOut}>Sign out</button>
            </div>
          )}
        </div>
      </header>
      <div style={wrap}>
        {view === "auth" && <Auth onAuth={onAuth} />}
        {view === "classes" && user &&
          <Classes onOpen={openClass} />}
        {view === "board" && cls &&
          <Board cls={cls} onBack={() => setView("classes")} onOpen={openPost}
            onInsights={() => setView("insights")} />}
        {view === "thread" && cls && postId != null &&
          <Thread postId={postId} cls={cls} onBack={() => setView("board")} />}
        {view === "insights" && cls &&
          <Insights cls={cls} onBack={() => setView("board")} />}
      </div>
    </div>
  );
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ background: "#fff", border: "1px solid #e7e3f5", borderRadius: 14,
    padding: 20, marginBottom: 16, ...style }}>{children}</div>;
}

// ----------------------------------------------------------------- Auth
function Auth({ onAuth }: { onAuth: (a: SageAuth) => void }) {
  const [mode, setMode] = useState<"signup" | "join" | "login">("signup");
  const [name, setName] = useState(""); const [email, setEmail] = useState("");
  const [pw, setPw] = useState(""); const [code, setCode] = useState("");
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  async function go(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      if (mode === "signup") onAuth(await sageApi.signup(name, email, pw));
      else if (mode === "login") {
        const t = await sageApi.login(email, pw);
        onAuth({ access_token: t.access_token, token_type: t.token_type,
          user_id: 0, full_name: email, role: "instructor" });
      } else onAuth(await sageApi.guestJoin(code.trim().toUpperCase(), name));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const tab = (m: typeof mode, label: string) => (
    <button onClick={() => { setMode(m); setErr(null); }}
      style={{ flex: 1, padding: "8px 0", border: "none", cursor: "pointer",
        background: mode === m ? ink : "transparent", color: mode === m ? "#fff" : ink,
        borderRadius: 8, fontWeight: 600, fontSize: 14 }}>{label}</button>
  );

  return (
    <div style={{ maxWidth: 440, margin: "24px auto" }}>
      <h1 style={{ textAlign: "center", color: ink, marginBottom: 6 }}>Welcome to Sage</h1>
      <p style={{ textAlign: "center", color: "#6b6585", marginTop: 0, fontSize: 14 }}>
        An AI-guided class Q&amp;A board. Ask, answer, learn — no LMS required.
      </p>
      <Card>
        <div style={{ display: "flex", gap: 6, marginBottom: 16, background: "#f1eefb",
          padding: 4, borderRadius: 10 }}>
          {tab("signup", "Teach")}{tab("join", "Join a class")}{tab("login", "Log in")}
        </div>
        <form onSubmit={go} className="stack" style={{ gap: 10 }}>
          {mode === "join" && (
            <input placeholder="Class join code (e.g. 7QK4PD)" value={code}
              onChange={(e) => setCode(e.target.value)} />
          )}
          {mode !== "login" && (
            <input placeholder="Your name" value={name} onChange={(e) => setName(e.target.value)} />
          )}
          {mode !== "join" && (
            <input placeholder="Email" type="email" value={email}
              onChange={(e) => setEmail(e.target.value)} />
          )}
          {mode !== "join" && (
            <input placeholder="Password" type="password" value={pw}
              onChange={(e) => setPw(e.target.value)} />
          )}
          <button className="btn" disabled={busy} style={{ background: ink, color: "#fff" }}>
            {busy ? "…" : mode === "signup" ? "Create instructor account"
              : mode === "login" ? "Log in" : "Join class"}
          </button>
          {err && <div className="error">{err}</div>}
        </form>
      </Card>
    </div>
  );
}

// ----------------------------------------------------------------- Classes
function Classes({ onOpen }: { onOpen: (c: SageClassSummary) => void }) {
  const [classes, setClasses] = useState<SageClassSummary[]>([]);
  const [name, setName] = useState(""); const [subject, setSubject] = useState("");
  const [code, setCode] = useState(""); const [msg, setMsg] = useState<string | null>(null);

  const load = () => sageApi.classes().then(setClasses).catch(() => setClasses([]));
  useEffect(() => { load(); }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault(); if (!name) return;
    try { await sageApi.createClass(name, subject); setName(""); setSubject(""); load(); }
    catch (e) { setMsg((e as Error).message); }
  }
  async function join(e: React.FormEvent) {
    e.preventDefault(); if (!code) return;
    try { await sageApi.joinExisting(code.trim().toUpperCase()); setCode(""); load(); }
    catch (e) { setMsg((e as Error).message); }
  }

  return (
    <div>
      <h2 style={{ color: ink }}>Your classes</h2>
      {classes.length === 0 && <p style={{ color: "#6b6585" }}>No classes yet — create one or join with a code.</p>}
      {classes.map((c) => (
        <Card key={c.id} style={{ cursor: "pointer" }}>
          <div onClick={() => onOpen(c)} style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{c.name}</div>
              <div style={{ color: "#6b6585", fontSize: 13 }}>
                {c.subject || "—"} · {c.member_count} members · {c.post_count} questions
                {c.role === "instructor" && <> · join code <b>{c.join_code}</b></>}
              </div>
            </div>
            <span className="pill" style={{ background: "#f1eefb", color: ink }}>{c.role}</span>
          </div>
        </Card>
      ))}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 8 }}>
        <Card>
          <h3 style={{ marginTop: 0 }}>Create a class</h3>
          <form onSubmit={create} className="stack" style={{ gap: 8 }}>
            <input placeholder="Class name" value={name} onChange={(e) => setName(e.target.value)} />
            <input placeholder="Subject (optional)" value={subject}
              onChange={(e) => setSubject(e.target.value)} />
            <button className="btn" style={{ background: ink, color: "#fff" }}>Create</button>
          </form>
        </Card>
        <Card>
          <h3 style={{ marginTop: 0 }}>Join a class</h3>
          <form onSubmit={join} className="stack" style={{ gap: 8 }}>
            <input placeholder="Join code" value={code} onChange={(e) => setCode(e.target.value)} />
            <button className="btn">Join</button>
          </form>
        </Card>
      </div>
      {msg && <div className="error">{msg}</div>}
    </div>
  );
}

// ----------------------------------------------------------------- Board
function Board({ cls, onBack, onOpen, onInsights }: {
  cls: SageClassSummary; onBack: () => void; onOpen: (id: number) => void; onInsights: () => void;
}) {
  const [posts, setPosts] = useState<SagePostItem[]>([]);
  const [title, setTitle] = useState(""); const [body, setBody] = useState("");
  const [tags, setTags] = useState(""); const [anon, setAnon] = useState(false);
  const [busy, setBusy] = useState(false); const [show, setShow] = useState(false);

  const load = () => sageApi.posts(cls.id).then(setPosts).catch(() => setPosts([]));
  useEffect(() => { load(); }, [cls.id]);

  async function ask(e: React.FormEvent) {
    e.preventDefault(); if (!title) return; setBusy(true);
    try { await sageApi.createPost(cls.id, title, body, tags, anon);
      setTitle(""); setBody(""); setTags(""); setAnon(false); setShow(false); load(); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <button className="btn" style={{ padding: "4px 10px", marginBottom: 12 }} onClick={onBack}>← Classes</button>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ color: ink, margin: 0 }}>{cls.name}</h2>
        <div style={{ display: "flex", gap: 8 }}>
          {cls.role === "instructor" &&
            <button className="btn" onClick={onInsights}>Insights</button>}
          <button className="btn" style={{ background: ink, color: "#fff" }}
            onClick={() => setShow((s) => !s)}>{show ? "Cancel" : "Ask a question"}</button>
        </div>
      </div>
      {cls.role === "instructor" &&
        <p style={{ color: "#6b6585", fontSize: 13 }}>Share join code <b>{cls.join_code}</b> with students.</p>}

      {show && (
        <Card>
          <form onSubmit={ask} className="stack" style={{ gap: 8 }}>
            <input placeholder="Question title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <textarea placeholder="Add details…" value={body} rows={3}
              onChange={(e) => setBody(e.target.value)} />
            <input placeholder="Tags (comma-separated)" value={tags}
              onChange={(e) => setTags(e.target.value)} />
            <label style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
              <input type="checkbox" checked={anon} onChange={(e) => setAnon(e.target.checked)} />
              Post anonymously to classmates
            </label>
            <button className="btn" disabled={busy} style={{ background: ink, color: "#fff" }}>
              {busy ? "Posting…" : "Post — Sage will reply"}
            </button>
          </form>
        </Card>
      )}

      {posts.length === 0 && <p style={{ color: "#6b6585" }}>No questions yet. Be the first to ask.</p>}
      {posts.map((p) => (
        <Card key={p.id} style={{ cursor: "pointer" }}>
          <div onClick={() => onOpen(p.id)}>
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span style={{ fontWeight: 600 }}>{p.title}</span>
              <span style={{ fontSize: 12, color: "#6b6585" }}>
                {p.resolved ? "✓ resolved" : `${p.answer_count} answers`}
                {p.has_endorsed && " · endorsed"}
              </span>
            </div>
            <div style={{ fontSize: 12, color: "#6b6585", marginTop: 4 }}>
              {p.author}{p.tags ? ` · ${p.tags}` : ""}
              {p.ai_misconception && <span style={{ color: "#b4530c" }}> · flag: {p.ai_misconception}</span>}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ----------------------------------------------------------------- Thread
function Thread({ postId, cls, onBack }: {
  postId: number; cls: SageClassSummary; onBack: () => void;
}) {
  const [p, setP] = useState<SagePostDetail | null>(null);
  const [reply, setReply] = useState(""); const [busy, setBusy] = useState(false);
  const isInstr = cls.role === "instructor";

  const load = () => sageApi.post(postId).then(setP).catch(() => setP(null));
  useEffect(() => { load(); }, [postId]);
  if (!p) return <p>Loading…</p>;

  async function send(e: React.FormEvent) {
    e.preventDefault(); if (!reply.trim()) return; setBusy(true);
    try { setP(await sageApi.answer(postId, reply)); setReply(""); } finally { setBusy(false); }
  }

  return (
    <div>
      <button className="btn" style={{ padding: "4px 10px", marginBottom: 12 }} onClick={onBack}>← {cls.name}</button>
      <Card>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <h2 style={{ margin: 0, color: ink }}>{p.title}</h2>
          {(isInstr) && <button className="btn" style={{ padding: "4px 10px" }}
            onClick={() => sageApi.resolve(p.id).then(load)}>{p.resolved ? "Reopen" : "Resolve"}</button>}
        </div>
        {p.body && <p style={{ color: "#3a3a3a" }}>{p.body}</p>}
        <div style={{ fontSize: 12, color: "#6b6585" }}>
          {p.author}{p.tags ? ` · ${p.tags}` : ""}
          {p.ai_misconception && <span style={{ color: "#b4530c" }}> · flag: {p.ai_misconception}</span>}
        </div>
      </Card>

      {p.answers.map((a) => (
        <Card key={a.id} style={{
          borderLeft: a.is_ai ? "3px solid #7c5cff" : a.endorsed ? "3px solid #16a34a" : undefined,
          background: a.is_ai ? "#f7f5ff" : "#fff" }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
            <span style={{ fontWeight: 600, color: a.is_ai ? "#5b3fd6" : ink, fontSize: 14 }}>
              {a.author}{a.endorsed && " ✓ endorsed"}
            </span>
            {isInstr && !a.is_ai && (
              <button className="btn" style={{ padding: "2px 8px", fontSize: 12 }}
                onClick={() => sageApi.endorse(a.id).then(load)}>
                {a.endorsed ? "Unendorse" : "Endorse"}
              </button>
            )}
          </div>
          <div style={{ whiteSpace: "pre-wrap", fontSize: 14 }}>{a.body}</div>
        </Card>
      ))}

      <Card>
        <form onSubmit={send} className="stack" style={{ gap: 8 }}>
          <textarea placeholder="Write an answer…" rows={3} value={reply}
            onChange={(e) => setReply(e.target.value)} />
          <button className="btn" disabled={busy} style={{ background: ink, color: "#fff", alignSelf: "flex-start" }}>
            {busy ? "Posting…" : "Post answer"}
          </button>
        </form>
      </Card>
    </div>
  );
}

// ----------------------------------------------------------------- Insights
function Insights({ cls, onBack }: { cls: SageClassSummary; onBack: () => void }) {
  const [d, setD] = useState<SageInsights | null>(null);
  useEffect(() => { sageApi.insights(cls.id).then(setD).catch(() => setD(null)); }, [cls.id]);
  if (!d) return <p>Loading…</p>;
  const stat = (label: string, n: number) => (
    <div style={{ background: "#fff", border: "1px solid #e7e3f5", borderRadius: 12,
      padding: "12px 16px", flex: 1 }}>
      <div style={{ fontSize: 12, color: "#6b6585" }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700, color: ink }}>{n}</div>
    </div>
  );
  return (
    <div>
      <button className="btn" style={{ padding: "4px 10px", marginBottom: 12 }} onClick={onBack}>← {cls.name}</button>
      <h2 style={{ color: ink }}>Class insights</h2>
      <div style={{ display: "flex", gap: 12, marginBottom: 16, flexWrap: "wrap" }}>
        {stat("Members", d.members)}{stat("Questions", d.total_posts)}
        {stat("Open", d.open_count)}{stat("Unanswered", d.unanswered_by_humans)}
      </div>
      <Card>
        <h3 style={{ marginTop: 0 }}>Most common confusions (AI-flagged)</h3>
        {d.top_misconceptions.length === 0 && <p style={{ color: "#6b6585" }}>None flagged yet.</p>}
        {d.top_misconceptions.map((m) => (
          <div key={m.label} style={{ display: "flex", justifyContent: "space-between",
            padding: "6px 0", borderBottom: "1px solid #f0eef8" }}>
            <span>{m.label}</span><b>{m.count}</b>
          </div>
        ))}
      </Card>
      <Card>
        <h3 style={{ marginTop: 0 }}>Top tags</h3>
        {d.top_tags.length === 0 && <p style={{ color: "#6b6585" }}>No tags yet.</p>}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {d.top_tags.map((t) => (
            <span key={t.tag} className="pill" style={{ background: "#f1eefb", color: ink }}>
              {t.tag} · {t.count}
            </span>
          ))}
        </div>
      </Card>
    </div>
  );
}
