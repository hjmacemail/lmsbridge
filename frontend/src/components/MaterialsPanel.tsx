import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { ConceptOut, Material } from "../types";

function fmtSize(n: number) {
  return n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1048576).toFixed(1)} MB`;
}

export default function MaterialsPanel({
  courseId, concepts,
}: { courseId: number; concepts: ConceptOut[] }) {
  const { t } = useTranslation();
  const [materials, setMaterials] = useState<Material[]>([]);
  const [title, setTitle] = useState("");
  const [conceptId, setConceptId] = useState<number | "">("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // One-click LMS import: the institution admin connects the LMS once; the instructor enters nothing.
  const [lms, setLms] = useState<
    { connected: boolean; provider: string | null; has_course_ref: boolean; can_import: boolean } | null>(null);
  const [cvBusy, setCvBusy] = useState(false);
  const [cvNote, setCvNote] = useState<string | null>(null);

  function load() {
    api.materials(courseId).then(setMaterials).catch((e) => setErr((e as Error).message));
  }
  useEffect(load, [courseId]);

  useEffect(() => {
    api.lmsImportStatus(courseId).then(setLms).catch(() => setLms(null));
  }, [courseId]);

  async function importLmsAuto() {
    setCvBusy(true); setCvNote(null);
    try {
      const r = await api.importLmsAuto(courseId);
      setCvNote(t("instructor.materials.importedFiles", { imported: r.imported, skipped: r.skipped, total: r.total }));
      load();
    } catch (e) {
      setCvNote((e as Error).message);
    } finally {
      setCvBusy(false);
    }
  }

  async function upload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileRef.current?.files?.[0];
    if (!file) { setErr(t("instructor.materials.chooseFile")); return; }
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
    if (!window.confirm(t("instructor.materials.confirmDelete", { defaultValue: "Delete this material? This cannot be undone." }))) return;
    setErr(null);
    try {
      await api.deleteMaterial(id);
      load();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <div>
      <div className="card" style={{ marginBottom: 18 }}>
        <h3>{t("instructor.materials.uploadTitle")}</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          {t("instructor.materials.uploadHelp")}
        </p>
        <form onSubmit={upload}>
          <div className="grid cols-3" style={{ alignItems: "end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="material-title">{t("instructor.materials.titleOptional")}</label>
              <input id="material-title" value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder={t("instructor.materials.titlePlaceholder")} />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="material-concept">{t("instructor.materials.conceptOptional")}</label>
              <select id="material-concept" value={conceptId} onChange={(e) =>
                setConceptId(e.target.value === "" ? "" : Number(e.target.value))}>
                <option value="">{t("instructor.materials.wholeCourse")}</option>
                {concepts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label htmlFor="material-file">{t("instructor.materials.fileLabel")}</label>
              <input id="material-file" ref={fileRef} type="file" accept=".pdf,.docx,.md,.markdown,.txt" />
            </div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} disabled={busy}>
            {busy ? t("instructor.materials.uploading") : t("instructor.materials.uploadBtn")}
          </button>
          {err && <div className="error">{err}</div>}
        </form>
      </div>

      {lms && (
        <div className="card" style={{ marginBottom: 18 }}>
          <h3 style={{ marginBottom: 6 }}>
            {t("instructor.materials.importTitle")}{" "}
            <span className="pill pending" style={{ fontWeight: 600, marginLeft: 4 }}>{t("instructor.materials.importTag")}</span>
          </h3>
          <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>{t("instructor.materials.importDesc")}</p>
          {lms.can_import ? (
            <>
              <button className="btn" onClick={importLmsAuto} disabled={cvBusy}>
                {cvBusy ? t("instructor.materials.importing") : t("instructor.materials.importOneClick")}
              </button>
              {cvNote && <div className="muted" style={{ fontSize: 13, marginTop: 8 }}>{cvNote}</div>}
            </>
          ) : lms.connected ? (
            <div className="feedback" style={{ fontSize: 13 }}>{t("instructor.materials.importOpenFromLms")}</div>
          ) : (
            <div className="feedback" style={{ fontSize: 13 }}>{t("instructor.materials.importAdminNeeded")}</div>
          )}
        </div>
      )}

      <div className="card">
        <h3>{t("instructor.materials.libraryTitle", { count: materials.length })}</h3>
        <table>
          <thead>
            <tr><th>{t("instructor.materials.thTitle")}</th><th>{t("instructor.materials.thFile")}</th><th>{t("instructor.materials.thSize")}</th><th>{t("instructor.materials.thText")}</th><th></th></tr>
          </thead>
          <tbody>
            {materials.length === 0 && (
              <tr><td colSpan={5} className="muted">{t("instructor.materials.noMaterials")}</td></tr>
            )}
            {materials.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.title}</td>
                <td className="muted">{m.filename}</td>
                <td>{fmtSize(m.size_bytes)}</td>
                <td>{m.has_text
                  ? <span className="pill mastered">{t("instructor.materials.extracted")}</span>
                  : <span className="pill at_risk">{t("instructor.materials.none")}</span>}</td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button className="btn secondary" style={{ padding: "6px 10px" }}
                    onClick={() => api.authedDownload(`/materials/${m.id}/download`, m.filename)}>
                    {t("common.download")}
                  </button>{" "}
                  <button className="btn secondary" style={{ padding: "6px 10px", color: "var(--at-risk)" }}
                    onClick={() => remove(m.id)}>{t("common.delete")}</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
