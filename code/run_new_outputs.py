"""Master runner for all new outputs (extended data + M-1…M-14 + tables)."""
import os, sys, time, subprocess

sys.path.insert(0, os.path.dirname(__file__))

def banner(msg):
    print(f"\n{'='*60}\n  {msg}\n{'='*60}")

def step(label, fn):
    t0 = time.time()
    print(f"\n>>> {label}")
    fn()
    print(f"    Done in {time.time()-t0:.1f}s")

banner("STEP 1 — Extended Simulation Data")
from extended_simulation import run_all as run_ext
step("14 new CSV tables", run_ext)

banner("STEP 2 — New Figures M-1 to M-14 (Python PNG+PDF)")
from generate_new_figures import run_all as run_figs
step("14 new figures", run_figs)

banner("STEP 3 — Word Documents (Main-Body + Appendix Tables)")
from generate_tables_doc import build_main_tables, build_appendix_tables
step("Main-body tables T-A to T-D", build_main_tables)
step("Appendix tables App-A to App-H", build_appendix_tables)

banner("STEP 4 — MATLAB .fig Files for M-1 to M-14")
matlab_exe = r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe"
m_script   = r"E:\Working Docs\Papers\Reliability CAV\code\generate_new_matlab_figs.m"
cmd = f"cd('E:\\Working Docs\\Papers\\Reliability CAV'); run('code\\generate_new_matlab_figs.m'); exit"
print(f"  Running MATLAB...")
result = subprocess.run([matlab_exe, "-batch", cmd], capture_output=True, text=True, timeout=600)
print(result.stdout[-3000:] if len(result.stdout)>3000 else result.stdout)
if result.returncode != 0:
    print("  MATLAB stderr:", result.stderr[-1000:])

banner("COMPLETE")
from config import TABLES, REPORT
new_fig_dir = os.path.join(os.path.dirname(TABLES), "figures", "new")
matlab_dir  = os.path.join(os.path.dirname(TABLES), "figures", "matlab")
def cnt(d, ext): return sum(1 for f in os.listdir(d) if f.endswith(ext)) if os.path.isdir(d) else 0
print(f"  New figures (PNG):     {cnt(new_fig_dir, '.png')} files")
print(f"  New figures (PDF):     {cnt(new_fig_dir, '.pdf')} files")
print(f"  New MATLAB .fig:       {cnt(matlab_dir,  '.fig')} files total")
print(f"  New CSV tables:        {cnt(TABLES, '.csv')} files total")
print(f"  Word reports:          {cnt(REPORT, '.docx')} files")
