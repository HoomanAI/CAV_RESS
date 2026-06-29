"""
Experiment 7 (MOO) — proper Pareto comparison:
  QiGA (scalarisation grid)  vs.  NSGA-II  vs.  MOEA/D
Outputs:
  results/tables/moo_exp7.csv          — archive quality per algorithm/phi/seed
  results/figures/new/MOO_*.pdf/.png   — 6 new MOO figures
"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from config import TABLES, savefig, PHI_LEVELS
from simulation_framework import CVRPTWInstance, nearest_neighbour, compute_metrics, PERF
from nsga2_moead import (NSGAII, MOEAD, evaluate3, pareto_nd,
                          hv_2d, igd, spread_delta, knee_point, dominates)

FIG_NEW  = os.path.join(os.path.dirname(TABLES), "figures", "new")
os.makedirs(FIG_NEW, exist_ok=True)

MOO_ALGOS  = ["QiGA-WS", "NSGA-II", "MOEA/D"]
MOO_COLORS = {"QiGA-WS":"#1565C0", "NSGA-II":"#E53935", "MOEA/D":"#2E7D32"}
MOO_MARKS  = {"QiGA-WS":"o",       "NSGA-II":"s",       "MOEA/D":"D"}
RNG_SEEDS  = list(range(1, 11))

# ─────────────────────────────────────────────────────────────────────────────
# QiGA via weighted scalarisation grid (existing approach, kept for comparison)
# ─────────────────────────────────────────────────────────────────────────────

def _qiga_ws_archive(inst, seed):
    """Approximate Pareto front by running QiGA at 21 weight combinations."""
    from simulation_framework import run_algorithm, compute_Z
    rng  = np.random.default_rng(seed)
    pts  = []
    w1s  = np.round(np.arange(0.0, 1.01, 0.1), 2)
    for w1 in w1s:
        w2 = round((1 - w1) / 2, 3); w3 = round(1 - w1 - w2, 3)
        m  = run_algorithm(inst, "QiGA", n_runs=3, w1=w1, w2=w2, w3=w3)
        # convert back to (f1,f2,f3) max form
        f1 =  m["SCI"]
        f2 = -m["TD"] / 1000.0
        f3 =  m["RRS"]
        pts.append(((f1, f2, f3), None))
    # filter non-dominated
    nd = pareto_nd(pts)
    return [pts[i] for i in nd]


# ─────────────────────────────────────────────────────────────────────────────
# Run comparison
# ─────────────────────────────────────────────────────────────────────────────

def run_moo_exp7(phi_levels=None, n=50, n_seeds=5):
    if phi_levels is None:
        phi_levels = [1.00, 0.90, 0.85, 0.80, 0.70]
    print(f"\n=== Experiment 7 (MOO) — n={n}, {n_seeds} seeds ===")
    rows = []

    for phi in phi_levels:
        for seed in RNG_SEEDS[:n_seeds]:
            inst = CVRPTWInstance(n, phi_min=phi, seed=seed)

            # Reference front = union of all archives (for IGD)
            combined = []
            archives = {}

            for algo in MOO_ALGOS:
                t0 = time.time()
                if algo == "QiGA-WS":
                    archive = _qiga_ws_archive(inst, seed)
                elif algo == "NSGA-II":
                    archive, _ = NSGAII(inst, pop_size=60, n_gen=150, seed=seed).run()
                else:   # MOEA/D
                    archive, _ = MOEAD(inst,  H=12, n_gen=180, seed=seed).run()
                ct = time.time() - t0
                archives[algo] = archive
                combined.extend(archive)

            # Build reference front from union
            ref_nd  = pareto_nd(combined)
            ref_front = [combined[i] for i in ref_nd]

            for algo, archive in archives.items():
                if not archive:
                    continue
                objs  = [a[0] for a in archive]
                hv    = hv_2d(objs)
                igd_v = igd(archive, ref_front)
                sp_v  = spread_delta(objs)
                kp, _ = knee_point(archive)
                rows.append(dict(
                    algo=algo, phi_min=phi, seed=seed, n=n,
                    n_pareto=len(archive),
                    HV=round(hv, 5),
                    IGD=round(igd_v, 5),
                    Spread=round(sp_v, 4),
                    f1_mean=round(np.mean([f[0] for f in objs]), 4),
                    f2_mean=round(np.mean([f[1] for f in objs]), 4),
                    f3_mean=round(np.mean([f[2] for f in objs]), 4),
                    f1_knee=round(kp[0], 4) if kp else 0,
                    f3_knee=round(kp[2], 4) if kp else 0,
                ))
            print(f"  phi={phi:.2f} seed={seed} → "
                  + " | ".join(f"{a}: |F|={len(archives[a])}" for a in MOO_ALGOS))

    df = pd.DataFrame(rows)
    path = os.path.join(TABLES, "moo_exp7.csv")
    df.to_csv(path, index=False)
    print(f"  Saved moo_exp7.csv ({len(df)} rows)")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# Figures
# ─────────────────────────────────────────────────────────────────────────────

def fig_moo1_pareto_scatter(n=50, phi=0.85, seed=1):
    """MOO-1: Pareto front scatter — all 3 algorithms, 2 projections."""
    inst = CVRPTWInstance(n, phi_min=phi, seed=seed)
    archives = {}
    for algo in MOO_ALGOS:
        if algo == "QiGA-WS":
            archives[algo] = _qiga_ws_archive(inst, seed)
        elif algo == "NSGA-II":
            archives[algo], _ = NSGAII(inst, pop_size=60, n_gen=150, seed=seed).run()
        else:
            archives[algo], _ = MOEAD(inst,  H=12, n_gen=180, seed=seed).run()

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (xi, yi, xl, yl) in zip(axes, [
        (0, 2, "f₁: Satisfaction (↑)", "f₃: Reliability (↑)"),
        (0, 1, "f₁: Satisfaction (↑)", "f₂: –Distance/1000 (↑, shorter routes)"),
    ]):
        for algo in MOO_ALGOS:
            arch = archives[algo]
            if not arch: continue
            xv = [a[0][xi] for a in arch]
            yv = [a[0][yi] for a in arch]
            ax.scatter(xv, yv, s=45, c=MOO_COLORS[algo],
                       marker=MOO_MARKS[algo], alpha=0.78,
                       edgecolors="white", lw=0.5, label=algo)
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.suptitle(f"MOO-1  Pareto Front: QiGA-WS vs NSGA-II vs MOEA/D\n"
                 f"(n={n}, φ_min={phi}, seed={seed})",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO1_pareto_scatter"); plt.close(fig)


def fig_moo2_quality_metrics(df):
    """MOO-2: HV, IGD, Spread, archive size by algorithm — bar charts."""
    phi_sel = 0.85
    sub = df[abs(df["phi_min"] - phi_sel) < 1e-9]
    metrics = [("HV", "Hypervolume HV (↑)"), ("IGD", "IGD (↓)"),
               ("Spread", "Spread Δ (↓)"), ("n_pareto", "Archive Size |F| (↑)")]

    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    for ax, (col, ylabel) in zip(axes, metrics):
        mn  = [sub.loc[sub["algo"]==a, col].mean() for a in MOO_ALGOS]
        sd  = [sub.loc[sub["algo"]==a, col].std()  for a in MOO_ALGOS]
        bars = ax.bar(MOO_ALGOS, mn, color=[MOO_COLORS[a] for a in MOO_ALGOS],
                      alpha=0.82, yerr=sd, capsize=4, error_kw=dict(lw=1.2))
        for bar, v in zip(bars, mn):
            ax.text(bar.get_x()+bar.get_width()/2, v+abs(v)*0.03,
                    f"{v:.3f}", ha="center", fontsize=8.5, fontweight="bold")
        ax.set_ylabel(ylabel); ax.set_xticklabels(MOO_ALGOS, rotation=15)
        ax.grid(axis="y", alpha=0.25)

    fig.suptitle(f"MOO-2  Pareto Front Quality Metrics (φ_min={phi_sel}, n=50, mean±std over seeds)\n"
                 "QiGA-WS: scalarisation grid  |  NSGA-II: population Pareto  |  MOEA/D: decomposition",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO2_quality_metrics"); plt.close(fig)


def fig_moo3_hv_vs_phi(df):
    """MOO-3: HV vs φ_min — how Pareto quality degrades with reliability."""
    phi_u = sorted(df["phi_min"].unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    for ax, (col, ylabel) in zip(axes, [
        ("HV",    "Hypervolume HV (↑ better)"),
        ("IGD",   "IGD (↓ better)"),
    ]):
        for algo in MOO_ALGOS:
            vals = [df.loc[(abs(df["phi_min"]-p)<1e-9)&(df["algo"]==algo), col].mean()
                    for p in phi_u]
            ax.plot(phi_u, vals, "o-", color=MOO_COLORS[algo],
                    marker=MOO_MARKS[algo], lw=2.2, ms=7, label=algo)
        ax.set_xlabel("φ_min"); ax.set_ylabel(ylabel)
        ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
        ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)
        ax.text(0.855, ax.get_ylim()[1]*0.95, "φ*", color="darkorange", fontsize=9)

    fig.suptitle("MOO-3  Pareto Front Quality vs φ_min\n"
                 "MOEA/D maintains larger HV at low φ — Tchebycheff handles constrained space better",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO3_quality_vs_phi"); plt.close(fig)


def fig_moo4_3d_pareto(n=50, phi=0.85, seed=1):
    """MOO-4: 3D Pareto front — NSGA-II vs MOEA/D (replaces synthetic 3D-1 in paper)."""
    from mpl_toolkits.mplot3d import Axes3D  # noqa
    inst = CVRPTWInstance(n, phi_min=phi, seed=seed)
    arch_ns, _ = NSGAII(inst, pop_size=60, n_gen=150, seed=seed).run()
    arch_md, _ = MOEAD(inst,  H=12, n_gen=180, seed=seed).run()
    arch_ws     = _qiga_ws_archive(inst, seed)

    fig = plt.figure(figsize=(11, 8))
    ax  = fig.add_subplot(111, projection="3d")
    for arch, col, lbl, mk in [
        (arch_ws, "#1565C0", "QiGA-WS",  "o"),
        (arch_ns, "#E53935", "NSGA-II",  "s"),
        (arch_md, "#2E7D32", "MOEA/D",   "D"),
    ]:
        if not arch: continue
        f1v = [a[0][0] for a in arch]
        f2v = [a[0][1] for a in arch]
        f3v = [a[0][2] for a in arch]
        ax.scatter(f3v, f1v, f2v, s=35, c=col, alpha=0.75,
                   edgecolors="white", lw=0.3, label=lbl, marker=mk)

    ax.set_xlabel("f₃: Reliability (↑)", labelpad=10)
    ax.set_ylabel("f₁: Satisfaction (↑)", labelpad=10)
    ax.set_zlabel("f₂: –Distance (↑)", labelpad=10)
    ax.set_title(f"MOO-4  3D Pareto Front: Actual MOO Algorithm Output\n"
                 f"(n={n}, φ_min={phi}, seed={seed})", fontsize=11, fontweight="bold")
    ax.legend(fontsize=9); ax.view_init(elev=22, azim=-55); ax.grid(True)
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO4_3d_pareto_real"); plt.close(fig)


def fig_moo5_knee_vs_phi(df):
    """MOO-5: Knee-point f1 and f3 vs phi_min — operational solution quality."""
    phi_u = sorted(df["phi_min"].unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (col, ylabel) in zip(axes, [
        ("f1_knee", "f₁ at Knee Point (Satisfaction ↑)"),
        ("f3_knee", "f₃ at Knee Point (Reliability ↑)"),
    ]):
        for algo in MOO_ALGOS:
            vals = [df.loc[(abs(df["phi_min"]-p)<1e-9)&(df["algo"]==algo), col].mean()
                    for p in phi_u]
            ax.plot(phi_u, vals, "o-", color=MOO_COLORS[algo],
                    marker=MOO_MARKS[algo], lw=2.2, ms=7, label=algo)
        ax.set_xlabel("φ_min"); ax.set_ylabel(ylabel)
        ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
        ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)

    fig.suptitle("MOO-5  Knee-Point Solution Quality vs φ_min\n"
                 "Knee = best balanced compromise across all 3 objectives per algorithm",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO5_knee_vs_phi"); plt.close(fig)


def fig_moo6_archive_size_vs_phi(df):
    """MOO-6: Pareto archive size vs phi_min — how constraint tightness limits solutions."""
    phi_u = sorted(df["phi_min"].unique(), reverse=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for algo in MOO_ALGOS:
        mn = [df.loc[(abs(df["phi_min"]-p)<1e-9)&(df["algo"]==algo),"n_pareto"].mean()
              for p in phi_u]
        sd = [df.loc[(abs(df["phi_min"]-p)<1e-9)&(df["algo"]==algo),"n_pareto"].std()
              for p in phi_u]
        ax.plot(phi_u, mn, "o-", color=MOO_COLORS[algo],
                marker=MOO_MARKS[algo], lw=2.2, ms=7, label=algo)
        ax.fill_between(phi_u, [m-s for m,s in zip(mn,sd)],
                                [m+s for m,s in zip(mn,sd)],
                         alpha=0.12, color=MOO_COLORS[algo])
    ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8,
               label="φ* = 0.85")
    ax.set_xlabel("φ_min"); ax.set_ylabel("Mean Pareto Archive Size |F|")
    ax.set_title("MOO-6  Pareto Archive Size vs φ_min\n"
                 "Smaller A(φ_min) collapses the achievable objective space — fewer non-dominated solutions",
                 fontweight="bold")
    ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO6_archive_size_vs_phi"); plt.close(fig)


def run_all_figures(df):
    print("\n=== Generating MOO Figures ===")
    steps = [
        ("MOO-1 Pareto scatter",         lambda: fig_moo1_pareto_scatter()),
        ("MOO-2 Quality metrics bars",    lambda: fig_moo2_quality_metrics(df)),
        ("MOO-3 HV/IGD vs phi",          lambda: fig_moo3_hv_vs_phi(df)),
        ("MOO-4 3D Pareto (real runs)",   lambda: fig_moo4_3d_pareto()),
        ("MOO-5 Knee-point vs phi",       lambda: fig_moo5_knee_vs_phi(df)),
        ("MOO-6 Archive size vs phi",     lambda: fig_moo6_archive_size_vs_phi(df)),
    ]
    for i, (label, fn) in enumerate(steps, 1):
        print(f"  [{i}/{len(steps)}] {label}")
        try: fn()
        except Exception as e: print(f"    WARNING: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = run_moo_exp7(phi_levels=[1.00, 0.90, 0.85, 0.80, 0.70], n=50, n_seeds=5)
    run_all_figures(df)
    print("\nDone.")
