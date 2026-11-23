"""Render the saved console logs and key source excerpts as VS Code-style images (dark theme).
These are renders of the REAL logs in results/*.txt; for the submission you may replace them with real VS Code captures."""
import ast, os, textwrap
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import ImageFormatter

ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ROOT, "screenshots"); os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"; FB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
BG, FG, BAR, TAB = (30, 30, 30), (204, 204, 204), (51, 51, 51), (37, 37, 38)
GREEN, BLUE, YEL, RED = (78, 201, 176), (86, 156, 214), (220, 220, 170), (244, 135, 113)


def colour(line):
    if line.startswith(("=", "-" * 10)): return BLUE
    if "PASS" in line or "MATCH" in line or "IDENTICAL" in line or "VALID" in line or "BALANCED" in line or "AGREE" in line: return GREEN
    if "FAIL" in line or "MISMATCH" in line or "DIFFERENT" in line or "BROKEN" in line or "DISAGREE" in line: return RED
    if line[:3] in ("2.1", "2.2", "2.3", "2.4", "4.1", "4.2", "4.3", "4.4", "6.1", "6.2", "6.3", "6.4") or line.startswith(("STAGE", "PREDICTION", "OBSERVATION", "ATTACK", "TASK", "---", "BOUNDARY", "Q1", "Q3", "TUNING", "STRESS", "CHOSEN", "UTILITY")): return YEL
    return FG


def render_console(script, lines, path, page, pages, size=15, maxc=118):
    f, fb = ImageFont.truetype(FONT, size), ImageFont.truetype(FB, size); lh = size + 6
    wrapped = []
    for l in lines:
        wrapped += textwrap.wrap(l, maxc, replace_whitespace=False, drop_whitespace=False, subsequent_indent="    ") or [""]
    W, H = int(size * 0.602 * (maxc + 4)) + 30, 100 + lh * (len(wrapped) + 3)
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 34], fill=BAR)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))): d.ellipse([14 + i * 22, 11, 26 + i * 22, 23], fill=c)
    d.text((W // 2 - 190, 8), "CO4_BigData_Assignment - Visual Studio Code", font=f, fill=(200, 200, 200))
    d.rectangle([0, 34, W, 66], fill=TAB); d.rectangle([0, 34, 250, 66], fill=BG); d.text((14, 42), script, font=f, fill=FG)
    d.text((270, 42), "TERMINAL   PROBLEMS   OUTPUT", font=f, fill=(140, 140, 140))
    y = 80; d.text((14, y), "(.venv) PS C:\\CO4_BigData_Assignment> python %s" % script, font=fb, fill=GREEN); y += lh
    for l in wrapped:
        d.text((14, y), l, font=f, fill=colour(l)); y += lh
    d.text((W - 150, H - 24), "page %d/%d" % (page, pages), font=f, fill=(120, 120, 120))
    im.save(path)


def console_pages(task, per=42):
    txt = open(os.path.join(ROOT, "results", "task%d_console.txt" % task)).read().splitlines()
    chunks = [txt[i:i + per] for i in range(0, len(txt), per)]; paths = []
    for i, ch in enumerate(chunks, 1):
        p = os.path.join(OUT, "task%d_console_%d.png" % (task, i)); render_console("run_task%d.py" % task, ch, p, i, len(chunks)); paths.append(p)
    return paths


def code_image(task, fname, funcs, path):
    src = open(os.path.join(ROOT, fname)).read(); tree = ast.parse(src); lines = src.splitlines(); parts = []
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in funcs:
            parts.append("\n".join(lines[n.lineno - 1:n.end_lineno]))
    code = "\n\n".join(parts)
    fm = ImageFormatter(font_name="DejaVu Sans Mono", font_size=15, style="monokai", line_numbers=True, image_pad=14, line_pad=3)
    open(path, "wb").write(highlight(code, PythonLexer(), fm))


if __name__ == "__main__":
    for t in range(1, 7): print(t, [os.path.basename(p) for p in console_pages(t)])
    spec = {1: ("task1/mapreduce.py", ["parse_line", "map_stage", "shuffle_stage", "reduce_stage"]),
            2: ("task2/engines.py", ["StreamEngine"]), 3: ("task3/access.py", ["AuditLog", "run_query"]),
            4: ("task4/cleaning.py", ["clean_line"]), 5: ("task5/stores.py", ["q1_parquet", "q2_parquet", "q1_sqlite", "q2_sqlite"]),
            6: ("task6/detector.py", ["naive", "keyed"])}
    for t, (f, fn) in spec.items(): code_image(t, f, fn, os.path.join(OUT, "task%d_code.png" % t))
