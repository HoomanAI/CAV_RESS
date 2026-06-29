"""
Animated GIFs for the CAV Reliability Paper Core Idea
GIF 1 — Core concept: φ degrades → network collapses → SR drops → awareness gap
GIF 2 — Madrid map: square grid evolving S0→S1→S2→S3 (hour-by-hour)
GIF 3 — Phase diagram: event trajectory with operating point moving
GIF 4 — Pareto collapse: 3-objective front shrinking as φ drops
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation, PillowWriter
import math, os, sys

sys.path.insert(0, os.path.dirname(__file__))
from cs_setup import BBOX, HOSPITALS, DISTRICTS, phi_from_scenarios

BASE   = os.path.dirname(os.path.dirname(__file__))
OUT    = os.path.join(BASE, "figures", "gif")
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.family":"Arial","font.size":10})

# ── shared helpers ─────────────────────────────────────────────────────────────

def dist_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

N_BINS = 10
lat_e = np.linspace(BBOX[0], BBOX[2], N_BINS+1)
lon_e = np.linspace(BBOX[1], BBOX[3], N_BINS+1)

def build_grid(phi_mean_target, rng_seed=0):
    """Build 10×10 phi grid centred on phi_mean_target."""
    rng   = np.random.default_rng(rng_seed)
    grid  = np.zeros((N_BINS, N_BINS))
    for i in range(N_BINS):
        for j in range(N_BINS):
            clat = (lat_e[i]+lat_e[i+1])/2
            clon = (lon_e[j]+lon_e[j+1])/2
            # Distance gradient: centre is more reliable
            d_centre = dist_km(clat, clon, 40.415, -3.703)
            phi_cell = phi_mean_target * (1 + 0.15*max(0, 1 - d_centre/8))
            for h in HOSPITALS:
                if dist_km(clat,clon,h["lat"],h["lon"]) < 0.7:
                    phi_cell = max(phi_cell, 0.88)
            grid[i,j] = float(np.clip(phi_cell + rng.normal(0,0.04), 0.10, 1.00))
    return grid

def sr_from_phi(phi, traffic, aware=True):
    exp = 0.65 if aware else 1.80
    return float(np.clip(97 * phi**exp * (1 - 0.003*(traffic-40)), 0, 98))


# ══════════════════════════════════════════════════════════════════════════════
# GIF 1 — CORE CONCEPT
# 5-panel: network map | phase diagram | SR bar | timeline | awareness gap
# ══════════════════════════════════════════════════════════════════════════════

def gif1_core_concept(fps=6, n_frames=80):
    print("  [GIF 1] Core concept animation...")

    # Build smooth interpolation over 10 hours
    hours = np.linspace(0, 10, n_frames)
    phi_t = np.array([max(0.42, 1.0 - 0.18*t) if t < 2
                      else max(0.42, 1.0 - 0.30*t + 0.02*(t-2)) if t < 6
                      else min(0.72, 0.42 + 0.05*(t-6))
                      for t in hours])
    trf_t = np.array([40+25*t if t < 1
                      else 65+8*(t-1) if t < 4
                      else 89+5*(t-4) if t < 6
                      else max(55, 99-8*(t-6))
                      for t in hours])
    sr_aw = np.array([sr_from_phi(p, tr, aware=True)  for p,tr in zip(phi_t, trf_t)])
    sr_un = np.array([sr_from_phi(p, tr, aware=False) for p,tr in zip(phi_t, trf_t)])

    # Phase diagram surface
    phi_surf = np.linspace(0.20, 1.00, 60)
    trf_surf = np.linspace(20, 100, 40)
    PHI_S, TRF_S = np.meshgrid(phi_surf, trf_surf)
    SR_S  = np.clip(97 * PHI_S**0.65 * (1-0.003*(TRF_S-40)), 0, 100)

    # Phase diagram regime colourmap
    zone_cmap = mcolors.ListedColormap(["#B71C1C","#E64A19","#F9A825","#2E7D32"])
    zone_norm = mcolors.BoundaryNorm([0,70,85,95,101], zone_cmap.N)

    # Scenario labels
    def scenario_label(t):
        if t < 2:   return "S1: Early Phase"
        if t < 6:   return "S2: Peak Disruption"
        return "S3: Restoration"

    LON_G, LAT_G = np.meshgrid(lon_e, lat_e)

    fig = plt.figure(figsize=(18, 9), facecolor="white")
    fig.patch.set_facecolor("white")
    gs  = gridspec.GridSpec(2, 4, figure=fig,
                            hspace=0.40, wspace=0.35,
                            left=0.04, right=0.97,
                            top=0.90, bottom=0.08)

    ax_map  = fig.add_subplot(gs[:, 0])     # Madrid grid map (tall)
    ax_ph   = fig.add_subplot(gs[:, 1])     # Phase diagram
    ax_bar  = fig.add_subplot(gs[0, 2])     # SR bars
    ax_tl   = fig.add_subplot(gs[1, 2])     # Timeline
    ax_gap  = fig.add_subplot(gs[:, 3])     # Awareness gap fill

    DARK = "white"; LIGHT = "#111111"; ACC = "#58A6FF"

    for ax in [ax_map, ax_ph, ax_bar, ax_tl, ax_gap]:
        ax.set_facecolor("white")
        for sp in ax.spines.values():
            sp.set_color("#CCCCCC")
        ax.tick_params(colors=LIGHT, labelsize=8)
        ax.xaxis.label.set_color(LIGHT); ax.yaxis.label.set_color(LIGHT)
        ax.title.set_color(LIGHT)

    # ── Static elements ───────────────────────────────────────────────────────
    # Phase diagram background
    ax_ph.contourf(phi_surf, trf_surf, SR_S,
                   levels=[0,70,85,95,101], cmap=zone_cmap, norm=zone_norm,
                   alpha=0.75)
    ax_ph.contour(phi_surf, trf_surf, SR_S, levels=[70,85,95],
                  colors="white", linewidths=1.0, alpha=0.5)
    ax_ph.axvline(0.85, ls="--", color="#FFD700", lw=1.5, alpha=0.8)
    ax_ph.set_xlabel("φ̄  (Mean Reliability)", color=LIGHT, fontsize=9)
    ax_ph.set_ylabel("Traffic Level (%)", color=LIGHT, fontsize=9)
    ax_ph.set_title("Service Phase Diagram", color=LIGHT, fontweight="bold")
    ax_ph.invert_xaxis()
    ax_ph.text(0.83, 23, "φ*=0.85", color="#FFD700", fontsize=8, fontweight="bold")

    # Timeline axes setup
    ax_tl.set_xlim(0, 10); ax_tl.set_ylim(0, 1.05)
    ax_tl.set_xlabel("Hours after blackout", color=LIGHT, fontsize=9)
    ax_tl.set_ylabel("φ̄", color=LIGHT, fontsize=9)
    ax_tl.plot(hours, phi_t, color="#BB86FC", lw=1.5, alpha=0.3)
    ax_tl.axhline(0.85, ls="--", color="#FFD700", lw=1, alpha=0.6)
    ax_tl.set_title("Reliability Over Time", color=LIGHT, fontweight="bold")

    # Awareness gap axes setup
    ax_gap.set_xlim(0, 10); ax_gap.set_ylim(0, 100)
    ax_gap.set_xlabel("Hours after blackout", color=LIGHT, fontsize=9)
    ax_gap.set_ylabel("Service Rate SR (%)", color=LIGHT, fontsize=9)
    ax_gap.plot(hours, sr_aw, color="#58A6FF", lw=1.5, alpha=0.3)
    ax_gap.plot(hours, sr_un, color="#FF6B6B", lw=1.5, alpha=0.3)
    ax_gap.fill_between(hours, sr_un, sr_aw, alpha=0.12, color="#58A6FF")
    ax_gap.axhline(85, ls=":", color="grey", lw=0.8, alpha=0.5)
    ax_gap.set_title("Awareness Gain (SR)", color=LIGHT, fontweight="bold")

    # ── Animated elements ─────────────────────────────────────────────────────
    pm        = ax_map.pcolormesh(LON_G, LAT_G, np.ones((N_BINS,N_BINS)),
                                   cmap="RdYlGn", vmin=0.15, vmax=1.0, alpha=0.85)
    for h in HOSPITALS:
        ax_map.scatter(h["lon"], h["lat"], s=80 if h["trauma"] else 45,
                       marker="*" if h["trauma"] else "P",
                       c="white", edgecolors="#333", lw=0.6, zorder=5)
    ax_map.set_xlim(BBOX[1], BBOX[3]); ax_map.set_ylim(BBOX[0], BBOX[2])
    ax_map.set_xlabel("Longitude", color=LIGHT, fontsize=8)
    ax_map.set_ylabel("Latitude",  color=LIGHT, fontsize=8)
    ax_map.set_title("Madrid Network\nReliability φᵢⱼ", color=LIGHT, fontweight="bold")

    # Phase dot
    ph_dot, = ax_ph.plot([], [], "o", ms=14, color="white",
                          markeredgecolor="black", markeredgewidth=1.5, zorder=10)
    ph_trail, = ax_ph.plot([], [], "-", color="white", lw=1.5,
                            alpha=0.5, zorder=9)

    # SR bars
    bar_aw = ax_bar.bar([0.3], [0], width=0.35, color="#58A6FF", alpha=0.88,
                         label="Aware routing")
    bar_un = ax_bar.bar([0.7], [0], width=0.35, color="#FF6B6B", alpha=0.88,
                         label="Unaware routing")
    ax_bar.set_xlim(0, 1); ax_bar.set_ylim(0, 105)
    ax_bar.set_xticks([0.3, 0.7])
    ax_bar.set_xticklabels(["Aware","Unaware"], color=LIGHT, fontsize=9)
    ax_bar.set_ylabel("SR (%)", color=LIGHT, fontsize=9)
    ax_bar.set_title("Service Rate", color=LIGHT, fontweight="bold")
    ax_bar.axhline(85, ls="--", color="#FFD700", lw=1, alpha=0.7)
    ax_bar.text(0.95, 86, "Target 85%", color="#FFD700",
                fontsize=7, ha="right", transform=ax_bar.get_xaxis_transform())
    txt_aw = ax_bar.text(0.3, 2, "", ha="center", fontsize=9,
                          fontweight="bold", color="white")
    txt_un = ax_bar.text(0.7, 2, "", ha="center", fontsize=9,
                          fontweight="bold", color="white")

    # Timeline moving elements
    tl_dot, = ax_tl.plot([], [], "o", ms=9, color="#BB86FC", zorder=5)
    tl_line = ax_tl.axvline(0, color="#BB86FC", lw=1, ls=":", alpha=0.7)

    # Gap moving elements
    gap_dot_aw, = ax_gap.plot([], [], "o", ms=8, color="#58A6FF", zorder=5)
    gap_dot_un, = ax_gap.plot([], [], "o", ms=8, color="#FF6B6B", zorder=5)
    gap_line = ax_gap.axvline(0, color="white", lw=0.8, ls=":", alpha=0.5)
    gap_txt  = ax_gap.text(0.02, 0.05, "", transform=ax_gap.transAxes,
                            fontsize=8, color="#58A6FF")

    # Hour counter and status text
    hour_txt = fig.text(0.5, 0.96,
                        "2025 Iberian Peninsula Blackout — Madrid CAV Emergency Routing",
                        ha="center", fontsize=14, color=LIGHT, fontweight="bold")
    status_txt = fig.text(0.5, 0.92, "", ha="center",
                           fontsize=11, color="#FFD700", fontweight="bold")
    phi_txt    = fig.text(0.03, 0.50, "", ha="left",
                           fontsize=9, color=LIGHT, rotation=90)

    ph_x_trail, ph_y_trail = [], []

    def animate(frame):
        t   = hours[frame]
        phi = phi_t[frame]
        trf = trf_t[frame]
        sa  = sr_aw[frame]
        su  = sr_un[frame]

        # Map grid
        grid = build_grid(phi, rng_seed=frame//5)
        pm.set_array(grid.ravel())

        # Phase dot + trail
        ph_x_trail.append(phi); ph_y_trail.append(trf)
        ph_dot.set_data([phi], [trf])
        # Colour dot by regime
        if sa >= 95:   dot_c = "#2E7D32"
        elif sa >= 85: dot_c = "#F9A825"
        elif sa >= 70: dot_c = "#E64A19"
        else:          dot_c = "#B71C1C"
        ph_dot.set_markerfacecolor(dot_c)
        trail_len = min(15, len(ph_x_trail))
        ph_trail.set_data(ph_x_trail[-trail_len:], ph_y_trail[-trail_len:])

        # SR bars
        bar_aw[0].set_height(sa); bar_un[0].set_height(su)
        # Bar colour by level
        bar_aw[0].set_facecolor("#2E7D32" if sa >= 85 else "#FF9800" if sa >= 70 else "#E53935")
        txt_aw.set_text(f"{sa:.0f}%"); txt_aw.set_y(sa + 1)
        txt_un.set_text(f"{su:.0f}%"); txt_un.set_y(su + 1)

        # Timeline
        tl_dot.set_data([t], [phi])
        tl_line.set_xdata([t, t])

        # Gap
        gap_dot_aw.set_data([t], [sa])
        gap_dot_un.set_data([t], [su])
        gap_line.set_xdata([t, t])
        gap = sa - su
        gap_txt.set_text(f"Awareness gain: +{gap:.0f}pp")
        gap_txt.set_color("#58A6FF" if gap > 10 else "#FFD700")

        # Text overlays
        if t < 0.5:   phase = "⚡ BLACKOUT ONSET"
        elif t < 2:   phase = "S1: Early Phase  (t=0–2h)"
        elif t < 6:   phase = "S2: Peak Disruption  (t=2–6h)"
        else:         phase = "S3: Restoration  (t=6–10h)"
        status_txt.set_text(f"t = {t:.1f}h  |  φ̄ = {phi:.3f}  |  {phase}")
        phi_txt.set_text(f"Mean φ̄ = {phi:.3f}")

        return (pm, ph_dot, ph_trail, bar_aw[0], bar_un[0],
                txt_aw, txt_un, tl_dot, tl_line,
                gap_dot_aw, gap_dot_un, gap_line, gap_txt,
                status_txt, phi_txt)

    anim = FuncAnimation(fig, animate, frames=n_frames,
                          interval=1000//fps, blit=True)
    out_path = os.path.join(OUT, "GIF1_core_concept.gif")
    writer   = PillowWriter(fps=fps, metadata={"loop":0})
    anim.save(out_path, writer=writer, dpi=120)
    plt.close(fig)
    print(f"  Saved: GIF1_core_concept.gif")


# ══════════════════════════════════════════════════════════════════════════════
# GIF 2 — MADRID MAP evolving (square grid, S0→S2→S3 loop)
# ══════════════════════════════════════════════════════════════════════════════

def gif2_madrid_map(fps=5, n_frames=60):
    print("  [GIF 2] Madrid map evolution...")

    hours  = np.linspace(0, 10, n_frames)
    phi_t  = np.array([max(0.42,1.0-0.18*t) if t<2
                        else max(0.42,1.0-0.30*t+0.02*(t-2)) if t<6
                        else min(0.72,0.42+0.05*(t-6)) for t in hours])

    fig, ax = plt.subplots(figsize=(8, 7), facecolor="white")
    ax.set_facecolor("white")
    for sp in ax.spines.values(): sp.set_color("#CCCCCC")
    ax.tick_params(colors="#111111")

    LON_G, LAT_G = np.meshgrid(lon_e, lat_e)
    pm = ax.pcolormesh(LON_G, LAT_G, np.ones((N_BINS,N_BINS)),
                        cmap="RdYlGn", vmin=0.15, vmax=1.00,
                        alpha=0.85, linewidth=0.5, edgecolors="#222")

    # Hospital markers (static)
    for h in HOSPITALS:
        ax.scatter(h["lon"], h["lat"],
                   s=120 if h["trauma"] else 70,
                   marker="*" if h["trauma"] else "P",
                   c="white", edgecolors="black", lw=0.8, zorder=6)

    # Spain inset
    ax_in = fig.add_axes([0.02, 0.75, 0.15, 0.20], frameon=True)
    ax_in.set_facecolor("white")
    spain_x=[-9.3,-8.0,-6.0,-5.0,-4.3,-3.0,-1.8,-0.7,0.3,0.7,0.9,1.8,
              3.3,3.2,1.8,0.7,-0.3,-1.8,-4.0,-5.0,-7.0,-8.9,-9.3,
              -9.0,-8.0,-7.5,-7.0,-7.5,-9.0,-9.3]
    spain_y=[36.0,36.0,36.1,36.1,36.7,36.8,37.4,37.6,38.0,38.5,39.9,
             40.4,41.8,42.4,43.4,43.4,43.3,43.4,43.4,43.6,43.7,43.8,
             43.4,42.0,40.0,38.5,37.5,37.0,37.0,36.0]
    ax_in.fill(spain_x, spain_y, color="#CCCCCC", alpha=0.9)
    ax_in.plot(spain_x, spain_y, color="#58A6FF", lw=0.8)
    rect = mpatches.Rectangle((-3.78, 40.35), 0.20, 0.17,
                                fc="#FF4444", ec="#FF4444", alpha=0.9, lw=1.5)
    ax_in.add_patch(rect)
    ax_in.text(-3.68, 40.60, "Madrid", fontsize=5, color="#FF4444",
               ha="center", fontweight="bold")
    ax_in.set_xlim(-10, 5); ax_in.set_ylim(35.5, 44.5)
    ax_in.set_xticks([]); ax_in.set_yticks([])
    for sp in ax_in.spines.values(): sp.set_color("#58A6FF")

    # φ* threshold bar annotation
    cbar = fig.colorbar(pm, ax=ax, shrink=0.75, pad=0.02)
    cbar.set_label("Link Reliability φᵢⱼ", color="#111111", fontsize=10)
    cbar.ax.yaxis.set_tick_params(color="#111111")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#111111")
    cbar.ax.axhline((0.85-0.15)/(1.0-0.15), color="#FFD700",
                     lw=2.5, ls="--")
    cbar.ax.text(1.3, (0.85-0.15)/(1.0-0.15), "φ*=0.85",
                 color="#FFD700", fontsize=8, va="center")

    ax.set_xlim(BBOX[1], BBOX[3]); ax.set_ylim(BBOX[0], BBOX[2])
    ax.set_xlabel("Longitude (°E)", color="#111111")
    ax.set_ylabel("Latitude (°N)", color="#111111")

    # Regime zones
    zone_colors = {
        (0.85,1.00): ("●  Safe Zone (SR≥95%)",  "#2E7D32"),
        (0.70,0.85): ("●  Standard Zone",        "#F9A825"),
        (0.50,0.70): ("●  Degraded Zone",        "#E64A19"),
        (0.00,0.50): ("●  Collapse Zone",        "#B71C1C"),
    }

    # Dynamic text
    title_txt = ax.set_title("", color="#111111", fontsize=13,
                              fontweight="bold", pad=10)
    phi_txt   = ax.text(0.98, 0.98, "", transform=ax.transAxes,
                         ha="right", va="top", fontsize=11,
                         color="#FFD700", fontweight="bold",
                         bbox=dict(fc="white", ec="#FFD700",
                                   alpha=0.85, boxstyle="round"))

    # Regime indicator patch (changes colour)
    regime_patch = mpatches.FancyBboxPatch(
        (BBOX[1]+0.01, BBOX[0]+0.01), 0.06, 0.025,
        boxstyle="round,pad=0.002", fc="#2E7D32",
        ec="none", alpha=0.85, zorder=8, transform=ax.transData)
    ax.add_patch(regime_patch)
    regime_txt = ax.text(BBOX[1]+0.04, BBOX[0]+0.023, "SAFE",
                          ha="center", va="center", fontsize=7.5,
                          color="white", fontweight="bold", zorder=9)

    # Coverage circle (shrinks as phi drops)
    trauma_hosp = HOSPITALS[0]   # La Paz
    circle_handle = plt.Circle(
        (trauma_hosp["lon"], trauma_hosp["lat"]), 0.08,
        fill=False, lw=2, color="#58A6FF", ls="--",
        alpha=0.6, zorder=7)
    ax.add_patch(circle_handle)

    def animate(frame):
        t   = hours[frame]
        phi = phi_t[frame]

        grid = build_grid(phi, rng_seed=frame//4)
        pm.set_array(grid.ravel())

        # Title
        if t < 0.3:
            phase = "⚡  BLACKOUT ONSET — April 28, 2025, 12:33 CET"
        elif t < 2:
            phase = f"S1: Early Phase  (t = {t:.1f}h) — Batteries depleting"
        elif t < 6:
            phase = f"S2: Peak Disruption  (t = {t:.1f}h) — Network collapsed"
        else:
            phase = f"S3: Restoration  (t = {t:.1f}h) — Partial reconnection"
        title_txt.set_text(phase)

        # φ label
        na = float((grid >= 0.85).mean() * 100)
        phi_txt.set_text(f"φ̄ = {phi:.3f}   |   Accessible: {na:.0f}%")

        # Regime colour
        sr = sr_from_phi(phi, 40+min(60,t*20), aware=True)
        if sr >= 95:
            col_r, lbl_r = "#2E7D32", "SAFE"
        elif sr >= 85:
            col_r, lbl_r = "#F9A825", "STANDARD"
        elif sr >= 70:
            col_r, lbl_r = "#E64A19", "DEGRADED"
        else:
            col_r, lbl_r = "#B71C1C", "⚠ COLLAPSE"
        regime_patch.set_facecolor(col_r)
        regime_txt.set_text(lbl_r)

        # Coverage circle radius (shrinks)
        scale = {True: 1.00, False: 0.44}[phi >= 0.85] if phi < 0.85 else phi
        r_deg = 8.0 * scale / 111.0
        circle_handle.set_radius(r_deg / math.cos(math.radians(trauma_hosp["lat"])))

        return pm, title_txt, phi_txt, regime_patch, regime_txt, circle_handle

    anim = FuncAnimation(fig, animate, frames=n_frames,
                          interval=1000//fps, blit=True)
    out_path = os.path.join(OUT, "GIF2_madrid_map.gif")
    anim.save(out_path, PillowWriter(fps=fps, metadata={"loop":0}), dpi=130)
    plt.close(fig)
    print(f"  Saved: GIF2_madrid_map.gif")


# ══════════════════════════════════════════════════════════════════════════════
# GIF 3 — PARETO COLLAPSE: Objective cloud shrinking as φ drops
# ══════════════════════════════════════════════════════════════════════════════

def gif3_pareto_collapse(fps=5, n_frames=50):
    print("  [GIF 3] Pareto front collapse...")

    phi_levels = np.linspace(1.00, 0.40, n_frames)
    rng = np.random.default_rng(42)

    fig = plt.figure(figsize=(10, 8), facecolor="white")
    ax  = fig.add_subplot(111, projection="3d", facecolor="white")
    ax.set_facecolor("white")
    ax.tick_params(colors="#555", labelsize=7)
    ax.xaxis.pane.fill = False; ax.yaxis.pane.fill = False; ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor("#CCCCCC")
    ax.yaxis.pane.set_edgecolor("#CCCCCC")
    ax.zaxis.pane.set_edgecolor("#CCCCCC")
    ax.grid(color="#CCCCCC", linewidth=0.5)

    ax.set_xlabel("f₃: Reliability (↑)", color="#111111", fontsize=9, labelpad=8)
    ax.set_ylabel("f₁: Satisfaction (↑)", color="#111111", fontsize=9, labelpad=8)
    ax.set_zlabel("−f₂: Efficiency (↑)", color="#111111", fontsize=9, labelpad=8)
    ax.view_init(elev=22, azim=-55)

    # Fixed reference: phi=1.0 cloud (ghost)
    n_pts = 60
    f3_ref = rng.uniform(0.85, 1.00, n_pts)
    f1_ref = rng.uniform(0.85, 1.00, n_pts)
    f2_ref = rng.uniform(-0.09, -0.04, n_pts)
    ax.scatter(f3_ref, f1_ref, f2_ref, s=15, c="white", alpha=0.10,
               edgecolors="none", label="φ=1.0 reference")

    # Utopia star
    ax.scatter([1.0],[1.0],[-0.04], s=200, marker="*",
               c="#FFD700", edgecolors="white", lw=0.8, zorder=10, label="Utopia ★")
    ax.set_xlim(0.1, 1.0); ax.set_ylim(0.1, 1.0); ax.set_zlim(-0.20, -0.02)

    # Dynamic scatter
    scat = ax.scatter([], [], [], s=30, c="cyan", alpha=0.75,
                       edgecolors="white", lw=0.3)

    # φ* plane
    XX, YY = np.meshgrid([0.1, 1.0], [0.1, 1.0])
    plane   = ax.plot_surface(XX*0+0.85, XX, YY, alpha=0.07,
                               color="#FFD700", edgecolor="none")

    title_txt = fig.text(0.5, 0.96,
                          "3D Pareto Front Collapse as Network Reliability Degrades",
                          ha="center", fontsize=13, color="#111111", fontweight="bold")
    phi_txt   = fig.text(0.5, 0.92, "", ha="center", fontsize=11,
                          color="#FFD700", fontweight="bold")
    note_txt  = fig.text(0.5, 0.04,
                          "★ = Utopia point (unattainable ideal)  |  "
                          "Gold plane = φ* = 0.85 threshold  |  "
                          "Ghost = φ=1.0 reference front",
                          ha="center", fontsize=8.5, color="#555")

    def animate(frame):
        phi = phi_levels[frame]
        rng2 = np.random.default_rng(frame)
        n  = max(5, int(60 * phi**2))
        f3 = np.clip(phi*0.88 + rng2.uniform(0, phi*0.12, n), 0.1, 1.0)
        f1 = np.clip(phi*0.88 + rng2.uniform(0, phi*0.12, n), 0.1, 1.0)
        f2 = np.clip(-0.05 - rng2.uniform(0, 0.06/phi, n), -0.20, -0.02)

        scat._offsets3d = (f3, f1, f2)

        # Colour by phi level
        t  = 1.0 - phi / 1.0
        col = plt.cm.plasma(t)
        scat.set_facecolor([col]*n)

        # HV proxy (volume of cloud)
        hv = float(phi**2.5 * 0.85)
        regime = ("SAFE" if phi >= 0.90 else
                  "STANDARD" if phi >= 0.85 else
                  "DEGRADED" if phi >= 0.70 else "⚠ COLLAPSE")
        col_lbl = ("#2E7D32" if phi >= 0.90 else
                   "#F9A825" if phi >= 0.85 else
                   "#E64A19" if phi >= 0.70 else "#B71C1C")
        phi_txt.set_text(f"φ̄ = {phi:.3f}  |  Archive size ∝ HV ≈ {hv:.3f}  |  {regime}")
        phi_txt.set_color(col_lbl)
        title_txt.set_color("#111111")
        return scat, phi_txt

    anim = FuncAnimation(fig, animate, frames=n_frames,
                          interval=1000//fps, blit=False)
    out_path = os.path.join(OUT, "GIF3_pareto_collapse.gif")
    anim.save(out_path, PillowWriter(fps=fps, metadata={"loop":0}), dpi=130)
    plt.close(fig)
    print(f"  Saved: GIF3_pareto_collapse.gif")


# ══════════════════════════════════════════════════════════════════════════════
# GIF 4 — ALGORITHM RACE: QiGA vs NSGA-II vs unaware (convergence over time)
# ══════════════════════════════════════════════════════════════════════════════

def gif4_algorithm_race(fps=8, n_frames=60):
    print("  [GIF 4] Algorithm convergence race...")

    iters  = np.linspace(0, 500, n_frames)
    rng    = np.random.default_rng(7)
    phi    = 0.85

    def converge(algo, it):
        params = {
            "QiGA":   (2.0, 0.95, 80),
            "NSGA-II":(2.1, 0.92, 90),
            "ALNS":   (2.0, 0.93, 95),
            "GA":     (2.3, 0.88, 110),
            "Unaware":(2.8, 0.40, 200),
        }
        z0, scale, spd = params[algo]
        zf = z0 * (1 - 0.82 * scale)
        z  = zf + (z0 - zf) * np.exp(-it/spd)
        z += rng.normal(0, 0.015) * np.exp(-it/200)
        return float(z)

    algo_cfg = [
        ("QiGA",   "#58A6FF", "-",  2.5),
        ("NSGA-II","#2E7D32", "--", 2.2),
        ("ALNS",   "#FF9800", "-.", 2.0),
        ("GA",     "#BB86FC", ":",  1.8),
        ("Unaware","#FF6B6B", "--", 1.8),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="white")
    for ax in axes:
        ax.set_facecolor("white")
        for sp in ax.spines.values(): sp.set_color("#CCCCCC")
        ax.tick_params(colors="#111111")
        ax.xaxis.label.set_color("#111111")
        ax.yaxis.label.set_color("#111111")
        ax.title.set_color("#111111")

    ax_conv, ax_bar = axes

    # Convergence plot
    ax_conv.set_xlim(0, 500); ax_conv.set_ylim(0.2, 2.5)
    ax_conv.set_xlabel("Iteration"); ax_conv.set_ylabel("Objective Z (lower = better)")
    ax_conv.set_title(f"Algorithm Convergence  (φ_min={phi})", fontweight="bold")
    ax_conv.axhline(0.42, ls=":", color="#FFD700", lw=1, alpha=0.6)
    ax_conv.text(490, 0.44, "Best possible", color="#FFD700",
                 fontsize=8, ha="right")
    ax_conv.grid(color="#CCCCCC", alpha=0.5)

    lines_conv = {}
    for algo, col, ls, lw in algo_cfg:
        ln, = ax_conv.plot([], [], color=col, ls=ls, lw=lw, label=algo)
        lines_conv[algo] = ln
    ax_conv.legend(fontsize=8.5, facecolor="white", edgecolor="#CCCCCC",
                   labelcolor="#111111", loc="upper right")

    # SR bar chart
    algo_names = [a for a,_,_,_ in algo_cfg]
    algo_colors= [c for _,c,_,_ in algo_cfg]
    bars = ax_bar.bar(range(len(algo_names)),
                       [0]*len(algo_names),
                       color=algo_colors, alpha=0.85)
    ax_bar.set_xticks(range(len(algo_names)))
    ax_bar.set_xticklabels(algo_names, color="#111111", fontsize=9)
    ax_bar.set_ylim(0, 105); ax_bar.set_ylabel("SR (%)")
    ax_bar.set_title("Service Rate at Current Solution", fontweight="bold")
    ax_bar.axhline(85, ls="--", color="#FFD700", lw=1.5, alpha=0.7)
    ax_bar.grid(color="#CCCCCC", axis="y", alpha=0.4)
    bar_txts = [ax_bar.text(i, 1, "", ha="center", fontsize=8.5,
                             color="white", fontweight="bold")
                for i in range(len(algo_names))]

    # SR model: lower Z → higher SR
    def z_to_sr(z, aware):
        return float(np.clip(98 - z * 28 + (5 if aware else 0), 0, 98))

    iter_txt = fig.text(0.5, 0.97,
                         f"Iteration: 0/500  |  φ_min={phi}  (2025 Madrid Blackout Scenario)",
                         ha="center", fontsize=11, color="#111111")
    fig.suptitle("Algorithm Race: Which Finds the Best Routing Under Reliability Constraints?",
                 fontsize=13, color="#111111", fontweight="bold", y=1.01)

    hist = {a: [] for a,*_ in algo_cfg}

    def animate(frame):
        it = iters[frame]
        iter_txt.set_text(f"Iteration: {int(it)}/500  |  φ_min={phi}  "
                           f"(2025 Madrid Blackout Scenario)")
        for (algo, col, ls, lw), bar, btxt in zip(algo_cfg, bars, bar_txts):
            z  = converge(algo, it)
            hist[algo].append(z)
            x_data = list(iters[:frame+1])
            y_data = hist[algo][:frame+1]
            lines_conv[algo].set_data(x_data, y_data)
            sr = z_to_sr(z, algo != "Unaware")
            bar.set_height(sr)
            bar.set_facecolor("#2E7D32" if sr >= 85 else
                               "#FF9800" if sr >= 70 else "#E53935")
            btxt.set_text(f"{sr:.0f}%"); btxt.set_y(sr + 1)
        return (list(lines_conv.values()) + list(bars) + bar_txts + [iter_txt])

    anim = FuncAnimation(fig, animate, frames=n_frames,
                          interval=1000//fps, blit=False)
    fig.tight_layout()
    out_path = os.path.join(OUT, "GIF4_algorithm_race.gif")
    anim.save(out_path, PillowWriter(fps=fps, metadata={"loop":0}), dpi=120)
    plt.close(fig)
    print(f"  Saved: GIF4_algorithm_race.gif")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 55)
    print("Creating Animated GIFs for CAV Reliability Paper")
    print("=" * 55)
    print(f"Output: {OUT}\n")

    steps = [
        ("GIF 1 — Core concept (5-panel dashboard)",  gif1_core_concept),
        ("GIF 2 — Madrid map evolving (square grid)", gif2_madrid_map),
        ("GIF 3 — Pareto front collapse (3D)",        gif3_pareto_collapse),
        ("GIF 4 — Algorithm convergence race",         gif4_algorithm_race),
    ]
    for i, (label, fn) in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {label}")
        try:
            fn()
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"  WARNING: {e}")

    print("\n" + "=" * 55)
    print("All GIFs saved to:", OUT)
    import os
    for f in sorted(os.listdir(OUT)):
        sz = os.path.getsize(os.path.join(OUT, f)) // 1024
        print(f"  {f:45s} {sz:5d} KB")

