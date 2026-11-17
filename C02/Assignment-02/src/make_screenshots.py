"""Renders VS Code-style screenshots (code editor + integrated terminal) from the REAL source files and REAL logs in results/logs."""
import os
from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "screenshots"); os.makedirs(OUT, exist_ok=True)
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
W, H = 1600, 940
BG, SIDE, ACT, TAB, PANEL, STATUS = "#1e1e1e", "#252526", "#333333", "#2d2d2d", "#1e1e1e", "#007acc"
COL = {Token.Keyword: "#569cd6", Token.Keyword.Namespace: "#c586c0", Token.Name.Function: "#dcdcaa", Token.Name.Class: "#4ec9b0",
       Token.Literal.String: "#ce9178", Token.Literal.String.Doc: "#6a9955", Token.Comment: "#6a9955", Token.Literal.Number: "#b5cea8",
       Token.Name.Builtin: "#4ec9b0", Token.Operator.Word: "#569cd6", Token.Name.Decorator: "#dcdcaa"}
def tcol(t):
    while t is not None:
        if t in COL: return COL[t]
        t = t.parent
    return "#d4d4d4"

def shot(code_file, a, b, cmd, log, l0, l1, out, title=None, image=None):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FM, 14); fb = ImageFont.truetype(FB, 14); fs = ImageFont.truetype(FS, 12); fsb = ImageFont.truetype(FS, 13)
    d.rectangle([0, 0, W, 30], fill="#3c3c3c"); d.text((W // 2, 15), "%s - EduCloud_CO2_Virtualization - Visual Studio Code" % os.path.basename(code_file), font=fs, fill="#cccccc", anchor="mm")
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")): d.ellipse([12 + i * 22, 9, 24 + i * 22, 21], fill=c)
    d.rectangle([0, 30, 48, H - 24], fill=ACT)
    for i in range(5): d.rectangle([14, 50 + i * 52, 34, 70 + i * 52], outline="#858585", width=2)
    d.rectangle([48, 30, 308, H - 24], fill=SIDE); d.text((64, 44), "EXPLORER", font=fs, fill="#bbbbbb")
    tree = [("v EDUCLOUD_CO2_VIRTUALIZATION", 0), ("v src", 1), ("model.py", 2), ("simulate.py", 2), ("real_bench.py", 2), ("security_check.py", 2), ("design.py", 2), ("tradeoff.py", 2), ("make_figures.py", 2), ("run_all.py", 2),
            ("> figures", 1), ("> results", 1), ("> screenshots", 1), ("> configs", 1), ("> scripts", 1), ("> docs", 1), ("README.md", 1), ("requirements.txt", 1)]
    y = 70
    for t, lv in tree:
        act = os.path.basename(code_file) == t
        if act: d.rectangle([48, y - 2, 308, y + 18], fill="#37373d")
        d.text((62 + lv * 14, y), t, font=fsb, fill="#ffffff" if act or lv == 0 else "#cccccc"); y += 22
    d.rectangle([308, 30, W, 66], fill=TAB); d.rectangle([308, 30, 308 + 210, 66], fill=BG); d.rectangle([308, 30, 518, 32], fill="#007acc")
    d.text((324, 40), (os.path.basename(code_file) if not image else os.path.basename(image)), font=fsb, fill="#ffffff")
    top = 66; eh = 430
    if image:
        pic = Image.open(image).convert("RGB"); pic.thumbnail((1200, eh - 20)); im.paste(pic, (308 + (W - 308 - pic.width) // 2, top + 10))
    else:
        lines = open(os.path.join(ROOT, code_file)).read().split("\n")[a - 1:b]
        full = "\n".join(lines); toks = list(lex(full, PythonLexer())); x0 = 308 + 64; ln = a; yy = top + 6; xx = x0
        d.text((308 + 14, yy), str(ln).rjust(3), font=f, fill="#858585")
        for tt, val in toks:
            for k, part in enumerate(val.split("\n")):
                if k > 0:
                    ln += 1; yy += 20; xx = x0
                    if yy > top + eh - 20: break
                    d.text((308 + 14, yy), str(ln).rjust(3), font=f, fill="#858585")
                if part and yy <= top + eh - 20:
                    d.text((xx, yy), part, font=f, fill=tcol(tt)); xx += int(f.getlength(part))
            if yy > top + eh - 20: break
    py = top + eh; d.rectangle([308, py, W, py + 30], fill=BG); d.line([308, py, W, py], fill="#3c3c3c")
    for i, t in enumerate(("PROBLEMS", "OUTPUT", "DEBUG CONSOLE", "TERMINAL", "PORTS")):
        d.text((324 + i * 130, py + 8), t, font=fs, fill="#ffffff" if t == "TERMINAL" else "#999999")
    d.line([324 + 3 * 130, py + 28, 324 + 3 * 130 + 72, py + 28], fill="#ffffff", width=2)
    ty = py + 40; d.text((324, ty), "$ ", font=fb, fill="#6a9955"); d.text((344, ty), cmd, font=f, fill="#d4d4d4"); ty += 22
    for line in open(os.path.join(ROOT, log)).read().split("\n")[l0:l1]:
        if ty > H - 50: break
        d.text((324, ty), line[:170], font=f, fill="#cccccc"); ty += 19
    d.text((324, min(ty + 4, H - 44)), "$ ", font=fb, fill="#6a9955"); d.rectangle([344, min(ty + 4, H - 44), 353, min(ty + 4, H - 44) + 16], fill="#aeafad")
    d.rectangle([0, H - 24, W, H], fill=STATUS); d.text((12, H - 19), "  main    Python 3.12.3    Ln %d, Col 1    Spaces: 4    UTF-8    Python" % a, font=fs, fill="#ffffff")
    im.save(os.path.join(OUT, out)); print("saved", out)

S = [("src/model.py", 25, 46, "python src/model.py", "results/logs/model.txt", 0, 30, "01_model_py_task3_output.png"),
     ("src/simulate.py", 20, 41, "python src/simulate.py", "results/logs/simulate.txt", 8, 38, "02_simulate_py_emulated_testbed.png"),
     ("src/real_bench.py", 17, 38, "python src/real_bench.py", "results/logs/real_bench.txt", 0, 30, "03_real_bench_py_measurements.png"),
     ("src/security_check.py", 1, 24, "python src/security_check.py", "results/logs/security_check.txt", 0, 30, "04_security_check_py_validation.png"),
     ("src/tradeoff.py", 1, 22, "python src/tradeoff.py", "results/logs/tradeoff.txt", 0, 30, "05_tradeoff_py_task6_task7.png"),
     ("src/design.py", 1, 32, "python src/design.py", "results/logs/design.txt", 0, 30, "06_design_py_task12.png"),
     ("src/run_all.py", 1, 14, "python src/run_all.py", "results/logs/make_figures.txt", 0, 6, "07_run_all_py_pipeline.png")]
for a in S: shot(*a)
shot("src/make_figures.py", 1, 10, "python src/make_figures.py", "results/logs/make_figures.txt", 0, 4, "08_graph_preview_cpu_scaling.png", image=os.path.join(ROOT, "figures", "graph1_cpu.png"))
