"""
Hexagonal Cell Maps — 2025 Iberian Blackout Case Study
Creates H3-style hexagonal grid maps over Madrid showing:
  Map 1: φ_ij reliability per hex cell (4 scenarios)
  Map 2: Zone failure risk (1 − φ)
  Map 3: Comparison S0 vs S2 (before vs peak disruption)
  Map 4: Network accessibility (% feasible arcs per hex)
  Map 5: Hospital coverage under S0 and S2
  Map 6: SOO vs MOO routing difference map
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import matplotlib.cm as cm
from matplotlib.patches import RegularPolygon
from shapely.geometry import Point, Polygon
import os, sys, math

sys.path.insert(0, os.path.dirname(__file__))
from cs_setup import BBOX, HOSPITALS, DISTRICTS, phi_from_scenarios, CENTER

BASE    = os.path.dirname(os.path.dirname(__file__))
DATA    = os.path.join(BASE, "data")
FIG_MAP = os.path.join(BASE, "figures", "maps")
os.makedirs(FIG_MAP, exist_ok=True)

plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                      "axes.titlesize":11})

# ── Hex grid builder ──────────────────────────────────────────────────────────

def hex_grid(bbox_ll, hex_size_km=0.8):
    """
    Build a regular hexagonal grid over bbox (south,west,north,east).
    Returns list of (center_lat, center_lon, hex_polygon_lonlat).
    hex_size_km = approximate hex 'radius' in km.
    """
    south, west, north, east = bbox_ll
    # Convert km to degrees (approximate)
    d_lat = hex_size_km / 111.0
    d_lon = hex_size_km / (111.0 * math.cos(math.radians((south+north)/2)))

    hexes = []
    row = 0
    lat = south
    while lat <= north + d_lat:
        offset = (row % 2) * d_lon * 0.5
        lon = west - d_lon
        while lon <= east + d_lon:
            clat = lat
            clon = lon + offset
            # Build flat-top hexagon in lat/lon coords
            angles = [math.pi/6 + math.pi/3 * i for i in range(6)]
            verts = [(clon + d_lon * math.cos(a),
                      clat + d_lat * math.sin(a)) for a in angles]
            hexes.append({"clat": clat, "clon": clon,
                          "poly": Polygon(verts)})
            lon += d_lon * math.sqrt(3)
        lat += d_lat * 1.5
        row += 1
    return hexes


def assign_hex_phi(hexes, scenario):
    """Assign mean φ to each hex based on district model."""
    def dist_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2-lat1); dlon = math.radians(lon2-lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    rng = np.random.default_rng(scenario * 100 + 7)
    for h in hexes:
        best_phi = 0.55
        best_d   = 1e9
        for d in DISTRICTS:
            dk = dist_km(h["clat"], h["clon"], d["lat"], d["lon"])
            if dk < d["r"] and dk < best_d:
                best_d   = dk
                best_phi = phi_from_scenarios(d, scenario)
        # Hospital proximity boost
        for hosp in HOSPITALS:
            dk = dist_km(h["clat"], h["clon"], hosp["lat"], hosp["lon"])
            if dk < 0.8:
                best_phi = max(best_phi, 0.88)
        # Spatial noise
        noise = float(rng.normal(0, 0.035))
        h[f"phi_s{scenario}"] = float(np.clip(best_phi + noise, 0.10, 1.00))
    return hexes


def _in_bbox(h, bbox):
    s,w,n,e = bbox
    return s <= h["clat"] <= n and w <= h["clon"] <= e


def load_edge_gdf(scenario):
    path = os.path.join(DATA, f"edges_S{scenario}.gpkg")
    if os.path.exists(path):
        return gpd.read_file(path)
    return None


def _save(fig, name):
    for ext in ("pdf","png"):
        fig.savefig(os.path.join(FIG_MAP, f"{name}.{ext}"),
                    dpi=300, bbox_inches="tight")
    print(f"  Saved: {name}.pdf/.png")
    plt.close(fig)


# ── Shared drawing helpers ─────────────────────────────────────────────────────

def _draw_hexes(ax, hexes, values, cmap, vmin, vmax, alpha=0.82):
    """Draw filled hexagons coloured by values dict keyed by index."""
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap_fn = plt.get_cmap(cmap)
    for i, h in enumerate(hexes):
        v   = values.get(i, np.nan)
        if np.isnan(v): continue
        col = cmap_fn(norm(v))
        poly = h["poly"]
        xs, ys = poly.exterior.xy
        ax.fill(xs, ys, color=col, alpha=alpha, linewidth=0, zorder=2)
        ax.plot(xs, ys, color="white", linewidth=0.15, alpha=0.4, zorder=3)
    return norm, cmap_fn

def _draw_roads(ax, edge_gdf, lw=0.25, color="#555555", alpha=0.3):
    if edge_gdf is not None:
        edge_gdf.plot(ax=ax, linewidth=lw, color=color, alpha=alpha, zorder=1)

def _draw_hospitals(ax, size=80, zorder=10):
    for h in HOSPITALS:
        mk = "H" if h["trauma"] else "+"
        ax.scatter(h["lon"], h["lat"], s=size, marker=mk,
                   c="white", edgecolors="black", linewidths=0.8,
                   zorder=zorder)

def _style_ax(ax, title, bbox=BBOX):
    ax.set_xlim(bbox[1], bbox[3]); ax.set_ylim(bbox[0], bbox[2])
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title(title, fontweight="bold", pad=6)
    ax.set_aspect("equal"); ax.grid(alpha=0.15)

def _scalebar(ax, lon_left, lat_bottom, km=5):
    deg = km / (111.0 * math.cos(math.radians(lat_bottom)))
    ax.plot([lon_left, lon_left+deg], [lat_bottom, lat_bottom],
            "k-", lw=3, solid_capstyle="butt", zorder=15)
    ax.text(lon_left+deg/2, lat_bottom+0.003, f"{km} km",
            ha="center", fontsize=7, zorder=15)

def _north_arrow(ax, lon, lat):
    ax.annotate("N", xy=(lon, lat+0.006), xytext=(lon, lat),
                ha="center", fontsize=9, fontweight="bold",
                arrowprops=dict(arrowstyle="->", lw=1.5))

# ─────────────────────────────────────────────────────────────────────────────
# MAP 1 — Reliability φ per hex: 4-panel (S0 to S3)
# ─────────────────────────────────────────────────────────────────────────────

def map1_phi_four_scenarios():
    print("  [Map 1] Reliability φ — 4 scenarios...")
    hexes = hex_grid(BBOX, hex_size_km=0.9)
    hexes = [h for h in hexes if _in_bbox(h, BBOX)]
    for s in range(4): assign_hex_phi(hexes, s)

    titles = ["S0: Pre-Event (normal, φ̄=1.00)",
              "S1: Early Phase t=0-2h (φ̄≈0.80)",
              "S2: Peak Disruption t=2-6h (φ̄≈0.42)",
              "S3: Partial Restoration t=6-10h (φ̄≈0.67)"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    axes = axes.flatten()

    for s, ax in enumerate(axes):
        phi_key = f"phi_s{s}"
        vals = {i: h[phi_key] for i, h in enumerate(hexes)}
        edge_gdf = load_edge_gdf(s)
        _draw_roads(ax, edge_gdf)
        norm, cmap_fn = _draw_hexes(ax, hexes, vals, "RdYlGn", 0.1, 1.0)
        _draw_hospitals(ax)
        _style_ax(ax, titles[s])

        mean_phi = np.mean(list(vals.values()))
        ax.text(0.02, 0.97, f"φ̄ = {mean_phi:.3f}",
                transform=ax.transAxes, fontsize=9, va="top",
                bbox=dict(fc="white", alpha=0.8, ec="grey"))

        if s == 3:
            _scalebar(ax, BBOX[1]+0.01, BBOX[0]+0.01)
            _north_arrow(ax, BBOX[3]-0.03, BBOX[0]+0.01)

    # Shared colourbar
    sm = cm.ScalarMappable(cmap="RdYlGn",
                           norm=mcolors.Normalize(vmin=0.1, vmax=1.0))
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=axes, orientation="vertical",
                        fraction=0.02, pad=0.04, shrink=0.8)
    cbar.set_label("Link Reliability φᵢⱼ", fontsize=11)
    cbar.ax.axhline(0.85, color="orange", lw=2, ls="--")
    cbar.ax.text(1.05, 0.85, "φ*", transform=cbar.ax.transAxes,
                 color="orange", fontsize=9, va="center")

    # Legend
    h_patch  = mpatches.Patch(fc="white", ec="k", label="Trauma centre (H)")
    h2_patch = mpatches.Patch(fc="white", ec="k", label="Hospital (+)")
    fig.legend(handles=[h_patch, h2_patch], loc="lower left",
               fontsize=8.5, framealpha=0.8)

    fig.suptitle("MAP-1  Network Link Reliability φᵢⱼ by Hexagonal Zone\n"
                 "2025 Iberian Peninsula Blackout — Madrid Metropolitan Area",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP1_reliability_hex_4scenarios")


# ─────────────────────────────────────────────────────────────────────────────
# MAP 2 — Zone Failure Risk (1 − φ) at peak disruption
# ─────────────────────────────────────────────────────────────────────────────

def map2_failure_risk():
    print("  [Map 2] Zone failure risk...")
    hexes = hex_grid(BBOX, hex_size_km=0.9)
    hexes = [h for h in hexes if _in_bbox(h, BBOX)]
    assign_hex_phi(hexes, 2)   # peak disruption

    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))

    # Left: failure probability (1−φ)
    ax = axes[0]
    vals = {i: 1.0 - h["phi_s2"] for i, h in enumerate(hexes)}
    edge_gdf = load_edge_gdf(2)
    _draw_roads(ax, edge_gdf)
    norm, cmap_fn = _draw_hexes(ax, hexes, vals, "YlOrRd", 0.0, 0.85)
    _draw_hospitals(ax)
    _style_ax(ax, "Failure Probability (1 − φᵢⱼ) at Peak Disruption (S2)")
    sm = cm.ScalarMappable(cmap="YlOrRd", norm=norm)
    sm.set_array([])
    plt.colorbar(sm, ax=ax, label="Failure Probability", shrink=0.8)
    _scalebar(ax, BBOX[1]+0.01, BBOX[0]+0.01)
    _north_arrow(ax, BBOX[3]-0.03, BBOX[0]+0.01)

    # Right: risk classification (4 zones)
    ax = axes[1]
    zone_cmap = mcolors.ListedColormap(["#2E7D32","#F9A825","#E64A19","#B71C1C"])
    zone_bounds = [0.0, 0.25, 0.45, 0.65, 1.0]
    zone_norm   = mcolors.BoundaryNorm(zone_bounds, zone_cmap.N)
    _draw_roads(ax, edge_gdf, color="#888888")
    for i, h in enumerate(hexes):
        fp   = vals[i]
        col  = zone_cmap(zone_norm(fp))
        poly = h["poly"]; xs, ys = poly.exterior.xy
        ax.fill(xs, ys, color=col, alpha=0.80, linewidth=0, zorder=2)
        ax.plot(xs, ys, color="white", linewidth=0.15, alpha=0.4, zorder=3)
    _draw_hospitals(ax)
    _style_ax(ax, "Failure Risk Classification (S2 — Peak)")
    patches = [mpatches.Patch(color=zone_cmap(zone_norm(v)), label=l) for v,l in [
        (0.10, "LOW  (φ≥0.75)"),
        (0.35, "MODERATE  (0.55–0.75)"),
        (0.55, "HIGH  (0.35–0.55)"),
        (0.75, "CRITICAL  (φ<0.35)")]]
    ax.legend(handles=patches, loc="lower right", fontsize=8.5,
              title="Risk Level", title_fontsize=8.5)

    fig.suptitle("MAP-2  Zone Failure Risk — 2025 Iberian Blackout\n"
                 "Peak Disruption Phase (t = 2–6 hours post-event)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP2_failure_risk_zones")


# ─────────────────────────────────────────────────────────────────────────────
# MAP 3 — Reliability change S0 → S2 (delta map)
# ─────────────────────────────────────────────────────────────────────────────

def map3_delta_map():
    print("  [Map 3] Reliability change S0 → S2...")
    hexes = hex_grid(BBOX, hex_size_km=0.9)
    hexes = [h for h in hexes if _in_bbox(h, BBOX)]
    assign_hex_phi(hexes, 0)
    assign_hex_phi(hexes, 2)

    delta = {i: h["phi_s2"] - h["phi_s0"] for i, h in enumerate(hexes)}

    fig, ax = plt.subplots(figsize=(10, 8))
    edge_gdf = load_edge_gdf(2)
    _draw_roads(ax, edge_gdf)
    norm, cmap_fn = _draw_hexes(ax, hexes, delta, "RdBu", -0.8, 0.0, alpha=0.85)
    _draw_hospitals(ax)
    _style_ax(ax, "Reliability Loss Δφ = φ(S2) − φ(S0)\n"
              "Darker red = greater disruption from blackout")
    sm = cm.ScalarMappable(cmap="RdBu", norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, label="Δφ (negative = reliability lost)",
                        shrink=0.8)
    _scalebar(ax, BBOX[1]+0.01, BBOX[0]+0.01)
    _north_arrow(ax, BBOX[3]-0.03, BBOX[0]+0.01)

    # Annotate worst zones
    worst = sorted(hexes, key=lambda h: h["phi_s2"])[:3]
    for h in worst:
        ax.text(h["clon"], h["clat"], f"{h['phi_s2']:.2f}",
                fontsize=6.5, ha="center", va="center",
                color="white", fontweight="bold", zorder=10)

    fig.suptitle("MAP-3  Reliability Loss Map: Before vs Peak Blackout\n"
                 "2025 Iberian Peninsula Blackout — Madrid",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP3_reliability_delta_S0_to_S2")


# ─────────────────────────────────────────────────────────────────────────────
# MAP 4 — Network accessibility (% arcs feasible at φ_min=0.85 threshold)
# ─────────────────────────────────────────────────────────────────────────────

def map4_accessibility():
    print("  [Map 4] Network accessibility per scenario...")
    hexes = hex_grid(BBOX, hex_size_km=1.2)
    hexes = [h for h in hexes if _in_bbox(h, BBOX)]
    for s in range(4): assign_hex_phi(hexes, s)

    PHI_MIN = 0.85
    fig, axes = plt.subplots(1, 4, figsize=(18, 5.5))
    titles = [f"S{s}" for s in range(4)]
    label_extra = ["normal","early","peak","restore"]

    for s, ax in enumerate(axes):
        # Accessibility = I(phi >= phi_min) per hex (1=accessible, 0=excluded)
        vals = {i: 1.0 if h[f"phi_s{s}"] >= PHI_MIN else 0.0
                for i, h in enumerate(hexes)}
        accessible_pct = np.mean(list(vals.values())) * 100
        edge_gdf = load_edge_gdf(s)
        _draw_roads(ax, edge_gdf, lw=0.2, color="#444")
        cmap_acc = mcolors.ListedColormap(["#E53935","#43A047"])
        for i, h in enumerate(hexes):
            col  = cmap_acc(int(vals[i]))
            poly = h["poly"]; xs, ys = poly.exterior.xy
            ax.fill(xs, ys, color=col, alpha=0.75, linewidth=0, zorder=2)
            ax.plot(xs, ys, color="white", lw=0.1, alpha=0.3, zorder=3)
        _draw_hospitals(ax, size=55)
        _style_ax(ax, f"S{s}: {label_extra[s].capitalize()}")
        ax.text(0.02, 0.97, f"Accessible:\n{accessible_pct:.0f}%",
                transform=ax.transAxes, fontsize=8.5, va="top",
                bbox=dict(fc="white", alpha=0.8, ec="grey"))

    patches = [mpatches.Patch(color="#43A047", label=f"Accessible (φ≥{PHI_MIN})"),
               mpatches.Patch(color="#E53935", label=f"Excluded (φ<{PHI_MIN})")]
    fig.legend(handles=patches, loc="lower center", ncol=2,
               fontsize=9, framealpha=0.8)
    fig.suptitle(f"MAP-4  Network Accessibility under φ_min={PHI_MIN} Threshold\n"
                 "Green = feasible arcs; Red = excluded by reliability constraint",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP4_network_accessibility")


# ─────────────────────────────────────────────────────────────────────────────
# MAP 5 — Hospital service coverage radius under S0 and S2
# ─────────────────────────────────────────────────────────────────────────────

def map5_hospital_coverage():
    print("  [Map 5] Hospital coverage radius S0 vs S2...")
    # Coverage radius shrinks as φ drops (longer travel times mean smaller catchment)
    # Estimate: coverage_km = base_km * phi_factor
    # At S0 (phi=1.0): trauma centre covers ~8km in 30 min
    # At S2 (phi=0.42): same 30min limit gives ~3.5km (BPR ×2 travel times)

    def coverage_radius(scenario, is_trauma):
        base = 8.0 if is_trauma else 5.0
        phi_factors = {0: 1.00, 1: 0.75, 2: 0.44, 3: 0.68}
        return base * phi_factors[scenario]

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    scenario_pairs = [(0, "S0: Normal (30-min coverage)"),
                      (2, "S2: Peak Disruption (30-min coverage)")]

    for ax, (s, title) in zip(axes, scenario_pairs):
        hexes = hex_grid(BBOX, hex_size_km=0.9)
        hexes = [h for h in hexes if _in_bbox(h, BBOX)]
        assign_hex_phi(hexes, s)

        phi_vals = {i: h[f"phi_s{s}"] for i, h in enumerate(hexes)}
        edge_gdf = load_edge_gdf(s)
        _draw_roads(ax, edge_gdf)

        # Background hex reliability
        norm, cmap_fn = _draw_hexes(ax, hexes, phi_vals, "Greys_r", 0.1, 1.0,
                                     alpha=0.35)

        # Coverage circles per hospital
        for hosp in HOSPITALS:
            r_km  = coverage_radius(s, hosp["trauma"])
            r_deg = r_km / (111.0 * math.cos(math.radians(hosp["lat"])))
            col   = "#1565C0" if hosp["trauma"] else "#2E7D32"
            circle = plt.Circle((hosp["lon"], hosp["lat"]), r_deg,
                                 fill=True, alpha=0.18, color=col, zorder=4)
            ax.add_patch(circle)
            circle2 = plt.Circle((hosp["lon"], hosp["lat"]), r_deg,
                                  fill=False, lw=1.2, color=col, zorder=5)
            ax.add_patch(circle2)
            mk = "H" if hosp["trauma"] else "+"
            ax.scatter(hosp["lon"], hosp["lat"], s=90, marker=mk,
                       c="white", edgecolors=col, linewidths=1.2, zorder=10)

        _style_ax(ax, title)
        _scalebar(ax, BBOX[1]+0.01, BBOX[0]+0.01)

    patches = [mpatches.Patch(color="#1565C0", alpha=0.5, label="Trauma centre coverage"),
               mpatches.Patch(color="#2E7D32", alpha=0.5, label="Hospital coverage"),
               mpatches.Patch(color="#888888", alpha=0.5, label="Low reliability zone")]
    fig.legend(handles=patches, loc="lower center", ncol=3,
               fontsize=9, framealpha=0.8)
    fig.suptitle("MAP-5  Hospital 30-Minute Service Coverage\n"
                 "Coverage radius shrinks as network reliability degrades "
                 "(BPR travel-time inflation)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP5_hospital_coverage_S0_vs_S2")


# ─────────────────────────────────────────────────────────────────────────────
# MAP 6 — Patient demand density by tier (S2)
# ─────────────────────────────────────────────────────────────────────────────

def map6_patient_demand():
    print("  [Map 6] Patient demand density...")
    from cs_setup import generate_demand
    demand_s0 = generate_demand(60, scenario=0, seed=42)
    demand_s2 = generate_demand(60, scenario=2, seed=42)

    tier_colors = {1:"#E53935", 2:"#FF9800", 3:"#2196F3"}
    tier_labels = {1:"Type 1 — Critical","2":"Type 2 — Serious","3":"Type 3 — Minor"}

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    for ax, (dem, title) in zip(axes, [
        (demand_s0, "S0: Normal Demand Pattern"),
        (demand_s2, "S2: Peak Blackout Demand\n(device failures, accidents, heat)"),
    ]):
        hexes = hex_grid(BBOX, hex_size_km=0.9)
        hexes = [h for h in hexes if _in_bbox(h, BBOX)]
        assign_hex_phi(hexes, 2)
        phi_vals = {i: h["phi_s2"] for i, h in enumerate(hexes)}
        edge_gdf = load_edge_gdf(2)
        _draw_roads(ax, edge_gdf, alpha=0.2)
        _draw_hexes(ax, hexes, phi_vals, "Greys_r", 0.1, 1.0, alpha=0.25)

        for tier in [3, 2, 1]:
            sub = dem[dem["tier"]==tier]
            ax.scatter(sub["lon"], sub["lat"],
                       s=60 if tier==1 else 40 if tier==2 else 25,
                       c=tier_colors[tier], alpha=0.85,
                       edgecolors="white", lw=0.5, zorder=8,
                       label=f"Type {tier} ({'Critical' if tier==1 else 'Serious' if tier==2 else 'Minor'})")
        _draw_hospitals(ax, size=70)
        _style_ax(ax, title)

    axes[0].legend(fontsize=8.5, loc="lower right", framealpha=0.8)
    fig.suptitle("MAP-6  Patient Demand Distribution by Injury Priority Tier\n"
                 "Blackout causes shift toward critical (Type 1) demand: "
                 "medical devices fail, traffic accidents surge",
                 fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "MAP6_patient_demand_tiers")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("\n=== Generating Hexagonal Maps ===")
    steps = [
        ("Map 1 — Reliability φ (4 scenarios)",       map1_phi_four_scenarios),
        ("Map 2 — Zone failure risk",                  map2_failure_risk),
        ("Map 3 — Reliability delta S0→S2",            map3_delta_map),
        ("Map 4 — Network accessibility",              map4_accessibility),
        ("Map 5 — Hospital coverage radius",           map5_hospital_coverage),
        ("Map 6 — Patient demand density",             map6_patient_demand),
    ]
    for i, (label, fn) in enumerate(steps, 1):
        print(f"  [{i}/{len(steps)}] {label}")
        try: fn()
        except Exception as e:
            import traceback; traceback.print_exc()
            print(f"    WARNING: {e}")
    print(f"  All maps saved to: {FIG_MAP}")

if __name__ == "__main__":
    run_all()
