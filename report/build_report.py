"""Build the submission PDF from the official Apart template.

python report/build_report.py   (after `python -m swarm_evidence analyze`)

Keeps the template's title block, author table, abstract box, styles and event footnote;
removes all guidance text; writes content from report/content.py; converts to PDF with
LibreOffice; records every result number used in report/numbers_used.json.
"""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "report"))

TEMPLATE = ROOT / "report/template/official-report-template.docx"
OUT_DOCX = ROOT / "report/swarm_evidence_report.docx"
OUT_PDF = ROOT / "report/swarm_evidence_report.pdf"
SOFFICE = "/Applications/LibreOffice.app/Contents/MacOS/soffice"


class Numbers:
    """Fetch values from results/analysis/summary.json by dotted path and remember them for the audit."""

    def __init__(self, summary):
        self.s = summary
        self.used = {}
        self.missing = []

    def get(self, path):
        cur = self.s
        try:
            for part in path.split("/"):
                cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        except (KeyError, IndexError, TypeError):
            if os.environ.get("REPORT_DRAFT"):
                self.missing.append(path)
                return float("nan")
            raise
        self.used[path] = round(cur, 3) if isinstance(cur, float) else cur
        return cur

    def has(self, path):
        """True if the path resolves to a value (used to drop sentences about stages that did not finish)."""
        cur = self.s
        try:
            for part in path.split("/"):
                cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        except (KeyError, IndexError, TypeError, ValueError):
            return False
        return not (isinstance(cur, dict) and cur.get("incomplete"))

    def f(self, path, nd=2):
        v = self.get(path)
        return "n/a" if v is None else f"{v:.{nd}f}"

    def i(self, path):
        return str(self.get(path))

    def pct(self, path, nd=0):
        v = self.get(path)
        return f"{100 * v:.{nd}f}%"


INLINE = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")


def add_runs(par, text, size=None, italic=None, color=None):
    for tok in INLINE.split(text):
        if not tok:
            continue
        if tok.startswith("**"):
            r = par.add_run(tok[2:-2])
            r.bold = True
        elif tok.startswith("*"):
            r = par.add_run(tok[1:-1])
            r.italic = True
        elif tok.startswith("`"):
            r = par.add_run(tok[1:-1])
            r.font.name = "Courier New"
            r.font.size = Pt(8.5)
        else:
            r = par.add_run(tok)
        if size:
            r.font.size = Pt(size)
        if italic is not None and not tok.startswith("*"):
            r.italic = italic
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def _set_cell_text(cell, lines, bold_first=False, size=None):
    p = cell.paragraphs[0]
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    for k, line in enumerate(lines):
        r = p.add_run(line)
        if bold_first and k == 0:
            r.bold = True
        if size:
            r.font.size = Pt(size)
        if k < len(lines) - 1:
            r.add_break()


def fill_front_matter(doc, title, authors, abstract):
    t0 = doc.tables[0]
    # title (keep footnote reference runs)
    for p in t0.rows[0].cells[0].paragraphs:
        if p.text.strip() == "PROJECT TITLE":
            p.runs[0].text = title
    # author table: nested inside row 1
    cell = t0.rows[1].cells[0]
    cands = [nt for nt in cell._element.iter(qn("w:tbl")) if "Author name 1" in "".join(nt.itertext())]
    author_tbl = cands[-1]  # innermost table holding the author grid
    rows = author_tbl.findall(qn("w:tr"))
    n = len(authors)
    per_row = min(3, n)
    width = 4600 if n == 1 else 3000
    grid = author_tbl.find(qn("w:tblGrid"))
    for g in list(grid):
        grid.remove(g)
    for _ in range(per_row):
        gc = grid.makeelement(qn("w:gridCol"), {qn("w:w"): str(width)})
        grid.append(gc)
    tblw = author_tbl.find(qn("w:tblPr")).find(qn("w:tblW"))
    tblw.set(qn("w:w"), str(width * per_row))
    # reuse first row's first cell as prototype
    proto = copy.deepcopy(rows[0].findall(qn("w:tc"))[0])
    for r in rows:
        author_tbl.remove(r)
    n_rows = (n + per_row - 1) // per_row
    for ri in range(n_rows):
        tr = copy.deepcopy(rows[0])
        for tc in tr.findall(qn("w:tc")):
            tr.remove(tc)
        for ci in range(per_row):
            k = ri * per_row + ci
            tc = copy.deepcopy(proto)
            tcpr = tc.find(qn("w:tcPr"))
            tcw = tcpr.find(qn("w:tcW"))
            if tcw is None:
                tcw = tcpr.makeelement(qn("w:tcW"), {})
                tcpr.insert(0, tcw)
            tcw.set(qn("w:w"), str(width))
            tcw.set(qn("w:type"), "dxa")
            ts = list(tc.iter(qn("w:t")))
            name, aff = (authors[k] if k < n else ("", ""))
            ts[0].text = name
            ts[1].text = aff
            tr.append(tc)
        author_tbl.append(tr)
    # abstract: the 1x1 nested table holding the guidance
    for nt in cell.tables:
        if "Summarize your project" in nt.rows[0].cells[0].text:
            c = nt.rows[0].cells[0]
            p = c.paragraphs[0]
            for r in list(p.runs):
                r._element.getparent().remove(r._element)
            add_runs(p, abstract, italic=False)
            for extra in c.paragraphs[1:]:
                extra._element.getparent().remove(extra._element)


def clear_body_after_front_matter(doc):
    body = doc.element.body
    tables = body.findall(qn("w:tbl"))
    info_box = tables[1]
    started = False
    for child in list(body):
        if child is info_box:
            started = True
        if started and child.tag != qn("w:sectPr"):
            body.remove(child)


def add_heading(doc, text, level):
    p = doc.add_paragraph(style="Heading 2" if level == 2 else "Heading 3")
    r = p.add_run(text)
    r.bold = True
    return p


def add_par(doc, text, size=None, align=None, space_after=None, italic=None):
    p = doc.add_paragraph(style="normal")
    add_runs(p, text, size=size, italic=italic)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if space_after is not None:
        p.paragraph_format.space_after = Pt(space_after)
    return p


def add_bullets(doc, items, numbered=False, size=None):
    for k, it in enumerate(items):
        p = doc.add_paragraph(style="normal")
        p.paragraph_format.left_indent = Inches(0.25)
        p.paragraph_format.first_line_indent = Inches(-0.18)
        p.paragraph_format.space_after = Pt(2)
        add_runs(p, (f"{k + 1}. " if numbered else "• ") + it, size=size)


def add_figure(doc, path, width_in, caption):
    p = doc.add_paragraph(style="normal")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width_in))
    c = add_par(doc, caption, size=8.5, space_after=6)
    return c


def add_table(doc, header, rows, caption, col_widths=None, size=7.5):
    cap = add_par(doc, caption, size=8.5, space_after=2)
    cap.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1 + len(rows), cols=len(header))
    t.style = doc.styles["Table Grid"] if "Table Grid" in [s.name for s in doc.styles] else None
    t.alignment = 1
    for j, h in enumerate(header):
        _set_cell_text(t.rows[0].cells[j], [h], bold_first=True, size=size)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            _set_cell_text(t.rows[i + 1].cells[j], [str(v)], size=size)
    _borders(t)
    if col_widths:
        t.autofit = False
        grid = t._element.find(qn("w:tblGrid"))
        for j, gc in enumerate(grid.findall(qn("w:gridCol"))):
            gc.set(qn("w:w"), str(int(col_widths[j] * 1440)))
        tblPr = t._element.find(qn("w:tblPr"))
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = tblPr.makeelement(qn("w:tblW"), {})
            tblPr.append(tblW)
        tblW.set(qn("w:w"), str(int(sum(col_widths) * 1440)))
        tblW.set(qn("w:type"), "dxa")
        layout = tblPr.makeelement(qn("w:tblLayout"), {qn("w:type"): "fixed"})
        tblPr.append(layout)
        for row in t.rows:
            for j, w in enumerate(col_widths):
                row.cells[j].width = Inches(w)
    n_rows = len(t.rows)
    for ri, row in enumerate(t.rows):
        trPr = row._tr.get_or_add_trPr()
        trPr.append(trPr.makeelement(qn("w:cantSplit"), {}))
        for c in row.cells:
            for p in c.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                if os.environ.get("REPORT_TABLE_KEEP", "all") == "all":
                    p.paragraph_format.keep_with_next = ri < n_rows - 1
                else:  # keep only caption, header and first body row together; rows never split
                    p.paragraph_format.keep_with_next = ri < 1
    spacer = doc.add_paragraph(style="normal")
    spacer.paragraph_format.space_after = Pt(2)
    return t


def _borders(table):
    tbl = table._element
    tblPr = tbl.find(qn("w:tblPr"))
    borders = tblPr.makeelement(qn("w:tblBorders"), {})
    for edge in ("top", "bottom", "insideH"):
        e = borders.makeelement(qn(f"w:{edge}"), {qn("w:val"): "single", qn("w:sz"): "4", qn("w:space"): "0",
                                                  qn("w:color"): "888888"})
        borders.append(e)
    for edge in ("left", "right", "insideV"):
        e = borders.makeelement(qn(f"w:{edge}"), {qn("w:val"): "nil"})
        borders.append(e)
    tblPr.append(borders)


def render(blocks, doc):
    for b in blocks:
        kind = b[0]
        if kind == "h2":
            add_heading(doc, b[1], 2)
        elif kind == "h3":
            add_heading(doc, b[1], 3)
        elif kind == "p":
            add_par(doc, b[1], **(b[2] if len(b) > 2 else {}))
        elif kind == "bullets":
            add_bullets(doc, b[1], **(b[2] if len(b) > 2 else {}))
        elif kind == "fig":
            add_figure(doc, ROOT / b[1], b[2], b[3])
        elif kind == "table":
            add_table(doc, b[1], b[2], b[3], **(b[4] if len(b) > 4 else {}))
        elif kind == "pagebreak":
            doc.add_page_break()
        else:
            raise ValueError(kind)


def main():
    import content  # report/content.py

    summary = json.loads((ROOT / "results/analysis/summary.json").read_text())
    N = Numbers(summary)
    doc = Document(str(TEMPLATE))
    meta = content.front_matter(N)
    fill_front_matter(doc, meta["title"], meta["authors"], meta["abstract"])
    clear_body_after_front_matter(doc)
    render(content.body(N), doc)
    if not os.environ.get("REPORT_DRAFT"):  # a final build must not ship placeholders or missing values
        text = " ".join(doc.element.body.itertext())  # includes nested tables (author block, abstract box)
        bad = sorted({m for m in re.findall(r"TO CONFIRM|\[AUTHOR[^\]]*\]|\bnan\b|PENDING|\{[A-Za-z_][^{}]*\}", text)})
        if bad:
            raise SystemExit(f"refusing final build, placeholders or missing values remain: {bad}")
    doc.save(str(OUT_DOCX))
    (ROOT / "report/numbers_used.json").write_text(json.dumps(N.used, indent=1, sort_keys=True) + "\n")
    words = len(re.findall(r"\S+", re.sub(r"[*`]", "", meta["abstract"])))
    subprocess.run([SOFFICE, "--headless", "--convert-to", "pdf", "--outdir", str(OUT_PDF.parent), str(OUT_DOCX)],
                   check=True, capture_output=True)
    import pymupdf
    d = pymupdf.open(str(OUT_PDF))
    ref_page = next((i + 1 for i in range(len(d)) if re.search(r"^\s*References\s*$", d[i].get_text(), re.M)), None)
    if N.missing:
        print("DRAFT: missing numbers:", len(N.missing), sorted(set(p.split("/")[0] + "/" + p.split("/")[1] if "/" in p else p for p in N.missing))[:12])
    print(json.dumps({"pdf": str(OUT_PDF.relative_to(ROOT)), "pages": len(d), "references_heading_page": ref_page,
                      "abstract_words": words, "numbers_used": len(N.used),
                      "pdf_mb": round(OUT_PDF.stat().st_size / 1e6, 2)}))


if __name__ == "__main__":
    main()
