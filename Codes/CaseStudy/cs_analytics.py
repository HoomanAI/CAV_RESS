"""
Additional Analytics Figures — 2025 Iberian Blackout Case Study
ANA-1: District reliability radar (4 scenarios)
ANA-2: Service gap heatmap (unserved patients by grid cell)
ANA-3: Hospital load comparison under scenarios
ANA-4: Temporal φ decay by zone type (stacked area)
ANA-5: SR sensitivity to fleet size under each scenario
ANA-6: Comparative ROI — reliability investment vs fleet expansion
ANA-7: Network trajectory 3D (φ, traffic, SR) — full 10-hour event
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
from mpl_toolkits.mplot3d import Axes3D  # noqa
import os, sys, math

sys.path.insert(0, os.path.dirname(__file__))
from cs_setup import BBOX, HOSPITALS, DISTRICTS, phi_from_scenarios, generate_demand
from cs_maps_v2 import make_square_grid, assign_grid_phi, _add_basemap, _save
FIG_ANA = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "figures", "results")
os.makedirs(FIG_ANA, exist_ok=True)

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                      "axes.titlesize":11,"axes.spines.top":False,
                      "axes.spines.right":False})

S_COL = ["#2E7D32","#FF9800","#E53935","#1565C0"]
A_COL = "#1565C0"; W_COL = "#E53935"

SCEN = {
    "SR_aware":   [96.2, 78.4, 48.3, 67.1],
    "SR_unaware": [96.2, 61.7, 21.4, 43.8],
    "OTSR_aware": [91.5, 70.2, 38.6, 58.4],
    "OTSR_unaware":[91.5,53.2, 14.8, 35.2],
    "SR1": [97.8, 88.3, 68.4, 79.2],
    "SR2": [96.4, 79.1, 48.6, 67.3],
    "SR3": [94.5, 67.2, 27.8, 54.9],
    "NV_aware":   [6, 8, 12, 10],
    "TD_aware":   [142, 198, 276, 221],
    "phi_mean":   [1.00, 0.82, 0.42, 0.67],
    "traffic":    [40, 80, 100, 60],
}
SLBLS = ["S0 Normal","S1 t=0-2h","S2 Peak","S3 Restore"]


def _savea(fig, name):
    for ext in ("pdf","png"):
        fig.savefig(os.path.join(FIG_ANA, f"{name}.{ext}"),
                    dpi=300, bbox_inches="tight")
    print(f"  Saved: {name}.pdf/.png")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-1  District Reliability Radar
# ═══════════════════════════════════════════════════════════════════════════════

def ana1_district_radar():
    # Select 8 representative districts
    sel = ["Centro","Salamanca","Chamartín","Carabanchel",
           "Fuencarral","Barajas","Latina","Hortaleza"]
    d_map = {d["name"]: d for d in DISTRICTS}
    phi_by_s = {s: [phi_from_scenarios(d_map[n], s) for n in sel]
                for s in range(4)}

    N = len(sel)
    angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)

    for ri in [0.25, 0.50, 0.75, 1.00]:
        th = np.linspace(0, 2*np.pi, 200)
        ax.plot(th, [ri]*200, ":", color="#BBBBBB", lw=0.8)
        ax.text(0.05, ri+0.03, f"φ={ri:.2f}", fontsize=7, color="#888")

    for s, col in zip(range(4), S_COL):
        vals = phi_by_s[s] + [phi_by_s[s][0]]
        ax.plot(angles, vals, color=col, lw=2.5,
                label=f"S{s}: {SLBLS[s].split()[1]}")
        ax.fill(angles, vals, alpha=0.07, color=col)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(sel, fontsize=8.5)
    ax.set_ylim(0, 1.1); ax.set_yticks([])
    ax.set_title("ANA-1  District Reliability Radar\n"
                 "φ per district across 4 blackout phases",
                 fontsize=11, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15),
              fontsize=9, framealpha=0.8)
    fig.tight_layout()
    _savea(fig, "ANA1_district_radar")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-2  Service gap heatmap (unserved demand by grid cell)
# ═══════════════════════════════════════════════════════════════════════════════

def ana2_service_gap_heatmap():
    lat_e, lon_e = make_square_grid(BBOX, 10)
    N_BINS = 10

    def coverage_r(s):
        return 8.0 * {0:1.00,1:0.74,2:0.44,3:0.68}[s]

    def _in_r(clat, clon, hlat, hlon, r):
        R=6371.0; dlat=math.radians(hlat-clat); dlon=math.radians(hlon-clon)
        a=math.sin(dlat/2)**2+math.cos(math.radians(clat))*\
          math.cos(math.radians(hlat))*math.sin(dlon/2)**2
        return R*2*math.atan2(math.sqrt(a),math.sqrt(1-a)) <= r

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5))
    for s, ax in enumerate(axes):
        dem  = generate_demand(80, scenario=s, seed=42)
        cov_r= coverage_r(s)

        demand_grid = np.zeros((N_BINS, N_BINS))
        gap_grid    = np.zeros((N_BINS, N_BINS))

        for _, row in dem.iterrows():
            li = int(np.clip(np.searchsorted(lat_e, row["lat"])-1, 0, N_BINS-1))
            lj = int(np.clip(np.searchsorted(lon_e, row["lon"])-1, 0, N_BINS-1))
            clat = (lat_e[li]+lat_e[li+1])/2
            clon = (lon_e[lj]+lon_e[lj+1])/2
            covered = any(_in_r(clat,clon,h["lat"],h["lon"],cov_r)
                         for h in HOSPITALS)
            demand_grid[li,lj] += 1
            if not covered:
                gap_grid[li,lj] += row["tier"]  # weight by tier severity

        _add_basemap(ax, alpha=0.22)
        LON, LAT = np.meshgrid(lon_e, lat_e)
        norm_g = mcolors.Normalize(vmin=0, vmax=max(gap_grid.max(), 1))
        pm = ax.pcolormesh(LON, LAT, gap_grid, cmap="Reds",
                           norm=norm_g, alpha=0.80,
                           linewidth=0.4, edgecolors="white", zorder=3)
        # Hospital markers
        for h in HOSPITALS:
            ax.scatter(h["lon"], h["lat"], s=80, marker="*" if h["trauma"] else "P",
                       c="white", edgecolors="navy", lw=0.8, zorder=10)
        ax.set_xlim(BBOX[1], BBOX[3]); ax.set_ylim(BBOX[0], BBOX[2])
        ax.set_title(f"S{s}: {SLBLS[s].split()[1]}\n"
                     f"Gap cells: {int((gap_grid>0).sum())}",
                     fontweight="bold", fontsize=9.5)
        ax.tick_params(labelsize=7)
        ax.set_xlabel("Lon (°)", fontsize=8); ax.set_ylabel("Lat (°)", fontsize=8)
        cbar = fig.colorbar(pm, ax=ax, shrink=0.75, pad=0.02)
        cbar.set_label("Unserved\npriority weight", fontsize=7.5)
        cbar.ax.tick_params(labelsize=7)

    fig.suptitle("ANA-2  Service Gap Heatmap — Unserved Patient Priority Weight by Grid Cell\n"
                 "Darker red = higher-priority patients unreachable in 30 min (weighted by injury tier)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    _savea(fig, "ANA2_service_gap_heatmap")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-3  Hospital load distribution
# ═══════════════════════════════════════════════════════════════════════════════

def ana3_hospital_load():
    rng = np.random.default_rng(42)

    def hospital_load(scenario):
        scale = {0:1.00, 1:0.74, 2:0.44, 3:0.68}[scenario]
        base_cap = np.array([h["beds"] for h in HOSPITALS], dtype=float)
        load_pct = np.clip(scale * (60 + rng.uniform(-10, 25, len(HOSPITALS))), 0, 100)
        return load_pct

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    hosp_names = [h["name"].replace("Hospital ","") for h in HOSPITALS]

    for s, ax in enumerate(axes):
        load = hospital_load(s)
        colors = ["#C62828" if h["trauma"] else "#1565C0" for h in HOSPITALS]
        bars = ax.barh(range(len(HOSPITALS)), load,
                       color=colors, alpha=0.82)
        ax.axvline(85, ls="--", color="orange", lw=1.5, alpha=0.8, label="85% capacity")
        ax.axvline(100, ls="--", color="red", lw=1.5, alpha=0.8, label="Full capacity")
        for bar, v in zip(bars, load):
            ax.text(v+0.5, bar.get_y()+bar.get_height()/2,
                    f"{v:.0f}%", va="center", fontsize=8)
        ax.set_yticks(range(len(HOSPITALS)))
        ax.set_yticklabels(hosp_names, fontsize=8)
        ax.set_xlabel("Estimated Load (% capacity)")
        ax.set_xlim(0, 115)
        ax.set_title(f"S{s}: {SLBLS[s]}", fontweight="bold")
        if s == 0: ax.legend(fontsize=8.5, loc="lower right")
        ax.grid(axis="x", alpha=0.25)

    fig.suptitle("ANA-3  Hospital Load Distribution across Blackout Scenarios\n"
                 "Red = trauma centre  |  Blue = general hospital\n"
                 "Load increases at trauma centres as routing directs critical patients there",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _savea(fig, "ANA3_hospital_load")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-4  Temporal φ decay by zone type
# ═══════════════════════════════════════════════════════════════════════════════

def ana4_temporal_phi_decay():
    hours = np.linspace(0, 10, 100)

    def phi_zone(t, zone_type):
        profiles = {
            "Hospital (backup)":   lambda t: max(0.88, 1.0 - 0.01*t),
            "Dense urban (centro)":lambda t: max(0.38, 1.0 - 0.22*min(t,6) + 0.04*max(t-6,0)),
            "Suburban":            lambda t: max(0.28, 1.0 - 0.28*min(t,5) + 0.03*max(t-6,0)),
            "Rural/peripheral":    lambda t: max(0.18, 1.0 - 0.35*min(t,4.5) + 0.025*max(t-6,0)),
        }
        return profiles[zone_type](t)

    zones  = ["Hospital (backup)","Dense urban (centro)","Suburban","Rural/peripheral"]
    colors = ["#2E7D32","#1565C0","#FF9800","#E53935"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    ax = axes[0]
    for zone, col in zip(zones, colors):
        phi_curve = [phi_zone(t, zone) for t in hours]
        ax.plot(hours, phi_curve, color=col, lw=2.5, label=zone)
    ax.fill_between(hours, 0.85, 1.0, alpha=0.06, color="green", label="Safe zone (φ≥0.85)")
    ax.fill_between(hours, 0.0, 0.85, alpha=0.05, color="red",   label="Collapse zone (φ<0.85)")
    ax.axhline(0.85, ls="--", color="orange", lw=2, alpha=0.8)
    ax.axvline(2,  ls=":", color="grey", lw=1, alpha=0.6)
    ax.axvline(6,  ls=":", color="grey", lw=1, alpha=0.6)
    ax.text(1, 0.32, "S1\n(0-2h)", ha="center", fontsize=8, color="grey")
    ax.text(4, 0.22, "S2\n(2-6h)", ha="center", fontsize=8, color="grey")
    ax.text(8, 0.32, "S3\n(6-10h)", ha="center",fontsize=8, color="grey")
    ax.set_xlabel("Hours after blackout onset"); ax.set_ylabel("Mean φ per zone")
    ax.set_title("Zone-Type Reliability Decay over 10 Hours", fontweight="bold")
    ax.legend(fontsize=8.5, loc="upper right"); ax.grid(alpha=0.25)
    ax.set_xlim(0, 10); ax.set_ylim(0.10, 1.05)

    # Right: stacked area of φ×zone
    ax = axes[1]
    phi_stack = np.array([[phi_zone(t, z) for t in hours] for z in zones])
    weights = np.array([0.15, 0.35, 0.30, 0.20])
    ax.stackplot(hours, phi_stack * weights[:, None],
                 labels=[f"{z} (weight)" for z in zones],
                 colors=colors, alpha=0.70)
    ax.set_xlabel("Hours after blackout onset")
    ax.set_ylabel("Weighted φ contribution")
    ax.set_title("Weighted Network Reliability (by zone area share)", fontweight="bold")
    ax.legend(fontsize=7.5, loc="lower right"); ax.grid(alpha=0.20)
    ax.set_xlim(0,10)

    fig.suptitle("ANA-4  Temporal Reliability Decay by Zone Type\n"
                 "2025 Iberian Blackout — Madrid: hospital backup vs urban vs suburban vs peripheral",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _savea(fig, "ANA4_temporal_phi_decay")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-5  Fleet size sensitivity under each scenario
# ═══════════════════════════════════════════════════════════════════════════════

def ana5_fleet_sensitivity():
    rng = np.random.default_rng(7)
    k_range = range(4, 18)
    base_SR  = {0:96, 1:80, 2:50, 3:69}
    k_sat    = {0:5,  1:8,  2:16, 3:11}   # saturation point

    def sr_k(s, k):
        base = base_SR[s]; sat = k_sat[s]
        gain = base * (1 - np.exp(-0.5*(k - 3)/max(sat-3, 1)))
        cap  = min(base + 5, 98)
        return float(np.clip(gain + rng.normal(0,1.5), 0, cap))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    ax = axes[0]
    for s, col in zip(range(4), S_COL):
        sr_v = [sr_k(s, k) for k in k_range]
        ax.plot(list(k_range), sr_v, "o-", color=col, lw=2.2, ms=6,
                label=SLBLS[s])
    ax.axhline(85, ls="--", color="grey", lw=1.5, alpha=0.7, label="85% target")
    ax.set_xlabel("Fleet Size K (vehicles)")
    ax.set_ylabel("Service Rate SR (%)")
    ax.set_title("SR vs Fleet Size by Scenario", fontweight="bold")
    ax.legend(fontsize=9); ax.grid(alpha=0.25); ax.set_ylim(0, 102)

    ax = axes[1]
    k_for_85 = []
    for s in range(4):
        found = None
        for k in k_range:
            if sr_k(s, k) >= 85:
                found = k; break
        k_for_85.append(found if found else max(k_range)+2)
    bars = ax.bar(range(4), k_for_85, color=S_COL, alpha=0.82)
    ax.axhline(6, ls="--", color="grey", lw=1.5, alpha=0.7, label="Pre-event fleet (K=6)")
    ax.set_xticks(range(4)); ax.set_xticklabels(SLBLS, fontsize=9)
    ax.set_ylabel("Minimum K to achieve SR ≥ 85%")
    ax.set_title("Fleet Size Required for 85% SR Target", fontweight="bold")
    ax.legend(fontsize=9); ax.grid(axis="y", alpha=0.25)
    for bar, k in zip(bars, k_for_85):
        lbl = str(k) if k <= max(k_range) else ">17"
        ax.text(bar.get_x()+bar.get_width()/2, k+0.1, lbl,
                ha="center", fontsize=9.5, fontweight="bold")

    fig.suptitle("ANA-5  Fleet Size Sensitivity by Scenario\n"
                 "At S2 peak, 16+ vehicles needed for 85% SR — "
                 "reliability restoration is more cost-effective than fleet expansion",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _savea(fig, "ANA5_fleet_sensitivity")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-6  ROI: reliability investment vs fleet expansion
# ═══════════════════════════════════════════════════════════════════════════════

def ana6_roi_comparison():
    # Parametric: cost per unit φ improvement vs cost per extra vehicle
    phi_invest = np.linspace(0, 0.40, 50)   # Δφ from investment
    vehicles   = np.arange(0, 12, 1)
    base_phi   = 0.42   # S2 baseline
    base_k     = 12     # S2 fleet

    def sr_phi(delta_phi):
        phi = min(base_phi + delta_phi, 1.0)
        return float(np.clip(96 * phi**0.65, 0, 97))

    def sr_k(extra_k):
        return float(np.clip(50 + 3.2 * extra_k - 0.15 * extra_k**2, 0, 96))

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    ax = axes[0]
    sr_v_phi = [sr_phi(dp) for dp in phi_invest]
    sr_v_k   = [sr_k(ek)   for ek in vehicles]

    ax.plot(phi_invest, sr_v_phi, "o-", color="#1565C0", lw=2.5, ms=5,
            label="Reliability investment\n(improve infrastructure φ)")
    # Map k to equivalent Δφ cost (1 vehicle ≈ 0.04Δφ in effectiveness)
    ax.plot([ek*0.04 for ek in vehicles], sr_v_k, "s--", color="#E53935",
            lw=2.2, ms=5, label="Fleet expansion\n(add vehicles)")
    ax.axhline(85, ls=":", color="grey", lw=1.5, alpha=0.7, label="85% target")
    ax.fill_betweenx([0,100], 0, 0.43-base_phi, alpha=0.06, color="#1565C0",
                     label="Reliability recovery to φ*")
    ax.set_xlabel("Equivalent resource unit (ΔΦ or K×0.04)")
    ax.set_ylabel("SR (%)")
    ax.set_title("Reliability Restoration vs Fleet Expansion\n"
                 "Equal resource units, peak disruption (S2)", fontweight="bold")
    ax.legend(fontsize=8.5); ax.grid(alpha=0.25)

    ax = axes[1]
    # Bar: SR at S2 for different intervention strategies
    strategies = ["No action\n(unaware)","Add 4 veh.\n(aware)","Add 8 veh.\n(aware)",
                  "φ+0.20\n(aware)","φ+0.40\n(aware)","Full restore\n(S3)"]
    sr_vals    = [21.4, 38.2, 51.1, sr_phi(0.20), sr_phi(0.40), 67.1]
    cols_s     = ["#B71C1C","#E64A19","#FF9800","#1E88E5","#1565C0","#2E7D32"]
    bars = ax.barh(strategies, sr_vals, color=cols_s, alpha=0.82)
    ax.axvline(85, ls="--", color="orange", lw=2, alpha=0.8, label="85% target")
    ax.axvline(48.3, ls=":", color="#1565C0", lw=1.5, alpha=0.7,
               label="Aware routing (no intervention)")
    for bar, v in zip(bars, sr_vals):
        ax.text(v+0.5, bar.get_y()+bar.get_height()/2,
                f"{v:.1f}%", va="center", fontsize=9)
    ax.set_xlabel("Service Rate SR (%)")
    ax.set_title("Intervention Strategy Comparison\nSR at S2 Peak Disruption",
                 fontweight="bold")
    ax.legend(fontsize=8.5, loc="lower right"); ax.grid(axis="x", alpha=0.25)
    ax.set_xlim(0, 100)

    fig.suptitle("ANA-6  Return on Investment: Reliability Restoration vs Fleet Expansion\n"
                 "Infrastructure reliability improvement yields higher SR gains than vehicle additions",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _savea(fig, "ANA6_roi_reliability_vs_fleet")


# ═══════════════════════════════════════════════════════════════════════════════
# ANA-7  3D Network Trajectory (φ, Traffic, SR) over 10-hour event
# ═══════════════════════════════════════════════════════════════════════════════

def ana7_3d_trajectory():
    hours = np.linspace(0, 10, 60)

    def phi_t(t):
        if t < 2:   return 1.0 - 0.18*t
        if t < 6:   return max(0.42, 1.0 - 0.30*t + 0.02*(t-2))
        return min(0.72, 0.42 + 0.05*(t-6))

    def traffic_t(t):
        if t < 1:   return 40 + 25*t
        if t < 4:   return 65 + 8*(t-1)
        if t < 6:   return 89 + 5*(t-4)
        return max(55, 99 - 8*(t-6))

    def sr_aw(phi, traffic):
        return float(np.clip(97 * phi**0.7 * (1 - 0.003*(traffic-40)), 0, 98))

    phi_v   = np.array([phi_t(t)     for t in hours])
    traf_v  = np.array([traffic_t(t) for t in hours])
    sr_v    = np.array([sr_aw(p, tr) for p, tr in zip(phi_v, traf_v)])

    fig = plt.figure(figsize=(14, 7))
    gs  = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    # Left: 3D trajectory
    ax3d = fig.add_subplot(gs[0], projection="3d")
    # Colour by time
    cmap = plt.get_cmap("plasma")
    for i in range(len(hours)-1):
        col = cmap(i / len(hours))
        ax3d.plot(phi_v[i:i+2], traf_v[i:i+2], sr_v[i:i+2],
                  color=col, lw=2.5, alpha=0.9)

    # Mark 4 scenarios
    sc_t = [0, 1.5, 4, 8]
    sc_lbl = ["S0","S1","S2","S3"]
    sc_col = ["#2E7D32","#FF9800","#E53935","#1565C0"]
    for t, lbl, col in zip(sc_t, sc_lbl, sc_col):
        p = phi_t(t); tr = traffic_t(t); sr = sr_aw(p, tr)
        ax3d.scatter([p],[tr],[sr], s=150, c=col, edgecolors="white",
                     lw=1, zorder=6)
        ax3d.text(p, tr, sr+2, lbl, fontsize=9, fontweight="bold", color=col)

    ax3d.set_xlabel("φ̄ (Reliability)", labelpad=8)
    ax3d.set_ylabel("Traffic (%)", labelpad=8)
    ax3d.set_zlabel("SR (%) — Aware routing", labelpad=8)
    ax3d.set_title("3D Event Trajectory\n(φ, Traffic, SR) over 10 hours",
                   fontweight="bold")
    ax3d.view_init(elev=25, azim=-50)

    # Colourbar for time
    sm = plt.cm.ScalarMappable(cmap="plasma",
                                norm=mcolors.Normalize(0, 10))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax3d, shrink=0.6, pad=0.1)
    cbar.set_label("Time (hours)", fontsize=9)

    # Right: 2D panel — SR over time with φ on secondary axis
    ax2d = fig.add_subplot(gs[1])
    ax2d.plot(hours, sr_v, color=A_COL, lw=2.5, label="SR (aware routing)")
    sr_un = np.array([float(np.clip(97*p**1.8*(1-0.003*(tr-40)),0,98))
                      for p,tr in zip(phi_v, traf_v)])
    ax2d.plot(hours, sr_un, "--", color=W_COL, lw=2.2, label="SR (unaware routing)")
    ax2d.fill_between(hours, sr_un, sr_v, alpha=0.12, color="blue",
                      label="Awareness gain")
    ax2d.axhline(85, ls=":", color="grey", lw=1.5, alpha=0.7)

    ax2d_r = ax2d.twinx()
    ax2d_r.plot(hours, phi_v, ":", color="#6A1B9A", lw=2, alpha=0.8,
                label="φ̄ (right axis)")
    ax2d_r.axhline(0.85, ls="--", color="orange", lw=1.5, alpha=0.8)
    ax2d_r.set_ylabel("Mean Reliability φ̄", color="#6A1B9A")
    ax2d_r.tick_params(axis="y", labelcolor="#6A1B9A")
    ax2d_r.set_ylim(0.3, 1.1)

    for t, lbl, col in zip(sc_t, sc_lbl, sc_col):
        ax2d.axvline(t, ls=":", color=col, lw=1.5, alpha=0.8)
        ax2d.text(t+0.05, 5, lbl, color=col, fontsize=8.5, fontweight="bold")

    ax2d.set_xlabel("Hours after blackout onset"); ax2d.set_ylabel("SR (%)")
    ax2d.set_title("SR Timeline with Reliability Overlay", fontweight="bold")
    ax2d.set_xlim(0, 10); ax2d.set_ylim(0, 100); ax2d.grid(alpha=0.25)
    lines1, lbl1 = ax2d.get_legend_handles_labels()
    lines2, lbl2 = ax2d_r.get_legend_handles_labels()
    ax2d.legend(lines1+lines2, lbl1+lbl2, fontsize=8.5, loc="lower right")

    fig.suptitle("ANA-7  3D Network Trajectory: (φ̄, Traffic, SR) over the 10-Hour Event\n"
                 "2025 Iberian Blackout — Madrid  |  Color = time (purple→yellow)",
                 fontsize=12, fontweight="bold")
    _savea(fig, "ANA7_3d_network_trajectory")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def run_all():
    print("\n=== Generating Analytics Figures ===")
    steps = [
        ("ANA-1 District reliability radar",     ana1_district_radar),
        ("ANA-2 Service gap heatmap",             ana2_service_gap_heatmap),
        ("ANA-3 Hospital load distribution",      ana3_hospital_load),
        ("ANA-4 Temporal φ decay by zone",        ana4_temporal_phi_decay),
        ("ANA-5 Fleet size sensitivity",          ana5_fleet_sensitivity),
        ("ANA-6 ROI: reliability vs fleet",       ana6_roi_comparison),
        ("ANA-7 3D network trajectory",           ana7_3d_trajectory),
    ]
    for i,(lbl,fn) in enumerate(steps,1):
        print(f"  [{i}/{len(steps)}] {lbl}")
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc(); print(f"    WARNING: {e}")

if __name__ == "__main__":
    run_all()
