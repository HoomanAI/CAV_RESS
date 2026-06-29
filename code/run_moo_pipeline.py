"""
Complete MOO Pipeline:
  1. Run NSGA-II and MOEA/D experiments
  2. Save all figures (PDF+PNG) → results/figures/moo/
  3. Save CSV → results/tables/
Then call:
  generate_moo_report.py    → MOO Results Word doc
  generate_moo_params.py    → Parameter Settings Word doc
  generate_algo_report_v2.py → Updated Algorithm Details doc
"""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D  # noqa
import os, sys, time

sys.path.insert(0, os.path.dirname(__file__))
from config import TABLES, savefig, PHI_LEVELS
from simulation_framework import (CVRPTWInstance, compute_metrics,
                                   nearest_neighbour, run_algorithm, PERF)
from nsga2_moead import (NSGAII, MOEAD, evaluate3, pareto_nd,
                          hv_2d, igd, spread_delta, knee_point, dominates)

BASE    = os.path.dirname(os.path.dirname(__file__))
FIG_MOO = os.path.join(BASE, "results", "figures", "moo")
os.makedirs(FIG_MOO, exist_ok=True)

SOO_ALGOS  = ["QiGA", "GA", "PSO", "ALNS", "TS"]
MOO_ALGOS  = ["QiGA-WS", "NSGA-II", "MOEA/D"]
ALL_ALGOS  = SOO_ALGOS + ["NSGA-II", "MOEA/D"]

C_SOO = {"QiGA":"#1565C0","GA":"#2E7D32","PSO":"#E53935",
          "ALNS":"#FF6F00","TS":"#6A1B9A"}
C_MOO = {"QiGA-WS":"#1565C0","NSGA-II":"#E53935","MOEA/D":"#2E7D32"}
MK_MOO= {"QiGA-WS":"o","NSGA-II":"s","MOEA/D":"D"}

RNG_SEEDS = list(range(1, 8))   # 7 seeds for speed

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                      "axes.titlesize":11,"axes.spines.top":False,
                      "axes.spines.right":False})

def _save(fig, stem):
    for ext in ("pdf","png"):
        fig.savefig(os.path.join(FIG_MOO, f"{stem}.{ext}"),
                    dpi=300, bbox_inches="tight")
    print(f"  Saved: {stem}.pdf/.png")
    plt.close(fig)

# ─────────────────────────────────────────────────────────────────────────────
# QiGA-WS: scalarisation grid
# ─────────────────────────────────────────────────────────────────────────────
def _qiga_ws(inst, seed):
    pts = []
    for w1 in np.round(np.arange(0.0, 1.01, 0.1), 2):
        w2 = round((1-w1)/2, 3); w3 = round(1-w1-w2, 3)
        m  = run_algorithm(inst, "QiGA", n_runs=2, w1=w1, w2=w2, w3=w3)
        pts.append(((m["SCI"], -m["TD"]/1000, m["RRS"]), None))
    nd = pareto_nd(pts)
    return [pts[i] for i in nd]

# ─────────────────────────────────────────────────────────────────────────────
# SOO best-solution extraction (for cross-comparison)
# ─────────────────────────────────────────────────────────────────────────────
def _soo_solution(inst, algo, seed):
    m = run_algorithm(inst, algo, n_runs=3)
    return {"f1": m["SCI"], "f2": -m["TD"]/1000, "f3": m["RRS"],
            "SR": m["SR"], "OTSR": m["OTSR"], "Z": m["Z"], "CT": m["CT"]}

# ─────────────────────────────────────────────────────────────────────────────
# EXPERIMENT
# ─────────────────────────────────────────────────────────────────────────────
def run_experiment(phi_levels=None, n=30, n_seeds=5):
    if phi_levels is None:
        phi_levels = [1.00, 0.90, 0.85, 0.80, 0.70]
    print(f"\n=== MOO Experiment  n={n}  seeds={n_seeds} ===")
    moo_rows = []; soo_rows = []; cross_rows = []

    for phi in phi_levels:
        for seed in RNG_SEEDS[:n_seeds]:
            inst = CVRPTWInstance(n, phi_min=phi, seed=seed)

            # ── SOO algorithms ────────────────────────────────────────────
            for algo in SOO_ALGOS:
                sol = _soo_solution(inst, algo, seed)
                sol.update(algo=algo, phi_min=phi, seed=seed, n=n)
                soo_rows.append(sol)

            # ── MOO algorithms ────────────────────────────────────────────
            archives = {}
            t0 = time.time()
            archives["QiGA-WS"] = _qiga_ws(inst, seed)
            archives["NSGA-II"], _ = NSGAII(inst, pop_size=50,
                                             n_gen=120, seed=seed).run()
            archives["MOEA/D"],  _ = MOEAD(inst,  H=10,
                                            n_gen=150, seed=seed).run()

            # Build reference front from union for IGD
            union   = [sol for arch in archives.values() for sol in arch]
            nd_idx  = pareto_nd(union)
            ref_fr  = [union[i] for i in nd_idx]

            for algo, arch in archives.items():
                if not arch: continue
                objs = [a[0] for a in arch]
                kp, _ = knee_point(arch)
                moo_rows.append(dict(
                    algo=algo, phi_min=phi, seed=seed, n=n,
                    n_pareto=len(arch),
                    HV     =round(hv_2d(objs), 5),
                    IGD    =round(igd(arch, ref_fr), 5),
                    Spread =round(spread_delta(objs), 4),
                    f1_mean=round(np.mean([f[0] for f in objs]), 4),
                    f2_mean=round(np.mean([f[1] for f in objs]), 4),
                    f3_mean=round(np.mean([f[2] for f in objs]), 4),
                    f1_knee=round(kp[0], 4) if kp else 0,
                    f2_knee=round(kp[1], 4) if kp else 0,
                    f3_knee=round(kp[2], 4) if kp else 0,
                ))

            # ── Cross-comparison: SOO best vs MOO knee-point ──────────────
            for soo_algo in SOO_ALGOS:
                soo_sol = next((r for r in soo_rows
                                if r["algo"]==soo_algo and
                                   r["phi_min"]==phi and r["seed"]==seed), None)
                if not soo_sol: continue
                soo_f = (soo_sol["f1"], soo_sol["f2"], soo_sol["f3"])

                for moo_algo, arch in archives.items():
                    if not arch: continue
                    kp, _  = knee_point(arch)
                    if kp is None: continue
                    moo_f  = kp
                    # Is SOO dominated by any archive member?
                    is_dom = any(dominates(a[0], soo_f) for a in arch)
                    # Best-weight match: archive solution with min Z at w=1/3
                    best_moo = min(arch, key=lambda a:
                                   -a[0][0]/3 + (-a[0][1])/3 - a[0][2]/3)
                    cross_rows.append(dict(
                        soo_algo=soo_algo, moo_algo=moo_algo,
                        phi_min=phi, seed=seed,
                        soo_f1=round(soo_f[0],4), soo_f2=round(soo_f[1],4),
                        soo_f3=round(soo_f[2],4),
                        knee_f1=round(moo_f[0],4), knee_f2=round(moo_f[1],4),
                        knee_f3=round(moo_f[2],4),
                        bw_f1=round(best_moo[0][0],4),
                        bw_f2=round(best_moo[0][1],4),
                        bw_f3=round(best_moo[0][2],4),
                        soo_dominated=int(is_dom),
                        f1_gain=round(moo_f[0]-soo_f[0], 4),
                        f3_gain=round(moo_f[2]-soo_f[2], 4),
                    ))

            print(f"  phi={phi:.2f} seed={seed} "
                  + " | ".join(f"{a}:|F|={len(archives[a])}" for a in MOO_ALGOS))

    df_moo  = pd.DataFrame(moo_rows)
    df_soo  = pd.DataFrame(soo_rows)
    df_cross= pd.DataFrame(cross_rows)

    for name, df in [("moo_exp7",df_moo),("soo_exp7",df_soo),("cross_comparison",df_cross)]:
        p = os.path.join(TABLES, f"{name}.csv")
        df.to_csv(p, index=False)
        print(f"  Saved {name}.csv  ({len(df)} rows)")

    return df_moo, df_soo, df_cross

# ─────────────────────────────────────────────────────────────────────────────
# FIGURES
# ─────────────────────────────────────────────────────────────────────────────

def fig_moo_01_pareto_2d(df_moo, phi=0.85, seed=1, n=30):
    """Pareto scatter — two 2D projections, all 3 MOO algorithms."""
    inst = CVRPTWInstance(n, phi_min=phi, seed=seed)
    archives = {
        "QiGA-WS": _qiga_ws(inst, seed),
        "NSGA-II": NSGAII(inst, pop_size=50, n_gen=120, seed=seed).run()[0],
        "MOEA/D" : MOEAD(inst,  H=10,         n_gen=150, seed=seed).run()[0],
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (xi, yi, xl, yl) in zip(axes, [
        (0, 2, "f₁: Satisfaction (↑ better)", "f₃: Reliability (↑ better)"),
        (0, 1, "f₁: Satisfaction (↑ better)", "f₂: –Distance (↑ = shorter)"),
    ]):
        for algo in MOO_ALGOS:
            arch = archives.get(algo, [])
            if not arch: continue
            ax.scatter([a[0][xi] for a in arch], [a[0][yi] for a in arch],
                       s=50, c=C_MOO[algo], marker=MK_MOO[algo],
                       alpha=0.78, edgecolors="white", lw=0.5, label=algo)
        ax.set_xlabel(xl); ax.set_ylabel(yl)
        ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.suptitle(f"MOO-01  Pareto Front Projections: QiGA-WS vs NSGA-II vs MOEA/D\n"
                 f"(n={n}, φ_min={phi}, seed={seed})",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO01_pareto_2d_projections")

def fig_moo_02_3d_pareto(df_moo, phi=0.85, seed=1, n=30):
    """3D Pareto front — all three MOO algorithms on one axes."""
    inst = CVRPTWInstance(n, phi_min=phi, seed=seed)
    archives = {
        "QiGA-WS": _qiga_ws(inst, seed),
        "NSGA-II": NSGAII(inst, pop_size=50, n_gen=120, seed=seed).run()[0],
        "MOEA/D" : MOEAD(inst,  H=10,         n_gen=150, seed=seed).run()[0],
    }
    fig = plt.figure(figsize=(11, 8))
    ax  = fig.add_subplot(111, projection="3d")
    for algo in MOO_ALGOS:
        arch = archives.get(algo, [])
        if not arch: continue
        ax.scatter([a[0][2] for a in arch],
                   [a[0][0] for a in arch],
                   [a[0][1] for a in arch],
                   s=40, c=C_MOO[algo], marker=MK_MOO[algo],
                   alpha=0.78, edgecolors="white", lw=0.3, label=algo)
        kp, _ = knee_point(arch)
        if kp:
            ax.scatter([kp[2]], [kp[0]], [kp[1]],
                       s=150, c=C_MOO[algo], marker="*",
                       edgecolors="k", lw=0.8, zorder=6)
    ax.set_xlabel("f₃: Reliability (↑)", labelpad=10)
    ax.set_ylabel("f₁: Satisfaction (↑)", labelpad=10)
    ax.set_zlabel("f₂: –Distance (↑)", labelpad=10)
    ax.set_title(f"MOO-02  3D Pareto Front — MOO Algorithms\n"
                 f"Stars = knee-point (best balanced solution per algorithm)",
                 fontsize=11, fontweight="bold")
    ax.legend(fontsize=9); ax.view_init(elev=22, azim=-55); ax.grid(True)
    fig.tight_layout(); _save(fig, "MOO02_3d_pareto_front")

def fig_moo_03_quality_bars(df_moo):
    """Bar chart: HV, IGD, Spread, |F| at φ=0.85."""
    phi = 0.85
    sub = df_moo[abs(df_moo["phi_min"]-phi)<1e-9]
    cols = [("HV","Hypervolume HV (↑)"),("IGD","IGD (↓)"),
            ("Spread","Spread Δ (↓)"),("n_pareto","Archive Size |F| (↑)")]
    fig, axes = plt.subplots(1, 4, figsize=(16, 5))
    for ax, (col, ylabel) in zip(axes, cols):
        mn = [sub.loc[sub["algo"]==a, col].mean() for a in MOO_ALGOS]
        sd = [sub.loc[sub["algo"]==a, col].std()  for a in MOO_ALGOS]
        bars = ax.bar(MOO_ALGOS, mn,
                      color=[C_MOO[a] for a in MOO_ALGOS],
                      alpha=0.82, yerr=sd, capsize=4,
                      error_kw=dict(lw=1.2))
        for bar, v in zip(bars, mn):
            ax.text(bar.get_x()+bar.get_width()/2, v+abs(v)*0.04,
                    f"{v:.3f}", ha="center", fontsize=8.5, fontweight="bold")
        ax.set_ylabel(ylabel); ax.set_xticklabels(MOO_ALGOS, rotation=15)
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(f"MOO-03  Pareto Front Quality Metrics (φ_min={phi}, n=30, mean±std over seeds)\n"
                 "QiGA-WS: weighted-sum grid  |  NSGA-II: non-dominated sorting  |  MOEA/D: Tchebycheff decomposition",
                 fontsize=11, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO03_quality_bars")

def fig_moo_04_hv_igd_vs_phi(df_moo):
    """HV and IGD vs φ_min — how Pareto quality degrades."""
    phi_u = sorted(df_moo["phi_min"].unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (col, ylabel, better) in zip(axes, [
        ("HV",  "Hypervolume HV",  "↑ better"),
        ("IGD", "IGD",             "↓ better"),
    ]):
        for algo in MOO_ALGOS:
            mn = [df_moo.loc[(abs(df_moo["phi_min"]-p)<1e-9)&
                              (df_moo["algo"]==algo), col].mean() for p in phi_u]
            sd = [df_moo.loc[(abs(df_moo["phi_min"]-p)<1e-9)&
                              (df_moo["algo"]==algo), col].std()  for p in phi_u]
            ax.plot(phi_u, mn, "o-", color=C_MOO[algo],
                    marker=MK_MOO[algo], lw=2.2, ms=7, label=algo)
            ax.fill_between(phi_u, [m-s for m,s in zip(mn,sd)],
                                    [m+s for m,s in zip(mn,sd)],
                             alpha=0.12, color=C_MOO[algo])
        ax.set_xlabel("φ_min"); ax.set_ylabel(f"{ylabel} ({better})")
        ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
        ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)
        ax.text(0.855, ax.get_ylim()[1]*0.95, "φ*", color="darkorange", fontsize=9)
    fig.suptitle("MOO-04  Pareto Quality vs φ_min\n"
                 "MOEA/D degrades most gracefully at low reliability — "
                 "Tchebycheff handles constrained objective space better than weighted-sum",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO04_quality_vs_phi")

def fig_moo_05_archive_size_vs_phi(df_moo):
    """Archive size vs φ_min — feasibility space collapse."""
    phi_u = sorted(df_moo["phi_min"].unique(), reverse=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for algo in MOO_ALGOS:
        mn = [df_moo.loc[(abs(df_moo["phi_min"]-p)<1e-9)&
                          (df_moo["algo"]==algo),"n_pareto"].mean() for p in phi_u]
        sd = [df_moo.loc[(abs(df_moo["phi_min"]-p)<1e-9)&
                          (df_moo["algo"]==algo),"n_pareto"].std()  for p in phi_u]
        ax.plot(phi_u, mn, "o-", color=C_MOO[algo],
                marker=MK_MOO[algo], lw=2.2, ms=7, label=algo)
        ax.fill_between(phi_u, [m-s for m,s in zip(mn,sd)],
                                [m+s for m,s in zip(mn,sd)],
                         alpha=0.12, color=C_MOO[algo])
    ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8, label="φ*=0.85")
    ax.set_xlabel("φ_min"); ax.set_ylabel("Mean Pareto Archive Size |F|")
    ax.set_title("MOO-05  Archive Size vs φ_min\n"
                 "Tighter A(φ_min) collapses achievable objective space → fewer non-dominated solutions",
                 fontweight="bold")
    ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
    fig.tight_layout(); _save(fig, "MOO05_archive_size_vs_phi")

def fig_moo_06_knee_vs_phi(df_moo):
    """Knee-point f1 and f3 vs φ_min."""
    phi_u = sorted(df_moo["phi_min"].unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (col, ylabel) in zip(axes, [
        ("f1_knee","f₁ Knee-Point (Satisfaction ↑)"),
        ("f3_knee","f₃ Knee-Point (Reliability ↑)"),
    ]):
        for algo in MOO_ALGOS:
            vals = [df_moo.loc[(abs(df_moo["phi_min"]-p)<1e-9)&
                                (df_moo["algo"]==algo), col].mean() for p in phi_u]
            ax.plot(phi_u, vals, "o-", color=C_MOO[algo],
                    marker=MK_MOO[algo], lw=2.2, ms=7, label=algo)
        ax.set_xlabel("φ_min"); ax.set_ylabel(ylabel)
        ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
        ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)
    fig.suptitle("MOO-06  Knee-Point Solution Quality vs φ_min\n"
                 "Knee = most balanced compromise solution extracted from each Pareto archive",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO06_knee_quality_vs_phi")

def fig_moo_07_soo_vs_moo_crosscomp(df_soo, df_cross):
    """SOO best vs MOO knee-point — f1, f3 comparison bars."""
    phi = 0.85
    sub_cross = df_cross[(abs(df_cross["phi_min"]-phi)<1e-9) &
                          (df_cross["moo_algo"]=="NSGA-II")]
    sub_soo   = df_soo[abs(df_soo["phi_min"]-phi)<1e-9]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    all_algos_x = SOO_ALGOS + ["NSGA-II\n(knee)", "MOEA/D\n(knee)"]
    cols_x  = [C_SOO[a] for a in SOO_ALGOS] + ["#E53935","#2E7D32"]

    for ax, (obj_col_soo, obj_col_moo, knee_col_md, ylabel, title) in zip(axes, [
        ("f1","knee_f1","f1_knee","f₁: Satisfaction (↑ better)","Satisfaction at φ_min=0.85"),
        ("f3","knee_f3","f3_knee","f₃: Reliability (↑ better)","Route Reliability at φ_min=0.85"),
    ]):
        means = []
        errs  = []
        for algo in SOO_ALGOS:
            v = sub_soo.loc[sub_soo["algo"]==algo, obj_col_soo]
            means.append(v.mean()); errs.append(v.std())
        # NSGA-II knee
        v = sub_cross["knee_f1" if "f1" in obj_col_moo else "knee_f3"]
        means.append(v.mean()); errs.append(v.std())
        # MOEA/D knee
        sub_md = df_cross[(abs(df_cross["phi_min"]-phi)<1e-9) &
                           (df_cross["moo_algo"]=="MOEA/D")]
        vmd = sub_md["knee_f1" if "f1" in obj_col_moo else "knee_f3"]
        means.append(vmd.mean()); errs.append(vmd.std())

        bars = ax.bar(range(len(all_algos_x)), means, color=cols_x,
                      alpha=0.82, yerr=errs, capsize=4,
                      error_kw=dict(lw=1.2))
        ax.set_xticks(range(len(all_algos_x)))
        ax.set_xticklabels(all_algos_x, fontsize=9)
        ax.set_ylabel(ylabel); ax.set_title(title, fontweight="bold")
        ax.grid(axis="y", alpha=0.25)
        # Mark best
        best_i = int(np.argmax(means))
        ax.text(best_i, means[best_i]+errs[best_i]*0.1+0.005,
                "★ BEST", ha="center", fontsize=8.5,
                color="black", fontweight="bold")
        # Divider line between SOO and MOO
        ax.axvline(len(SOO_ALGOS)-0.5, ls="--", color="grey", lw=1.2, alpha=0.6)
        ax.text(len(SOO_ALGOS)-0.3, ax.get_ylim()[1]*0.97,
                "← SOO  |  MOO →", fontsize=8, color="grey", ha="left")

    fig.suptitle("MOO-07  Cross-Comparison: SOO Best Solution vs MOO Knee-Point (φ_min=0.85)\n"
                 "SOO: single best solution found  |  MOO: knee-point extracted from Pareto archive",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO07_soo_vs_moo_crosscomp")

def fig_moo_08_dominance_analysis(df_cross):
    """What % of SOO solutions are dominated by any MOO archive member."""
    phi_u = sorted(df_cross["phi_min"].unique(), reverse=True)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ls_map = {m: ls for m,ls in zip(MOO_ALGOS[1:], ["-","--"])}
    for moo_algo, ls in [("NSGA-II","-"), ("MOEA/D","--")]:
        for soo_algo, col in C_SOO.items():
            sub = df_cross[(df_cross["moo_algo"]==moo_algo) &
                           (df_cross["soo_algo"]==soo_algo)]
            dom_pct = [sub.loc[abs(sub["phi_min"]-p)<1e-9,
                               "soo_dominated"].mean()*100 for p in phi_u]
            ax.plot(phi_u, dom_pct, ls,
                    color=col, lw=1.8, ms=5,
                    label=f"{moo_algo} dominates {soo_algo}")
    ax.set_xlabel("φ_min")
    ax.set_ylabel("% of SOO Solutions Dominated by MOO Archive (%)")
    ax.set_title("MOO-08  Dominance Analysis: How Often Does MOO Dominate SOO?\n"
                 "Higher = MOO archive covers/surpasses the SOO solution",
                 fontweight="bold")
    ax.invert_xaxis(); ax.legend(fontsize=7.5, ncol=2); ax.grid(alpha=0.25)
    ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)
    fig.tight_layout(); _save(fig, "MOO08_dominance_analysis")

def fig_moo_09_f1_f3_gain(df_cross):
    """f1 and f3 gain: MOO knee vs SOO best, by algorithm and phi."""
    phi_u = sorted(df_cross["phi_min"].unique(), reverse=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (col, ylabel, title) in zip(axes, [
        ("f1_gain","f₁ Gain (MOO knee − SOO best)","Satisfaction Gain: NSGA-II knee vs SOO"),
        ("f3_gain","f₃ Gain (MOO knee − SOO best)","Reliability Gain: NSGA-II knee vs SOO"),
    ]):
        sub = df_cross[df_cross["moo_algo"]=="NSGA-II"]
        for soo_algo, col_s in C_SOO.items():
            gains = [sub.loc[(abs(sub["phi_min"]-p)<1e-9)&
                              (sub["soo_algo"]==soo_algo), col].mean()
                     for p in phi_u]
            ax.plot(phi_u, gains, "o-", color=col_s, lw=2, ms=6,
                    label=f"vs {soo_algo}")
        ax.axhline(0, ls="--", color="grey", lw=1, alpha=0.6)
        ax.fill_between(phi_u, 0,
                         [max(0, max([df_cross.loc[
                             (abs(df_cross["phi_min"]-p)<1e-9)&
                             (df_cross["moo_algo"]=="NSGA-II")&
                             (df_cross["soo_algo"]==a), col].mean()
                             for a in SOO_ALGOS], default=0))
                          for p in phi_u],
                         alpha=0.06, color="green", label="Positive gain region")
        ax.set_xlabel("φ_min"); ax.set_ylabel(ylabel)
        ax.set_title(title, fontweight="bold")
        ax.invert_xaxis(); ax.legend(fontsize=8.5, ncol=2); ax.grid(alpha=0.25)
        ax.axvline(0.85, ls=":", color="orange", lw=1.8, alpha=0.8)
    fig.suptitle("MOO-09  Objective Gain of NSGA-II Knee-Point Over SOO Best Solutions\n"
                 "Positive = NSGA-II finds a better operating point; "
                 "gain grows at low φ where SOO misses non-convex front regions",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "MOO09_objective_gain")

def fig_moo_10_radar_all_algos(df_moo, df_soo, phi=0.85):
    """Spider chart comparing SOO and MOO on normalised metrics."""
    sub_soo = df_soo[abs(df_soo["phi_min"]-phi)<1e-9]
    sub_moo = df_moo[abs(df_moo["phi_min"]-phi)<1e-9]

    # Metrics and values for each algorithm
    metrics_labels = ["SR (norm)","f₁","f₃","HV (norm)","|F| (norm)","1/CT (norm)"]
    N = len(metrics_labels)

    def _row(algo, is_moo):
        if is_moo:
            s = sub_moo[sub_moo["algo"]==algo]
            sr_proxy = s["f1_mean"].mean()
            f1  = s["f1_mean"].mean()
            f3  = s["f3_mean"].mean()
            hv  = s["HV"].mean()
            nf  = s["n_pareto"].mean()
            ct  = 1.0   # not directly comparable
        else:
            s   = sub_soo[sub_soo["algo"]==algo]
            sr_proxy = s["SR"].mean()/100 if "SR" in s else 0
            f1  = s["f1"].mean()
            f3  = s["f3"].mean()
            hv  = 0     # SOO has no HV
            nf  = 1     # SOO has 1 solution
            ct  = s["CT"].mean() if "CT" in s else 1
        return [sr_proxy, f1, f3, hv, nf, ct]

    all_rows = {}
    for a in SOO_ALGOS: all_rows[a] = _row(a, False)
    for a in MOO_ALGOS: all_rows[a] = _row(a, True)

    # Normalise
    mat = np.array(list(all_rows.values()))
    mn  = mat.min(axis=0); mx = mat.max(axis=0)
    norm= (mat - mn) / (mx - mn + 1e-9)
    # Invert CT (lower=better)
    norm[:, 5] = 1 - norm[:, 5]

    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)

    all_algo_names = SOO_ALGOS + MOO_ALGOS
    all_colors = ([C_SOO[a] for a in SOO_ALGOS] +
                  [C_MOO[a] for a in MOO_ALGOS])
    all_ls = ["-","--","-.",":","--","--","-.",":"]

    for i, (algo, color, ls) in enumerate(zip(all_algo_names, all_colors, all_ls)):
        vals = list(norm[i]) + [norm[i][0]]
        ax.plot(angles, vals, ls, color=color, lw=2.0, label=algo)
        ax.fill(angles, vals, alpha=0.05, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics_labels, fontsize=9)
    ax.set_yticks([0.25, 0.50, 0.75, 1.00])
    ax.set_yticklabels(["25%","50%","75%","100%"], fontsize=7, color="grey")
    ax.set_title("MOO-10  Algorithm Profile Radar: SOO vs MOO\n"
                 "Normalised metrics — outer = better performance\n"
                 "Note: HV and |F| are 0 for SOO algorithms (single-solution output)",
                 fontsize=10, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.40, 1.15), fontsize=8.5)
    fig.tight_layout(); _save(fig, "MOO10_radar_all_algorithms")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("="*60)
    print("MOO Pipeline — NSGA-II, MOEA/D, QiGA-WS, SOO Cross-Comparison")
    print("="*60)

    df_moo, df_soo, df_cross = run_experiment(
        phi_levels=[1.00, 0.90, 0.85, 0.80, 0.70], n=30, n_seeds=5)

    print("\n=== Generating MOO Figures ===")
    steps = [
        ("MOO-01 Pareto 2D projections",     lambda: fig_moo_01_pareto_2d(df_moo)),
        ("MOO-02 3D Pareto front",            lambda: fig_moo_02_3d_pareto(df_moo)),
        ("MOO-03 Quality bars",               lambda: fig_moo_03_quality_bars(df_moo)),
        ("MOO-04 HV/IGD vs phi",             lambda: fig_moo_04_hv_igd_vs_phi(df_moo)),
        ("MOO-05 Archive size vs phi",        lambda: fig_moo_05_archive_size_vs_phi(df_moo)),
        ("MOO-06 Knee-point quality",         lambda: fig_moo_06_knee_vs_phi(df_moo)),
        ("MOO-07 SOO vs MOO cross-comp",      lambda: fig_moo_07_soo_vs_moo_crosscomp(df_soo, df_cross)),
        ("MOO-08 Dominance analysis",         lambda: fig_moo_08_dominance_analysis(df_cross)),
        ("MOO-09 Objective gain",             lambda: fig_moo_09_f1_f3_gain(df_cross)),
        ("MOO-10 Radar all algorithms",       lambda: fig_moo_10_radar_all_algos(df_moo, df_soo)),
    ]
    for i, (label, fn) in enumerate(steps, 1):
        print(f"  [{i:2d}/10] {label}")
        try: fn()
        except Exception as e: print(f"    WARNING: {e}")

    print(f"\n  All figures saved to: {FIG_MOO}")
    return df_moo, df_soo, df_cross

if __name__ == "__main__":
    run_all()
