"""Master runner — 2025 Iberian Blackout Case Study."""
import os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))

BASE = os.path.dirname(os.path.dirname(__file__))

def step(label, fn):
    print(f"\n>>> {label}")
    t0 = time.time()
    fn()
    print(f"    Done in {time.time()-t0:.1f}s")

print("="*60)
print("CASE STUDY: 2025 Iberian Peninsula Blackout — Madrid")
print("="*60)

step("1. Network setup + data generation", lambda: __import__("cs_setup").run_setup())
step("2. Hexagonal maps (6 maps)",         lambda: __import__("cs_maps").run_all())
step("3. Result figures (7 figures)",      lambda: __import__("cs_figures").run_all())

print("\n>>> 4. MATLAB .fig files")
matlab_exe = r"C:\Program Files\MATLAB\R2026a\bin\matlab.exe"
cs_dir     = os.path.dirname(__file__)
cmd        = (f"cd('{BASE.replace(chr(92),chr(92)*2)}'); "
              f"run('code\\\\cs_matlab_figs.m'); exit")
result = subprocess.run([matlab_exe, "-batch", cmd],
                        capture_output=True, text=True, timeout=300)
if result.returncode == 0:
    print("    MATLAB .fig files saved.")
    saved = [l for l in result.stdout.splitlines() if "Saved" in l]
    for s in saved: print(f"      {s}")
else:
    print(f"    MATLAB WARNING: {result.stderr[-400:]}")

print("\n>>> 5. Word report")
from cs_report import build_report
build_report()

print("\n" + "="*60)
print("CASE STUDY COMPLETE")
print("="*60)
# Summary
for folder, label in [
    (os.path.join(BASE,"figures","maps"),   "Maps (hex)"),
    (os.path.join(BASE,"figures","results"),"Result figures"),
    (os.path.join(BASE,"figures","matlab"), "MATLAB .fig"),
    (os.path.join(BASE,"data"),             "Data files"),
    (os.path.join(BASE,"report"),           "Reports"),
]:
    if os.path.isdir(folder):
        n = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder,f))])
        print(f"  {label:25s}: {n} files")
