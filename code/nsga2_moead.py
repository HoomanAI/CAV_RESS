"""
NSGA-II and MOEA/D implementations for CAV-VRPTW (3-objective MOO).
Both algorithms output a Pareto archive of (f1, f2, f3) solutions.
f1 = satisfaction (higher=better)
f2 = -distance   (higher=better, i.e. shorter routes)
f3 = reliability (higher=better)
"""
import numpy as np
import time
from simulation_framework import CVRPTWInstance, compute_metrics, nearest_neighbour

# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def evaluate3(inst, routes):
    """Return (f1, f2, f3) in maximisation form."""
    m  = compute_metrics(inst, routes)
    return (m["SCI"], -m["TD"] / 1000.0, m["RRS"])   # f2 negated so higher=better

def dominates(a, b):
    """True if a dominates b (all ≥, at least one >)."""
    return all(ai >= bi for ai, bi in zip(a, b)) and any(ai > bi for ai, bi in zip(a, b))

def pareto_nd(pop):
    """Return indices of non-dominated solutions in pop (list of (f_tuple, routes))."""
    n   = len(pop)
    dom = [False] * n
    for i in range(n):
        for j in range(n):
            if i != j and not dom[j] and dominates(pop[j][0], pop[i][0]):
                dom[i] = True; break
    return [i for i in range(n) if not dom[i]]

def crowding_dist(objs):
    """NSGA-II crowding distance for a list of (f1,f2,f3) tuples."""
    n = len(objs); dist = [0.0] * n
    if n <= 2: return [float("inf")] * n
    for m in range(3):
        order = sorted(range(n), key=lambda i: objs[i][m])
        dist[order[0]] = dist[order[-1]] = float("inf")
        rng_m = objs[order[-1]][m] - objs[order[0]][m]
        if rng_m == 0: continue
        for k in range(1, n - 1):
            dist[order[k]] += (objs[order[k+1]][m] - objs[order[k-1]][m]) / rng_m
    return dist

def seq_to_routes(seq, inst):
    """Convert flat customer sequence to routes respecting capacity."""
    routes = []; route = []; cap = inst.capacity
    for c in seq:
        d = inst.demand[c]
        if cap >= d: route.append(c); cap -= d
        else:
            if route: routes.append(route)
            route = [c]; cap = inst.capacity - d
    if route: routes.append(route)
    return routes

def perturb(inst, routes, rng, n_swaps=1):
    """Or-opt(1) perturbation — relocate random customer."""
    all_c = [c for r in routes for c in r]
    if not all_c: return routes
    new_r = [list(r) for r in routes]
    for _ in range(n_swaps):
        c_all = [c for r in new_r for c in r]
        if not c_all: break
        c = c_all[int(rng.integers(0, len(c_all)))]
        for vi, r in enumerate(new_r):
            if c in r: new_r[vi].remove(c); break
        new_r = [r for r in new_r if r]
        best_v, best_p, best_cost = -1, -1, float("inf")
        depot = inst.n
        for vi, r in enumerate(new_r):
            if sum(inst.demand[x] for x in r) + inst.demand[c] > inst.capacity:
                continue
            for p in range(len(r) + 1):
                prev  = r[p-1] if p > 0      else depot
                next_ = r[p]   if p < len(r) else depot
                cost  = (inst.dist[prev,c] + inst.dist[c,next_]
                         - inst.dist[prev,next_])
                if cost < best_cost: best_cost, best_v, best_p = cost, vi, p
        if best_v >= 0: new_r[best_v].insert(best_p, c)
        else:            new_r.append([c])
    return new_r

def crossover_seq(r1, r2, rng):
    """Sequence-level crossover: take prefix from parent1, fill with parent2 order."""
    flat1 = [c for r in r1 for c in r]
    flat2 = [c for r in r2 for c in r]
    if not flat1: return [list(r) for r in r2]
    cut  = int(rng.integers(1, len(flat1)))
    child = flat1[:cut] + [c for c in flat2 if c not in flat1[:cut]]
    return child

def knee_point(archive):
    """Return the solution in archive with best equally-weighted scalarised score."""
    if not archive: return None, None
    best_i, best_z = 0, float("inf")
    for i, (f, r) in enumerate(archive):
        z = -f[0] + (-f[1]) - f[2]      # minimise -f1 + |f2| - f3 (all higher=better negated)
        if z < best_z: best_z, best_i = z, i
    return archive[best_i]

def hv_2d(front_objs, ref=(0.0, 0.0)):
    """Hypervolume on (f1,f3) 2D projection."""
    pts = sorted([(f[0], f[2]) for f in front_objs], key=lambda p: -p[0])
    hv = 0.0; prev = ref[1]
    for f1, f3 in pts:
        if f1 > ref[0] and f3 > prev:
            hv += (f1 - ref[0]) * (f3 - prev); prev = max(prev, f3)
    return hv

def igd(approx, ref_front):
    """IGD: mean distance from reference front to nearest approx point."""
    if not approx or not ref_front: return float("nan")
    af = np.array([[f[0], f[2]] for f, _ in approx])
    ds = []
    for rf, _ in ref_front:
        d = np.linalg.norm(af - np.array([rf[0], rf[2]]), axis=1).min()
        ds.append(d)
    return float(np.mean(ds))

def spread_delta(front_objs):
    """Spread Δ on (f1,f3) projection."""
    pts = sorted([(f[0], f[2]) for f in front_objs], key=lambda p: p[0])
    if len(pts) < 3: return float("nan")
    dists = [np.linalg.norm(np.array(pts[i+1]) - np.array(pts[i])) for i in range(len(pts)-1)]
    d_mn  = np.mean(dists); d_f = dists[0]; d_l = dists[-1]
    denom = d_f + d_l + (len(dists)-1)*d_mn
    return float((d_f + d_l + sum(abs(d - d_mn) for d in dists)) / (denom + 1e-9))


# ═══════════════════════════════════════════════════════════════════════════════
# NSGA-II
# ═══════════════════════════════════════════════════════════════════════════════

class NSGAII:
    """
    Non-Dominated Sorting Genetic Algorithm II — Deb et al. (2002).
    Operates directly on 3 objectives, no scalarisation.
    """
    def __init__(self, inst, pop_size=80, n_gen=200, p_cross=0.90,
                 p_mut=0.10, seed=1):
        self.inst      = inst
        self.pop_size  = pop_size
        self.n_gen     = n_gen
        self.p_cross   = p_cross
        self.p_mut     = p_mut
        self.rng       = np.random.default_rng(seed)

    def _init(self):
        base = nearest_neighbour(self.inst)
        pop  = []
        for _ in range(self.pop_size):
            r = perturb(self.inst, [list(x) for x in base], self.rng, n_swaps=3)
            pop.append((evaluate3(self.inst, r), r))
        return pop

    def _fast_sort(self, pop):
        n  = len(pop); S = [[] for _ in range(n)]
        nd = [0]*n; rank = [0]*n; fronts = [[]]
        for i in range(n):
            for j in range(n):
                if i == j: continue
                if dominates(pop[i][0], pop[j][0]): S[i].append(j)
                elif dominates(pop[j][0], pop[i][0]): nd[i] += 1
            if nd[i] == 0: fronts[0].append(i)
        fi = 0
        while fronts[fi]:
            nxt = []
            for i in fronts[fi]:
                for j in S[i]:
                    nd[j] -= 1
                    if nd[j] == 0: rank[j] = fi+1; nxt.append(j)
            fi += 1; fronts.append(nxt)
        return fronts[:-1], rank

    def _tournament(self, pop, rank, crowd):
        def win(a, b):
            return a if (rank[a] < rank[b] or
                         (rank[a] == rank[b] and crowd[a] >= crowd[b])) else b
        idxs = self.rng.integers(0, len(pop), 4)
        p1 = win(idxs[0], idxs[1]); p2 = win(idxs[2], idxs[3])
        return pop[p1], pop[p2]

    def run(self):
        pop     = self._init()
        archive = []
        t0      = time.time()

        for _ in range(self.n_gen):
            fronts, rank = self._fast_sort(pop)

            # Crowding distances per front
            crowd = [0.0]*len(pop)
            for front in fronts:
                cd = crowding_dist([pop[i][0] for i in front])
                for k, idx in enumerate(front): crowd[idx] = cd[k]

            # Offspring
            offspring = []
            while len(offspring) < self.pop_size:
                (_, r1), (_, r2) = self._tournament(pop, rank, crowd)
                if self.rng.random() < self.p_cross:
                    seq = crossover_seq(r1, r2, self.rng)
                    child_r = seq_to_routes(seq, self.inst)
                else:
                    child_r = [list(r) for r in r1]
                if self.rng.random() < self.p_mut:
                    child_r = perturb(self.inst, child_r, self.rng)
                offspring.append((evaluate3(self.inst, child_r), child_r))

            # Combine and select
            combined  = pop + offspring
            f2, rank2 = self._fast_sort(combined)
            crowd2    = [0.0]*len(combined)
            for front in f2:
                cd = crowding_dist([combined[i][0] for i in front])
                for k, idx in enumerate(front): crowd2[idx] = cd[k]

            new_pop = []
            for front in f2:
                if len(new_pop) + len(front) <= self.pop_size:
                    new_pop += [combined[i] for i in front]
                else:
                    need    = self.pop_size - len(new_pop)
                    ordered = sorted(front, key=lambda i: -crowd2[i])
                    new_pop += [combined[i] for i in ordered[:need]]
                    break
            pop = new_pop

        # Final Pareto archive
        nd_idx  = pareto_nd(pop)
        archive = [pop[i] for i in nd_idx]
        return archive, time.time() - t0


# ═══════════════════════════════════════════════════════════════════════════════
# MOEA/D
# ═══════════════════════════════════════════════════════════════════════════════

class MOEAD:
    """
    Multi-Objective Evolutionary Algorithm based on Decomposition — Zhang & Li (2007).
    Uses Tchebycheff decomposition with H weight vectors on the 3-objective simplex.
    Handles non-convex Pareto fronts that weighted-sum scalarisation cannot find.
    """
    def __init__(self, inst, H=15, n_gen=250, T=5,
                 p_cross=0.90, p_mut=0.10, seed=1):
        self.inst    = inst
        self.n_gen   = n_gen
        self.T       = T          # neighbourhood size
        self.p_cross = p_cross
        self.p_mut   = p_mut
        self.rng     = np.random.default_rng(seed)
        self.W       = self._simplex_weights(H)
        self.H       = len(self.W)

    @staticmethod
    def _simplex_weights(H):
        W = []
        for i in range(H+1):
            for j in range(H+1-i):
                W.append(np.array([i/H, j/H, (H-i-j)/H], dtype=float))
        return np.array(W)

    def _nbhd(self):
        nbhd = []
        for i in range(self.H):
            d    = np.linalg.norm(self.W - self.W[i], axis=1)
            nbhd.append(np.argsort(d)[:self.T])
        return nbhd

    @staticmethod
    def _tcheby(f, w, z):
        """Tchebycheff scalar (minimise; z = ideal point in maximisation form)."""
        return max(w[m] * abs(f[m] - z[m]) for m in range(3))

    def _trim_archive(self, archive, max_size=100):
        """Trim archive to max_size using crowding distance (keep most spread)."""
        if len(archive) <= max_size:
            return archive
        objs = [a[0] for a in archive]
        cd   = crowding_dist(objs)
        keep = sorted(range(len(archive)), key=lambda i: -cd[i])[:max_size]
        return [archive[i] for i in keep]

    def run(self):
        nbhd  = self._nbhd()
        base  = nearest_neighbour(self.inst)

        pop   = []
        for _ in range(self.H):
            r = perturb(self.inst, [list(x) for x in base], self.rng, n_swaps=3)
            pop.append((evaluate3(self.inst, r), r))

        # Ideal point (maximisation: highest observed value per objective)
        z = [max(pop[i][0][m] for i in range(self.H)) for m in range(3)]

        archive = list(pop)
        t0      = time.time()

        for _ in range(self.n_gen):
            for i in range(self.H):
                nb         = nbhd[i]
                j, k       = self.rng.choice(nb, 2, replace=False)
                _, r1      = pop[j]; _, r2 = pop[k]

                if self.rng.random() < self.p_cross:
                    seq     = crossover_seq(r1, r2, self.rng)
                    child_r = seq_to_routes(seq, self.inst)
                else:
                    child_r = [list(r) for r in r1]
                if self.rng.random() < self.p_mut:
                    child_r = perturb(self.inst, child_r, self.rng)

                child_f = evaluate3(self.inst, child_r)

                # Update ideal point
                for m in range(3):
                    if child_f[m] > z[m]: z[m] = child_f[m]

                # Update neighbourhood
                for nb_idx in nb:
                    w_nb = self.W[nb_idx]
                    if (self._tcheby(child_f, w_nb, z) <=
                            self._tcheby(pop[nb_idx][0], w_nb, z)):
                        pop[nb_idx] = (child_f, child_r)

                # Update external archive (capped at 100)
                archive_objs = [a[0] for a in archive]
                if not any(dominates(ao, child_f) for ao in archive_objs):
                    archive = [(f, r) for f, r in archive
                               if not dominates(child_f, f)]
                    archive.append((child_f, child_r))
                    if len(archive) > 100:
                        archive = self._trim_archive(archive, max_size=100)

        # Also filter pop into archive
        for sol in pop:
            archive_objs = [a[0] for a in archive]
            if not any(dominates(ao, sol[0]) for ao in archive_objs):
                archive = [(f, r) for f, r in archive
                           if not dominates(sol[0], f)]
                archive.append(sol)

        # Final non-dominated filter
        nd_idx  = pareto_nd(archive)
        archive = [archive[i] for i in nd_idx]
        return archive, time.time() - t0
