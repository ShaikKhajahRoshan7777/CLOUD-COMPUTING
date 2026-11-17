import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)


def save_table(df, name: str):
    """Write a DataFrame as CSV + Markdown into results/ and print it."""
    df.to_csv(RESULTS / f"{name}.csv", index=False)
    try:
        (RESULTS / f"{name}.md").write_text(df.to_markdown(index=False))
    except ImportError:                      # 'tabulate' not installed -> plain text fallback
        (RESULTS / f"{name}.md").write_text(df.to_string(index=False))
    print(f"\n=== {name} ===")
    print(df.to_string(index=False))
