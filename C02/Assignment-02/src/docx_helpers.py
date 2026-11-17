"""python-docx helpers: Times New Roman only; heading 14 pt, sub-heading 12 pt, content 10 pt."""
import re
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT = "Times New Roman"
NAVY, BLUE, GREY = "1F3864", "2E74B5", "595959"
SZ_H, SZ_S, SZ_B = 14, 12, 10


def _fonts(run, size, bold=False, italic=False, color=None):
    run.font.name = FONT
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), FONT)
    run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
    if color: run.font.color.rgb = RGBColor.from_string(color)


def _shade(el_pr, fill):
    shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), fill); el_pr.append(shd)


def _pborder(p, side="bottom", color=BLUE, sz=8, space=1):
    ppr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); e = OxmlElement("w:" + side)
    e.set(qn("w:val"), "single"); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), str(space)); e.set(qn("w:color"), color); b.append(e); ppr.append(b)


def _spacing(p, before=0, after=4, line=1.08):
    pf = p.paragraph_format; pf.space_before = Pt(before); pf.space_after = Pt(after); pf.line_spacing = line


def _outline(p, level):
    ppr = p._p.get_or_add_pPr(); o = OxmlElement("w:outlineLvl"); o.set(qn("w:val"), str(level)); ppr.append(o)


class Doc:
    def __init__(self, doc):
        self.d = doc; self.nt = 0; self.nf = 0

    # ---- text ---------------------------------------------------------------------------------
    def runs(self, p, text, size=SZ_B, color=None, bold=False, italic=False):
        for part in re.split(r"(\*\*.+?\*\*|__.+?__)", text):
            if not part: continue
            if part.startswith("**"): r = p.add_run(part[2:-2]); _fonts(r, size, True, italic, color)
            elif part.startswith("__"): r = p.add_run(part[2:-2]); _fonts(r, size, bold, True, color)
            else: r = p.add_run(part); _fonts(r, size, bold, italic, color)

    def h1(self, text):
        p = self.d.add_paragraph(); _spacing(p, 14, 6, 1.0); p.paragraph_format.keep_with_next = True
        self.runs(p, text, SZ_H, NAVY, bold=True); _pborder(p, "bottom", NAVY, 10, 2); _outline(p, 0); return p

    def h2(self, text):
        p = self.d.add_paragraph(); _spacing(p, 8, 3, 1.0); p.paragraph_format.keep_with_next = True
        self.runs(p, text, SZ_S, BLUE, bold=True); _outline(p, 1); return p

    def p(self, text, align="j", after=4, italic=False, color=None, keep=False):
        p = self.d.add_paragraph(); _spacing(p, 0, after)
        p.alignment = {"j": WD_ALIGN_PARAGRAPH.JUSTIFY, "c": WD_ALIGN_PARAGRAPH.CENTER, "l": WD_ALIGN_PARAGRAPH.LEFT}[align]
        p.paragraph_format.keep_with_next = keep
        self.runs(p, text, SZ_B, color, italic=italic); return p

    def bullets(self, items, indent=0.22):
        for t in items:
            p = self.d.add_paragraph(); _spacing(p, 0, 2)
            p.paragraph_format.left_indent = Inches(indent); p.paragraph_format.first_line_indent = Inches(-0.16)
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            r = p.add_run("\u25AA  "); _fonts(r, SZ_B, True, False, BLUE); self.runs(p, t)

    def eq(self, text, tag=""):
        p = self.d.add_paragraph(); _spacing(p, 2, 3, 1.1); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ppr = p._p.get_or_add_pPr(); _shade(ppr, "EEF3FA"); _pborder(p, "left", BLUE, 18, 6)
        p.paragraph_format.left_indent = Inches(0.3); p.paragraph_format.right_indent = Inches(0.3)
        r = p.add_run(text); _fonts(r, SZ_B, False, True, NAVY)
        if tag: r = p.add_run("      " + tag); _fonts(r, SZ_B, True, False, GREY)
        return p

    def callout(self, title, text, fill="FFF4D6", edge="C55A11"):
        t = self.d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER
        c = t.rows[0].cells[0]; c.width = Inches(6.9)
        tcpr = c._tc.get_or_add_tcPr(); _shade(tcpr, fill)
        b = OxmlElement("w:tcBorders")
        for s in ("top", "bottom", "right"):
            e = OxmlElement("w:" + s); e.set(qn("w:val"), "nil"); b.append(e)
        e = OxmlElement("w:left"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "24"); e.set(qn("w:color"), edge); b.append(e); tcpr.append(b)
        p = c.paragraphs[0]; _spacing(p, 2, 2); self.runs(p, title, SZ_B, edge, bold=True)
        p2 = c.add_paragraph(); _spacing(p2, 0, 2); p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY; self.runs(p2, text)
        sp = self.d.add_paragraph(); _spacing(sp, 0, 2)

    # ---- tables -------------------------------------------------------------------------------
    def table(self, caption, headers, rows, widths, align=None, bold_first=False, hl_rows=()):
        self.nt += 1
        cp = self.d.add_paragraph(); _spacing(cp, 6, 3, 1.0); cp.paragraph_format.keep_with_next = True
        self.runs(cp, "Table %d: %s" % (self.nt, caption), SZ_B, NAVY, bold=True)
        t = self.d.add_table(rows=1 + len(rows), cols=len(headers)); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        tblPr = t._tbl.tblPr; lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        bd = OxmlElement("w:tblBorders")
        for s in ("top", "left", "bottom", "right", "insideH", "insideV"):
            e = OxmlElement("w:" + s); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "9DB7D9"); bd.append(e)
        tblPr.append(bd)
        mar = OxmlElement("w:tblCellMar")
        for s, v in (("top", 30), ("left", 70), ("bottom", 30), ("right", 70)):
            e = OxmlElement("w:" + s); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); mar.append(e)
        tblPr.append(mar)
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths): gc.set(qn("w:w"), str(int(w * 1440)))
        tw = tblPr.find(qn("w:tblW"))
        if tw is None: tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:type"), "dxa"); tw.set(qn("w:w"), str(int(sum(widths) * 1440)))
        align = align or ["l"] * len(headers)
        for ri, row in enumerate([headers] + rows):
            tr = t.rows[ri]
            if ri == 0:
                trpr = tr._tr.get_or_add_trPr(); th = OxmlElement("w:tblHeader"); th.set(qn("w:val"), "true"); trpr.append(th)
            cs = OxmlElement("w:cantSplit"); cs.set(qn("w:val"), "true"); tr._tr.get_or_add_trPr().append(cs)
            for ci, val in enumerate(row):
                c = tr.cells[ci]; c.width = Inches(widths[ci]); tcpr = c._tc.get_or_add_tcPr()
                if ri == 0: _shade(tcpr, NAVY)
                elif (ri - 1) in hl_rows: _shade(tcpr, "E2EFDA")
                elif ri % 2 == 0: _shade(tcpr, "F2F6FC")
                p = c.paragraphs[0]; _spacing(p, 0, 0, 1.0)
                p.alignment = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER, "r": WD_ALIGN_PARAGRAPH.RIGHT}[align[ci] if ri else "c"]
                if ri == 0: self.runs(p, str(val), SZ_B, "FFFFFF", bold=True)
                else: self.runs(p, str(val), SZ_B, None, bold=(bold_first and ci == 0))
        sp = self.d.add_paragraph(); _spacing(sp, 0, 3, 1.0)
        return t

    # ---- figures ------------------------------------------------------------------------------
    def fig(self, path, caption, width=6.2):
        self.nf += 1
        p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; _spacing(p, 4, 2, 1.0); p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(path, width=Inches(width))
        c = self.d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; _spacing(c, 0, 8, 1.0)
        self.runs(c, "Figure %d: %s" % (self.nf, caption), SZ_B, GREY, italic=True)

    def pagebreak(self):
        p = self.d.add_paragraph(); _spacing(p, 0, 0, 1.0); p.add_run().add_break(__import__("docx").enum.text.WD_BREAK.PAGE)
