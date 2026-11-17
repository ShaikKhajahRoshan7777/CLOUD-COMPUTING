"""Formatting helpers: Times New Roman only; heading 14 pt, sub-heading 12 pt, content 10 pt."""
import copy

from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

FONT = "Times New Roman"
H_SIZE, S_SIZE, B_SIZE = 14, 12, 10
NAVY, TEAL, GREY = "1F3A5F", "0E8A8A", "F2F5F9"
BULLET_NUM_ID = None
fig_counter = [0]
tab_counter = [0]


def set_font(run, size=B_SIZE, bold=None, italic=None, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rfonts.set(qn(a), FONT)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def _spacing(p, before=0, after=4, line=1.08):
    pf = p.paragraph_format
    pf.space_before, pf.space_after, pf.line_spacing = Pt(before), Pt(after), line


def setup_numbering(doc):
    """Create real bullet / decimal lists (no literal bullet characters)."""
    global BULLET_NUM_ID
    numbering = doc.part.numbering_part.element
    absid = 90
    xml = (f'<w:abstractNum {nsdecls("w")} w:abstractNumId="{absid}"><w:multiLevelType w:val="hybridMultilevel"/>'
           f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/>'
           f'<w:pPr><w:ind w:left="360" w:hanging="260"/></w:pPr><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/></w:rPr></w:lvl>'
           f'<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8211;"/><w:lvlJc w:val="left"/>'
           f'<w:pPr><w:ind w:left="720" w:hanging="260"/></w:pPr><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/></w:rPr></w:lvl></w:abstractNum>')
    first_num = numbering.find(qn("w:num"))
    el = parse_xml(xml)
    if first_num is not None:
        first_num.addprevious(el)
    else:
        numbering.append(el)
    num = parse_xml(f'<w:num {nsdecls("w")} w:numId="90"><w:abstractNumId w:val="{absid}"/></w:num>')
    numbering.append(num)
    BULLET_NUM_ID = 90


def heading(doc, text, page_break=False):
    p = doc.add_paragraph()
    if page_break:
        p.paragraph_format.page_break_before = True
    _spacing(p, 6, 6)
    p.paragraph_format.keep_with_next = True
    ppr = p._p.get_or_add_pPr()
    ol = OxmlElement("w:outlineLvl")
    ol.set(qn("w:val"), "0")
    ppr.append(ol)
    r = p.add_run(text)
    set_font(r, H_SIZE, True, color=NAVY)
    bdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="2" w:color="{TEAL}"/></w:pBdr>')
    ppr.append(bdr)
    return p


def sub(doc, text, color=TEAL):
    p = doc.add_paragraph()
    _spacing(p, 8, 3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    set_font(r, S_SIZE, True, color=color)
    return p


def para(doc, text="", bold_lead=None, align="justify", italic=False, after=4, keep=False):
    p = doc.add_paragraph()
    _spacing(p, 0, after)
    if align == "justify":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if keep:
        p.paragraph_format.keep_with_next = True
    if bold_lead:
        set_font(p.add_run(bold_lead + " "), B_SIZE, True)
    set_font(p.add_run(text), B_SIZE, italic=italic)
    return p


def bullets(doc, items, level=0):
    for it in items:
        p = doc.add_paragraph()
        _spacing(p, 0, 2)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        ppr = p._p.get_or_add_pPr()
        ppr.append(parse_xml(f'<w:numPr {nsdecls("w")}><w:ilvl w:val="{level}"/><w:numId w:val="{BULLET_NUM_ID}"/></w:numPr>'))
        if isinstance(it, tuple):
            set_font(p.add_run(it[0] + " "), B_SIZE, True)
            set_font(p.add_run(it[1]), B_SIZE)
        else:
            set_font(p.add_run(it), B_SIZE)


def _shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    for old in tcpr.findall(qn("w:shd")):
        tcpr.remove(old)
    tcpr.append(parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{fill}"/>'))


def _borders(table, color="B8C4D2", sz=4, style="single"):
    tblpr = table._tbl.tblPr
    for old in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(old)
    xml = f'<w:tblBorders {nsdecls("w")}>' + "".join(
        f'<w:{e} w:val="{style}" w:sz="{sz}" w:space="0" w:color="{color}"/>' for e in ("top", "left", "bottom", "right", "insideH", "insideV")) + "</w:tblBorders>"
    tblpr.append(parse_xml(xml))


def _cell_text(cell, text, bold=False, color=None, align=None, size=B_SIZE, italic=False):
    cell.text = ""
    parts = text.split("\n")
    for i, part in enumerate(parts):
        p = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
        _spacing(p, 1, 1, 1.0)
        if align == "center":
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_font(p.add_run(part), size, bold, italic, color)


def _fix_layout(table, widths):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tblpr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    tblpr.append(parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="40" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
                           f'<w:bottom w:w="40" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar>'))
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w * 1440)))
    for row in table.rows:
        for c, w in zip(row.cells, widths):
            c.width = Inches(w)


def table(doc, rows, widths, caption=None, header_fill=NAVY, first_col_bold=False, zebra=True, align_center_cols=()):
    if caption:
        tab_counter[0] += 1
        p = doc.add_paragraph()
        _spacing(p, 4, 2)
        p.paragraph_format.keep_with_next = True
        set_font(p.add_run(f"Table {tab_counter[0]}: {caption}"), B_SIZE, True, True, NAVY)
    t = doc.add_table(rows=len(rows), cols=len(widths))
    _borders(t)
    _fix_layout(t, widths)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            if i == 0:
                _shade(c, header_fill)
                _cell_text(c, val, True, "FFFFFF", "center" if j in align_center_cols else None)
            else:
                if zebra and i % 2 == 0:
                    _shade(c, GREY)
                _cell_text(c, val, bold=(first_col_bold and j == 0), align="center" if j in align_center_cols else None)
    trpr = t.rows[0]._tr.get_or_add_trPr()
    trpr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for r in t.rows:
        r._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
    if len(rows) <= 12:                      # keep short tables on one page
        for r in t.rows[:-1]:
            for c in r.cells:
                for pp in c.paragraphs:
                    pp.paragraph_format.keep_with_next = True
    spacer(doc)
    return t


def spacer(doc, pts=4):
    from docx.enum.text import WD_LINE_SPACING
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(pts + 2)
    set_font(p.add_run(" "), B_SIZE)
    return p


def callout(doc, title, text, fill="E8F4F4", bar=TEAL):
    t = doc.add_table(rows=1, cols=1)
    _fix_layout(t, [6.9])
    c = t.cell(0, 0)
    _shade(c, fill)
    tcpr = c._tc.get_or_add_tcPr()
    tcpr.append(parse_xml(f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="36" w:space="0" w:color="{bar}"/>'
                          f'<w:top w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/></w:tcBorders>'))
    c.text = ""
    p = c.paragraphs[0]
    _spacing(p, 2, 2)
    set_font(p.add_run(title), B_SIZE, True, color=bar)
    p2 = c.add_paragraph()
    _spacing(p2, 0, 2)
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    set_font(p2.add_run(text), B_SIZE)
    spacer(doc)


def figure(doc, path, caption, width=6.5):
    fig_counter[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 4, 2)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(cp, 0, 6)
    set_font(cp.add_run(f"Figure {fig_counter[0]}: {caption}"), B_SIZE, True, True, NAVY)


def evidence_slot(doc, label, height=0.85):
    fig_counter[0] += 1
    t = doc.add_table(rows=1, cols=1)
    _borders(t, "7F8FA6", 8, "dashed")
    _fix_layout(t, [6.5])
    c = t.cell(0, 0)
    _shade(c, "FAFBFD")
    t.rows[0].height = Inches(height)
    c.text = ""
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 8, 2)
    set_font(p.add_run(f"[ INSERT YOUR OWN SCREENSHOT ]"), B_SIZE, True, color="7F8FA6")
    p2 = c.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_font(p2.add_run(label), B_SIZE, italic=True, color="555555")
    cp = doc.add_paragraph()
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(cp, 2, 6)
    set_font(cp.add_run(f"Figure {fig_counter[0]}: {label}"), B_SIZE, True, True, NAVY)


def banner(doc, text, fill=NAVY, size=H_SIZE):
    t = doc.add_table(rows=1, cols=1)
    _fix_layout(t, [6.9])
    c = t.cell(0, 0)
    _shade(c, fill)
    c.text = ""
    p = c.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _spacing(p, 6, 6)
    set_font(p.add_run(text), size, True, color="FFFFFF")
    return t


def add_field(run, instr):
    for kind, txt in (("begin", None), (None, instr), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        run._r.append(el)
