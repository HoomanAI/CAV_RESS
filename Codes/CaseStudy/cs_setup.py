"""
Case Study Setup — 2025 Iberian Peninsula Blackout
Downloads Madrid road network, assigns φ_ij per district,
places hospitals, generates patient demand for 4 scenarios.
Saves all data to case_study_iberia/data/
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point, Polygon, box
import os, sys, json, warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

# ── Madrid bounding box (inner city + near suburbs) ──────────────────────────
# lat: 40.35 – 40.52, lon: -3.78 – -3.58
BBOX = (40.35, -3.78, 40.52, -3.58)   # south, west, north, east
CENTER = (40.4168, -3.7038)            # Puerta del Sol

# ── District reliability model (April 28, 2025 blackout) ────────────────────
# φ_ij per zone estimated from:
#   - GSMA cellular outage percentages
#   - REE grid substation loss data
#   - MINETUR base station density
#   - Hospital backup generator coverage

DISTRICTS = [
    # name, center_lat, center_lon, radius_km, phi_scenario2, phi_scenario3
    # (S0=1.0, S1=0.80-0.90, S2=peak disruption, S3=partial restore)
    {"name":"Centro",          "lat":40.4150,"lon":-3.7010,"r":1.2, "phi2":0.42,"phi3":0.68},
    {"name":"Salamanca",       "lat":40.4270,"lon":-3.6800,"r":1.0, "phi2":0.48,"phi3":0.72},
    {"name":"Retiro",          "lat":40.4060,"lon":-3.6840,"r":1.0, "phi2":0.45,"phi3":0.70},
    {"name":"Chamartín",       "lat":40.4560,"lon":-3.6760,"r":1.2, "phi2":0.52,"phi3":0.75},
    {"name":"Tetuán",          "lat":40.4480,"lon":-3.7030,"r":0.9, "phi2":0.47,"phi3":0.71},
    {"name":"Chamberí",        "lat":40.4330,"lon":-3.7010,"r":0.8, "phi2":0.50,"phi3":0.74},
    {"name":"Moncloa-Aravaca", "lat":40.4330,"lon":-3.7280,"r":1.5, "phi2":0.55,"phi3":0.78},
    {"name":"Latina",          "lat":40.4040,"lon":-3.7320,"r":1.5, "phi2":0.40,"phi3":0.65},
    {"name":"Carabanchel",     "lat":40.3850,"lon":-3.7310,"r":1.5, "phi2":0.35,"phi3":0.62},
    {"name":"Usera",           "lat":40.3930,"lon":-3.7120,"r":0.9, "phi2":0.38,"phi3":0.63},
    {"name":"Puente Vallecas", "lat":40.3820,"lon":-3.6770,"r":1.3, "phi2":0.33,"phi3":0.60},
    {"name":"Moratalaz",       "lat":40.4060,"lon":-3.6550,"r":1.0, "phi2":0.36,"phi3":0.62},
    {"name":"Ciudad Lineal",   "lat":40.4360,"lon":-3.6520,"r":1.2, "phi2":0.44,"phi3":0.69},
    {"name":"Hortaleza",       "lat":40.4760,"lon":-3.6430,"r":1.8, "phi2":0.50,"phi3":0.74},
    {"name":"Fuencarral",      "lat":40.4850,"lon":-3.7280,"r":2.0, "phi2":0.38,"phi3":0.64},
    {"name":"Barajas",         "lat":40.4730,"lon":-3.5840,"r":2.5, "phi2":0.30,"phi3":0.58},
    {"name":"San Blas",        "lat":40.4210,"lon":-3.6230,"r":1.5, "phi2":0.35,"phi3":0.61},
    {"name":"Vicálvaro",       "lat":40.4050,"lon":-3.6100,"r":1.5, "phi2":0.28,"phi3":0.55},
    {"name":"Villa de Vallecas","lat":40.3740,"lon":-3.6420,"r":2.0,"phi2":0.30,"phi3":0.57},
]

# Scenario phi assignments
# S0: normal  S1: early (t=0-2h)  S2: peak (t=2-6h)  S3: restore (t=6-10h)
def phi_from_scenarios(district, scenario):
    if scenario == 0: return 1.00
    if scenario == 1: return district["phi2"] + 0.35   # early: less degraded
    if scenario == 2: return district["phi2"]            # peak disruption
    if scenario == 3: return district["phi3"]            # partial restore
    return 1.00

# ── Real Madrid hospitals (public, from Comunidad de Madrid) ─────────────────
HOSPITALS = [
    {"name":"Hospital La Paz",                "lat":40.4771,"lon":-3.6894,"beds":1300,"trauma":True},
    {"name":"Hospital Gregorio Marañón",       "lat":40.4094,"lon":-3.6932,"beds":1500,"trauma":True},
    {"name":"Hospital Ramón y Cajal",          "lat":40.4714,"lon":-3.6618,"beds":1100,"trauma":True},
    {"name":"Hospital 12 de Octubre",          "lat":40.3765,"lon":-3.7039,"beds":1300,"trauma":True},
    {"name":"Hospital La Princesa",            "lat":40.4256,"lon":-3.6854,"beds":700, "trauma":False},
    {"name":"Hospital Clínico San Carlos",     "lat":40.4402,"lon":-3.7185,"beds":1100,"trauma":True},
    {"name":"Hospital Puerta de Hierro",       "lat":40.5036,"lon":-3.7903,"beds":900, "trauma":False},
    {"name":"Hospital Severo Ochoa",           "lat":40.3447,"lon":-3.7836,"beds":500, "trauma":False},
    {"name":"Hospital Infanta Leonor",         "lat":40.3763,"lon":-3.6560,"beds":400, "trauma":False},
    {"name":"Hospital de Fuenlabrada",         "lat":40.2894,"lon":-3.8019,"beds":400, "trauma":False},
]

# ── Download Madrid road network ─────────────────────────────────────────────

def download_network():
    net_path = os.path.join(DATA, "madrid_network.graphml")
    if os.path.exists(net_path):
        print("  Loading cached network...")
        G = ox.load_graphml(net_path)
    else:
        print("  Downloading Madrid road network (drive)...")
        # bbox tuple: (left, bottom, right, top) = (west, south, east, north)
        G = ox.graph_from_bbox(
            bbox=(BBOX[1], BBOX[0], BBOX[3], BBOX[2]),
            network_type="drive",
            simplify=True
        )
        ox.save_graphml(G, net_path)
        print(f"  Saved network: {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G


def assign_phi(G, scenario=2):
    """Assign reliability φ_ij to each edge based on district and scenario."""
    import math
    def dist_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    # Node coordinates
    node_data = {n: (d["y"], d["x"]) for n, d in G.nodes(data=True)}

    edge_phi = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        lat_u, lon_u = node_data.get(u, CENTER)
        lat_v, lon_v = node_data.get(v, CENTER)
        mid_lat = (lat_u + lat_v) / 2
        mid_lon = (lon_u + lon_v) / 2

        # Assign phi from nearest district
        best_phi = 0.55   # default
        best_d   = 1e9
        for dist in DISTRICTS:
            d = dist_km(mid_lat, mid_lon, dist["lat"], dist["lon"])
            if d < dist["r"] and d < best_d:
                best_d   = d
                best_phi = phi_from_scenarios(dist, scenario)

        # Hospitals have backup power → higher phi
        for hosp in HOSPITALS:
            d = dist_km(mid_lat, mid_lon, hosp["lat"], hosp["lon"])
            if d < 0.5:
                best_phi = max(best_phi, 0.88)

        # Add small spatial noise (σ = 0.05)
        rng = np.random.default_rng(hash((u, v)) % (2**32))
        noise = rng.normal(0, 0.04)
        best_phi = float(np.clip(best_phi + noise, 0.10, 1.00))
        edge_phi[(u, v, k)] = best_phi

    return edge_phi


# ── Patient demand generation ─────────────────────────────────────────────────

def generate_demand(n_patients=60, scenario=2, seed=42):
    """
    Generate patient locations and priority tiers.
    During peak blackout (S2), more critical patients due to:
      - medical device failures (ventilators, ICU equipment)
      - heat stress (no air conditioning in July)
      - road accident surge (no traffic signals)
    """
    rng = np.random.default_rng(seed)
    # Demand scales with scenario severity
    demand_weights = {0: [0.10, 0.30, 0.60],   # S0: mostly minor
                      1: [0.20, 0.40, 0.40],   # S1: mixed
                      2: [0.40, 0.35, 0.25],   # S2: peak — many critical
                      3: [0.25, 0.40, 0.35]}   # S3: recovering

    tiers    = rng.choice([1, 2, 3], size=n_patients,
                          p=demand_weights[scenario])
    # Patient locations within Madrid bbox
    lats = rng.uniform(BBOX[0]+0.02, BBOX[2]-0.02, n_patients)
    lons = rng.uniform(BBOX[1]+0.02, BBOX[3]-0.02, n_patients)
    return pd.DataFrame({"patient_id": range(n_patients),
                         "lat": lats, "lon": lons, "tier": tiers,
                         "scenario": scenario})


# ── Build GeoDataFrame of edges with phi ─────────────────────────────────────

def build_edge_gdf(G, edge_phi):
    rows = []
    for u, v, k, data in G.edges(keys=True, data=True):
        phi = edge_phi.get((u, v, k), 0.5)
        geom = data.get("geometry", None)
        if geom is None:
            from shapely.geometry import LineString
            nu, nv = G.nodes[u], G.nodes[v]
            geom = LineString([(nu["x"], nu["y"]), (nv["x"], nv["y"])])
        rows.append({"u": u, "v": v, "k": k, "phi": phi,
                     "length_m": data.get("length", 100),
                     "geometry": geom})
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


# ── Save district polygons for maps ──────────────────────────────────────────

def build_district_gdf():
    from shapely.geometry import Point
    rows = []
    for s in range(4):
        for d in DISTRICTS:
            phi = phi_from_scenarios(d, s)
            rows.append({"name": d["name"], "scenario": s, "phi": phi,
                         "lat": d["lat"], "lon": d["lon"], "r_km": d["r"],
                         "geometry": Point(d["lon"], d["lat"])})
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def run_setup():
    print("=== Case Study Setup: 2025 Iberian Blackout — Madrid ===")

    # Download network
    G = download_network()
    print(f"  Network: {len(G.nodes)} nodes, {len(G.edges)} edges")

    # Assign phi for each scenario
    for s in range(4):
        print(f"  Assigning phi for scenario S{s}...")
        phi = assign_phi(G, scenario=s)
        gdf = build_edge_gdf(G, phi)
        gdf.to_file(os.path.join(DATA, f"edges_S{s}.gpkg"),
                    driver="GPKG")
        # CSV version for quick access
        gdf[["u","v","k","phi","length_m"]].to_csv(
            os.path.join(DATA, f"edges_S{s}.csv"), index=False)

    # District summary
    d_gdf = build_district_gdf()
    d_gdf.to_csv(os.path.join(DATA, "districts.csv"), index=False)

    # Hospitals
    hosp_df = pd.DataFrame(HOSPITALS)
    hosp_df.to_csv(os.path.join(DATA, "hospitals.csv"), index=False)

    # Patient demand per scenario
    for s in range(4):
        dem = generate_demand(n_patients=60, scenario=s, seed=42)
        dem.to_csv(os.path.join(DATA, f"demand_S{s}.csv"), index=False)

    # Summary stats
    print("\n  Scenario summary (mean φ across all edges):")
    for s in range(4):
        phi_vals = pd.read_csv(os.path.join(DATA, f"edges_S{s}.csv"))["phi"]
        print(f"    S{s}: mean φ = {phi_vals.mean():.3f}, "
              f"feasible (φ≥0.85): {(phi_vals>=0.85).mean()*100:.1f}%")

    print("\n  Setup complete. Data saved to:", DATA)
    return G

if __name__ == "__main__":
    run_setup()
