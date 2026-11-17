"""
Renders VS Code (Dark+) style images from the REAL source files and REAL captured output
in ../src and ../outputs.  Replace these with your own VS Code screenshots (Win+Shift+S)
if your faculty needs original screen captures.
Run from repo root:  python tools/render_vscode_screenshots.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from pygments import lex
from pygments.lexers import PythonLexer
from pygments.token import Token

ROOT = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
UI = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F = ImageFont.truetype(FONT, 15)
FU = ImageFont.truetype(UI, 13)
LH, W = 22, 1500

C = dict(bg="#1e1e1e", side="#252526", act="#333333", tab="#2d2d2d", title="#3c3c3c", status="#007acc",
         term="#1e1e1e", line="#858585", text="#d4d4d4", border="#454545")
TOK = [(Token.Comment, "#6a9955"), (Token.Literal.String, "#ce9178"), (Token.Keyword.Namespace, "#c586c0"),
       (Token.Keyword, "#569cd6"), (Token.Name.Function, "#dcdcaa"), (Token.Name.Class, "#4ec9b0"),
       (Token.Name.Builtin, "#4ec9b0"), (Token.Literal.Number, "#b5cea8"), (Token.Operator.Word, "#569cd6")]


def color_for(tok):
    for t, c in TOK:
        if tok in t:
            return c
    return C["text"]


def draw_code(d, x, y, lines, start):
    src = "\n".join(lines)
    ln, col = 0, 0
    for i in range(len(lines)):
        d.text((x, y + i * LH), f"{start + i:>3}", font=F, fill=C["line"])
    for tok, val in lex(src, PythonLexer()):
        for j, piece in enumerate(val.split("\n")):
            if j > 0:
                ln += 1
                col = 0
            if piece:
                d.text((x + 50 + col * 9, y + ln * LH), piece, font=F, fill=color_for(tok))
                col += len(piece)


def term_color(line):
    if "PASS" in line or "200" in line[:20] or "STATUS   : 200" in line:
        return "#6ec26e"
    if "FAIL" in line or "STATUS   : 404" in line or "BLOCKED" in line or "DENIED" in line:
        return "#f48771"
    return C["text"]


def render(script, out, code_range, term_range, cmd, files):
    code = (ROOT / "src" / script).read_text().splitlines()[code_range[0] - 1:code_range[1]]
    outp = (ROOT / "outputs" / (script.split("_")[0] + "_output.txt")).read_text().splitlines()
    term = outp[term_range[0]:term_range[1]]
    ed_h = len(code) * LH + 20
    term_h = (len(term) + 3) * LH + 20
    H = 30 + 36 + ed_h + 30 + term_h + 24
    im = Image.new("RGB", (W, H), C["bg"])
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 30], fill=C["title"])
    d.text((W // 2 - 190, 7), f"{script} - cloud_co3_assignment - Visual Studio Code", font=FU, fill="#cccccc")
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        d.ellipse([14 + i * 22, 9, 26 + i * 22, 21], fill=c)
    body_top, body_bot = 30, H - 24
    d.rectangle([0, body_top, 48, body_bot], fill=C["act"])
    d.rectangle([48, body_top, 270, body_bot], fill=C["side"])
    d.text((60, body_top + 10), "EXPLORER", font=FU, fill="#bbbbbb")
    d.text((60, body_top + 36), "v CLOUD_CO3_ASSIGNMENT", font=FU, fill="#e0e0e0")
    for i, f in enumerate(files):
        act = f == script
        if act:
            d.rectangle([48, body_top + 62 + i * 24, 270, body_top + 84 + i * 24], fill="#37373d")
        d.text((78, body_top + 64 + i * 24), f, font=FU, fill="#ffffff" if act else "#cccccc")
    ex = 270
    d.rectangle([ex, body_top, W, body_top + 36], fill=C["tab"])
    d.rectangle([ex, body_top, ex + 250, body_top + 36], fill=C["bg"])
    d.text((ex + 14, body_top + 10), f"PY  {script}", font=FU, fill="#ffffff")
    cy = body_top + 36 + 10
    draw_code(d, ex + 10, cy, code, code_range[0])
    ty = cy + ed_h
    d.line([ex, ty, W, ty], fill=C["border"])
    d.text((ex + 14, ty + 6), "PROBLEMS      OUTPUT      DEBUG CONSOLE      TERMINAL", font=FU, fill="#bbbbbb")
    d.line([ex + 330, ty + 26, ex + 410, ty + 26], fill="#e7e7e7", width=2)
    y = ty + 34
    d.text((ex + 14, y), f"PS C:\\cloud_co3_assignment> {cmd}", font=F, fill="#dcdcaa")
    y += LH
    for line in term:
        d.text((ex + 14, y), line, font=F, fill=term_color(line))
        y += LH
    d.text((ex + 14, y), "PS C:\\cloud_co3_assignment> _", font=F, fill="#dcdcaa")
    d.rectangle([0, H - 24, W, H], fill=C["status"])
    d.text((14, H - 20), "main    Python 3.12    Ln 1, Col 1    Spaces: 4    UTF-8    CRLF", font=FU, fill="#ffffff")
    im.save(ROOT / "screenshots" / out)
    print("saved", out, im.size)


if __name__ == "__main__":
    files = ["q3_api_client.py", "q4_auth_demo.py", "cloud_collab.py", "q6_assignment_portal.py", "q7_validation_tests.py"]
    render("q3_api_client.py", "q3_1_code_and_test1.png", (19, 36), (0, 17), "python src/q3_api_client.py", files)
    render("q3_api_client.py", "q3_2_test2_different_input.png", (55, 70), (17, 34), "python src/q3_api_client.py", files)
    render("q3_api_client.py", "q3_3_test3_invalid_input.png", (55, 70), (34, 46), "python src/q3_api_client.py", files)
    render("q4_auth_demo.py", "q4_1_authentication_authorization.png", (40, 62), (0, 13), "python src/q4_auth_demo.py", files)
    render("q4_auth_demo.py", "q4_2_attacks_and_comparison.png", (66, 80), (14, 23), "python src/q4_auth_demo.py", files)
    render("q6_assignment_portal.py", "q6_1_scenarios.png", (20, 38), (0, 15), "python src/q6_assignment_portal.py", files)
    render("q6_assignment_portal.py", "q6_2_audit_log.png", (20, 29), (15, 24), "python src/q6_assignment_portal.py", files)
    render("q7_validation_tests.py", "q7_validation_results.png", (24, 40), (0, 13), "python src/q7_validation_tests.py", files)
