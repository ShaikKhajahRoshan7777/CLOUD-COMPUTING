#!/usr/bin/env python3
"""Render a VS Code (Dark+) style screenshot: Explorer + editor tab with real source + terminal
panel containing the REAL output of the command (captured by running it now)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
from pygments.lexers import PythonLexer
from pygments.token import Token

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONOB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BG, SIDE, TAB, PANEL, TITLE, STATUS = "#1E1E1E", "#252526", "#2D2D2D", "#181818", "#3C3C3C", "#007ACC"
COL = {Token.Keyword: "#569CD6", Token.Keyword.Namespace: "#C586C0", Token.Name.Function: "#DCDCAA", Token.Name.Class: "#4EC9B0",
       Token.Literal.String: "#CE9178", Token.Literal.String.Doc: "#6A9955", Token.Comment: "#6A9955", Token.Literal.Number: "#B5CEA8",
       Token.Name.Builtin: "#4EC9B0", Token.Operator.Word: "#569CD6", Token.Name.Decorator: "#DCDCAA"}


def color_for(tt):
    while tt is not Token:
        if tt in COL:
            return COL[tt]
        tt = tt.parent
    return "#D4D4D4"


def shot(script_rel, command, out_png, first_line=1, n_code=24, max_term=46, cwd=ROOT, term_title="TERMINAL"):
    path = os.path.join(ROOT, script_rel)
    src = open(path).read().splitlines()[first_line - 1:first_line - 1 + n_code]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    res = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, env=env)
    term = (res.stdout + res.stderr).expandtabs(8).rstrip("\n").splitlines()
    open(os.path.join(ROOT, "results", os.path.splitext(out_png)[0] + ".txt"), "w").write(res.stdout + res.stderr)
    import textwrap
    wrapped = []
    for l in term:
        wrapped += textwrap.wrap(l, 92, subsequent_indent="    ", replace_whitespace=False, drop_whitespace=False) or [""]
    term = wrapped
    if len(term) > max_term:
        term = term[:max_term - 1] + ["... (output truncated for screenshot; full log in results/)"]
    fs = 15; lh = 21
    f, fb, fsn = ImageFont.truetype(MONO, fs), ImageFont.truetype(MONOB, fs), ImageFont.truetype(SANS, 12)
    cw = f.getlength("M")
    W = 1100
    code_h = len(src) * lh + 16
    term_h = (len(term) + 3) * lh + 40
    H = 30 + 36 + code_h + term_h + 24
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 30], fill=TITLE)
    d.text((W // 2 - 190, 8), f"{os.path.basename(script_rel)} - CO5_Hadoop_Assignment - Visual Studio Code", font=fsn, fill="#CCCCCC")
    for i, c in enumerate(("#FF5F56", "#FFBD2E", "#27C93F")):
        d.ellipse([12 + i * 20, 9, 24 + i * 20, 21], fill=c)
    d.rectangle([0, 30, 48, H - 24], fill="#333333")
    for i in range(5):
        d.rectangle([14, 50 + i * 46, 34, 70 + i * 46], outline="#858585", width=2)
    d.rectangle([48, 30, 218, H - 24], fill=SIDE)
    d.text((60, 40), "EXPLORER", font=fsn, fill="#BBBBBB")
    tree = ["v CO5_Hadoop_Assignment", "  > conf", "  > data", "  > figures", "  > results", "  > schema", "  > scripts", "  v src"]
    tree += ["      " + x for x in sorted(os.listdir(os.path.join(ROOT, "src"))) if x.endswith(".py")][:11]
    tree += ["  > tests", "  README.md"]
    for i, t in enumerate(tree):
        hl = os.path.basename(script_rel) in t
        if hl: d.rectangle([48, 62 + i * 19, 218, 80 + i * 19], fill="#37373D")
        d.text((58, 64 + i * 19), t[:21], font=fsn, fill="#FFFFFF" if hl else "#CCCCCC")
    x0 = 218
    d.rectangle([x0, 30, W, 66], fill=TAB)
    d.rectangle([x0, 30, x0 + 220, 66], fill=BG); d.rectangle([x0, 30, x0 + 220, 32], fill=STATUS)
    d.text((x0 + 14, 40), os.path.basename(script_rel), font=fsn, fill="#FFFFFF")
    y = 76
    lexer = PythonLexer()
    code = "\n".join(src)
    ln = first_line; x = x0 + 56
    d.text((x0 + 14, y), f"{ln:>3}", font=f, fill="#858585")
    for tt, val in lexer.get_tokens(code):
        parts = val.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                y += lh; ln += 1; x = x0 + 56
                if ln - first_line < len(src):
                    d.text((x0 + 14, y), f"{ln:>3}", font=f, fill="#858585")
            if part:
                d.text((x, y), part, font=f, fill=color_for(tt)); x += cw * len(part)
    py = 30 + 36 + code_h
    d.rectangle([x0, py, W, H - 24], fill=PANEL); d.line([x0, py, W, py], fill="#454545")
    d.text((x0 + 14, py + 8), "PROBLEMS     OUTPUT     DEBUG CONSOLE", font=fsn, fill="#858585")
    d.text((x0 + 14 + 300, py + 8), term_title, font=fsn, fill="#FFFFFF")
    d.line([x0 + 314, py + 26, x0 + 390, py + 26], fill="#FFFFFF", width=1)
    ty = py + 36
    d.text((x0 + 14, ty), "CO5_Hadoop_Assignment $ ", font=fb, fill="#4EC9B0")
    d.text((x0 + 14 + cw * 24, ty), command, font=f, fill="#D4D4D4")
    for line in term:
        ty += lh
        c = "#D4D4D4"
        if "PASS" in line: c = "#6A9955"
        if "FAIL" in line or "MISMATCH" in line: c = "#F14C4C"
        if "MATCH" in line and "MISMATCH" not in line: c = "#6A9955"
        d.text((x0 + 14, ty), line[:100], font=f, fill=c)
    d.text((x0 + 14, ty + lh), "CO5_Hadoop_Assignment $ ", font=fb, fill="#4EC9B0")
    d.rectangle([x0 + 14 + cw * 24, ty + lh + 2, x0 + 22 + cw * 24, ty + lh + 18], fill="#AEAFAD")
    d.rectangle([0, H - 24, W, H], fill=STATUS)
    d.text((12, H - 19), "main*   0 errors   0 warnings", font=fsn, fill="white")
    d.text((W - 340, H - 19), "Ln 1, Col 1   Spaces: 4   UTF-8   Python 3.12.3", font=fsn, fill="white")
    im.save(os.path.join(ROOT, "screenshots", out_png))
    return out_png


if __name__ == "__main__":
    jobs = [
        ("src/generate_logs.py", "python src/generate_logs.py data/demo.csv --records 2000 --malformed 0.02 --seed 42 && head -n 5 data/demo.csv && wc -l data/demo.csv", "S0_generator.png", 31, 22),
        ("src/capacity_calc.py", "python src/capacity_calc.py", "A2_capacity_calc.png", 1, 26),
        ("src/reducer.py", "cat data/sample.csv | python src/mapper.py | sort | python src/reducer.py", "A3_streaming_pipeline.png", 1, 12),
        ("tests/test_q1.py", "python tests/test_q1.py", "B2_1_tests.png", 60, 22),
        ("src/run_combiner.py", "python src/run_combiner.py", "B2_2_combiner.png", 14, 22),
        ("src/run_topn.py", "python src/run_topn.py", "B2_3_topn.png", 12, 22),
        ("src/run_scaling.py", "python src/run_scaling.py", "B3_1_scaling.png", 8, 22),
        ("src/run_skew.py", "python src/run_skew.py", "B3_2_skew.png", 1, 20),
        ("src/failure_injection.py", "python src/failure_injection.py", "B4_1_failure.png", 22, 22),
        ("src/scheduler_sim.py", "python src/scheduler_sim.py", "B4_2_scheduler.png", 1, 22),
    ]
    for j in jobs:
        print("rendered", shot(*j[:3], first_line=j[3], n_code=j[4], max_term=56))
