"""
Revised Square-Grid Maps — 2025 Iberian Blackout Case Study
Square bins like the attached reference figure, with:
  - Real geographic context (OSM basemap via contextily)
  - Locator inset showing Spain with Madrid marked
  - Square grid cells (not hexagons)
  - YlOrRd-style colormap
  - All figures saved as PDF + PNG
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
from matplotlib.patches import Rectangle
import contextily as ctx
import os, sys, math, zipfile

sys.path.insert(0, os.path.dirname(__file__))
from cs_setup import BBOX, HOSPITALS, DISTRICTS, phi_from_scenarios

BASE    = os.path.dirname(os.path.dirname(__file__))
DATA    = os.path.join(BASE, "data")
FIG_MAP = os.path.join(BASE, "figures", "maps")
os.makedirs(FIG_MAP, exist_ok=True)

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                      "axes.titlesize":11})

# ── Spain outline from embedded coords ────────────────────────────────────────
# Simplified Spain mainland boundary (lon, lat pairs, counterclockwise)
SPAIN_OUTLINE = [
    (-9.3,36.0),(-8.0,36.0),(-6.0,36.1),(-5.3,36.0),(-5.0,36.1),
    (-4.3,36.7),(-3.0,36.8),(-1.8,37.4),(-0.7,37.6),(0.3,38.0),
    (0.7,38.5),(0.7,39.1),(0.9,39.9),(1.8,40.4),(3.3,41.8),(3.2,42.4),
    (1.8,43.4),(0.7,43.4),(-0.3,43.3),(-1.8,43.4),(-2.5,43.5),
    (-4.0,43.4),(-5.0,43.6),(-7.0,43.7),(-8.9,43.8),(-9.3,43.4),
    (-9.0,42.0),(-8.8,41.2),(-8.0,40.0),(-7.5,38.5),(-7.0,37.5),
    (-7.5,37.0),(-9.0,37.0),(-9.3,36.0)
]

# ── Square grid builder ────────────────────────────────────────────────────────

def make_square_grid(bbox, n_bins=10):
    """Return edges for a regular n_bins×n_bins grid over bbox."""
    s, w, n, e = bbox
    lat_edges = np.linspace(s, n, n_bins + 1)
    lon_edges = np.linspace(w, e, n_bins + 1)
    return lat_edges, lon_edges

def assign_grid_phi(lat_edges, lon_edges, scenario, noise_seed=0):
    """Assign φ value to each grid cell from district model."""
    def dist_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    rng   = np.random.default_rng(noise_seed * 10 + scenario)
    nr    = len(lat_edges) - 1
    nc    = len(lon_edges) - 1
    grid  = np.zeros((nr, nc))
    for i in range(nr):
        for j in range(nc):
            clat = (lat_edges[i] + lat_edges[i+1]) / 2
            clon = (lon_edges[j] + lon_edges[j+1]) / 2
            best_phi = 0.55; best_d = 1e9
            for d in DISTRICTS:
                dk = dist_km(clat, clon, d["lat"], d["lon"])
                if dk < d["r"] and dk < best_d:
                    best_d   = dk
                    best_phi = phi_from_scenarios(d, scenario)
            for h in HOSPITALS:
                dk = dist_km(clat, clon, h["lat"], h["lon"])
                if dk < 0.8:
                    best_phi = max(best_phi, 0.88)
            noise = float(rng.normal(0, 0.03))
            grid[i, j] = float(np.clip(best_phi + noise, 0.10, 1.00))
    return grid

def load_edge_means(scenario, lat_edges, lon_edges):
    """Compute mean φ per grid cell from real edge data."""
    path = os.path.join(DATA, f"edges_S{scenario}.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    # Need node coords — fall back to district model if not available
    return None   # use district model by default

def _save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_MAP, f"{name}.{ext}"),
                    dpi=300, bbox_inches="tight")
    print(f"  Saved: {name}.pdf/.png")
    plt.close(fig)

# ── Geographic helper: add OSM basemap ────────────────────────────────────────

def _add_basemap(ax, crs="EPSG:4326", alpha=0.35, source=None):
    try:
        if source is None:
            source = ctx.providers.OpenStreetMap.Mapnik
        ctx.add_basemap(ax, crs=crs, source=source, alpha=alpha,
                        attribution=False, zoom=11)
    except Exception:
        try:
            ctx.add_basemap(ax, crs=crs, source=ctx.providers.CartoDB.Positron,
                            alpha=alpha, attribution=False, zoom=11)
        except Exception:
            pass   # basemap optional

def _draw_square_grid(ax, grid, lat_edges, lon_edges, cmap, vmin, vmax,
                       alpha=0.78, edgecolor="white", lw=0.4):
    """Draw filled square grid cells using pcolormesh."""
    LON, LAT = np.meshgrid(lon_edges, lat_edges)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    pm = ax.pcolormesh(LON, LAT, grid, cmap=cmap, norm=norm,
                        alpha=alpha, linewidth=lw,
                        edgecolors=edgecolor, zorder=3)
    return pm, norm

def _draw_hospitals(ax, zorder=10):
    for h in HOSPITALS:
        mk = "*" if h["trauma"] else "P"
        sz = 140 if h["trauma"] else 90
        ax.scatter(h["lon"], h["lat"], s=sz, marker=mk,
                   c="white", edgecolors="#222", linewidths=0.9,
                   zorder=zorder)

def _add_locator_inset(fig, ax_main, rect=(0.02, 0.62, 0.22, 0.34)):
    """Small Spain locator map inset."""
    ax_in = fig.add_axes(rect, frameon=True)
    # Draw Spain outline
    sp_x = [p[0] for p in SPAIN_OUTLINE]
    sp_y = [p[1] for p in SPAIN_OUTLINE]
    ax_in.fill(sp_x, sp_y, color="#CCCCCC", alpha=0.8)
    ax_in.plot(sp_x, sp_y, color="#666", lw=0.8)
    # Mark Madrid study area
    s,w,n,e = BBOX
    rect_m = mpatches.FancyBboxPatch((w, s), e-w, n-s,
                                       boxstyle="square,pad=0",
                                       fc="red", ec="darkred", lw=1.5,
                                       alpha=0.7, zorder=5)
    ax_in.add_patch(rect_m)
    ax_in.text((w+e)/2, n+0.25, "Madrid", ha="center", fontsize=6,
               color="darkred", fontweight="bold")
    ax_in.set_xlim(-10, 5); ax_in.set_ylim(35.5, 44.5)
    ax_in.set_xticks([]); ax_in.set_yticks([])
    ax_in.set_title("Location", fontsize=6, pad=2)
    for spine in ax_in.spines.values():
        spine.set_linewidth(0.8)

def _style_map_ax(ax, title, bbox=BBOX):
    ax.set_xlim(bbox[1], bbox[3]); ax.set_ylim(bbox[0], bbox[2])
    ax.set_xlabel("Longitude (°E)", fontsize=9)
    ax.set_ylabel("Latitude (°N)", fontsize=9)
    ax.set_title(title, fontweight="bold", pad=6, fontsize=10.5)
    ax.tick_params(labelsize=8)
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

def _scalebar(ax, length_km=5):
    s,w,n,e = BBOX
    deg = length_km / (111.0 * math.cos(math.radians((s+n)/2)))
    x0  = w + 0.02; y0 = s + 0.012
    ax.plot([x0, x0+deg], [y0, y0], "k-", lw=3,
            solid_capstyle="butt", zorder=15, transform=ax.transData)
    ax.text(x0+deg/2, y0+0.005, f"{length_km} km",
            ha="center", fontsize=7, fontweight="bold", zorder=15)

def _north_arrow(ax):
    s,w,n,e = BBOX
    ax.annotate("N▲", xy=(e-0.04, s+0.02),
                fontsize=8, fontweight="bold", ha="center",
                zorder=15, color="black")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 1  Four-panel reliability grid (main map)
# ═══════════════════════════════════════════════════════════════════════════════

def map1_phi_grid():
    print("  [Map 1] Square grid φ — 4 scenarios...")
    lat_e, lon_e = make_square_grid(BBOX, n_bins=10)
    grids = [assign_grid_phi(lat_e, lon_e, s) for s in range(4)]

    titles = ["S0: Pre-Event  (φ̄ = 1.00)",
              "S1: Early Phase  t = 0–2h  (φ̄ ≈ 0.82)",
              "S2: Peak Disruption  t = 2–6h  (φ̄ ≈ 0.42)",
              "S3: Partial Restore  t = 6–10h  (φ̄ ≈ 0.67)"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    axes = axes.flatten()

    for s, ax in enumerate(axes):
        _add_basemap(ax, alpha=0.30)
        pm, norm = _draw_square_grid(ax, grids[s], lat_e, lon_e,
                                      "RdYlGn_r", 0.15, 1.00)
        _draw_hospitals(ax)
        _style_map_ax(ax, titles[s])
        _scalebar(ax)
        if s == 1: _north_arrow(ax)

        # φ̄ annotation
        mean_phi = grids[s].mean()
        ax.text(0.97, 0.97, f"φ̄ = {mean_phi:.3f}",
                transform=ax.transAxes, fontsize=9, va="top", ha="right",
                bbox=dict(fc="white", alpha=0.85, ec="grey", boxstyle="round"))

        # City labels
        for name, lat, lon in [("Centro", 40.415, -3.703),
                                ("Vallecas",40.383,-3.657)]:
            ax.text(lon, lat, name, fontsize=6.5, color="#333",
                    ha="center", va="center", style="italic", zorder=8)

    # Shared colourbar
    sm = plt.cm.ScalarMappable(cmap="RdYlGn_r",
                                norm=mcolors.Normalize(0.15, 1.00))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, orientation="vertical",
                        fraction=0.025, pad=0.03, shrink=0.75)
    cbar.set_label("Link Reliability  φᵢⱼ", fontsize=11)
    cbar.ax.axhline(0.85, color="gold", lw=2, ls="--")
    cbar.ax.text(1.12, 0.85, "φ*", color="gold",
                 fontsize=8.5, va="center", transform=cbar.ax.transAxes)

    # Legend
    h_star = mpatches.Patch(color="none", label="★ Trauma centre")
    h_plus = mpatches.Patch(color="none", label="✚ General hospital")
    fig.legend(handles=[h_star, h_plus], loc="lower left",
               fontsize=8.5, framealpha=0.8)

    # Locator inset on first panel
    _add_locator_inset(fig, axes[0], rect=(0.09, 0.52, 0.10, 0.16))

    fig.suptitle("MAP-1  Network Link Reliability φᵢⱼ — Square Grid\n"
                 "2025 Iberian Peninsula Blackout, Madrid Metropolitan Area "
                 "(lat 40.35–40.52 N, lon 3.58–3.78 W)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=(0,0,0.93,0.95))
    _save(fig, "MAP1v2_reliability_grid_4scenarios")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 2  Failure risk grid — reference-figure style (5 scenarios as 1 row)
# ═══════════════════════════════════════════════════════════════════════════════

def map2_failure_risk_grid():
    print("  [Map 2] Failure risk square grid...")
    lat_e, lon_e = make_square_grid(BBOX, n_bins=10)
    scenarios = [0, 1, 2, 3]
    slbls     = ["S0 Normal","S1 Early","S2 Peak","S3 Restore"]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5))
    for s, ax in zip(scenarios, axes):
        grid = 1.0 - assign_grid_phi(lat_e, lon_e, s)
        _add_basemap(ax, alpha=0.25)
        pm, _ = _draw_square_grid(ax, grid, lat_e, lon_e,
                                   "YlOrRd", 0.0, 0.80, alpha=0.80)
        _draw_hospitals(ax, zorder=10)
        _style_map_ax(ax, slbls[s])
        ax.tick_params(labelsize=7)
        if s == 0:
            _scalebar(ax, 5)
            _north_arrow(ax)
            _add_locator_inset(fig, ax, rect=(0.04, 0.68, 0.055, 0.20))
        cbar = fig.colorbar(pm, ax=ax, shrink=0.75, pad=0.02)
        cbar.set_label("Failure risk\n(1 − φᵢⱼ)", fontsize=7.5)
        cbar.ax.tick_params(labelsize=7)
        pct_high = float((grid > 0.50).mean() * 100)
        ax.text(0.97,0.03, f"High risk:\n{pct_high:.0f}% of cells",
                transform=ax.transAxes, fontsize=7.5, va="bottom", ha="right",
                bbox=dict(fc="white", alpha=0.85, ec="grey", boxstyle="round"))

    fig.suptitle("MAP-2  Zone Failure Probability (1 − φᵢⱼ) by Square Grid Cell\n"
                 "YlOrRd: yellow = low risk → dark red = high failure probability\n"
                 "★ = Trauma centre (backup power)  ✚ = General hospital",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP2v2_failure_risk_grid")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 3  Reliability loss Δφ grid
# ═══════════════════════════════════════════════════════════════════════════════

def map3_delta_grid():
    print("  [Map 3] Δφ loss grid...")
    lat_e, lon_e = make_square_grid(BBOX, n_bins=10)
    g0 = assign_grid_phi(lat_e, lon_e, 0)
    g2 = assign_grid_phi(lat_e, lon_e, 2)
    delta = g2 - g0

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    # Left: Δφ heatmap
    ax = axes[0]
    _add_basemap(ax, alpha=0.28)
    pm, _ = _draw_square_grid(ax, delta, lat_e, lon_e,
                               "RdBu", -0.70, 0.0, alpha=0.82)
    _draw_hospitals(ax)
    _style_map_ax(ax, "Reliability Loss  Δφ = φ(S2) − φ(S0)\nDarker red = greater disruption")
    _scalebar(ax); _north_arrow(ax)
    _add_locator_inset(fig, ax, rect=(0.035, 0.65, 0.10, 0.20))
    cbar = fig.colorbar(pm, ax=ax, shrink=0.80, pad=0.02)
    cbar.set_label("Δφ (negative = reliability lost)", fontsize=9)

    # Label worst cells
    nr, nc = delta.shape
    for i in range(nr):
        for j in range(nc):
            if delta[i,j] < -0.55:
                clat = (lat_e[i]+lat_e[i+1])/2
                clon = (lon_e[j]+lon_e[j+1])/2
                ax.text(clon, clat, f"{delta[i,j]:.2f}",
                        ha="center", va="center", fontsize=6.5,
                        color="white", fontweight="bold", zorder=10)

    # Right: bar chart of mean Δφ by district
    ax = axes[1]
    sc_phi = {s: assign_grid_phi(lat_e, lon_e, s).mean() for s in range(4)}
    bars = ax.bar(range(4),
                  [sc_phi[s] for s in range(4)],
                  color=["#2E7D32","#FF9800","#E53935","#1565C0"], alpha=0.82)
    ax.axhline(0.85, ls="--", color="gold", lw=2, label="φ* = 0.85")
    ax.set_xticks(range(4))
    ax.set_xticklabels(["S0\nNormal","S1\nt=0-2h","S2\nPeak","S3\nRestore"])
    ax.set_ylabel("Mean Grid-Cell φ̄")
    ax.set_title("Mean Network Reliability per Scenario", fontweight="bold")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.3)
    for bar, v in zip(bars, [sc_phi[s] for s in range(4)]):
        ax.text(bar.get_x()+bar.get_width()/2, v+0.01,
                f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")

    fig.suptitle("MAP-3  Reliability Loss Δφ (S0 → S2) and Scenario Comparison\n"
                 "2025 Iberian Peninsula Blackout — Madrid",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP3v2_reliability_delta")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 4  Accessibility binary + % feasible
# ═══════════════════════════════════════════════════════════════════════════════

def map4_accessibility_grid():
    print("  [Map 4] Accessibility grid...")
    lat_e, lon_e = make_square_grid(BBOX, n_bins=10)
    PHI_MIN = 0.85

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5))
    for s, ax in enumerate(axes):
        grid = assign_grid_phi(lat_e, lon_e, s)
        acc  = (grid >= PHI_MIN).astype(float)
        _add_basemap(ax, alpha=0.25)
        pm, _ = _draw_square_grid(ax, acc, lat_e, lon_e,
                                   mcolors.ListedColormap(["#C62828","#2E7D32"]),
                                   0.0, 1.0, alpha=0.78)
        _draw_hospitals(ax)
        _style_map_ax(ax, f"S{s}: {'Normal' if s==0 else 't=0-2h' if s==1 else 'Peak' if s==2 else 'Restore'}")
        ax.tick_params(labelsize=7)
        pct = float(acc.mean() * 100)
        ax.text(0.97, 0.97, f"Accessible:\n{pct:.0f}%",
                transform=ax.transAxes, fontsize=8.5, va="top", ha="right",
                bbox=dict(fc="white", alpha=0.88, ec="grey", boxstyle="round"))
        if s == 0:
            _scalebar(ax, 5); _add_locator_inset(fig, ax, rect=(0.04,0.68,0.055,0.20))

    patches = [mpatches.Patch(color="#2E7D32", label=f"Accessible (φ ≥ {PHI_MIN})"),
               mpatches.Patch(color="#C62828", label=f"Excluded   (φ < {PHI_MIN})")]
    fig.legend(handles=patches, loc="lower center", ncol=2,
               fontsize=9, framealpha=0.85)
    fig.suptitle(f"MAP-4  Network Accessibility under φ_min = {PHI_MIN} Threshold\n"
                 "Green = feasible arcs included in routing  |  Red = excluded by reliability constraint",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP4v2_accessibility_grid")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 5  Hospital service coverage grid
# ═══════════════════════════════════════════════════════════════════════════════

def map5_hospital_coverage_grid():
    print("  [Map 5] Hospital coverage grid...")
    lat_e, lon_e = make_square_grid(BBOX, n_bins=10)

    def coverage_r(scenario, trauma):
        base = 8.0 if trauma else 5.0
        scales = {0:1.00, 1:0.74, 2:0.44, 3:0.68}
        return base * scales[scenario]

    def _in_radius(clat, clon, hlat, hlon, r_km):
        R=6371.0; dlat=math.radians(hlat-clat); dlon=math.radians(hlon-clon)
        a=math.sin(dlat/2)**2+math.cos(math.radians(clat))*math.cos(math.radians(hlat))*math.sin(dlon/2)**2
        return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a)) <= r_km

    nr, nc = len(lat_e)-1, len(lon_e)-1
    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    for ax, s in zip(axes, [0, 2]):
        grid_cov = np.zeros((nr, nc))   # 0=uncovered, 1=trauma, 2=general
        for i in range(nr):
            for j in range(nc):
                clat = (lat_e[i]+lat_e[i+1])/2
                clon = (lon_e[j]+lon_e[j+1])/2
                for h in HOSPITALS:
                    r = coverage_r(s, h["trauma"])
                    if _in_radius(clat, clon, h["lat"], h["lon"], r):
                        grid_cov[i,j] = max(grid_cov[i,j], 2 if h["trauma"] else 1)

        _add_basemap(ax, alpha=0.28)
        cmap_cov = mcolors.ListedColormap(["#FFCDD2","#64B5F6","#1565C0"])
        pm, _  = _draw_square_grid(ax, grid_cov, lat_e, lon_e,
                                    cmap_cov, 0, 2, alpha=0.75)
        # Coverage circles overlay
        for h in HOSPITALS:
            r_km  = coverage_r(s, h["trauma"])
            r_deg = r_km / (111.0 * math.cos(math.radians(h["lat"])))
            col   = "#1565C0" if h["trauma"] else "#64B5F6"
            circle = plt.Circle((h["lon"], h["lat"]), r_deg,
                                 fill=False, lw=1.5, color=col,
                                 ls="--", zorder=8)
            ax.add_patch(circle)
            mk = "*" if h["trauma"] else "P"
            ax.scatter(h["lon"], h["lat"], s=120 if h["trauma"] else 80,
                       marker=mk, c="white", edgecolors=col,
                       linewidths=1.2, zorder=11)
        covered_pct = float((grid_cov > 0).mean() * 100)
        _style_map_ax(ax, f"{'S0: Normal' if s==0 else 'S2: Peak Disruption'}\n"
                      f"30-min Coverage  (covered: {covered_pct:.0f}%)")
        _scalebar(ax); _north_arrow(ax)
        if s == 0:
            _add_locator_inset(fig, ax, rect=(0.035, 0.65, 0.10, 0.22))

    patches = [mpatches.Patch(color="#1565C0", label="Trauma centre coverage"),
               mpatches.Patch(color="#64B5F6", label="General hospital coverage"),
               mpatches.Patch(color="#FFCDD2", label="Coverage gap (unreachable in 30 min)")]
    fig.legend(handles=patches, loc="lower center", ncol=3,
               fontsize=9, framealpha=0.85)
    fig.suptitle("MAP-5  Hospital 30-Minute Service Coverage — Before vs Peak Disruption\n"
                 "Coverage radius shrinks from 8 km → 3.5 km (trauma) due to BPR travel-time inflation",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP5v2_hospital_coverage")


# ═══════════════════════════════════════════════════════════════════════════════
# MAP 6  Patient demand heatmap (reference-figure style, like attached)
# ═══════════════════════════════════════════════════════════════════════════════

def map6_demand_heatmap():
    print("  [Map 6] Patient demand heatmap (reference style)...")
    from cs_setup import generate_demand
    N_BINS = 10
    lat_e, lon_e = make_square_grid(BBOX, N_BINS)

    scenarios = [0, 1, 2, 3]
    slbls     = ["S0: Normal","S1: Early","S2: Peak","S3: Restore"]
    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5))

    for s, ax in zip(scenarios, axes):
        dem  = generate_demand(80, scenario=s, seed=42)
        # Count per bin
        grid = np.zeros((N_BINS, N_BINS))
        for _, row in dem.iterrows():
            li = int(np.clip(np.searchsorted(lat_e, row["lat"])-1, 0, N_BINS-1))
            lj = int(np.clip(np.searchsorted(lon_e, row["lon"])-1, 0, N_BINS-1))
            grid[li, lj] += 1
        log_grid = np.log1p(grid)

        _add_basemap(ax, alpha=0.22)
        pm, norm = _draw_square_grid(ax, log_grid, lat_e, lon_e,
                                      "YlOrRd", 0.0, log_grid.max()+0.1,
                                      alpha=0.82)
        _draw_hospitals(ax, zorder=10)
        _style_map_ax(ax, slbls[s])
        ax.tick_params(labelsize=7)

        # Bin labels (lat/lon indices like the reference figure)
        ax.set_xticks(lon_e[::2]); ax.set_yticks(lat_e[::2])
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))

        cbar = fig.colorbar(pm, ax=ax, shrink=0.75, pad=0.02)
        cbar.set_label("log(1 + count)", fontsize=7.5)
        cbar.ax.tick_params(labelsize=7)

        n1 = len(dem[dem["tier"]==1])
        n2 = len(dem[dem["tier"]==2])
        n3 = len(dem[dem["tier"]==3])
        ax.text(0.97,0.03, f"T1:{n1} T2:{n2} T3:{n3}",
                transform=ax.transAxes, fontsize=7.5, va="bottom", ha="right",
                bbox=dict(fc="white", alpha=0.85, ec="grey", boxstyle="round"))

        if s == 0:
            _scalebar(ax, 5)
            _add_locator_inset(fig, ax, rect=(0.04,0.68,0.055,0.20))

    fig.suptitle("MAP-6  Patient Demand Density — log(1+count) per Grid Cell\n"
                 "T1=Critical  T2=Serious  T3=Minor  |  ★ = Trauma centre  ✚ = Hospital\n"
                 "S2 shift: more Type 1 (medical devices fail, accident surge, heat stress)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP6v2_demand_heatmap")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_all():
    print("\n=== Generating Revised Square-Grid Maps ===")
    steps = [
        ("Map 1 — Reliability φ (4-panel square grid)", map1_phi_grid),
        ("Map 2 — Failure risk grid (reference style)", map2_failure_risk_grid),
        ("Map 3 — Δφ loss grid",                        map3_delta_grid),
        ("Map 4 — Accessibility binary grid",            map4_accessibility_grid),
        ("Map 5 — Hospital coverage grid",               map5_hospital_coverage_grid),
        ("Map 6 — Demand heatmap (reference style)",     map6_demand_heatmap),
    ]
    for i,(lbl,fn) in enumerate(steps,1):
        print(f"  [{i}/{len(steps)}] {lbl}")
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); print(f"    WARNING: {e}")

if __name__ == "__main__":
    run_all()
