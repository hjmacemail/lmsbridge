import { useEffect, useRef, useState, type CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { renderMarkdown } from "../lib/richtext";

/**
 * A lightweight, dependency-free Markdown editor: a formatting toolbar (bold, italic, heading,
 * quote, lists, code, link) over a plain textarea, plus a live Write/Preview toggle.
 *
 * It stores plain Markdown (not HTML), so it stays compatible with everywhere the app already
 * renders `renderMarkdown()` — announcements, syllabus, course materials — and the preview is the
 * exact same, XSS-safe renderer used on display. Works in both LTR and RTL.
 */
export default function MarkdownEditor({
  value, onChange, placeholder, minHeight = 120, ariaLabel,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  minHeight?: number;
  ariaLabel?: string;
}) {
  const { t } = useTranslation();
  const taRef = useRef<HTMLTextAreaElement>(null);
  const selRef = useRef<[number, number] | null>(null);
  const [tab, setTab] = useState<"write" | "preview">("write");

  // Restore the caret/selection after a toolbar edit re-renders the controlled textarea.
  useEffect(() => {
    if (selRef.current && taRef.current) {
      const [s, e] = selRef.current;
      taRef.current.focus();
      taRef.current.setSelectionRange(s, e);
      selRef.current = null;
    }
  }, [value]);

  function wrap(before: string, after: string, ph: string) {
    const ta = taRef.current;
    const s = ta ? ta.selectionStart : value.length;
    const e = ta ? ta.selectionEnd : value.length;
    const sel = value.slice(s, e) || ph;
    const next = value.slice(0, s) + before + sel + after + value.slice(e);
    selRef.current = [s + before.length, s + before.length + sel.length];
    onChange(next);
  }

  function linePrefix(prefix: string) {
    const ta = taRef.current;
    const s = ta ? ta.selectionStart : 0;
    const e = ta ? ta.selectionEnd : 0;
    const lineStart = value.lastIndexOf("\n", s - 1) + 1;
    const segment = value.slice(lineStart, e) || "";
    const prefixed = segment.split("\n").map((l) => prefix + l).join("\n");
    const next = value.slice(0, lineStart) + prefixed + value.slice(e);
    selRef.current = [lineStart, lineStart + prefixed.length];
    onChange(next);
  }

  const tools: { label: string; title: string; run: () => void; style?: CSSProperties }[] = [
    { label: "B", title: t("editor.bold", { defaultValue: "Bold" }),
      run: () => wrap("**", "**", t("editor.boldText", { defaultValue: "bold text" })),
      style: { fontWeight: 800 } },
    { label: "I", title: t("editor.italic", { defaultValue: "Italic" }),
      run: () => wrap("*", "*", t("editor.italicText", { defaultValue: "italic text" })),
      style: { fontStyle: "italic" } },
    { label: "H", title: t("editor.heading", { defaultValue: "Heading" }),
      run: () => linePrefix("## "), style: { fontWeight: 800 } },
    { label: "“”", title: t("editor.quote", { defaultValue: "Quote" }), run: () => linePrefix("> ") },
    { label: "•", title: t("editor.bulleted", { defaultValue: "Bulleted list" }), run: () => linePrefix("- ") },
    { label: "1.", title: t("editor.numbered", { defaultValue: "Numbered list" }), run: () => linePrefix("1. ") },
    { label: "</>", title: t("editor.code", { defaultValue: "Code" }),
      run: () => wrap("`", "`", t("editor.codeText", { defaultValue: "code" })),
      style: { fontFamily: "monospace", fontSize: 12 } },
    { label: "🔗", title: t("editor.link", { defaultValue: "Link" }),
      run: () => wrap("[", "](https://)", t("editor.linkText", { defaultValue: "text" })) },
  ];

  const btn: CSSProperties = {
    minWidth: 30, height: 28, padding: "0 7px", border: "1px solid var(--line, #e2e8f0)",
    background: "#fff", color: "var(--ink, #1f2340)", borderRadius: 6, cursor: "pointer",
    fontSize: 13.5, lineHeight: 1, display: "inline-flex", alignItems: "center", justifyContent: "center",
  };
  const tabBtn = (active: boolean): CSSProperties => ({
    ...btn, minWidth: 0, fontWeight: 600,
    background: active ? "var(--primary, #6355e6)" : "#fff",
    color: active ? "#fff" : "var(--muted, #6b7183)",
    borderColor: active ? "var(--primary, #6355e6)" : "var(--line, #e2e8f0)",
  });

  return (
    <div style={{ border: "1px solid var(--line, #e2e8f0)", borderRadius: 8, overflow: "hidden",
      background: "#fff" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap",
        padding: 6, borderBottom: "1px solid var(--line, #e2e8f0)", background: "var(--soft, #f5f4fc)" }}>
        {tools.map((tool) => (
          <button key={tool.title} type="button" title={tool.title} aria-label={tool.title}
            onClick={tool.run} disabled={tab === "preview"}
            style={{ ...btn, ...tool.style, opacity: tab === "preview" ? 0.4 : 1,
              cursor: tab === "preview" ? "default" : "pointer" }}>{tool.label}</button>
        ))}
        <span style={{ flex: 1 }} />
        <button type="button" style={tabBtn(tab === "write")} onClick={() => setTab("write")}>
          {t("editor.write", { defaultValue: "Write" })}</button>
        <button type="button" style={tabBtn(tab === "preview")} onClick={() => setTab("preview")}>
          {t("editor.preview", { defaultValue: "Preview" })}</button>
      </div>

      {tab === "write" ? (
        <textarea
          ref={taRef}
          aria-label={ariaLabel}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          style={{ display: "block", width: "100%", border: "none", outline: "none",
            padding: "11px 13px", fontSize: 14, fontFamily: "inherit", resize: "vertical",
            minHeight, background: "#fff", color: "var(--ink, #1f2340)" }}
        />
      ) : (
        <div className="sage-md" style={{ padding: "11px 13px", minHeight, fontSize: 14,
          color: "var(--ink, #1f2340)" }}
          dangerouslySetInnerHTML={{
            __html: value.trim()
              ? renderMarkdown(value)
              : `<span style="color:var(--muted,#6b7183)">${t("editor.nothingToPreview", { defaultValue: "Nothing to preview yet." })}</span>`,
          }} />
      )}
    </div>
  );
}
