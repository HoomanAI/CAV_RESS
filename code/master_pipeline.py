"""
Master Pipeline — CAV Reliability Paper
Run this single script to generate ALL outputs:
  1. Simulation (all experiments → CSV tables)
  2. 3D figures (PDF + PNG)
  3. Innovative figures (PDF + PNG)
  4. Summary 2D figures (PDF + PNG)
  5. Word report

Usage:  python code/master_pipeline.py
        (run from: E:\\Working Docs\\Papers\\Reliability CAV)
"""
import os, sys, time

sys.path.insert(0, os.path.dirname(__file__))

def banner(msg):
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def run_step(label, fn):
    t0 = time.time()
    print(f"\n>>> {label}")
    fn()
    print(f"    Done in {time.time()-t0:.1f}s")


# ---- Step 1: Simulations ----
banner("STEP 1 — Running Experiments")
from simulation_framework import run_all as run_sim
run_step("All 10 Experiments -> CSV tables", run_sim)

# ---- Step 2: 3D Figures ----
banner("STEP 2 — 3D Figures")
from generate_3d_figures import run_all as run_3d
run_step("5 × 3D Figures (PDF + PNG)", run_3d)

# ---- Step 3: Innovative Figures ----
banner("STEP 3 — Innovative Figures")
from innovative_figures import run_all as run_innov
run_step("11 × Innovative Figures (PDF + PNG)", run_innov)

# ---- Step 4: Summary Figures ----
banner("STEP 4 — Summary 2D Figures")
from generate_summary_figures import run_all as run_summary
run_step("6 × Summary Figures (PDF + PNG)", run_summary)

# ---- Step 5: Word Report ----
banner("STEP 5 — Word Report")
from generate_report import build_report
run_step("14-table Results Report (.docx)", build_report)

# ---- Final summary ----
banner("COMPLETE")
from config import BASE, FIG_3D, FIG_IN, FIG_SM, FIG_ML, TABLES, REPORT
import os

def count_files(folder, ext):
    return sum(1 for f in os.listdir(folder) if f.endswith(ext))

print(f"  Output directory: {BASE}")
print(f"\n  results/tables/        : {count_files(TABLES, '.csv')} CSV files")
print(f"  results/figures/3d/    : {count_files(FIG_3D, '.pdf')} PDFs, {count_files(FIG_3D, '.png')} PNGs")
print(f"  results/figures/innovative/: {count_files(FIG_IN, '.pdf')} PDFs, {count_files(FIG_IN, '.png')} PNGs")
print(f"  results/figures/summary/: {count_files(FIG_SM, '.pdf')} PDFs, {count_files(FIG_SM, '.png')} PNGs")
print(f"  results/figures/matlab/ : MATLAB .m script (run from MATLAB to generate .fig)")
print(f"  results/report/        : {count_files(REPORT, '.docx')} Word report(s)")
print(f"\n  MATLAB figures: open MATLAB and run code\\matlab_figures.m")
