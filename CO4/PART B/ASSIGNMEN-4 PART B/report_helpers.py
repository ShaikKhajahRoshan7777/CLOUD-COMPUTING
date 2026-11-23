"""python-docx helpers: every run is Times New Roman; heading 14 pt, sub-heading 12 pt, body 10 pt."""
import re
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FONT, NAVY, ORANGE = "Times New Roman", "1F4E79", "C55A11"
PAGE_W_IN = 6.27


def fmt(run, size=10, bold=False, italic=False, color=None):
    run.font.name = FONT; run.font.size = Pt(size); run.font.bold = bold; run.font.italic = italic
    rpr = run._element.get_or_add_rPr(); rf = rpr.find(qn("w:rFonts"))
    if rf is None: rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"): rf.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
    if color: run.font.color.rgb = RGBColor.from_string(color)


def spacing(p, before=0, after=4, line=1.08, keep_next=False, left=None, first=None):
    pf = p.paragraph_format; pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line
    pf.keep_with_next = keep_next
    if left is not None: pf.left_indent = Inches(left)
    if first is not None: pf.first_line_indent = Inches(first)


def runs(p, text, size=10, color=None, italic=False, bold=False):
    """Mini-markup: **bold** segments."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part: fmt(p.add_run(part), size, bold or i % 2 == 1, italic, color)


def border_bottom(p, color=NAVY, sz=8):
    ppr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); e = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", str(sz)), ("w:space", "1"), ("w:color", color)): e.set(qn(k), v)
    b.append(e); ppr.append(b)


def shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), fill); tcpr.append(sh)


def borders(table, color="9DB2C8", sz=4):
    tblpr = table._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        for k, v in (("w:val", "single"), ("w:sz", str(sz)), ("w:space", "0"), ("w:color", color)): e.set(qn(k), v)
        b.append(e)
    tblpr.append(b)


def fix_widths(t, widths_in):
    """Real fixed layout: tblW, tblLayout and gridCol widths (python-docx cell widths alone are ignored by Word/LibreOffice)."""
    tbl = t._tbl; tblPr = tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout"):
        for e in tblPr.findall(qn(tag)): tblPr.remove(e)
    w = OxmlElement("w:tblW"); w.set(qn("w:w"), str(int(sum(widths_in) * 1440))); w.set(qn("w:type"), "dxa"); tblPr.append(w)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
    grid = tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn("w:gridCol"))): gc.set(qn("w:w"), str(int(widths_in[i] * 1440)))
    for row in t.rows:
        for i, c in enumerate(row.cells): c.width = Inches(widths_in[i])


class Report:
    def __init__(self, doc):
        self.d, self.fig, self.tab = doc, 0, 0

    def h1(self, text):
        p = self.d.add_paragraph(style="Heading 1"); runs(p, text, 14, NAVY, bold=True); spacing(p, 10, 6, keep_next=True); border_bottom(p)
        if self._pb: p.paragraph_format.page_break_before = True; self._pb = False
        return p

    def h2(self, text):
        p = self.d.add_paragraph(style="Heading 2"); runs(p, text, 12, ORANGE, bold=True); spacing(p, 8, 3, keep_next=True); return p

    def p(self, text, after=4, italic=False, align=None, color=None):
        p = self.d.add_paragraph(); runs(p, text, 10, color, italic); spacing(p, 0, after)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY if align is None else align; return p

    def bullets(self, items):
        for t in items:
            p = self.d.add_paragraph(); runs(p, "\u2022  " + t, 10); spacing(p, 0, 2, left=0.28, first=-0.18); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    _pb = False

    def page_break(self):
        """Deferred: the NEXT heading/banner starts on a new page (no empty paragraph that could create a blank page)."""
        self._pb = True

    def table(self, rows, widths, caption=None, header=True, align_right_from=None, bold_first_col=False):
        if caption:
            self.tab += 1; p = self.d.add_paragraph(); runs(p, "Table %d: %s" % (self.tab, caption), 10, NAVY, bold=True); spacing(p, 4, 2, keep_next=True)
        t = self.d.add_table(rows=len(rows), cols=len(rows[0])); t.alignment = WD_TABLE_ALIGNMENT.CENTER; borders(t); t.autofit = False
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                c = t.cell(i, j); c.width = Inches(widths[j]); c.text = ""; p = c.paragraphs[0]; spacing(p, 1, 1, 1.0)
                hdr = header and i == 0
                runs(p, str(val), 10, "FFFFFF" if hdr else None, bold=hdr or (bold_first_col and j == 0))
                if hdr: shade(c, NAVY)
                elif i % 2 == 0: shade(c, "EEF3F9")
                if align_right_from is not None and j >= align_right_from and not hdr: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        fix_widths(t, widths)
        sp = self.d.add_paragraph(); spacing(sp, 0, 4); return t

    def callout(self, title, text, fill="E8F0FA", edge=NAVY):
        t = self.d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        c = t.cell(0, 0); c.width = Inches(PAGE_W_IN); shade(c, fill)
        tcpr = c._tc.get_or_add_tcPr(); b = OxmlElement("w:tcBorders")
        for edge_name, sz, col in (("left", 36, edge), ("top", 4, "C9D6E5"), ("bottom", 4, "C9D6E5"), ("right", 4, "C9D6E5")):
            e = OxmlElement("w:" + edge_name)
            for k, v in (("w:val", "single"), ("w:sz", str(sz)), ("w:space", "0"), ("w:color", col)): e.set(qn(k), v)
            b.append(e)
        tcpr.append(b); p = c.paragraphs[0]; spacing(p, 2, 2); runs(p, title + "  ", 10, edge, bold=True); runs(p, text, 10)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        fix_widths(t, [PAGE_W_IN])
        sp = self.d.add_paragraph(); spacing(sp, 0, 4)

    def image(self, path, caption, width=PAGE_W_IN):
        self.fig += 1; p = self.d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; spacing(p, 2, 2, keep_next=True)
        p.add_run().add_picture(path, width=Inches(width))
        c = self.d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; runs(c, "Figure %d: %s" % (self.fig, caption), 10, NAVY, italic=True); spacing(c, 0, 8)

    def banner(self, lines):
        if self._pb:                                   # 1-pt paragraph that carries the page break before the banner table
            q = self.d.add_paragraph(); q.paragraph_format.page_break_before = True; spacing(q, 0, 0, 1.0); self._pb = False
            r = q.add_run(" "); fmt(r, 1)
            rpr = q._p.get_or_add_pPr(); m = OxmlElement("w:rPr"); sz = OxmlElement("w:sz"); sz.set(qn("w:val"), "2"); m.append(sz); rpr.append(m)
        t = self.d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        c = t.cell(0, 0); c.width = Inches(PAGE_W_IN); shade(c, NAVY); c.text = ""
        for i, (txt, size, col) in enumerate(lines):
            p = c.paragraphs[0] if i == 0 else c.add_paragraph(); spacing(p, 5 if i == 0 else 1, 3); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; runs(p, txt, size, col, bold=size >= 12)
        fix_widths(t, [PAGE_W_IN])
        sp = self.d.add_paragraph(); spacing(sp, 0, 6)
