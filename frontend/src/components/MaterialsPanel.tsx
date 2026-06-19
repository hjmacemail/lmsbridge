import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { ConceptOut, Material } from "../types";

function fmtSize(n: number) {
  return n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1048576).toFixed(1)} MB`;
}

export default function MaterialsPanel({
  courseId, concepts,
}: { courseId: number; concepts: ConceptOut[] }) {
  const [materials, setMaterials] = useState<Material[]>([]);
  const [title, setTitle] = useState("");
  const [conceptId, setConceptId] = useState<number | "">("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  function load() {
    api.materials(courseId).then(setMaterials).catch((e) => setErr((e as Error).message));
  }
  useEffect(load, [courseId]);

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) { setErr("Choose a file first."); return; }
    setBusy(true); setErr(null);
    try {
      await api.uploadMaterial(courseId, file, title, conceptId === "" ? null : conceptId);
      setTitle(""); setConceptId("");
      if (fileRef.current) fileRef.current.value = "";
      load();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    await api.deleteMaterial(id);
    load();
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: 18 }}>
        <h3>Upload course material</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          PDF, DOCX, Markdown or text. Extracted text grounds the AI remediation so activities
          use your course's notation, terminology, and examples. Tag a concept to target it.
        </p>
        <form onSubmit={upload}>
          <div className="grid cols-3" style={{ alignItems: "end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Title (optional)</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Week 2 Lecture Notes" />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>Concept (optional)</label>
              <select value={conceptId} onChange={(e) =>
                setConceptId(e.target.value === "" ? "" : Number(e.target.value))}>
                <option value="">— whole course —</option>
                {concepts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>File</label>
              <input ref={fileRef} type="file" accept=".pdf,.docx,.md,.markdown,.txt" />
            </div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} disabled={busy}>
            {busy ? "Uploading…" : "Upload"}
          </button>
          {err && <div className="error">{err}</div>}
        </form>
      </div>

      <div className="card">
        <h3>Library ({materials.length})</h3>
        <table>
          <thead>
            <tr><th>Title</th><th>File</th><th>Size</th><th>Text</th><th></th></tr>
          </thead>
          <tbody>
            {materials.length === 0 && (
              <tr><td colSpan={5} className="muted">No materials yet.</td></tr>
            )}
            {materials.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.title}</td>
                <td className="muted">{m.filename}</td>
                <td>{fmtSize(m.size_bytes)}</td>
                <td>{m.has_text
                  ? <span className="pill mastered">extracted</span>
                  : <span className="pill at_risk">none</span>}</td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button className="btn secondary" style={{ padding: "6px 10px" }}
                    onClick={() => api.authedDownload(`/materials/${m.id}/download`, m.filename)}>
                    Download
                  </button>{" "}
                  <button className="btn secondary" style={{ padding: "6px 10px", color: "var(--at-risk)" }}
                    onClick={() => remove(m.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
