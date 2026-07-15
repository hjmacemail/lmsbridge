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

  // LMS file import
  const [cvProvider, setCvProvider] = useState("canvas");
  const [cvBase, setCvBase] = useState("");
  const [cvToken, setCvToken] = useState("");
  const [cvCourse, setCvCourse] = useState("");
  const [cvBusy, setCvBusy] = useState(false);
  const [cvNote, setCvNote] = useState<string | null>(null);

  function load() {
    api.materials(courseId).then(setMaterials).catch((e) => setErr((e as Error).message));
  }
  useEffect(load, [courseId]);

  // Prefill provider + course id from the LTI launch context.
  useEffect(() => {
    api.lmsContext(courseId).then((c) => {
      if (c.provider) setCvProvider(c.provider);
      if (c.lms_course_ref) setCvCourse(c.lms_course_ref);
    }).catch(() => {});
  }, [courseId]);

  const ID_LABEL: Record<string, string> = {
    canvas: t("instructor.materials.idCanvas"), moodle: t("instructor.materials.idMoodle"),
    brightspace: t("instructor.materials.idBrightspace"),
  };
  const TOKEN_HELP: Record<string, string> = {
    canvas: t("instructor.materials.tokenCanvas"),
    moodle: t("instructor.materials.tokenMoodle"),
    brightspace: t("instructor.materials.tokenBrightspace"),
  };

  async function importLms(e: React.FormEvent) {
    e.preventDefault();
    if (!cvBase || !cvToken || !cvCourse) {
      setCvNote(t("instructor.materials.enterLmsFields")); return;
    }
    setCvBusy(true); setCvNote(null);
    try {
      const r = await api.importLmsFiles(courseId, cvProvider, cvBase, cvToken, cvCourse);
      setCvNote(t("instructor.materials.importedFiles", { imported: r.imported, skipped: r.skipped, total: r.total }));
      setCvToken("");
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
    await api.deleteMaterial(id);
    load();
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
              <label>{t("instructor.materials.titleOptional")}</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder={t("instructor.materials.titlePlaceholder")} />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t("instructor.materials.conceptOptional")}</label>
              <select value={conceptId} onChange={(e) =>
                setConceptId(e.target.value === "" ? "" : Number(e.target.value))}>
                <option value="">{t("instructor.materials.wholeCourse")}</option>
                {concepts.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t("instructor.materials.fileLabel")}</label>
              <input ref={fileRef} type="file" accept=".pdf,.docx,.md,.markdown,.txt" />
            </div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} disabled={busy}>
            {busy ? t("instructor.materials.uploading") : t("instructor.materials.uploadBtn")}
          </button>
          {err && <div className="error">{err}</div>}
        </form>
      </div>

      <div className="card" style={{ marginBottom: 18 }}>
        <h3>{t("instructor.materials.importTitle")}</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          {t("instructor.materials.importHelp")} <em>{TOKEN_HELP[cvProvider]}.</em>
        </p>
        <form onSubmit={importLms}>
          <div className="grid cols-2" style={{ alignItems: "end" }}>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t("instructor.materials.lmsLabel")}</label>
              <select value={cvProvider} onChange={(e) => setCvProvider(e.target.value)}>
                <option value="canvas">Canvas</option>
                <option value="moodle">Moodle</option>
                <option value="brightspace">Brightspace</option>
              </select>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t("instructor.materials.lmsUrl")}</label>
              <input value={cvBase} onChange={(e) => setCvBase(e.target.value)}
                placeholder="https://school.instructure.com" />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{t("instructor.materials.accessToken")}</label>
              <input type="password" value={cvToken} onChange={(e) => setCvToken(e.target.value)}
                placeholder={t("instructor.materials.pasteToken")} autoComplete="off" />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label>{ID_LABEL[cvProvider]}</label>
              <input value={cvCourse} onChange={(e) => setCvCourse(e.target.value)}
                placeholder="e.g. 12345" />
            </div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} disabled={cvBusy}>
            {cvBusy ? t("instructor.materials.importing") : t("instructor.materials.importBtn")}
          </button>
          {cvNote && <div className="muted" style={{ fontSize: 13, marginTop: 8 }}>{cvNote}</div>}
        </form>
      </div>

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
