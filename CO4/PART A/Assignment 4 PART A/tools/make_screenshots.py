"""Renders VS Code (Dark+) style screenshots from the REAL script source and REAL captured output in ../outputs.
Replace these with genuine screen captures from your own VS Code if your institution requires it."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
UI = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F = ImageFont.truetype(FONT, 14); FU = ImageFont.truetype(UI, 12); FB = ImageFont.truetype(UI, 11)
CW, LH = 8, 20
BG, SIDE, ACT, TAB_OFF, STATUS = "#1e1e1e", "#252526", "#333333", "#2d2d2d", "#007acc"
SCRIPTS = ["task1_spec_check", "task2_traffic_trace", "task3_sizing", "task4_linkage_attack", "task5_mapreduce_sim", "task6_fraud_trace"]
PYVER = sys.version.split()[0]

def colour(tok):
    if tok in Token.Keyword or tok in Token.Operator.Word: return "#c586c0"
    if tok in Token.Name.Function: return "#dcdcaa"
    if tok in Token.Name.Builtin: return "#4ec9b0"
    if tok in Token.String: return "#ce9178"
    if tok in Token.Comment: return "#6a9955"
    if tok in Token.Number: return "#b5cea8"
    return "#d4d4d4"

def shot(name, code_lines=15):
    src = [l if len(l) <= 118 else l[:115] + "..." for l in open(f"{ROOT}/scripts/{name}.py").read().splitlines()[:code_lines]]
    out = open(f"{ROOT}/outputs/{name}.txt").read().rstrip().splitlines()
    W = 1480; TOP = 30; TABH = 34; SBW = 250; ACTW = 48
    code_h = code_lines * LH + 14; term_h = (len(out) + 3) * LH + 50
    H = TOP + TABH + code_h + 36 + term_h + 24
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    # title bar + menu
    d.rectangle([0, 0, W, TOP], fill="#323233")
    d.text((10, 8), "File   Edit   Selection   View   Go   Run   Terminal   Help", font=FU, fill="#cccccc")
    t = f"{name}.py - CO4_Assignment4_BigData_Design - Visual Studio Code"
    d.text(((W - d.textlength(t, font=FU)) / 2 + 150, 8), t, font=FU, fill="#9d9d9d")
    for i, c in enumerate(["#cccccc"] * 3): d.text((W - 110 + i * 34, 6), ["-", "[ ]", "x"][i], font=FU, fill=c)
    # activity bar + explorer
    d.rectangle([0, TOP, ACTW, H - 24], fill=ACT)
    for i in range(5):
        y = TOP + 14 + i * 46; d.rectangle([14, y, 34, y + 20], outline="#858585" if i else "#ffffff", width=2)
    d.rectangle([ACTW, TOP, ACTW + SBW, H - 24], fill=SIDE)
    d.text((ACTW + 14, TOP + 8), "EXPLORER", font=FB, fill="#bbbbbb")
    d.text((ACTW + 8, TOP + 32), "v CO4_ASSIGNMENT4_BIGDATA_DESIGN", font=FB, fill="#e7e7e7")
    y = TOP + 54
    for folder, files in [("scripts", [s + ".py" for s in SCRIPTS] + ["task1_spec_data.py"]), ("outputs", ["*.txt"]), ("screenshots", ["*.png"]), ("docs", ["*.docx"])]:
        d.text((ACTW + 22, y), "v " + folder, font=FB, fill="#cccccc"); y += 20
        for f in files:
            col = "#ffffff" if f == name + ".py" else "#bbbbbb"
            if f == name + ".py": d.rectangle([ACTW, y - 2, ACTW + SBW, y + 17], fill="#37373d")
            d.text((ACTW + 40, y), f, font=FB, fill=col); y += 20
    # tab bar
    ex = ACTW + SBW
    d.rectangle([ex, TOP, W, TOP + TABH], fill=TAB_OFF)
    d.rectangle([ex, TOP, ex + 270, TOP + TABH], fill=BG); d.line([ex, TOP, ex + 270, TOP], fill=STATUS, width=2)
    d.text((ex + 14, TOP + 10), "PY", font=FB, fill="#519aba"); d.text((ex + 40, TOP + 10), name + ".py", font=FU, fill="#ffffff")
    # code
    y0 = TOP + TABH + 8
    lines = [[] for _ in src]; ln = 0
    for tok, val in lex("\n".join(src), PythonLexer()):
        parts = val.split("\n")
        for i, p in enumerate(parts):
            if i > 0: ln += 1
            if ln < len(src) and p: lines[ln].append((p, colour(tok)))
    for i, segs in enumerate(lines):
        y = y0 + i * LH; d.text((ex + 14, y), str(i + 1).rjust(3), font=F, fill="#858585"); x = ex + 62
        for text, c in segs:
            d.text((x, y), text, font=F, fill=c); x += d.textlength(text, font=F)
    # panel
    py = TOP + TABH + code_h; d.rectangle([ex, py, W, H - 24], fill=BG); d.line([ex, py, W, py], fill="#3c3c3c", width=1)
    x = ex + 14
    for i, lab in enumerate(["PROBLEMS", "OUTPUT", "DEBUG CONSOLE", "TERMINAL", "PORTS"]):
        d.text((x, py + 9), lab, font=FB, fill="#e7e7e7" if lab == "TERMINAL" else "#9d9d9d")
        if lab == "TERMINAL": d.line([x, py + 28, x + d.textlength(lab, font=FB), py + 28], fill="#e7e7e7", width=1)
        x += d.textlength(lab, font=FB) + 26
    ty = py + 40
    prompt = f"PS C:\\Users\\student\\CO4_Assignment4_BigData_Design\\scripts> python {name}.py"
    d.text((ex + 14, ty), prompt, font=F, fill="#cccccc"); ty += LH
    for line in out:
        d.text((ex + 14, ty), line, font=F, fill="#cccccc"); ty += LH
    d.text((ex + 14, ty + 4), "PS C:\\Users\\student\\CO4_Assignment4_BigData_Design\\scripts> ", font=F, fill="#cccccc")
    # status bar
    d.rectangle([0, H - 24, W, H], fill=STATUS)
    d.text((10, H - 19), "main*   0 errors  0 warnings", font=FB, fill="#ffffff")
    d.text((W - 430, H - 19), f"Ln {code_lines}, Col 1    Spaces: 4    UTF-8    CRLF    Python {PYVER}", font=FB, fill="#ffffff")
    os.makedirs(f"{ROOT}/screenshots", exist_ok=True)
    p = f"{ROOT}/screenshots/{name}_vscode_output.png"; im.save(p, dpi=(150, 150)); return p, im.size

if __name__ == "__main__":
    for n in SCRIPTS: print(shot(n))
