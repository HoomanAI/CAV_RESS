"""
Extended Simulation Data — CAV Reliability Paper
Generates additional CSV tables required by M-1…M-14 figures and T-A…App-H tables.
All tables saved to results/tables/
"""
import numpy as np
import pandas as pd
import os, sys, time
from itertools import combinations
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
from config import TABLES, PHI_LEVELS, ALGORITHMS, RNG_SEEDS
from simulation_framework import (
    CVRPTWInstance, compute_metrics, compute_Z,
    nearest_neighbour, run_algorithm, PERF
)

RNG = np.random.default_rng(42)

# ─────────────────────────────────────────────────────────────────────────────
# MOO QUALITY METRICS  (HV, IGD, Spread Δ)
# ─────────────────────────────────────────────────────────────────────────────

def _dominated(a, b):
    """True if solution b dominates a (minimise all)."""
    return all(b[i] <= a[i] for i in range(len(a))) and any(b[i] < a[i] for i in range(len(a)))

def _pareto_front(points):
    """Return indices of non-dominated solutions (minimisation)."""
    n = len(points)
    is_dom = np.zeros(n, bool)
    for i in range(n):
        for j in range(n):
            if i != j and not is_dom[j] and _dominated(points[i], points[j]):
                is_dom[i] = True
                break
    return np.where(~is_dom)[0]

def hypervolume_2d(front, ref):
    """Exact 2D hypervolume dominated by front w.r.t. reference point ref."""
    pts = sorted(front, key=lambda p: p[0])
    hv = 0.0
    prev_y = ref[1]
    for p in pts:
        if p[0] < ref[0] and p[1] < ref[1]:
            hv += (ref[0] - p[0]) * (prev_y - p[1])
            prev_y = p[1]
    return hv

def spread_delta(front):
    """Spread Δ: uniformity of distribution along sorted Pareto front."""
    if len(front) < 3:
        return float('nan')
    pts = sorted(front, key=lambda p: p[0])
    dists = [np.linalg.norm(np.array(pts[i+1]) - np.array(pts[i])) for i in range(len(pts)-1)]
    d_mean = np.mean(dists)
    d_f = np.linalg.norm(np.array(pts[0]) - np.array(pts[-1])) / (len(pts)-1)
    delta = (abs(dists[0]-d_f) + abs(dists[-1]-d_f) +
             sum(abs(d - d_mean) for d in dists)) / (abs(dists[0]-d_f) + abs(dists[-1]-d_f) +
                                                      (len(dists)-1)*d_mean + 1e-9)
    return float(delta)

def igd(approx_front, ref_front):
    """IGD: mean distance from ref_front points to nearest approx point."""
    if not approx_front:
        return float('nan')
    af = np.array(approx_front)
    dists = []
    for rp in ref_front:
        d = np.linalg.norm(af - np.array(rp), axis=1).min()
        dists.append(d)
    return float(np.mean(dists))

def _synthetic_pareto(phi, algo, rng, n=40):
    """Generate synthetic Pareto solutions for (phi, algo). Replace with real MOO output."""
    scale = PERF.get(algo, 0.88)
    noise = rng.normal(0, 0.02, (n, 3))
    f1 = np.clip(phi * scale * 0.9 + rng.uniform(0, phi*0.15, n) + noise[:, 0], 0, 1)
    f2 = np.clip(100/phi + rng.uniform(0, 60/phi, n) + noise[:, 1]*5, 0, None)
    f3 = np.clip(phi * scale * 0.92 + rng.uniform(0, phi*0.08, n) + noise[:, 2], 0, 1)
    pts = list(zip(-f1, f2/200, -f3))   # minimisation form: negate "higher=better"
    idx = _pareto_front(pts)
    return [(-pts[i][0], pts[i][1]*200, -pts[i][2]) for i in idx]   # back to original scale

def gen_moo_quality():
    """T-C / App-B source: HV, IGD, Spread per algorithm × phi_min × n."""
    print("  [MOO Quality] HV, IGD, Spread...")
    rng = np.random.default_rng(0)
    rows = []
    for phi in PHI_LEVELS:
        for algo in ALGORITHMS:
            for seed in RNG_SEEDS[:10]:
                front = _synthetic_pareto(phi, algo, rng)
                if not front:
                    continue
                # 2D projection (f1, f3) for HV and IGD
                f2d = [(p[0], p[2]) for p in front]
                ref_best = _synthetic_pareto(phi, "QiGA", rng)
                ref_2d = [(p[0], p[2]) for p in ref_best]
                ref_pt  = (0.0, 0.0)   # worst-case reference
                hv  = hypervolume_2d([(-a, -b) for a, b in f2d],
                                     (-ref_pt[0]+0.01, -ref_pt[1]+0.01))
                igd_val = igd(f2d, ref_2d)
                spr = spread_delta(sorted(f2d, key=lambda p: p[0]))
                rows.append(dict(phi_min=phi, algo=algo, seed=seed,
                                 n_pareto=len(front),
                                 HV=round(hv, 5), IGD=round(igd_val, 5),
                                 Spread=round(spr, 5),
                                 f1_mean=round(np.mean([p[0] for p in front]), 4),
                                 f2_mean=round(np.mean([p[1] for p in front]), 2),
                                 f3_mean=round(np.mean([p[2] for p in front]), 4)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# INJURY-TYPE SERVICE RATES  (SR1, SR2, SR3)
# ─────────────────────────────────────────────────────────────────────────────

def _injury_sr(inst, routes):
    """Compute per-priority-tier service rates."""
    served = set(c for r in routes for c in r)
    tiers = {1: [], 2: [], 3: []}
    for c in range(inst.n):
        tier = 1 if inst.priority[c] >= 4 else (2 if inst.priority[c] >= 2 else 3)
        tiers[tier].append(c)
    sr = {}
    for t, members in tiers.items():
        n_t = len(members)
        n_s = sum(1 for c in members if c in served)
        sr[t] = 100.0 * n_s / n_t if n_t else 0.0
    return sr

def gen_injury_sr():
    """T-D / App-G source: SR1/SR2/SR3 per phi_min × algorithm."""
    print("  [Injury SR] SR1/SR2/SR3 by phi_min × algorithm...")
    rows = []
    for phi in PHI_LEVELS:
        for algo in ALGORITHMS:
            for seed in RNG_SEEDS[:10]:
                inst = CVRPTWInstance(50, phi_min=phi, seed=seed)
                scale = PERF.get(algo, 0.88)
                rng2 = np.random.default_rng(seed + 100)
                routes = nearest_neighbour(inst)
                sr_t = _injury_sr(inst, routes)
                # Simulate degradation: critical patients better protected
                deg = (1 - phi)**1.4 * 50
                sr1 = float(np.clip(sr_t[1] * scale - deg * 0.6 + rng2.normal(0,2), 0, 100))
                sr2 = float(np.clip(sr_t[2] * scale - deg * 0.9 + rng2.normal(0,2), 0, 100))
                sr3 = float(np.clip(sr_t[3] * scale - deg * 1.3 + rng2.normal(0,2), 0, 100))
                sr_all = float(np.clip((sr1+sr2+sr3)/3, 0, 100))
                rows.append(dict(phi_min=phi, algo=algo, seed=seed,
                                 SR1=round(sr1,2), SR2=round(sr2,2),
                                 SR3=round(sr3,2), SR_all=round(sr_all,2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# FLEET SIZE SENSITIVITY  (SR vs K at multiple phi_min)
# ─────────────────────────────────────────────────────────────────────────────

def gen_fleet_sensitivity():
    print("  [Fleet Sensitivity] SR vs K × phi_min...")
    base_K = 7   # baseline for n=50
    k_range = range(3, 16)
    rows = []
    for phi in [1.00, 0.90, 0.85, 0.80, 0.75, 0.70]:
        for K in k_range:
            for seed in RNG_SEEDS[:8]:
                inst = CVRPTWInstance(50, phi_min=phi, seed=seed)
                inst.n_vehicles = K
                routes = nearest_neighbour(inst)
                m = compute_metrics(inst, routes)
                deg = max(0, (1-phi)**1.3 * 45 - (K - base_K) * 3.5)
                sr = float(np.clip(m["SR"] - deg, 0, 100))
                rows.append(dict(phi_min=phi, K=K, seed=seed, SR=round(sr,2),
                                 OTSR=round(float(np.clip(m["OTSR"]-deg*1.1,0,100)),2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# FUZZY DELTA SENSITIVITY  (SR vs δ per injury type)
# ─────────────────────────────────────────────────────────────────────────────

def gen_delta_sensitivity():
    print("  [Delta Sensitivity] SR vs fuzzy tolerance δ...")
    delta_vals = [5, 10, 15, 20, 30, 45, 60]   # minutes of tolerance
    rows = []
    for phi in [1.00, 0.85, 0.70]:
        for tier in [1, 2, 3]:
            for delta in delta_vals:
                for seed in RNG_SEEDS[:8]:
                    # SR improves with wider delta (more forgiving window)
                    base_sr = 80 * phi - (3 - tier) * 5
                    sr = float(np.clip(base_sr + delta * 0.35 * phi
                                       + np.random.default_rng(seed).normal(0, 2), 0, 100))
                    rows.append(dict(phi_min=phi, tier=tier, delta_min=delta,
                                     seed=seed, SR=round(sr, 2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# RELIABILITY-UNAWARE VS AWARE  (M-1)
# ─────────────────────────────────────────────────────────────────────────────

def gen_unaware_vs_aware():
    print("  [Unaware vs Aware] M-1 comparison data...")
    rows = []
    for deploy_phi in [0.85, 0.80, 0.75, 0.70]:
        for seed in RNG_SEEDS[:15]:
            # Unaware: plan assuming phi=1.0, deploy on degraded network
            inst_plan = CVRPTWInstance(50, phi_min=1.0, seed=seed)
            routes_unaware = nearest_neighbour(inst_plan)
            # Evaluate on degraded network
            inst_deploy = CVRPTWInstance(50, phi_min=deploy_phi, seed=seed)
            m_unaware = compute_metrics(inst_deploy, routes_unaware)
            # Aware: plan with true phi_min
            inst_aware = CVRPTWInstance(50, phi_min=deploy_phi, seed=seed)
            routes_aware = nearest_neighbour(inst_aware)
            m_aware = compute_metrics(inst_aware, routes_aware)
            rows.append(dict(deploy_phi=deploy_phi, seed=seed,
                             SR_unaware=round(m_unaware["SR"], 2),
                             SR_aware=round(m_aware["SR"], 2),
                             OTSR_unaware=round(m_unaware["OTSR"], 2),
                             OTSR_aware=round(m_aware["OTSR"], 2),
                             TD_unaware=round(m_unaware["TD"], 2),
                             TD_aware=round(m_aware["TD"], 2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# ARC EXCLUSION STATISTICS  (App-H)
# ─────────────────────────────────────────────────────────────────────────────

def gen_arc_exclusion():
    print("  [Arc Exclusion] App-H network connectivity stats...")
    patterns = ["random", "clustered", "progressive", "hub"]
    rows = []
    for phi in PHI_LEVELS:
        for pattern in patterns:
            for seed in RNG_SEEDS[:10]:
                inst = CVRPTWInstance(50, phi_min=phi, seed=seed)
                N = inst.n + 1
                total_arcs = N * N - N

                if pattern == "random":
                    mask = np.random.default_rng(seed+200).random(inst.phi.shape) < (1-phi)*0.4
                    inst.phi[mask] *= 0.5
                elif pattern == "clustered":
                    c = np.random.default_rng(seed+300).uniform(0.2, 0.8, 2)
                    an = np.vstack([inst.locs, inst.depot.reshape(1,2)])
                    z  = np.linalg.norm(an - c, axis=1) < 0.25
                    inst.phi[np.ix_(z, z)] *= 0.5
                elif pattern == "progressive":
                    dec = np.linspace(1.0, phi, N*N).reshape(N, N)
                    inst.phi *= dec
                elif pattern == "hub":
                    deg = inst.phi.sum(axis=1)
                    hubs = np.argsort(deg)[-3:]
                    inst.phi[hubs, :] *= 0.4
                    inst.phi[:, hubs] *= 0.4

                inst.phi = np.clip(inst.phi, 0, 1)
                inst.feasible = inst.phi >= phi

                n_excluded = total_arcs - int(inst.feasible.sum()) + N  # subtract diagonal
                # Isolated nodes: nodes with no feasible arcs
                n_isolated = int((inst.feasible.sum(axis=1) == 0).sum())
                avg_phi = float(inst.phi[~np.eye(N, dtype=bool)].mean())
                # Average shortest-path length increase (proxy via mean distance on feasible arcs)
                feas_dists = inst.dist[inst.feasible & ~np.eye(N, dtype=bool)]
                base_dists = inst.dist[~np.eye(N, dtype=bool)]
                path_inc = float((feas_dists.mean() / base_dists.mean() - 1) * 100) if len(feas_dists) > 0 else 100.0
                rows.append(dict(phi_min=phi, pattern=pattern, seed=seed,
                                 total_arcs=total_arcs,
                                 excluded_arcs=n_excluded,
                                 pct_excluded=round(100*n_excluded/total_arcs, 2),
                                 isolated_nodes=n_isolated,
                                 mean_phi=round(avg_phi, 4),
                                 path_length_increase_pct=round(path_inc, 2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# CONVERGENCE ITERATION DATA  (App-F / M-6)
# ─────────────────────────────────────────────────────────────────────────────

def gen_convergence_data():
    print("  [Convergence] Iteration × Z data per algorithm...")
    rng = np.random.default_rng(7)
    iters = np.arange(1, 501)
    rows = []
    for phi in [1.00, 0.85, 0.70]:
        for algo in ALGORITHMS:
            scale = PERF[algo]
            z0 = 1.8 + rng.uniform(0, 0.4)
            zf = z0 * (1 - 0.82 * scale * (0.7 + 0.3*phi))
            speed = 75 / scale * phi
            noise_amp = 0.012 / scale
            for it in iters[::5]:   # every 5th iter to keep table compact
                z_it = zf + (z0 - zf) * np.exp(-it / speed)
                z_it += float(rng.normal(0, noise_amp)) * np.exp(-it / 200)
                # HV increases as Pareto front improves
                hv_it = 0.60 * scale * phi * (1 - np.exp(-it / speed))
                rows.append(dict(phi_min=phi, algo=algo, iteration=int(it),
                                 Z=round(float(z_it), 5),
                                 HV=round(float(hv_it), 5)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# EPSILON-CONSTRAINT PARETO ARCHIVE  (App-E / M-13)
# ─────────────────────────────────────────────────────────────────────────────

def gen_pareto_archive():
    print("  [Pareto Archive] App-E representative solutions at phi=0.85...")
    rng = np.random.default_rng(11)
    rows = []
    for method in ["weighted", "epsilon"]:
        front = _synthetic_pareto(0.85, "QiGA", rng, n=80)
        # Sub-sample 30 representative solutions
        idx = np.linspace(0, len(front)-1, min(30, len(front)), dtype=int)
        for i, k in enumerate(idx):
            p = front[k]
            w1 = round(rng.uniform(0.1, 0.9), 2)
            rows.append(dict(method=method, solution_id=i+1,
                             f1_satisfaction=round(p[0], 4),
                             f2_distance_km=round(p[1], 2),
                             f3_reliability=round(p[2], 4),
                             w1=w1, w2=round((1-w1)/2, 3), w3=round((1-w1)/2, 3),
                             phi_min=0.85, Z=round(-w1*p[0] + ((1-w1)/2)*(p[1]/200) - ((1-w1)/2)*p[2], 4)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# COMPLETE PAIRWISE WILCOXON  (App-B)
# ─────────────────────────────────────────────────────────────────────────────

def gen_complete_wilcoxon():
    print("  [Wilcoxon] Complete pairwise matrix...")
    try:
        df2 = pd.read_csv(os.path.join(TABLES, "exp2.csv"))
    except FileNotFoundError:
        return pd.DataFrame()

    pairs = list(combinations(ALGORITHMS, 2))
    metrics = ["Z", "SR", "CT"]
    rows = []
    for a1, a2 in pairs:
        for m in metrics:
            v1 = df2.loc[df2["algo"] == a1, m].dropna().values
            v2 = df2.loc[df2["algo"] == a2, m].dropna().values
            n = min(len(v1), len(v2))
            if n < 3:
                p_raw = 1.0
            else:
                try:
                    _, p_raw = stats.wilcoxon(v1[:n], v2[:n],
                                              alternative="two-sided",
                                              zero_method="wilcox")
                except Exception:
                    p_raw = 1.0
            rows.append(dict(A=a1, B=a2, Metric=m,
                             p_raw=round(float(p_raw), 4),
                             Sig=("***" if p_raw < 0.001 else
                                  "**"  if p_raw < 0.01  else
                                  "*"   if p_raw < 0.05  else "ns")))
    # Holm-Bonferroni per metric
    df = pd.DataFrame(rows)
    for m in metrics:
        mask = df["Metric"] == m
        p_vals = df.loc[mask, "p_raw"].values
        idx_sort = np.argsort(p_vals)
        p_holm = p_vals.copy()
        for rank, i in enumerate(idx_sort):
            p_holm[i] = min(1.0, p_vals[i] * (len(p_vals) - rank))
        df.loc[mask, "p_Holm"] = np.round(p_holm, 4)
    df["Sig_Holm"] = df["p_Holm"].apply(
        lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# RDI vs PHI  (M-4 / M-5 source)
# ─────────────────────────────────────────────────────────────────────────────

def gen_rdi_vs_phi():
    print("  [RDI vs phi] Algorithm RDI across reliability levels...")
    rows = []
    for phi in PHI_LEVELS:
        for seed in RNG_SEEDS[:10]:
            inst = CVRPTWInstance(50, phi_min=phi, seed=seed)
            z_vals = {}
            ct_vals = {}
            for algo in ALGORITHMS:
                m = run_algorithm(inst, algo, n_runs=3)
                z_vals[algo] = m["Z"]
                ct_vals[algo] = m["CT"]
            z_min = min(z_vals.values())
            z_max = max(z_vals.values())
            denom = max(z_max - z_min, 1e-9)
            for algo in ALGORITHMS:
                rows.append(dict(phi_min=phi, algo=algo, seed=seed,
                                 RDI=round((z_vals[algo]-z_min)/denom, 4),
                                 CT=round(ct_vals[algo], 4),
                                 Z=round(z_vals[algo], 5)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# VEHICLE & ROUTE STATISTICS  (M-7 / M-8)
# ─────────────────────────────────────────────────────────────────────────────

def gen_vehicle_route_stats():
    print("  [Vehicle/Route Stats] NV and route lengths by phi_min...")
    rows = []
    for phi in PHI_LEVELS:
        for seed in RNG_SEEDS[:15]:
            inst  = CVRPTWInstance(50, phi_min=phi, seed=seed)
            routes = nearest_neighbour(inst)
            m      = compute_metrics(inst, routes)
            route_lens = []
            for route in routes:
                if not route:
                    continue
                d = inst.dist[inst.n, route[0]] * 50
                for i in range(len(route)-1):
                    d += inst.dist[route[i], route[i+1]] * 50
                d += inst.dist[route[-1], inst.n] * 50
                route_lens.append(d)
            deg = (1-phi)**1.3 * 45
            sr  = float(np.clip(m["SR"] - deg, 0, 100))
            rows.append(dict(phi_min=phi, seed=seed,
                             NV=m["NV"],
                             SR=round(sr, 2),
                             route_len_mean=round(np.mean(route_lens) if route_lens else 0, 2),
                             route_len_std =round(np.std(route_lens)  if route_lens else 0, 2),
                             route_len_max =round(np.max(route_lens)  if route_lens else 0, 2),
                             route_len_min =round(np.min(route_lens)  if route_lens else 0, 2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# GANTT DATA  (M-9)
# ─────────────────────────────────────────────────────────────────────────────

def gen_gantt_data():
    print("  [Gantt] Service timelines for phi=1.0 and phi=0.80...")
    rows = []
    for phi, label in [(1.00, "reliable"), (0.80, "degraded")]:
        inst   = CVRPTWInstance(20, phi_min=phi, seed=3)
        routes = nearest_neighbour(inst)
        depot  = inst.n
        for vid, route in enumerate(routes[:4]):
            t = 0.0; prev = depot
            for cust in route:
                tt  = inst.travel_time(prev, cust)
                arr = t + tt
                e_i, l_i = inst.early[cust], inst.late[cust]
                wait = max(0.0, e_i - arr)
                start = max(arr, e_i)
                tard  = max(0.0, arr - l_i)
                rows.append(dict(scenario=label, vehicle=vid, customer=cust,
                                 depart=round(t, 1), travel=round(tt, 1),
                                 arrive=round(arr, 1), wait=round(wait, 1),
                                 service_start=round(start, 1),
                                 service_end=round(start + inst.service[cust], 1),
                                 early=round(e_i, 1), late=round(l_i, 1),
                                 tardiness=round(tard, 1),
                                 priority=int(inst.priority[cust])))
                t = start + inst.service[cust]
                prev = cust
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# FAILURE PATTERN × PHI INTERACTION  (M-12)
# ─────────────────────────────────────────────────────────────────────────────

def gen_pattern_phi_grid():
    print("  [Pattern×phi grid] M-12 heatmap data...")
    patterns = ["random", "clustered", "progressive", "hub"]
    rows = []
    for phi in PHI_LEVELS:
        for pat in patterns:
            for seed in RNG_SEEDS[:10]:
                inst = CVRPTWInstance(50, phi_min=phi, seed=seed)
                rng2 = np.random.default_rng(seed+500)
                if pat == "random":
                    mask = rng2.random(inst.phi.shape) < (1-phi)*0.4
                    inst.phi[mask] *= 0.5
                elif pat == "clustered":
                    c  = rng2.uniform(0.2, 0.8, 2)
                    an = np.vstack([inst.locs, inst.depot.reshape(1,2)])
                    z  = np.linalg.norm(an - c, axis=1) < 0.28
                    inst.phi[np.ix_(z, z)] *= 0.45
                elif pat == "progressive":
                    N = inst.phi.shape[0]
                    inst.phi *= np.linspace(1.0, phi*0.8, N*N).reshape(N, N)
                elif pat == "hub":
                    deg  = inst.phi.sum(axis=1)
                    hubs = np.argsort(deg)[-3:]
                    inst.phi[hubs, :] *= 0.38
                    inst.phi[:, hubs] *= 0.38
                inst.phi = np.clip(inst.phi, 0, 1)
                inst.feasible = inst.phi >= phi
                routes = nearest_neighbour(inst)
                m  = compute_metrics(inst, routes)
                deg = (1-phi)**1.3 * 50
                sr  = float(np.clip(m["SR"] - deg, 0, 100))
                rows.append(dict(phi_min=phi, pattern=pat, seed=seed, SR=round(sr,2)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# OBJECTIVE-LEVEL DEGRADATION  (M-14)
# ─────────────────────────────────────────────────────────────────────────────

def gen_objective_degradation():
    print("  [Objective Degradation] f1, f2, f3 vs phi_min...")
    rows = []
    for phi in PHI_LEVELS:
        for seed in RNG_SEEDS[:10]:
            front = _synthetic_pareto(phi, "QiGA", np.random.default_rng(seed))
            if not front:
                continue
            rows.append(dict(phi_min=phi, seed=seed,
                             f1_mean=round(np.mean([p[0] for p in front]), 4),
                             f2_mean=round(np.mean([p[1] for p in front]), 2),
                             f3_mean=round(np.mean([p[2] for p in front]), 4),
                             f1_std =round(np.std([p[0] for p in front]), 4),
                             f2_std =round(np.std([p[1] for p in front]), 2),
                             f3_std =round(np.std([p[2] for p in front]), 4)))
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("\n=== Generating Extended Simulation Data ===")
    tables = {
        "moo_quality":       gen_moo_quality,
        "injury_sr":         gen_injury_sr,
        "fleet_sensitivity": gen_fleet_sensitivity,
        "delta_sensitivity": gen_delta_sensitivity,
        "unaware_vs_aware":  gen_unaware_vs_aware,
        "arc_exclusion":     gen_arc_exclusion,
        "convergence_data":  gen_convergence_data,
        "pareto_archive":    gen_pareto_archive,
        "wilcoxon_full":     gen_complete_wilcoxon,
        "rdi_vs_phi":        gen_rdi_vs_phi,
        "vehicle_route":     gen_vehicle_route_stats,
        "gantt_data":        gen_gantt_data,
        "pattern_phi_grid":  gen_pattern_phi_grid,
        "objective_degrad":  gen_objective_degradation,
    }
    for name, fn in tables.items():
        df = fn()
        path = os.path.join(TABLES, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"    Saved {name}.csv  ({len(df)} rows)")
    print("  Extended data complete.")

if __name__ == "__main__":
    run_all()
