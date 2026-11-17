"""Master script: reproduces every table, graph and log of the report.   python src/run_all.py"""
import subprocess, sys, os
here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)
logs = os.path.join(here, "..", "results", "logs"); os.makedirs(logs, exist_ok=True)
steps = ["model.py", "tradeoff.py", "simulate.py", "real_bench.py", "security_check.py", "design.py", "make_figures.py"]
for s in steps:
    print("\n>>> python src/%s" % s)
    out = subprocess.run([sys.executable, s], capture_output=True, text=True).stdout
    open(os.path.join(logs, s.replace(".py", ".txt")), "w").write(out)
    print("\n".join(out.strip().splitlines()[:6]), "\n   ... (full log saved in results/logs/%s)" % s.replace(".py", ".txt"))
print("\nALL DONE - figures in /figures, tables in /results")
