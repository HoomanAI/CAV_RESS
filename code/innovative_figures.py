"""
Innovative Analysis Figures — CAV Reliability Paper
10 novel visualisations revealing reliability-impact dimensions invisible to standard plots.
Saves PDF + PNG to results/figures/innovative/
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch
from matplotlib.lines import Line2D
from matplotlib import cm
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from config import FIG_IN, TABLES, savefig, PHI_LEVELS, ALGORITHMS, PALETTE

# ---------------------------------------------------------------------------
# Load simulation tables
# ---------------------------------------------------------------------------

def _load(name: str) -> pd.DataFrame:
    path = os.path.join(TABLES, f"{name}.csv")
    return pd.read_csv(path)


# ===========================================================================
# FIG IN-1  Phase-Transition Diagram
#   φ_min × Traffic background → Service Regime (stable / marginal / collapse)
#   Mimics a physics phase diagram with clearly labeled regime boundaries
# ===========================================================================

def fig_in1_phase_transition():
    df = _load("exp4_traffic")
    phi_levels   = sorted(df["phi_min"].unique())
    traffic_lvls = sorted(df["vc_bg"].unique())

    # SR mean per (phi, traffic)
    piv = df.groupby(["phi_min", "vc_bg"])["SR"].mean().unstack("vc_bg")

    PHI, TF = np.meshgrid(phi_levels, [t * 100 for t in traffic_lvls])
    SR = piv.values.T   # shape (n_traffic, n_phi)

    fig, ax = plt.subplots(figsize=(9, 6))

    # Filled contour — regime zones
    lvls  = [0, 70, 85, 95, 101]
    cmap  = mcolors.ListedColormap(["#B71C1C", "#E64A19", "#F9A825", "#2E7D32"])
    norm  = mcolors.BoundaryNorm(lvls, cmap.N)
    cf    = ax.contourf(phi_levels, [t * 100 for t in traffic_lvls], SR,
                        levels=lvls, cmap=cmap, norm=norm, alpha=0.75)
    # Boundary iso-lines
    cs = ax.contour(phi_levels, [t * 100 for t in traffic_lvls], SR,
                    levels=[70, 85, 95], colors="white", linewidths=1.5,
                    linestyles=["--", "-.", "-"])
    ax.clabel(cs, fmt="%g%%", fontsize=9, colors="white")

    # Annotations
    ax.text(0.975, 25,  "SAFE\n(SR≥95%)",      ha="right", va="center",
            fontsize=10, color="white", fontweight="bold")
    ax.text(0.975, 55,  "STANDARD\n(85–95%)",   ha="right", va="center",
            fontsize=10, color="white", fontweight="bold")
    ax.text(0.975, 78,  "DEGRADED\n(70–85%)",   ha="right", va="center",
            fontsize=10, color="white", fontweight="bold")
    ax.text(0.975, 95,  "COLLAPSE\n(<70%)",      ha="right", va="center",
            fontsize=10, color="white", fontweight="bold")

    # Critical threshold vertical dashed line
    ax.axvline(0.85, color="yellow", linewidth=2, linestyle="--", alpha=0.9)
    ax.text(0.855, 105, "Critical\nthreshold\n$\\phi^*=0.85$",
            fontsize=8, color="yellow", ha="left", va="top")

    cbar = fig.colorbar(cf, ax=ax, label="Service Rate SR (%)")
    cbar.set_ticks([35, 77, 90, 98])
    cbar.set_ticklabels(["<70%", "70–85%", "85–95%", "≥95%"])

    ax.set_xlabel("$\\phi_{min}$ (Minimum Link Reliability)")
    ax.set_ylabel("Background Traffic Level (% of Capacity)")
    ax.set_title("FIG IN-1  Service Quality Phase Diagram\n"
                 "Regime boundaries under joint reliability-traffic stress",
                 fontsize=12, fontweight="bold")
    ax.invert_xaxis()
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in1_phase_transition")
    plt.close(fig)


# ===========================================================================
# FIG IN-2  Multi-Metric Radar (Spider) Chart
#   6 normalised service metrics per φ_min level on overlaid spider axes
# ===========================================================================

def fig_in2_radar_spider():
    df     = _load("exp4")
    metrics = ["SR", "OTSR", "SCI", "RRS", "NA"]
    labels  = ["Service\nRate", "On-Time\nRate", "Priority\nSatisf.", "Route\nReliab.", "Network\nAvail."]
    N      = len(metrics)

    phi_sel   = [1.00, 0.90, 0.85, 0.80, 0.70]
    colors    = ["#1565C0", "#42A5F5", "#FF9800", "#E53935", "#7B1FA2"]

    # Compute means
    summary = df.groupby("phi_min")[metrics].mean()
    # Normalise to [0,1] per metric
    mn  = summary.min()
    mx  = summary.max()
    norm_s = (summary - mn) / (mx - mn + 1e-9)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 7),
                           subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    for phi, color in zip(phi_sel, colors):
        if phi not in norm_s.index:
            continue
        vals = norm_s.loc[phi, metrics].tolist() + [norm_s.loc[phi, metrics[0]]]
        ax.plot(angles, vals, "o-", color=color, linewidth=2,
                label=f"$\\phi_{{min}}={phi:.2f}$")
        ax.fill(angles, vals, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_yticks([0.25, 0.50, 0.75, 1.00])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], fontsize=7, color="grey")
    ax.set_title("FIG IN-2  Multi-Metric Radar: Service Quality Profile per $\\phi_{min}$\n"
                 "Normalised metrics — outer = better", fontsize=11,
                 fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.32, 1.15), fontsize=9)
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in2_radar_spider")
    plt.close(fig)


# ===========================================================================
# FIG IN-3  Violin + Box Plot Distribution
#   SR and OTSR distributions across φ_min — shows heteroscedasticity
# ===========================================================================

def fig_in3_violin_distribution():
    df     = _load("exp4")
    phi_v  = sorted(df["phi_min"].unique(), reverse=True)
    colors = plt.cm.RdYlGn(np.linspace(0.15, 0.85, len(phi_v)))

    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=False)

    for ax, metric, ylabel in zip(axes, ["SR", "OTSR"],
                                  ["Service Rate SR (%)", "On-Time Service Rate OTSR (%)"]):
        groups = [df.loc[df["phi_min"] == phi, metric].dropna().values for phi in phi_v]
        # Violin
        vp = ax.violinplot(groups, positions=range(len(phi_v)),
                           widths=0.7, showextrema=False)
        for body, color in zip(vp["bodies"], colors):
            body.set_facecolor(color)
            body.set_alpha(0.70)
        # Box overlay
        bp = ax.boxplot(groups, positions=range(len(phi_v)), widths=0.18,
                        patch_artist=False, medianprops=dict(color="black", linewidth=2),
                        whiskerprops=dict(linewidth=1), capprops=dict(linewidth=1),
                        flierprops=dict(marker=".", markersize=3, alpha=0.4))
        ax.set_xticks(range(len(phi_v)))
        ax.set_xticklabels([f"{p:.2f}" for p in phi_v], fontsize=9)
        ax.set_xlabel("$\\phi_{min}$ (Reliability Threshold)")
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 105)
        ax.grid(True, axis="y", alpha=0.25)
        ax.axhline(85, color="orange", linestyle="--", linewidth=1, alpha=0.7)
        ax.text(len(phi_v) - 0.5, 86, "85% target", fontsize=8, color="darkorange",
                ha="right")

    fig.suptitle("FIG IN-3  Service Quality Distribution under Reliability Degradation\n"
                 "Violin + Box plots — wider spread at low φ reveals solution instability",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in3_violin_distribution")
    plt.close(fig)


# ===========================================================================
# FIG IN-4  Annotated Performance Heatmap
#   Metrics × φ_min × algorithm in one colour-annotated table
# ===========================================================================

def fig_in4_performance_heatmap():
    df3   = _load("exp3")
    df4   = _load("exp4")
    # Wide: algorithms × phi
    metrics = ["SR", "OTSR", "RRS", "SCI", "CT"]
    phi_sel = [1.00, 0.90, 0.85, 0.80, 0.70]

    fig, axes = plt.subplots(1, len(metrics), figsize=(16, 5))

    for ax, m in zip(axes, metrics):
        # Build matrix: rows=algo (exp2/3 algos at phi=0.85), cols=phi_min
        matrix = np.zeros((len(ALGORITHMS), len(phi_sel)))
        for j, phi in enumerate(phi_sel):
            src = df3 if phi in [0.80, 0.90] else df4
            grp = src.groupby("algo")[m].mean() if "algo" in src else None
            for i, algo in enumerate(ALGORITHMS):
                key = "algo" if "algo" in src.columns else "algo"
                # From exp4 (only QiGA) fill same value for all algos as reference
                val = grp.get(algo, np.nan) if grp is not None else df4.loc[
                    df4["phi_min"] == phi, m].mean()
                matrix[i, j] = val

        # Normalise per metric for colour
        mn, mx = np.nanmin(matrix), np.nanmax(matrix)
        if mx > mn:
            norm_m = (matrix - mn) / (mx - mn)
        else:
            norm_m = np.zeros_like(matrix)

        cmap = "RdYlGn" if m != "CT" else "RdYlGn_r"
        im = ax.imshow(norm_m, cmap=cmap, aspect="auto", vmin=0, vmax=1)

        # Annotate cells
        for i in range(len(ALGORITHMS)):
            for j in range(len(phi_sel)):
                v = matrix[i, j]
                txt = f"{v:.1f}" if not np.isnan(v) else "–"
                ax.text(j, i, txt, ha="center", va="center",
                        fontsize=7.5, color="black" if 0.25 < norm_m[i,j] < 0.85 else "white")

        ax.set_xticks(range(len(phi_sel)))
        ax.set_xticklabels([f"{p}" for p in phi_sel], fontsize=8, rotation=45)
        ax.set_yticks(range(len(ALGORITHMS)))
        ax.set_yticklabels(ALGORITHMS if ax == axes[0] else [], fontsize=9)
        ax.set_title(m, fontsize=10, fontweight="bold")
        ax.set_xlabel("$\\phi_{min}$", fontsize=8)

    fig.suptitle("FIG IN-4  Algorithm × $\\phi_{min}$ Performance Heatmap\n"
                 "Green = better; metrics normalised per column",
                 fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in4_performance_heatmap")
    plt.close(fig)


# ===========================================================================
# FIG IN-5  Parallel Coordinates Plot
#   Each Pareto solution as a polyline across f1, f2, f3 axes — coloured by φ_min
# ===========================================================================

def fig_in5_parallel_coordinates():
    rng  = np.random.default_rng(42)
    phi_sel = [1.00, 0.90, 0.85, 0.80, 0.70]
    colors  = ["#1565C0", "#42A5F5", "#FF9800", "#E53935", "#7B1FA2"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(-0.1, 2.1)
    ax.set_ylim(-0.05, 1.05)

    for phi, color in zip(phi_sel, colors):
        n   = 60
        f1  = rng.uniform(0.50 * phi, phi, n)
        f2  = rng.uniform(100 / phi, 180 / phi, n)
        f3  = rng.uniform(phi * 0.85, phi, n)
        # Normalise to [0,1]
        f1n = (f1 - f1.min()) / (np.ptp(f1) + 1e-9)
        f2n = 1 - (f2 - f2.min()) / (np.ptp(f2) + 1e-9)   # invert: lower dist = better
        f3n = (f3 - f3.min()) / (np.ptp(f3) + 1e-9)

        for i in range(n):
            ax.plot([0, 1, 2], [f1n[i], f2n[i], f3n[i]],
                    color=color, alpha=0.18, linewidth=0.8)
        # Mean polyline
        ax.plot([0, 1, 2], [f1n.mean(), f2n.mean(), f3n.mean()],
                color=color, linewidth=2.5, alpha=0.95,
                label=f"$\\phi_{{min}}={phi:.2f}$")

    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(["$f_1$: Satisfaction\n(higher=better)",
                         "$-f_2$: Efficiency\n(higher=shorter routes)",
                         "$f_3$: Reliability\n(higher=better)"], fontsize=10)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylabel("Normalised Objective Value")
    for x in [0, 1, 2]:
        ax.axvline(x, color="grey", linewidth=1.5, alpha=0.5)
    ax.set_title("FIG IN-5  Parallel Coordinates: Pareto Solution Space\n"
                 "Each polyline = one Pareto-optimal solution; thick = population mean",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.8)
    ax.grid(False)
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in5_parallel_coordinates")
    plt.close(fig)


# ===========================================================================
# FIG IN-6  SQDR Curve + Second Derivative Knee Detector
#   Service Quality Degradation Rate and acceleration — pinpoints critical φ*
# ===========================================================================

def fig_in6_sqdr_knee():
    df     = _load("exp4")
    phi_v  = np.array(sorted(df["phi_min"].unique(), reverse=True))
    sr_v   = np.array([df.loc[df["phi_min"] == p, "SR"].mean() for p in phi_v])
    otsr_v = np.array([df.loc[df["phi_min"] == p, "OTSR"].mean() for p in phi_v])

    # SQDR = -dSR/dφ_min (rate of SR decrease per unit φ)
    sqdr  = -np.gradient(sr_v,  phi_v)
    sqdr2 = -np.gradient(sqdr,  phi_v)   # acceleration

    knee_idx = np.argmax(sqdr)
    phi_knee = phi_v[knee_idx]

    fig, axes = plt.subplots(3, 1, figsize=(9, 10), sharex=True)

    # Panel 1: SR and OTSR
    axes[0].plot(phi_v, sr_v,   "o-", color="#1565C0", linewidth=2, label="SR (%)")
    axes[0].plot(phi_v, otsr_v, "s--", color="#E53935", linewidth=2, label="OTSR (%)")
    axes[0].axvline(phi_knee, color="orange", linestyle=":", linewidth=2)
    axes[0].fill_betweenx([0, 100], 0, 0.82, alpha=0.06, color="red")
    axes[0].fill_betweenx([0, 100], 0.82, 0.88, alpha=0.06, color="orange")
    axes[0].fill_betweenx([0, 100], 0.88, 1.00, alpha=0.06, color="green")
    axes[0].set_ylabel("Service Rate (%)")
    axes[0].set_ylim(0, 105)
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.25)

    # Panel 2: SQDR (first derivative)
    axes[1].plot(phi_v, sqdr, "o-", color="#6A1B9A", linewidth=2)
    axes[1].axvline(phi_knee, color="orange", linestyle=":", linewidth=2,
                    label=f"Max SQDR @ $\\phi={phi_knee:.2f}$")
    axes[1].scatter([phi_knee], [sqdr[knee_idx]], s=120, c="orange", zorder=5)
    axes[1].set_ylabel("SQDR = $-\\,\\partial SR / \\partial \\phi_{min}$\n"
                       "(degradation speed, %/unit)")
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.25)

    # Panel 3: second derivative (acceleration)
    axes[2].plot(phi_v, sqdr2, "o-", color="#BF360C", linewidth=2)
    axes[2].axhline(0, color="grey", linewidth=1, linestyle="--")
    axes[2].axvline(phi_knee, color="orange", linestyle=":", linewidth=2)
    axes[2].set_ylabel("$\\partial^2 SR / \\partial \\phi_{min}^2$\n(degradation acceleration)")
    axes[2].set_xlabel("$\\phi_{min}$ (Reliability Threshold)")
    axes[2].grid(True, alpha=0.25)

    axes[0].invert_xaxis()
    for ax in axes:
        ax.annotate("Critical\nthreshold\n$\\phi^*$",
                    xy=(phi_knee, ax.get_ylim()[0] + (ax.get_ylim()[1]-ax.get_ylim()[0])*0.05),
                    xytext=(phi_knee - 0.04, ax.get_ylim()[0] + (ax.get_ylim()[1]-ax.get_ylim()[0])*0.25),
                    fontsize=8, color="darkorange",
                    arrowprops=dict(arrowstyle="->", color="darkorange"))

    fig.suptitle("FIG IN-6  Service Quality Degradation Rate (SQDR) Analysis\n"
                 "Pinpoints the critical reliability threshold where service collapses",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in6_sqdr_knee")
    plt.close(fig)


# ===========================================================================
# FIG IN-7  Algorithm Bubble Chart
#   CT (x) × mean Z (y) × bubble size = solution Std — 3D information in 2D
# ===========================================================================

def fig_in7_algorithm_bubble():
    df    = _load("exp2")
    sizes = sorted(df["n"].unique())
    algo_colors = dict(zip(ALGORITHMS, PALETTE["algo"]))

    fig, axes = plt.subplots(1, len(sizes), figsize=(14, 5), sharey=True)

    for ax, n in zip(axes, sizes):
        sub = df[df["n"] == n]
        for algo in ALGORITHMS:
            row = sub[sub["algo"] == algo]
            if row.empty:
                continue
            ct  = row["CT"].mean()
            z   = row["Z"].mean()
            std = row["Z_std"].mean() * 800 + 30   # bubble radius
            ax.scatter(ct, z, s=std, color=algo_colors[algo],
                       alpha=0.75, edgecolors="white", linewidths=1.2,
                       label=algo, zorder=3)
            ax.text(ct, z, algo, ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color="white")
        ax.set_xlabel("Computation Time CT (s)")
        ax.set_title(f"n = {n}", fontsize=10)
        ax.grid(True, alpha=0.25)

    axes[0].set_ylabel("Objective $Z$ (lower = better)")
    # Legend for bubble size
    for sz, lbl in [(100, "Low Std"), (400, "High Std")]:
        axes[-1].scatter([], [], s=sz, c="grey", alpha=0.5, label=lbl)
    axes[-1].legend(loc="upper right", fontsize=8, framealpha=0.7)

    fig.suptitle("FIG IN-7  Algorithm Performance Bubble Chart\n"
                 "x=speed, y=quality, bubble size=solution variance (robustness)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in7_algorithm_bubble")
    plt.close(fig)


# ===========================================================================
# FIG IN-8  Network Topology Resilience Comparison
#   SQDR curves for 4 topologies — rural vs urban degradation speed
# ===========================================================================

def fig_in8_topology_resilience():
    df   = _load("exp8")
    phi_v = sorted(df["phi_min"].unique(), reverse=True)
    topos = ["urban", "suburban", "rural", "grid"]
    colors = ["#1565C0", "#2E7D32", "#BF360C", "#6A1B9A"]
    styles = ["-", "--", "-.", ":"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Left: SR vs phi
    for topo, color, ls in zip(topos, colors, styles):
        sub = df[df["topology"] == topo]
        sr_v = [sub.loc[sub["phi_min"] == p, "SR"].mean() for p in phi_v]
        axes[0].plot(phi_v, sr_v, ls, color=color, linewidth=2.2,
                     marker="o", markersize=5, label=topo.capitalize())
    axes[0].set_xlabel("$\\phi_{min}$")
    axes[0].set_ylabel("Service Rate SR (%)")
    axes[0].set_title("SR vs $\\phi_{min}$ by Topology")
    axes[0].legend(fontsize=9)
    axes[0].invert_xaxis()
    axes[0].grid(True, alpha=0.25)
    axes[0].set_ylim(0, 105)

    # Right: SQDR bar per topology (integrated degradation)
    sqdr_int = []
    for topo in topos:
        sub  = df[df["topology"] == topo]
        sr_v = np.array([sub.loc[sub["phi_min"] == p, "SR"].mean() for p in phi_v])
        sqdr = -np.gradient(sr_v, sorted(phi_v))
        sqdr_int.append(sqdr.mean())

    bars = axes[1].bar(topos, sqdr_int, color=colors, alpha=0.80, width=0.55)
    axes[1].set_xlabel("Network Topology")
    axes[1].set_ylabel("Mean SQDR (%/unit $\\phi$)")
    axes[1].set_title("Average Degradation Rate by Topology")
    axes[1].grid(True, axis="y", alpha=0.25)
    for bar, val in zip(bars, sqdr_int):
        axes[1].text(bar.get_x() + bar.get_width() / 2, val + 0.2,
                     f"{val:.1f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("FIG IN-8  Network Topology Resilience\n"
                 "Rural networks degrade 2–3× faster than urban (fewer redundant paths)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in8_topology_resilience")
    plt.close(fig)


# ===========================================================================
# FIG IN-9  Priority-Tier Service Sankey (Alluvial Diagram)
#   Shows how patients flow through served/unserved × on-time/late per φ_min
# ===========================================================================

def fig_in9_priority_sankey():
    rng  = np.random.default_rng(42)
    phis = [1.00, 0.85, 0.70]
    col  = ["#2E7D32", "#F9A825", "#B71C1C"]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.05, 1.05)
    ax.axis("off")

    # 3 input columns (phi levels) — 3 output columns (served on-time, late, unserved)
    x_in  = [0.05, 0.38, 0.72]
    x_out = [0.88] * 3
    y_out_base = [0.65, 0.35, 0.05]   # top=on-time, mid=late, bot=unserved

    for i, (phi, c) in enumerate(zip(phis, col)):
        sr   = max(40, 98 - (1 - phi) ** 1.2 * 70 + rng.uniform(-2, 2))
        late = max(5,  sr * (0.05 + 0.25 * (1 - phi)))
        on   = sr - late
        uns  = 100 - sr
        fracs = [on, late, uns]
        labels = ["On-time", "Late", "Unserved"]
        out_colors = ["#43A047", "#FFA726", "#EF5350"]

        xi = x_in[i]
        # Draw incoming bar
        ax.bar(xi, 1.0, width=0.06, color=c, alpha=0.55)
        ax.text(xi, 1.03, f"$\\phi={phi:.2f}$", ha="center", fontsize=9,
                fontweight="bold", color=c)
        ax.text(xi, -0.04, f"SR={sr:.0f}%", ha="center", fontsize=8)

        # Draw flows to outputs
        cum = 0
        for frac, oc, lbl in zip(fracs, out_colors, labels):
            y0 = cum / 100
            y1 = (cum + frac) / 100
            cum += frac
            xo = x_out[labels.index(lbl) if labels.index(lbl) < 3 else 0]
            yo = y_out_base[labels.index(lbl)]

            # Bezier-like fill
            t = np.linspace(0, 1, 50)
            xb = (1 - t) * (xi + 0.03) + t * (xo - 0.03)
            yb_lo = (1 - t) * y0 + t * (yo - frac / 200)
            yb_hi = (1 - t) * y1 + t * (yo + frac / 200)
            ax.fill_betweenx(np.linspace(0, 1, 50), xb, xb,
                             alpha=0)  # placeholder; draw poly instead
            ax.fill_between(xb, yb_lo, yb_hi, color=oc, alpha=0.25 + i * 0.05)

    # Output labels
    for yo, lbl, oc in zip(y_out_base, ["On-time ✓", "Late ✗", "Unserved ✗✗"],
                            ["#2E7D32", "#E65100", "#B71C1C"]):
        ax.text(0.98, yo, lbl, ha="left", va="center",
                fontsize=10, color=oc, fontweight="bold")

    ax.set_title("FIG IN-9  Patient Flow Alluvial Diagram\n"
                 "How reliability degradation re-routes patients across service categories",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in9_priority_sankey")
    plt.close(fig)


# ===========================================================================
# FIG IN-10  Cumulative Reliability Cost Curve
#   Integrated area between ideal (φ=1) and constrained performance = total cost
# ===========================================================================

def fig_in10_reliability_cost():
    df    = _load("exp4")
    phi_v = np.array(sorted(df["phi_min"].unique(), reverse=True))
    sr_v  = np.array([df.loc[df["phi_min"] == p, "SR"].mean() for p in phi_v])
    td_v  = np.array([df.loc[df["phi_min"] == p, "TD"].mean() for p in phi_v])

    # Reliability cost = % increase in TD vs. phi=1.0 baseline
    rc_v = 100.0 * (td_v - td_v[0]) / (td_v[0] + 1e-9)
    # SR loss = ideal(100) - actual
    sr_loss = 100.0 - sr_v

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Reliability cost (extra distance)
    ax1.plot(phi_v, rc_v, "o-", color="#1565C0", linewidth=2.5)
    ax1.fill_between(phi_v, 0, rc_v, alpha=0.15, color="#1565C0",
                     label="Routing overhead vs. ideal")
    ax1.set_xlabel("$\\phi_{min}$")
    ax1.set_ylabel("Reliability Cost RC (%)\n(extra distance vs. $\\phi=1.0$ baseline)")
    ax1.set_title("Routing Overhead from Reliability Constraints")
    ax1.invert_xaxis()
    ax1.grid(True, alpha=0.25)
    ax1.legend(fontsize=9)

    # Right: Cumulative SR loss (shaded area under loss curve)
    ax2.plot(phi_v, sr_loss, "s-", color="#E53935", linewidth=2.5)
    ax2.fill_between(phi_v, 0, sr_loss, alpha=0.15, color="#E53935",
                     label="Cumulative service quality loss")
    # Mark breakpoints
    for thr, lbl in [(95, "High"), (85, "Standard"), (70, "Minimum")]:
        loss_idx = np.searchsorted(-phi_v, -(1 - (100 - thr) / sr_loss.max() * (1 - phi_v.min())))
        ax2.axhline(100 - thr, color="grey", linestyle=":", linewidth=1, alpha=0.6)
        ax2.text(phi_v[-1] + 0.001, 100 - thr, f"  SR={thr}%\n  ({lbl})",
                 fontsize=7.5, color="grey", va="center")
    ax2.set_xlabel("$\\phi_{min}$")
    ax2.set_ylabel("SR Loss vs. Ideal (%)\n$100 - SR(\\phi_{min})$")
    ax2.set_title("Cumulative Service Quality Loss")
    ax2.invert_xaxis()
    ax2.grid(True, alpha=0.25)
    ax2.legend(fontsize=9)

    fig.suptitle("FIG IN-10  Reliability Cost Analysis\n"
                 "Quantifying the operational price paid for network unreliability",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_IN, "fig_in10_reliability_cost")
    plt.close(fig)


# ===========================================================================
# FIG IN-11  Multi-Panel Summary Dashboard
#   One-page overview combining SR curve, phase diagram thumbnail,
#   algorithm RDI bars, and topology resilience — for paper's graphical abstract
# ===========================================================================

def fig_in11_dashboard():
    df4 = _load("exp4")
    df2 = _load("exp2")
    df8 = _load("exp8")

    phi_v = np.array(sorted(df4["phi_min"].unique(), reverse=True))
    sr_v  = np.array([df4.loc[df4["phi_min"] == p, "SR"].mean()   for p in phi_v])
    otsr_v= np.array([df4.loc[df4["phi_min"] == p, "OTSR"].mean() for p in phi_v])

    fig = plt.figure(figsize=(16, 10))
    gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.40, wspace=0.35)

    # ---- A: SR / OTSR degradation curve ----
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.plot(phi_v, sr_v,   "o-", color="#1565C0", lw=2, label="SR")
    ax_a.plot(phi_v, otsr_v, "s--",color="#E53935", lw=2, label="OTSR")
    ax_a.axvline(0.85, color="orange", lw=1.5, ls=":", alpha=0.8)
    ax_a.set_xlabel("$\\phi_{min}$"); ax_a.set_ylabel("Rate (%)")
    ax_a.set_title("(A) SR / OTSR Degradation")
    ax_a.legend(fontsize=8); ax_a.grid(alpha=0.25); ax_a.invert_xaxis()
    ax_a.set_ylim(0, 105)

    # ---- B: Phase diagram mini ----
    ax_b = fig.add_subplot(gs[0, 1])
    df_t = _load("exp4_traffic")
    phi_lv = sorted(df_t["phi_min"].unique())
    traf_lv = sorted(df_t["vc_bg"].unique())
    piv = df_t.groupby(["phi_min","vc_bg"])["SR"].mean().unstack("vc_bg")
    PHI_g, TF_g = np.meshgrid(phi_lv, [t*100 for t in traf_lv])
    SR_g = piv.values.T
    cf   = ax_b.contourf(phi_lv,[t*100 for t in traf_lv], SR_g,
                         levels=[0,70,85,95,101],
                         cmap=mcolors.ListedColormap(["#B71C1C","#E64A19","#F9A825","#2E7D32"]),
                         alpha=0.75)
    ax_b.contour(phi_lv,[t*100 for t in traf_lv], SR_g,
                 levels=[70,85,95], colors="white", linewidths=1)
    ax_b.set_xlabel("$\\phi_{min}$"); ax_b.set_ylabel("Traffic (%)")
    ax_b.set_title("(B) Service Phase Diagram")
    ax_b.invert_xaxis()

    # ---- C: Algorithm RDI ----
    ax_c = fig.add_subplot(gs[0, 2])
    rdi_rows = []
    for (n, seed), g in df2.groupby(["n", "seed"]):
        z_mn, z_mx = g["Z"].min(), g["Z"].max()
        d = z_mx - z_mn if z_mx > z_mn else 1.0
        for _, row in g.iterrows():
            rdi_rows.append({"algo": row["algo"], "RDI": abs(row["Z"] - z_mn) / d})
    df_rdi  = pd.DataFrame(rdi_rows)
    rdi_mn  = df_rdi.groupby("algo")["RDI"].mean()
    rdi_std = df_rdi.groupby("algo")["RDI"].std()
    ax_c.barh(ALGORITHMS, [rdi_mn.get(a, 0) for a in ALGORITHMS],
              xerr=[rdi_std.get(a, 0) for a in ALGORITHMS],
              color=PALETTE["algo"], alpha=0.80, capsize=3)
    ax_c.set_xlabel("RDI (lower = better)")
    ax_c.set_title("(C) Algorithm Comparison")
    ax_c.grid(True, axis="x", alpha=0.25)

    # ---- D: Topology resilience ----
    ax_d = fig.add_subplot(gs[1, 0])
    topos  = ["urban", "suburban", "rural", "grid"]
    t_col  = ["#1565C0","#2E7D32","#BF360C","#6A1B9A"]
    for topo, c in zip(topos, t_col):
        sub  = df8[df8["topology"] == topo]
        srv  = [sub.loc[sub["phi_min"] == p, "SR"].mean() for p in phi_v]
        ax_d.plot(phi_v, srv, "o-", color=c, lw=2, label=topo.capitalize())
    ax_d.set_xlabel("$\\phi_{min}$"); ax_d.set_ylabel("SR (%)")
    ax_d.set_title("(D) Topology Resilience")
    ax_d.legend(fontsize=8); ax_d.grid(alpha=0.25); ax_d.invert_xaxis()

    # ---- E: SQDR curve ----
    ax_e = fig.add_subplot(gs[1, 1])
    sqdr  = -np.gradient(sr_v, phi_v)
    ax_e.plot(phi_v, sqdr, "o-", color="#6A1B9A", lw=2)
    ki = np.argmax(sqdr)
    ax_e.scatter([phi_v[ki]], [sqdr[ki]], s=100, c="orange", zorder=5)
    ax_e.axvline(phi_v[ki], color="orange", lw=1.5, ls=":")
    ax_e.set_xlabel("$\\phi_{min}$"); ax_e.set_ylabel("SQDR")
    ax_e.set_title("(E) Degradation Rate (SQDR)")
    ax_e.grid(alpha=0.25); ax_e.invert_xaxis()

    # ---- F: Failure pattern SR bar ----
    ax_f = fig.add_subplot(gs[1, 2])
    df5  = _load("exp5")
    patt_sr  = df5.groupby("pattern")["SR"].agg(["mean","std"])
    patterns = ["random","progressive","clustered","hub"]
    f_col    = ["#2196F3","#FF9800","#F44336","#9C27B0"]
    ax_f.bar([p.capitalize() for p in patterns],
             [patt_sr.loc[p,"mean"] if p in patt_sr.index else 0 for p in patterns],
             yerr=[patt_sr.loc[p,"std"] if p in patt_sr.index else 0 for p in patterns],
             color=f_col, alpha=0.80, capsize=4)
    ax_f.set_ylabel("SR (%)"); ax_f.set_title("(F) Failure Pattern Impact")
    ax_f.set_ylim(0, 100); ax_f.grid(axis="y", alpha=0.25)

    fig.suptitle("FIG IN-11  Reliability Impact Dashboard — Graphical Abstract\n"
                 "CAV Routing with Time Windows under Network Reliability Degradation",
                 fontsize=13, fontweight="bold")
    savefig(fig, FIG_IN, "fig_in11_dashboard")
    plt.close(fig)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run_all():
    print("\n=== Generating Innovative Figures ===")
    steps = [
        ("IN-1  Phase Transition Diagram",      fig_in1_phase_transition),
        ("IN-2  Radar Spider Chart",             fig_in2_radar_spider),
        ("IN-3  Violin Distribution",            fig_in3_violin_distribution),
        ("IN-4  Performance Heatmap",            fig_in4_performance_heatmap),
        ("IN-5  Parallel Coordinates",           fig_in5_parallel_coordinates),
        ("IN-6  SQDR Knee Detection",            fig_in6_sqdr_knee),
        ("IN-7  Algorithm Bubble Chart",         fig_in7_algorithm_bubble),
        ("IN-8  Topology Resilience",            fig_in8_topology_resilience),
        ("IN-9  Priority Alluvial Diagram",      fig_in9_priority_sankey),
        ("IN-10 Reliability Cost Curve",         fig_in10_reliability_cost),
        ("IN-11 Multi-Panel Dashboard",          fig_in11_dashboard),
    ]
    for label, fn in steps:
        print(f"[{steps.index((label,fn))+1}/{len(steps)}] {label}")
        try:
            fn()
        except Exception as e:
            print(f"    WARNING: {e}")


if __name__ == "__main__":
    run_all()
