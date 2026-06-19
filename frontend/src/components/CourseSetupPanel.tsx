import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ConceptOut } from "../types";

export default function CourseSetupPanel({ courseId }: { courseId: number }) {
  const [concepts, setConcepts] = useState<ConceptOut[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  // New-concept form
  const [key, setKey] = useState("");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [misc, setMisc] = useState("");
  const [prereqs, setPrereqs] = useState<string[]>([]);

  // New-assessment form
  const [aTitle, setATitle] = useState("");
  const [aType, setAType] = useState("quiz");
  const [aMax, setAMax] = useState(20);

  const load = useCallback(() => {
    api.course(courseId).then((c) => setConcepts(c.concepts)).catch((e) => setErr((e as Error).message));
  }, [courseId]);
  useEffect(() => { load(); setNote(null); }, [load]);

  async function addConcept(e: React.FormEvent) {
    e.preventDefault();
    if (!key.trim() || !name.trim()) { setErr("Key and name are required."); return; }
    setErr(null);
    try {
      await api.addConcept(courseId, {
        key: key.trim(), name: name.trim(), description: desc || undefined,
        common_misconceptions: misc || undefined, sequence: concepts.length,
        prerequisite_keys: prereqs,
      });
      setKey(""); setName(""); setDesc(""); setMisc(""); setPrereqs([]);
      setNote("Concept added.");
      load();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  async function removeConcept(id: number) {
    await api.deleteConcept(courseId, id);
    load();
  }

  async function addAssessment(e: React.FormEvent) {
    e.preventDefault();
    if (!aTitle.trim()) return;
    try {
      await api.createAssessment(courseId, { title: aTitle.trim(), type: aType, max_score: aMax });
      setATitle("");
      setNote(`Assessment “${aTitle.trim()}” created. Ingest results for it from the Brightspace sync or your LMS.`);
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 820 }}>
      {err && <div className="card error">{err}</div>}
      {note && <div className="card" style={{ background: "#f0fdf4", color: "#166534" }}>{note}</div>}

      <div className="card">
        <h3>Concepts ({concepts.length})</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          Concepts are the learning objectives the adaptive engine tracks. Order them from
          foundational to advanced; prerequisites capture which concepts build on others.
        </p>
        <table>
          <thead><tr><th>#</th><th>Concept</th><th>Key</th><th>Prerequisites</th><th></th></tr></thead>
          <tbody>
            {concepts.length === 0 &&
              <tr><td colSpan={5} className="muted">No concepts yet — add the first below.</td></tr>}
            {concepts.map((c, i) => (
              <tr key={c.id}>
                <td className="muted">{i + 1}</td>
                <td style={{ fontWeight: 600 }}>{c.name}
                  {c.common_misconceptions &&
                    <div className="muted" style={{ fontSize: 12 }}>⚠ {c.common_misconceptions}</div>}</td>
                <td className="muted"><code>{c.key}</code></td>
                <td className="muted" style={{ fontSize: 13 }}>
                  {c.prerequisite_keys?.length ? c.prerequisite_keys.join(", ") : "—"}</td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn secondary" style={{ padding: "6px 10px", color: "var(--at-risk)" }}
                    onClick={() => removeConcept(c.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Add a concept</h3>
        <form onSubmit={addConcept}>
          <div className="grid cols-2">
            <div className="field"><label>Key (no spaces)</label>
              <input value={key} onChange={(e) => setKey(e.target.value.replace(/\s+/g, "_"))}
                placeholder="e.g. binary_arithmetic" /></div>
            <div className="field"><label>Display name</label>
              <input value={name} onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Binary Arithmetic" /></div>
          </div>
          <div className="field"><label>Description (optional)</label>
            <input value={desc} onChange={(e) => setDesc(e.target.value)} /></div>
          <div className="field"><label>Common misconceptions (optional — guides the AI)</label>
            <textarea value={misc} onChange={(e) => setMisc(e.target.value)} rows={2}
              placeholder="e.g. Students forget to carry when a column sums to two." /></div>
          {concepts.length > 0 && (
            <div className="field"><label>Prerequisites (concepts this builds on)</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                {concepts.map((c) => (
                  <label key={c.id} style={{ fontSize: 13, display: "flex", gap: 6, alignItems: "center" }}>
                    <input type="checkbox" style={{ width: "auto" }}
                      checked={prereqs.includes(c.key)}
                      onChange={(e) => setPrereqs((p) =>
                        e.target.checked ? [...p, c.key] : p.filter((k) => k !== c.key))} />
                    {c.name}
                  </label>
                ))}
              </div>
            </div>
          )}
          <button className="btn" style={{ marginTop: 8 }}>Add concept</button>
        </form>
      </div>

      <div className="card">
        <h3>Create an assessment</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          For a pilot you can define assessments here, then ingest results via the LMS sync or the
          results API. Quizzes/exams support per-question multiple-choice diagnosis.
        </p>
        <form onSubmit={addAssessment}>
          <div className="grid cols-3" style={{ alignItems: "end" }}>
            <div className="field" style={{ marginBottom: 0 }}><label>Title</label>
              <input value={aTitle} onChange={(e) => setATitle(e.target.value)}
                placeholder="e.g. Quiz 1" /></div>
            <div className="field" style={{ marginBottom: 0 }}><label>Type</label>
              <select value={aType} onChange={(e) => setAType(e.target.value)}>
                <option value="quiz">Quiz (MCQ)</option>
                <option value="exam">Exam (MCQ)</option>
                <option value="assignment">Assignment (rubric)</option>
                <option value="problem_set">Problem set</option>
              </select></div>
            <div className="field" style={{ marginBottom: 0 }}><label>Max score</label>
              <input type="number" value={aMax} onChange={(e) => setAMax(Number(e.target.value))} /></div>
          </div>
          <button className="btn" style={{ marginTop: 14 }}>Create assessment</button>
        </form>
      </div>
    </div>
  );
}
