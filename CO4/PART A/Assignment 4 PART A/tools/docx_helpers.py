"""Helpers for appending styled Times New Roman content (H1=14, H2=12, body=10) to the original Word file."""
import re
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY, TEAL, ORANGE, RED, GREEN, GOLD = "1F3864", "1B7F8C", "E07B39", "C0392B", "2E8B57", "B8860B"
LIGHT, ZEBRA, CALL = "EEF2F7", "F7F9FC", "FFF4E5"
FONT = "Times New Roman"
TOTAL_W = 9026  # twips (A4 with 1 inch margins)

def _fonts(rpr, name=FONT):
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"): rf.set(qn(a), name)

def make_styles(doc):
    st = doc.styles
    def mk(name, size, bold=False, color=None, italic=False):
        s = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH); s.base_style = None
        s.font.name = FONT; s.font.size = Pt(size); s.font.bold = bold; s.font.italic = italic
        if color: s.font.color.rgb = RGBColor.from_string(color)
        _fonts(s.element.get_or_add_rPr())
        return s
    h1 = mk("ANS Heading", 14, True, "FFFFFF"); h2 = mk("ANS Subheading", 12, True, NAVY); b = mk("ANS Body", 10)
    for s, lvl in ((h1, 0), (h2, 1)):
        ppr = s.element.get_or_add_pPr(); o = OxmlElement("w:outlineLvl"); o.set(qn("w:val"), str(lvl)); ppr.append(o)
    h1.paragraph_format.space_before = Pt(0); h1.paragraph_format.space_after = Pt(8); h1.paragraph_format.keep_with_next = True
    h2.paragraph_format.space_before = Pt(12); h2.paragraph_format.space_after = Pt(4); h2.paragraph_format.keep_with_next = True
    b.paragraph_format.space_after = Pt(4); b.paragraph_format.space_before = Pt(0); b.paragraph_format.line_spacing = 1.1
    # shading on H1 paragraphs
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), NAVY)
    h1.element.get_or_add_pPr().append(shd)
    # bottom border on H2
    pb = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "8"), ("space", "1"), ("color", TEAL)): bt.set(qn("w:" + k), v)
    pb.append(bt); h2.element.get_or_add_pPr().append(pb)

def runs(p, text, size=10, color=None, bold=False, italic=False):
    """Supports **bold** and _italic_ inline markers."""
    for part in re.split(r"(\*\*.+?\*\*|__.+?__)", text):
        if not part: continue
        b, i, t = bold, italic, part
        if part.startswith("**") and part.endswith("**"): b, t = True, part[2:-2]
        elif part.startswith("__") and part.endswith("__"): i, t = True, part[2:-2]
        r = p.add_run(t); r.font.name = FONT; r.font.size = Pt(size); r.bold = b; r.italic = i
        _fonts(r._r.get_or_add_rPr())
        if color: r.font.color.rgb = RGBColor.from_string(color)
    return p

class Builder:
    def __init__(self, doc):
        self.d = doc; self.fig = 0; make_styles(doc)

    # ---- text ----
    def h1(self, text, page_break=True):
        p = self.d.add_paragraph(style="ANS Heading"); p.paragraph_format.page_break_before = page_break
        runs(p, " " + text, 14, "FFFFFF", True); return p
    def h2(self, text):
        p = self.d.add_paragraph(style="ANS Subheading"); runs(p, text, 12, NAVY, True); return p
    def p(self, text, align=None, italic=False, keep=False, size=10, color=None):
        p = self.d.add_paragraph(style="ANS Body"); runs(p, text, size, color, False, italic)
        if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if align == "j": p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if keep: p.paragraph_format.keep_with_next = True
        return p
    def bullets(self, items, mark="•"):
        for t in items:
            p = self.d.add_paragraph(style="ANS Body"); pf = p.paragraph_format
            pf.left_indent = Inches(0.3); pf.first_line_indent = Inches(-0.2); pf.space_after = Pt(2)
            runs(p, f"{mark}\u00A0\u00A0" + t)
    def spacer(self, pts=4):
        p = self.d.add_paragraph(style="ANS Body"); p.paragraph_format.space_after = Pt(pts)
        for r in p.runs: r.font.size = Pt(2)
        return p

    # ---- tables ----
    def _tbl(self, rows, cols, widths):
        t = self.d.add_table(rows=rows, cols=cols); t.autofit = False
        tp = t._tbl.tblPr
        for tag in ("w:tblW", "w:tblLayout"):
            e = tp.find(qn(tag))
            if e is not None: tp.remove(e)
        w = OxmlElement("w:tblW"); w.set(qn("w:w"), str(sum(widths))); w.set(qn("w:type"), "dxa"); tp.append(w)
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tp.append(lay)
        bd = OxmlElement("w:tblBorders")
        for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement("w:" + side)
            for k, v in (("val", "single"), ("sz", "4"), ("space", "0"), ("color", "B7C3D6")): e.set(qn("w:" + k), v)
            bd.append(e)
        tp.append(bd)
        cm = OxmlElement("w:tblCellMar")
        for side, v in (("top", 40), ("left", 90), ("bottom", 40), ("right", 90)):
            e = OxmlElement("w:" + side); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); cm.append(e)
        tp.append(cm)
        grid = t._tbl.tblGrid
        for gc, wd in zip(grid.findall(qn("w:gridCol")), widths): gc.set(qn("w:w"), str(wd))
        for row in t.rows:
            trpr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trpr.append(cs)
            for c, wd in zip(row.cells, widths):
                tcw = c._tc.get_or_add_tcPr().find(qn("w:tcW"))
                if tcw is None:
                    tcw = OxmlElement("w:tcW"); c._tc.get_or_add_tcPr().append(tcw)
                tcw.set(qn("w:w"), str(wd)); tcw.set(qn("w:type"), "dxa")
        return t

    def _fill(self, cell, fill):
        tcpr = cell._tc.get_or_add_tcPr(); s = tcpr.find(qn("w:shd"))
        if s is None: s = OxmlElement("w:shd"); tcpr.append(s)
        s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill)

    def _cell(self, cell, text, bold=False, color=None, fill=None, align=None, size=10, keep=False, italic=False):
        if fill: self._fill(cell, fill)
        lines = text.split("\n") if isinstance(text, str) else text
        for i, line in enumerate(lines):
            p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
            p.style = self.d.styles["ANS Body"]; p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
            if align == "c": p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if keep: p.paragraph_format.keep_with_next = True
            runs(p, line, size, color, bold, italic)

    def grid(self, header, rows, widths, center=(), bold_first=False, zebra=True, head_fill=NAVY, keep=True, total_row=False):
        t = self._tbl(len(rows) + 1, len(header), widths)
        for j, h in enumerate(header):
            self._cell(t.rows[0].cells[j], h, True, "FFFFFF", head_fill, "c", keep=keep)
        th = OxmlElement("w:tblHeader"); t.rows[0]._tr.get_or_add_trPr().append(th)
        for i, r in enumerate(rows, 1):
            last = i == len(rows)
            for j, v in enumerate(r):
                fill = (ZEBRA if i % 2 == 0 else None) if zebra else None
                bold = (bold_first and j == 0) or (total_row and last)
                if total_row and last: fill = LIGHT
                self._cell(t.rows[i].cells[j], str(v), bold, None, fill, "c" if j in center else None, keep=keep and not last)
        self.spacer(4); return t

    def kv(self, rows, widths=(2300, 6726), head=None, head_fill=NAVY, key_fill=LIGHT):
        n = len(rows) + (1 if head else 0)
        t = self._tbl(n, 2, list(widths)); i0 = 0
        if head:
            m = t.rows[0].cells[0].merge(t.rows[0].cells[1]); self._cell(m, head, True, "FFFFFF", head_fill, keep=True); i0 = 1
        for i, (k, v) in enumerate(rows):
            last = i == len(rows) - 1
            self._cell(t.rows[i0 + i].cells[0], k, True, NAVY, key_fill, keep=not last)
            self._cell(t.rows[i0 + i].cells[1], v, keep=not last)
        self.spacer(4); return t

    def spec(self, no, name, fields, order, color=NAVY):
        rows = [(f, fields[f]) for f in order]
        return self.kv(rows, (1300, 7726), head=f"STAGE {no}  —  {name}", head_fill=color, key_fill=LIGHT)

    def callout(self, text, fill=CALL, edge=ORANGE, title=None):
        t = self._tbl(1, 1, [TOTAL_W]); c = t.rows[0].cells[0]; self._fill(c, fill)
        tcpr = c._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
        e = OxmlElement("w:left")
        for k, v in (("val", "single"), ("sz", "36"), ("space", "0"), ("color", edge)): e.set(qn("w:" + k), v)
        b.append(e); tcpr.append(b)
        lines = ([f"**{title}**"] if title else []) + text.split("\n")
        self._cell(c, "\n".join(lines)); self.spacer(4)

    def figure(self, path, caption, width=6.2):
        self.fig += 1
        p = self.d.add_paragraph(style="ANS Body"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Inches(width))
        c = self.d.add_paragraph(style="ANS Body"); c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        runs(c, f"Figure {self.fig}: {caption}", 10, NAVY, True, True)
