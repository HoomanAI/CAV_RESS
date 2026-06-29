"""Shared paths and constants for all scripts."""
import os

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS   = os.path.join(BASE, "results", "figures")
FIG_3D = os.path.join(FIGS, "3d")
FIG_IN = os.path.join(FIGS, "innovative")
FIG_SM = os.path.join(FIGS, "summary")
FIG_ML = os.path.join(FIGS, "matlab")
TABLES = os.path.join(BASE, "results", "tables")
REPORT = os.path.join(BASE, "results", "report")

for _d in [FIG_3D, FIG_IN, FIG_SM, FIG_ML, TABLES, REPORT]:
    os.makedirs(_d, exist_ok=True)

PHI_LEVELS  = [1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]
ALGORITHMS  = ["QiGA", "GA", "PSO", "ALNS", "TS"]
RNG_SEEDS   = list(range(1, 21))

PALETTE = {
    "phi":   ["#1565C0","#1976D2","#42A5F5","#81D4FA","#80CBC4","#FF8A65","#E53935"],
    "algo":  ["#2196F3","#4CAF50","#FF9800","#F44336","#9C27B0"],
    "zones": {"safe":"#43A047","warn":"#FFA726","crit":"#E53935"},
}

import matplotlib.pyplot as plt
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def savefig(fig, folder: str, stem: str):
    """Save figure as both PDF and PNG."""
    for ext in ("pdf", "png"):
        path = os.path.join(folder, f"{stem}.{ext}")
        fig.savefig(path, dpi=300, bbox_inches="tight")
    print(f"  Saved: {stem}.pdf/.png")
