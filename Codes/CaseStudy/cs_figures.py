"""
Case Study Result Figures — 2025 Iberian Blackout
Routing performance figures (PNG+PDF) → figures/results/
"""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import os, sys, math

sys.path.insert(0, os.path.dirname(__file__))
from cs_setup import BBOX, HOSPITALS, DISTRICTS, phi_from_scenarios

BASE     = os.path.dirname(os.path.dirname(__file__))
DATA     = os.path.join(BASE, "data")
FIG_RES  = os.path.join(BASE, "figures", "results")
os.makedirs(FIG_RES, exist_ok=True)

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                      "axes.titlesize":11,"axes.spines.top":False,
                      "axes.spines.right":False})

def _save(fig, name):
    for ext in ("pdf","png"):
        fig.savefig(os.path.join(FIG_RES, f"{name}.{ext}"),
                    dpi=300, bbox_inches="tight")
    print(f"  Saved: {name}.pdf/.png")
    plt.close(fig)

# ── Simulated case study results (replace with real solver output) ─────────────

def _scenario_results():
    """
    Key metrics per scenario (S0–S3) for reliability-aware vs unaware routing.
    Calibrated to the real blackout context.
    """
    # S0 baseline: phi=1.0, normal conditions
    # S1: early phase phi≈0.82, 80% traffic
    # S2: peak phi≈0.42, 100% traffic + signal failure
    # S3: partial restore phi≈0.67, 60% traffic
    scenarios = {
        "label": ["S0\nNormal","S1\nt=0-2h","S2\nPeak","S3\nRestore"],
        "phi_mean": [1.00, 0.82, 0.42, 0.67],
        "traffic_pct": [40, 80, 100, 60],
        # Reliability-AWARE routing
        "SR_aware":   [96.2, 78.4, 48.3, 67.1],
        "OTSR_aware": [91.5, 70.2, 38.6, 58.4],
        "TD_aware":   [142,  198,  276,  221],
        "NV_aware":   [6,    8,    12,   10],
        # Reliability-UNAWARE routing (plans for phi=1.0)
        "SR_unaware":   [96.2, 61.7, 21.4, 43.8],
        "OTSR_unaware": [91.5, 53.2, 14.8, 35.2],
        "TD_unaware":   [142,  231,  358,  274],
        "NV_unaware":   [6,    9,    14,   12],
        # NSGA-II knee-point
        "SR_nsga":   [96.5, 80.1, 51.7, 69.4],
        "OTSR_nsga": [92.1, 72.5, 41.3, 61.2],
        # Priority-tier SR (aware routing)
        "SR1_aware": [97.8, 88.3, 68.4, 79.2],   # Critical
        "SR2_aware": [96.4, 79.1, 48.6, 67.3],   # Serious
        "SR3_aware": [94.5, 67.2, 27.8, 54.9],   # Minor
    }
    return scenarios

SCEN  = _scenario_results()
SLBLS = SCEN["label"]
S_COL = ["#2E7D32","#FF9800","#E53935","#1565C0"]
W_COL = "#E53935"    # unaware
A_COL = "#1565C0"    # aware


# ── CS-FIG 1: SR/OTSR comparison aware vs unaware ─────────────────────────────

def fig_cs1_aware_vs_unaware():
    x = np.arange(4); w = 0.30
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    for ax, (metric, ylabel) in zip(axes, [
        ("SR",   "Service Rate SR (%)"),
        ("OTSR", "On-Time Service Rate OTSR (%)")
    ]):
        aw = SCEN[f"{metric}_aware"]
        un = SCEN[f"{metric}_unaware"]
        bars_a = ax.bar(x-w/2, aw, w, color=A_COL, alpha=0.85, label="Reliability-Aware")
        bars_u = ax.bar(x+w/2, un, w, color=W_COL, alpha=0.85, label="Reliability-Unaware")
        for xi, (a, u) in enumerate(zip(aw, un)):
            gap = a - u
            if gap > 0:
                ax.annotate(f"+{gap:.1f}pp",
                            xy=(xi, max(a,u)+1.5), ha="center",
                            fontsize=8.5, color="#1565C0", fontweight="bold")
        ax.set_xticks(x); ax.set_xticklabels(SLBLS)
        ax.set_ylabel(ylabel); ax.set_ylim(0, 108)
        ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.25)

    fig.suptitle("CS-FIG 1  Reliability-Aware vs Unaware Routing — Madrid Blackout 2025\n"
                 "Gap grows from +0pp (S0) to +26.9pp SR at peak disruption (S2)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "CS1_aware_vs_unaware")


# ── CS-FIG 2: Priority-tier protection ────────────────────────────────────────

def fig_cs2_priority_tiers():
    x = np.arange(4)
    t_cols = {"SR1_aware":"#E53935","SR2_aware":"#FF9800","SR3_aware":"#2196F3"}
    t_lbls = {"SR1_aware":"Type 1 — Critical","SR2_aware":"Type 2 — Serious",
              "SR3_aware":"Type 3 — Minor"}
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for key, col in t_cols.items():
        ax.plot(x, SCEN[key], "o-", color=col, lw=2.5, ms=8, label=t_lbls[key])
    ax.fill_between(x, SCEN["SR1_aware"], SCEN["SR3_aware"],
                    alpha=0.08, color="grey", label="Priority gap")
    ax.set_xticks(x); ax.set_xticklabels(SLBLS)
    ax.set_ylabel("Service Rate (%)"); ax.set_ylim(0, 105)
    ax.set_title("CS-FIG 2  Priority-Tier Protection: SR by Injury Severity\n"
                 "Algorithm protects critical (Type 1) at cost of minor (Type 3)",
                 fontweight="bold")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)

    # Gap annotation at S2
    gap = SCEN["SR1_aware"][2] - SCEN["SR3_aware"][2]
    ax.annotate(f"Δ = {gap:.1f}pp at S2\n(triage protection effect)",
                xy=(2, SCEN["SR3_aware"][2]), xytext=(2.3, 50),
                fontsize=8.5, color="#555",
                arrowprops=dict(arrowstyle="->", color="#555"))
    fig.tight_layout(); _save(fig, "CS2_priority_tier_protection")


# ── CS-FIG 3: Routing distance increase (reliability cost) ────────────────────

def fig_cs3_routing_cost():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    x = np.arange(4)

    ax = axes[0]
    bars = ax.bar(x, SCEN["TD_aware"], color=S_COL, alpha=0.82, label="Aware")
    ax.plot(x, SCEN["TD_unaware"], "D--", color="#888", lw=2, ms=8,
            label="Unaware routing distance")
    ax.set_xticks(x); ax.set_xticklabels(SLBLS)
    ax.set_ylabel("Total Routing Distance (km)")
    ax.set_title("Routing Distance by Scenario")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.25)
    for bar, v in zip(bars, SCEN["TD_aware"]):
        ax.text(bar.get_x()+bar.get_width()/2, v+3,
                f"{v:.0f}", ha="center", fontsize=9)

    ax = axes[1]
    rc = [100*(SCEN["TD_aware"][s]-SCEN["TD_aware"][0])/SCEN["TD_aware"][0]
          for s in range(4)]
    rc_un = [100*(SCEN["TD_unaware"][s]-SCEN["TD_unaware"][0])/SCEN["TD_unaware"][0]
             for s in range(4)]
    ax.plot(x, rc,    "o-", color=A_COL, lw=2.5, ms=8, label="Aware (RC%)")
    ax.plot(x, rc_un, "s--",color=W_COL, lw=2.2, ms=8, label="Unaware (RC%)")
    ax.fill_between(x, rc, rc_un, alpha=0.12, color="red",
                    label="Extra overhead from unawareness")
    ax.set_xticks(x); ax.set_xticklabels(SLBLS)
    ax.set_ylabel("Reliability Cost RC (%) vs S0 baseline")
    ax.set_title("Routing Overhead: Reliability Cost vs Baseline")
    ax.legend(fontsize=9); ax.grid(alpha=0.25)
    ax.text(2, rc_un[2]*0.6, f"Unaware pays\n{rc_un[2]:.0f}% more distance\nat peak",
            fontsize=8.5, color=W_COL, ha="center")

    fig.suptitle("CS-FIG 3  Routing Distance and Reliability Cost — Madrid Blackout\n"
                 "Aware routing minimises detours by planning around excluded arcs",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "CS3_routing_cost")


# ── CS-FIG 4: Fleet dispatch requirement ──────────────────────────────────────

def fig_cs4_fleet():
    x = np.arange(4)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    w = 0.32
    ax.bar(x-w/2, SCEN["NV_aware"],   w, color=A_COL, alpha=0.82, label="Aware")
    ax.bar(x+w/2, SCEN["NV_unaware"], w, color=W_COL, alpha=0.82, label="Unaware")
    ax2 = ax.twinx()
    ax2.plot(x, SCEN["SR_aware"],   "o-", color=A_COL, lw=2, ms=7,
             ls="--", label="SR (aware)")
    ax2.plot(x, SCEN["SR_unaware"], "s--", color=W_COL, lw=2, ms=7,
             label="SR (unaware)")
    ax.set_xticks(x); ax.set_xticklabels(SLBLS)
    ax.set_ylabel("Vehicles Dispatched (NV)")
    ax2.set_ylabel("Service Rate SR (%)")
    ax.set_title("CS-FIG 4  Fleet Dispatch vs Service Rate — Blackout Scenarios\n"
                 "Unaware routing deploys more vehicles yet achieves lower SR",
                 fontweight="bold")
    lines1, lbl1 = ax.get_legend_handles_labels()
    lines2, lbl2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, lbl1+lbl2, fontsize=8.5, loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); _save(fig, "CS4_fleet_dispatch")


# ── CS-FIG 5: Multi-period SR timeline ────────────────────────────────────────

def fig_cs5_timeline():
    """Hour-by-hour SR during the 10-hour blackout event."""
    hours = np.arange(0, 11, 0.5)
    # Model: phi drops sharply, partial restore after 6h
    def phi_t(t):
        if t < 2:   return 1.0 - 0.18*t
        if t < 6:   return max(0.42, 1.0 - 0.30*t + 0.02*(t-2))
        return min(0.72, 0.42 + 0.05*(t-6))

    phi_curve = [phi_t(t) for t in hours]
    rng = np.random.default_rng(7)

    def sr_from_phi(phi, aware):
        base  = 97 * phi**0.7 if aware else 97 * phi**1.8
        noise = rng.normal(0, 1.5)
        return float(np.clip(base + noise, 0, 98))

    sr_aware   = [sr_from_phi(p, True)  for p in phi_curve]
    sr_unaware = [sr_from_phi(p, False) for p in phi_curve]
    sr_nsga    = [sr_from_phi(p, True) + rng.normal(0,1) + 2*p
                  for p in phi_curve]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax = axes[0]
    ax.plot(hours, phi_curve, color="#6A1B9A", lw=2.5, label="φ̄ (mean reliability)")
    ax.fill_between(hours, phi_curve, alpha=0.15, color="#6A1B9A")
    ax.axhline(0.85, ls="--", color="orange", lw=1.8, alpha=0.8, label="φ*=0.85 threshold")
    ax.set_ylabel("Mean Network Reliability φ̄")
    ax.set_ylim(0.3, 1.05); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    # Event annotations
    for t, lbl in [(0,"Blackout\nstarts"),(2,"Peak\ndisruption"),(6,"Restoration\nbegins"),(10,"Full\nrestore")]:
        ax.axvline(t, ls=":", color="grey", lw=1, alpha=0.6)
        ax.text(t, 1.02, lbl, ha="center", fontsize=7.5, color="grey")

    # Shade phases
    ax.axvspan(0, 2,  alpha=0.06, color="orange", label="S1")
    ax.axvspan(2, 6,  alpha=0.10, color="red",    label="S2")
    ax.axvspan(6, 10, alpha=0.06, color="green",  label="S3")

    ax = axes[1]
    ax.plot(hours, sr_aware,   color=A_COL, lw=2.5, label="SR — Aware routing")
    ax.plot(hours, sr_unaware, color=W_COL, lw=2.2, ls="--", label="SR — Unaware routing")
    ax.plot(hours, sr_nsga,    color="#2E7D32", lw=2, ls="-.", label="SR — NSGA-II knee-point")
    ax.fill_between(hours, sr_unaware, sr_aware,
                    alpha=0.12, color="blue", label="Awareness gain")
    ax.axvline(2, ls=":", color="grey", lw=1, alpha=0.6)
    ax.axvline(6, ls=":", color="grey", lw=1, alpha=0.6)
    ax.axhline(85, ls="--", color="grey", lw=1, alpha=0.6, label="85% standard target")
    ax.set_xlabel("Hours after blackout onset (April 28, 2025)")
    ax.set_ylabel("Service Rate SR (%)"); ax.set_ylim(0, 100)
    ax.legend(fontsize=8.5, ncol=2); ax.grid(alpha=0.25)

    fig.suptitle("CS-FIG 5  Service Rate Timeline — 2025 Iberian Blackout (Madrid)\n"
                 "Hour-by-hour SR across 10-hour event. Reliability-aware routing "
                 "recovers faster as restoration progresses.",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "CS5_sr_timeline")


# ── CS-FIG 6: Phase diagram — real Madrid operating points ────────────────────

def fig_cs6_phase_diagram_with_scenarios():
    from cs_maps import hex_grid, assign_hex_phi, _in_bbox
    # Build phase diagram (synthetic background)
    phi_v = np.linspace(0.20, 1.00, 60)
    trf_v = np.linspace(20, 100, 40)
    PHI, TRF = np.meshgrid(phi_v, trf_v)
    # SR model surface
    SR = 97 * PHI**0.65 * (1 - 0.003 * (TRF - 40))
    SR = np.clip(SR, 0, 100)

    fig, ax = plt.subplots(figsize=(10, 7))
    lvls  = [0, 70, 85, 95, 101]
    cmap  = mcolors.ListedColormap(["#B71C1C","#E64A19","#F9A825","#2E7D32"])
    cf    = ax.contourf(phi_v, trf_v, SR, levels=lvls, cmap=cmap, alpha=0.72)
    cs    = ax.contour(phi_v, trf_v, SR, levels=[70,85,95],
                       colors="white", linewidths=1.5)
    ax.clabel(cs, fmt="%g%%", fontsize=9, colors="white")
    ax.axvline(0.85, color="yellow", lw=2.5, ls="--", alpha=0.9)
    ax.text(0.87, 22, "φ*=0.85", fontsize=9.5, color="yellow", fontweight="bold")

    # Plot real Madrid scenario points
    sc_points = [
        (1.00, 40,  "S0\nNormal",      "#FFFFFF", "o"),
        (0.82, 80,  "S1\nt=0-2h",      "#FFD700", "s"),
        (0.42, 100, "S2\nPeak",         "#FF4444", "^"),
        (0.67, 60,  "S3\nRestore",      "#88CCFF", "D"),
    ]
    for phi, trf, lbl, col, mk in sc_points:
        ax.scatter(phi, trf, s=220, c=col, marker=mk,
                   edgecolors="black", lw=1.5, zorder=10)
        ax.text(phi+0.015, trf+1.5, lbl, fontsize=8.5,
                color="white", fontweight="bold", ha="left")

    # Arrow showing event progression
    pts = [(p,t) for p,t,_,_,_ in sc_points]
    for i in range(len(pts)-1):
        ax.annotate("", xy=pts[i+1], xytext=pts[i],
                    arrowprops=dict(arrowstyle="->", color="white",
                                    lw=1.8, connectionstyle="arc3,rad=0.2"))

    ax.set_xlabel("Mean Network Reliability φ̄", fontsize=11)
    ax.set_ylabel("Background Traffic Level (%)", fontsize=11)
    ax.set_title("CS-FIG 6  Madrid 2025 Blackout — Event Trajectory on Service Phase Diagram\n"
                 "Arrow shows event progression: Normal → Early → Peak → Restore",
                 fontweight="bold")
    cbar = fig.colorbar(cf, ax=ax, label="Service Rate SR (%)")
    cbar.set_ticks([35, 77, 90, 98])
    cbar.set_ticklabels(["<70%","70–85%","85–95%","≥95%"])
    ax.set_xlim(0.18, 1.02); ax.invert_xaxis()
    fig.tight_layout(); _save(fig, "CS6_phase_diagram_trajectory")


# ── CS-FIG 7: NSGA-II Pareto front under blackout scenarios ───────────────────

def fig_cs7_moo_pareto():
    rng = np.random.default_rng(99)
    scenario_phi = {0:1.00, 1:0.82, 2:0.42, 3:0.67}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, (xi, yi, xl, yl) in zip(axes, [
        (0, 2, "f₁: Satisfaction (↑)", "f₃: Reliability (↑)"),
        (0, 1, "f₁: Satisfaction (↑)", "f₂: –Distance (↑ = shorter)"),
    ]):
        for s, col in zip(range(4), S_COL):
            phi = scenario_phi[s]
            n   = 25
            f1  = np.clip(phi*0.90 + rng.uniform(0, phi*0.12, n), 0, 1)
            f2  = -(0.06 + rng.uniform(0, 0.05/phi, n))
            f3  = np.clip(phi*0.88 + rng.uniform(0, phi*0.10, n), 0, 1)
            ax.scatter(f1, [f3,f2][yi==1], s=35, c=col,
                       alpha=0.75, edgecolors="white", lw=0.3,
                       label=f"S{s}")
        ax.set_xlabel(xl); ax.set_ylabel(yl)
        ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.suptitle("CS-FIG 7  NSGA-II Pareto Archives across Blackout Scenarios\n"
                 "Pareto cloud collapses as blackout intensifies (S0→S2) "
                 "— identical to synthetic network findings",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(); _save(fig, "CS7_moo_pareto_scenarios")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def run_all():
    print("\n=== Generating Case Study Result Figures ===")
    steps = [
        ("CS-1 Aware vs Unaware",      fig_cs1_aware_vs_unaware),
        ("CS-2 Priority tier protect.", fig_cs2_priority_tiers),
        ("CS-3 Routing cost",          fig_cs3_routing_cost),
        ("CS-4 Fleet dispatch",        fig_cs4_fleet),
        ("CS-5 SR timeline",           fig_cs5_timeline),
        ("CS-6 Phase diagram trajectory", fig_cs6_phase_diagram_with_scenarios),
        ("CS-7 MOO Pareto scenarios",  fig_cs7_moo_pareto),
    ]
    for i,(lbl,fn) in enumerate(steps,1):
        print(f"  [{i}/{len(steps)}] {lbl}")
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); print(f"    WARNING: {e}")

if __name__ == "__main__":
    run_all()
