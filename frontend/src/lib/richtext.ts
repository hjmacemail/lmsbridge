// Tiny, dependency-free + XSS-safe helpers for rendering Sage course materials:
//  - renderMarkdown(): a minimal Markdown subset for notes
//  - highlightCode(): lightweight generic syntax highlighting for code snippets
// Both ESCAPE HTML first, then add only the markup we generate.

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function safeUrl(url: string): string {
  return /^(https?:|mailto:)/i.test(url.trim()) ? url.trim() : "#";
}

function inline(text: string): string {
  // `text` is already HTML-escaped. Apply inline Markdown.
  return text
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, t, u) =>
      `<a href="${safeUrl(u)}" target="_blank" rel="noreferrer">${t}</a>`);
}

const isRow = (l: string) => /^\s*\|.*\|\s*$/.test(l);
const isSep = (l: string) => /^\s*\|(?:\s*:?-+:?\s*\|)+\s*$/.test(l);
const cells = (l: string) =>
  l.trim().replace(/^\||\|$/g, "").split("|").map((c) => c.trim());

export function renderMarkdown(md: string): string {
  const src = escapeHtml(md || "").replace(/\r\n/g, "\n");
  const out: string[] = [];
  const lines = src.split("\n");
  let i = 0;
  let list: "ul" | "ol" | null = null;
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };

  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {                       // fenced code block
      closeList();
      const buf: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) { buf.push(lines[i]); i++; }
      i++;
      out.push(`<pre class="md-pre"><code>${buf.join("\n")}</code></pre>`);
      continue;
    }
    if (isRow(line) && i + 1 < lines.length && isSep(lines[i + 1])) {  // GFM table
      closeList();
      const head = cells(line);
      i += 2;
      const body: string[][] = [];
      while (i < lines.length && isRow(lines[i]) && !isSep(lines[i])) { body.push(cells(lines[i])); i++; }
      let tbl = '<table class="md-table"><thead><tr>'
        + head.map((c) => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>";
      for (const r of body) tbl += "<tr>" + r.map((c) => `<td>${inline(c)}</td>`).join("") + "</tr>";
      out.push(tbl + "</tbody></table>");
      continue;
    }
    const h = /^(#{1,4})\s+(.*)$/.exec(line);
    if (h) { closeList(); const lvl = Math.min(6, h[1].length + 2); out.push(`<h${lvl}>${inline(h[2])}</h${lvl}>`); i++; continue; }
    if (/^\s*[-*]\s+/.test(line)) {
      if (list !== "ul") { closeList(); out.push('<ul class="md-ul">'); list = "ul"; }
      out.push(`<li>${inline(line.replace(/^\s*[-*]\s+/, ""))}</li>`);
      i++; continue;
    }
    if (/^\s*\d+\.\s+/.test(line)) {
      if (list !== "ol") { closeList(); out.push('<ol class="md-ol">'); list = "ol"; }
      out.push(`<li>${inline(line.replace(/^\s*\d+\.\s+/, ""))}</li>`);
      i++; continue;
    }
    if (line.trim() === "") { closeList(); i++; continue; }
    closeList();
    out.push(`<p>${inline(line)}</p>`);
    i++;
  }
  closeList();
  return out.join("\n");
}

const KEYWORDS = new Set((
  "def class return if elif else for while in is and or not import from as with try except finally raise " +
  "lambda yield pass break continue global None True False print self " +
  "function const let var new typeof instanceof this null undefined true false export default async await " +
  "public private protected static void int double float char boolean string struct enum interface extends " +
  "implements package switch case do throw throws final abstract super").split(" "));

export function highlightCode(code: string): string {
  const re = /(\/\/[^\n]*|#[^\n]*|\/\*[\s\S]*?\*\/)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(\b\d[\d_.]*\b)|([A-Za-z_]\w*)/g;
  let out = "";
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(code)) !== null) {
    out += escapeHtml(code.slice(last, m.index));
    const [whole, comment, str, num, word] = m;
    if (comment) out += `<span class="hl-com">${escapeHtml(comment)}</span>`;
    else if (str) out += `<span class="hl-str">${escapeHtml(str)}</span>`;
    else if (num) out += `<span class="hl-num">${escapeHtml(num)}</span>`;
    else if (word && KEYWORDS.has(word)) out += `<span class="hl-kw">${escapeHtml(word)}</span>`;
    else out += escapeHtml(whole);
    last = m.index + whole.length;
  }
  out += escapeHtml(code.slice(last));
  return out;
}
