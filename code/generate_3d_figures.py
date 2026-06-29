"""
3D Publication Figures — CAV Reliability Paper
Saves PDF + PNG to results/figures/3d/
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.mplot3d import Axes3D          # noqa: F401
from matplotlib import cm
import os, sys

sys.path.insert(0, os.path.dirname(__file__))
from config import FIG_3D, savefig, PHI_LEVELS

COLORS     = ["#1565C0", "#1976D2", "#42A5F5", "#FF9800", "#E53935"]
PHI_LABELS = [f"$\\phi_{{min}}={p:.2f}$" for p in PHI_LEVELS[::2]]   # 5 levels

# ---------------------------------------------------------------------------
# Synthetic data — replace with real simulation output
# ---------------------------------------------------------------------------

def _pareto_data(rng):
    data = {}
    for phi in PHI_LEVELS[::2]:          # 5 phi levels
        n   = 80
        f1  = rng.uniform(0.50 * phi, phi, n)
        f2  = rng.uniform(100 / phi, 180 / phi, n)
        f3  = rng.uniform(phi * 0.85, phi, n)
        pts = np.column_stack([f3, f1, f2])
        dom = np.zeros(n, bool)
        for i in range(n):
            if dom[i]: continue
            for j in range(n):
                if i == j: continue
                if (pts[j,0] >= pts[i,0] and pts[j,1] >= pts[i,1]
                        and pts[j,2] <= pts[i,2]
                        and (pts[j,0] > pts[i,0] or pts[j,1] > pts[i,1]
                             or pts[j,2] < pts[i,2])):
                    dom[i] = True; break
        data[phi] = pts[~dom]
    return data


def _sr_matrix():
    """SR[traffic_row, phi_col] shape (5,7). Replace with Exp-4 traffic results."""
    return np.array([
        [38, 48, 62, 78, 88, 93, 97],
        [30, 42, 55, 72, 83, 91, 96],
        [20, 32, 45, 64, 78, 88, 95],
        [12, 22, 35, 54, 71, 84, 93],
        [ 5, 13, 24, 42, 62, 79, 90],
    ], dtype=float)


def _policy_z(rng):
    phi_vals = np.array([0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00])
    w1_vals  = np.linspace(0.0, 1.0, 20)
    Z = np.zeros((7, 20))
    for i, phi in enumerate(phi_vals):
        for j, w1 in enumerate(w1_vals):
            best_w1  = 0.30 + 0.40 * phi
            flat     = 0.5 + 0.5 * (phi - 0.70) / 0.30
            Z[i, j]  = -phi * (1 - flat * (w1 - best_w1) ** 2
                                + rng.normal(0, 0.008))
    return phi_vals, w1_vals, Z


# ---------------------------------------------------------------------------
# 3D-1  Pareto Front
# ---------------------------------------------------------------------------

def fig_3d1_pareto(rng):
    data = _pareto_data(rng)
    fig  = plt.figure(figsize=(11, 8))
    ax   = fig.add_subplot(111, projection="3d")

    floor_z = min(-data[p][:, 2].max() for p in PHI_LEVELS[::2]) * 1.1

    for phi, color, label in zip(PHI_LEVELS[::2], COLORS, PHI_LABELS):
        pts = data[phi]
        f3, f1, f2 = pts[:,0], pts[:,1], pts[:,2]
        sz = 25 + 25 * (f1 - f1.min()) / (np.ptp(f1) + 1e-9)
        ax.scatter(f3, f1, -f2, c=color, s=sz, alpha=0.75, label=label,
                   edgecolors="white", linewidths=0.3)
        ax.scatter(f3, f1, floor_z, c=color, s=6, alpha=0.15, marker=".")

    # Utopia and knee
    ax.scatter([1.0], [1.0], [-100], marker="*", s=250, c="gold",
               edgecolors="k", linewidths=0.6, zorder=6, label="Utopia")
    knee_phi = min(data.keys(), key=lambda p: abs(p - 0.85))
    p_knee   = data[knee_phi]
    ki  = np.argmax(p_knee[:,1] - 0.01*p_knee[:,2] + p_knee[:,0])
    ax.scatter(*[[p_knee[ki,0]], [p_knee[ki,1]], [-p_knee[ki,2]]],
               marker="D", s=130, c="k", zorder=7, label=f"Knee (phi={knee_phi:.2f})")

    ax.set_xlabel("$f_3$: Route Reliability", labelpad=10)
    ax.set_ylabel("$f_1$: Priority-Weighted Satisfaction", labelpad=10)
    ax.set_zlabel("$-f_2$: Routing Efficiency (−distance)", labelpad=10)
    ax.set_title("3D-1  Pareto-Optimal Surface: $f_1 \\times f_2 \\times f_3$\n"
                 "Impact of $\\phi_{min}$ on MOO Trade-off Surface", pad=12)
    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.7)
    ax.view_init(elev=22, azim=-55)
    fig.tight_layout()
    savefig(fig, FIG_3D, "fig_3d1_pareto_front")
    plt.close(fig)


def fig_3d1_projections(rng):
    data = _pareto_data(rng)
    fig  = plt.figure(figsize=(13, 10))

    ax3d = fig.add_subplot(2, 2, 1, projection="3d")
    for phi, color, label in zip(PHI_LEVELS[::2], COLORS, PHI_LABELS):
        pts = data[phi]
        ax3d.scatter(pts[:,0], pts[:,1], -pts[:,2],
                     c=color, s=18, alpha=0.65, label=label)
    ax3d.set_xlabel("$f_3$", labelpad=5, fontsize=8)
    ax3d.set_ylabel("$f_1$", labelpad=5, fontsize=8)
    ax3d.set_zlabel("$-f_2$", labelpad=5, fontsize=8)
    ax3d.set_title("3D View", fontsize=9)
    ax3d.view_init(elev=22, azim=-55)
    ax3d.tick_params(labelsize=7)

    projs = [
        (fig.add_subplot(2, 2, 2), "$f_3$: Reliability", "$f_1$: Satisfaction", 0, 1, False),
        (fig.add_subplot(2, 2, 3), "$f_1$: Satisfaction", "$-f_2$: Efficiency",  1, 2, True),
        (fig.add_subplot(2, 2, 4), "$f_3$: Reliability",  "$-f_2$: Efficiency",  0, 2, True),
    ]
    for ax2, xl, yl, xi, yi, negy in projs:
        for phi, color, label in zip(PHI_LEVELS[::2], COLORS, PHI_LABELS):
            pts = data[phi]
            xd  = pts[:, xi]
            yd  = -pts[:, yi] if negy else pts[:, yi]
            ax2.scatter(xd, yd, c=color, s=12, alpha=0.65, label=label)
        ax2.set_xlabel(xl, fontsize=8)
        ax2.set_ylabel(yl, fontsize=8)
        ax2.tick_params(labelsize=7)
        ax2.grid(True, alpha=0.25)

    handles, labels = ax3d.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, fontsize=8.5,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("3D-1 Pareto Front + 2D Projections (IEEE supplement panel)", fontsize=11)
    fig.tight_layout()
    savefig(fig, FIG_3D, "fig_3d1_pareto_projections")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3D-2  SR Response Surface
# ---------------------------------------------------------------------------

def fig_3d2_sr_surface():
    phi     = np.array([0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00])
    traffic = np.array([0.20, 0.40, 0.60, 0.80, 1.00])
    SR      = _sr_matrix()
    PHI, TF = np.meshgrid(phi, traffic)

    fig  = plt.figure(figsize=(11, 8))
    ax   = fig.add_subplot(111, projection="3d")
    norm = mcolors.Normalize(vmin=0, vmax=100)
    cmap = cm.RdYlGn
    ax.plot_surface(PHI, TF * 100, SR, facecolors=cmap(norm(SR)),
                    alpha=0.88, linewidth=0.25, edgecolor="grey")
    ax.contourf(PHI, TF * 100, SR, zdir="z", offset=0, cmap="RdYlGn",
                alpha=0.35, levels=[70, 75, 85, 95, 100])

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    fig.colorbar(sm, ax=ax, shrink=0.48, aspect=12, pad=0.08,
                 label="Service Rate SR (%)")
    ax.set_xlabel("$\\phi_{min}$", labelpad=10)
    ax.set_ylabel("Traffic Level (% Capacity)", labelpad=10)
    ax.set_zlabel("Service Rate SR (%)", labelpad=10)
    ax.set_zlim(0, 100)
    ax.set_title("3D-2  SR Response Surface: $\\phi_{min}$ × Traffic Congestion\n"
                 "Non-linear joint degradation — cliff near $\\phi_{min}=0.82$, traffic>60%",
                 pad=12)
    ax.text(0.71, 22, 95, "Safe\nzone", fontsize=8, color="darkgreen")
    ax.text(0.71, 85, 18, "Collapse\ncliff", fontsize=8, color="darkred")
    ax.view_init(elev=28, azim=-55)
    fig.tight_layout()
    savefig(fig, FIG_3D, "fig_3d2_sr_surface")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3D-3  BPR Congestion Surface
# ---------------------------------------------------------------------------

def fig_3d3_bpr_surface():
    phi_v = np.linspace(0.50, 1.00, 60)
    vc_v  = np.linspace(0.00, 1.50, 60)
    PHI, VC = np.meshgrid(phi_v, vc_v)
    Z = np.clip(1 + 0.15 * (VC / PHI) ** 4, 1.0, 4.0)

    fig  = plt.figure(figsize=(11, 8))
    ax   = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(PHI, VC, Z, cmap="coolwarm",
                           alpha=0.90, linewidth=0.20, edgecolor="grey")
    ax.plot_surface(PHI, VC, np.full_like(Z, 1.15), alpha=0.12, color="green")
    ax.plot_surface(PHI, VC, np.full_like(Z, 2.00), alpha=0.08, color="red")
    ax.text(0.52, 1.48, 1.19, "At-capacity ×1.15", fontsize=8, color="darkgreen")
    ax.text(0.52, 1.48, 2.06, "Severe ×2.0",       fontsize=8, color="darkred")
    fig.colorbar(surf, ax=ax, shrink=0.48, aspect=12, pad=0.08,
                 label="Travel Time Multiplier $t_{ij}/t^0_{ij}$")
    ax.set_xlabel("$\\phi_{ij}$  (Link Reliability)", labelpad=10)
    ax.set_ylabel("$V/C^0$  (Volume/Capacity Ratio)", labelpad=10)
    ax.set_zlabel("$t_{ij}/t^0_{ij}$  (Multiplier)", labelpad=10)
    ax.set_title("3D-3  BPR Congestion Surface: $\\phi_{ij}$ × Volume/Capacity\n"
                 "$Z = 1 + 0.15 \\times (V/(C^0\\!\\cdot\\!\\phi))^4$", pad=12)
    ax.view_init(elev=25, azim=-60)
    fig.tight_layout()
    savefig(fig, FIG_3D, "fig_3d3_bpr_surface")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3D-4  Policy Landscape
# ---------------------------------------------------------------------------

def fig_3d4_policy_landscape(rng):
    phi_v, w1_v, Z = _policy_z(rng)
    W1, PHI = np.meshgrid(w1_v, phi_v)

    fig  = plt.figure(figsize=(11, 8))
    ax   = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(W1, PHI, Z, cmap="plasma",
                           alpha=0.88, linewidth=0.20, edgecolor="grey")
    opt_w1 = w1_v[np.argmin(Z, axis=1)]
    ridge  = Z.min(axis=1)
    ax.plot(opt_w1, phi_v, ridge, "w-", linewidth=2.5, label="Optimal $w_1$ ridge")
    ax.scatter(opt_w1, phi_v, ridge, c="white", s=28, zorder=5)
    fig.colorbar(surf, ax=ax, shrink=0.48, aspect=12, pad=0.08,
                 label="$Z^*$ (Optimal Objective)")
    ax.set_xlabel("$w_1$  (Weight on Satisfaction $f_1$)", labelpad=10)
    ax.set_ylabel("$\\phi_{min}$  (Reliability Threshold)", labelpad=10)
    ax.set_zlabel("$Z^*$  (Optimal Objective)", labelpad=10)
    ax.set_title("3D-4  Policy Sensitivity Landscape: $w_1 \\times \\phi_{min} \\rightarrow Z^*$\n"
                 "Managerial decision surface — flat=policy-robust, steep=policy-critical",
                 pad=12)
    ax.legend(loc="upper right", fontsize=9)
    ax.view_init(elev=30, azim=-50)
    fig.tight_layout()
    savefig(fig, FIG_3D, "fig_3d4_policy_landscape")
    plt.close(fig)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def run_all():
    rng = np.random.default_rng(42)
    print("\n=== Generating 3D Figures ===")
    print("[1] 3D-1 Pareto Front")
    fig_3d1_pareto(np.random.default_rng(42))
    print("[2] 3D-1 Pareto + Projections")
    fig_3d1_projections(np.random.default_rng(42))
    print("[3] 3D-2 SR Response Surface")
    fig_3d2_sr_surface()
    print("[4] 3D-3 BPR Congestion Surface")
    fig_3d3_bpr_surface()
    print("[5] 3D-4 Policy Landscape")
    fig_3d4_policy_landscape(rng)


if __name__ == "__main__":
    run_all()
