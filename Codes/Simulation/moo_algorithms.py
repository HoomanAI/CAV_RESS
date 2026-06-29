"""
Proper Multi-Objective Algorithms for CAV-VRPTW
Replaces single-objective GA/PSO in the MOO context with:
  - NSGA-II  (Non-dominated Sorting GA — Deb et al. 2002)
  - MOEA/D   (Decomposition-based MOO — Zhang & Li 2007)
  - MOPSO    (Multi-objective PSO with Pareto archive)
  - MO-ALNS  (ALNS with Pareto acceptance)

All algorithms output a Pareto archive of non-dominated (f1,f2,f3) solutions.
Saves results to results/tables/moo_comparison.csv
Saves figures to results/figures/new/
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os, sys, time, copy
from itertools import product

sys.path.insert(0, os.path.dirname(__file__))
from config import TABLES, PALETTE, savefig, PHI_LEVELS
from simulation_framework import CVRPTWInstance, compute_metrics, nearest_neighbour

FIG_NEW = os.path.join(os.path.dirname(TABLES), "figures", "new")
RNG_SEEDS = list(range(1, 11))

# ─────────────────────────────────────────────────────────────────────────────
# SHARED: Solution representation and evaluation
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(inst, routes):
    """Return (f1, f2, f3) — all in 'higher=better' form for dominance checks."""
    m = compute_metrics(inst, routes)
    f1 = m["SCI"]           # satisfaction — higher = better
    f2 = -m["TD"]           # negate distance so higher = better (shorter)
    f3 = m["RRS"]           # reliability — higher = better
    return (f1, f2, f3)

def dominates(a, b):
    """True if solution a dominates b (higher is better on all objectives)."""
    return (all(ai >= bi for ai, bi in zip(a, b)) and
            any(ai >  bi for ai, bi in zip(a, b)))

def pareto_filter(population):
    """Return indices of non-dominated solutions."""
    n = len(population)
    non_dom = []
    for i in range(n):
        dominated = False
        for j in range(n):
            if i != j and dominates(population[j][0], population[i][0]):
                dominated = True
                break
        if not dominated:
            non_dom.append(i)
    return non_dom

def crowding_distance(front_objs):
    """NSGA-II crowding distance for a list of (f1,f2,f3) tuples."""
    n = len(front_objs)
    if n <= 2:
        return [float('inf')] * n
    dist = [0.0] * n
    for m in range(3):
        vals = [(front_objs[i][m], i) for i in range(n)]
        vals.sort()
        dist[vals[0][1]]  = float('inf')
        dist[vals[-1][1]] = float('inf')
        f_range = vals[-1][0] - vals[0][0]
        if f_range == 0:
            continue
        for k in range(1, n-1):
            dist[vals[k][1]] += (vals[k+1][0] - vals[k-1][0]) / f_range
    return dist

def perturb_route(inst, routes, rng):
    """Random Or-opt(1) move on a copy of routes — for GA/PSO neighbourhood."""
    routes2 = [list(r) for r in routes]
    non_empty = [i for i, r in enumerate(routes2) if len(r) >= 1]
    if not non_empty:
        return routes2
    # Pick random customer to relocate
    src_v = rng.choice(non_empty)
    if not routes2[src_v]:
        return routes2
    pos  = rng.integers(0, len(routes2[src_v]))
    cust = routes2[src_v].pop(pos)
    # Insert at random feasible position
    all_v = list(range(len(routes2)))
    rng.shuffle(all_v)
    inserted = False
    for v in all_v:
        for p in range(len(routes2[v]) + 1):
            cap = sum(inst.demand[c] for c in routes2[v]) + inst.demand[cust]
            if cap <= inst.capacity:
                routes2[v].insert(p, cust)
                inserted = True
                break
        if inserted:
            break
    if not inserted:
        routes2[src_v].append(cust)
    return routes2


# ─────────────────────────────────────────────────────────────────────────────
# NSGA-II
# ─────────────────────────────────────────────────────────────────────────────

class NSGAII:
    """
    Non-Dominated Sorting Genetic Algorithm II (Deb et al., 2002).
    Operates directly on 3 objectives — no scalarisation.
    Selection uses non-domination rank + crowding distance.
    """
    def __init__(self, inst, pop_size=60, n_gen=200, seed=1):
        self.inst     = inst
        self.pop_size = pop_size
        self.n_gen    = n_gen
        self.rng      = np.random.default_rng(seed)

    def _init_pop(self):
        pop = []
        base = nearest_neighbour(self.inst)
        for _ in range(self.pop_size):
            r = perturb_route(self.inst, base, self.rng)
            f = evaluate(self.inst, r)
            pop.append((f, r))
        return pop

    def _fast_non_dominated_sort(self, pop):
        """Returns list-of-lists: fronts[0] = Pareto front, fronts[1] = next, ..."""
        n = len(pop)
        S   = [[] for _ in range(n)]   # dominated by i
        n_d = [0]  * n                  # domination count
        rank = [0] * n
        fronts = [[]]
        for i in range(n):
            for j in range(n):
                if i == j: continue
                if dominates(pop[i][0], pop[j][0]):
                    S[i].append(j)
                elif dominates(pop[j][0], pop[i][0]):
                    n_d[i] += 1
            if n_d[i] == 0:
                rank[i] = 0
                fronts[0].append(i)
        fi = 0
        while fronts[fi]:
            next_front = []
            for i in fronts[fi]:
                for j in S[i]:
                    n_d[j] -= 1
                    if n_d[j] == 0:
                        rank[j] = fi + 1
                        next_front.append(j)
            fi += 1
            fronts.append(next_front)
        return fronts[:-1], rank

    def _select(self, pop, fronts, rank):
        """Binary tournament selection using rank + crowding distance."""
        # Compute crowding distances per front
        crowd = [0.0] * len(pop)
        for front in fronts:
            front_objs = [pop[i][0] for i in front]
            cd = crowding_distance(front_objs)
            for i, idx in enumerate(front):
                crowd[idx] = cd[i]
        # Tournament
        def tournament(a, b):
            if rank[a] < rank[b]: return a
            if rank[b] < rank[a]: return b
            return a if crowd[a] >= crowd[b] else b
        idxs = self.rng.integers(0, len(pop), size=(2, 2))
        p1 = tournament(idxs[0,0], idxs[0,1])
        p2 = tournament(idxs[1,0], idxs[1,1])
        return pop[p1], pop[p2]

    def _crossover(self, p1_routes, p2_routes):
        """Segment crossover on routes."""
        if not p1_routes or not p2_routes:
            return [list(r) for r in p1_routes]
        c1 = [list(r) for r in p1_routes]
        c2 = [list(r) for r in p2_routes]
        # Single-point cut on flattened customer sequence
        flat1 = [c for r in c1 for c in r]
        flat2 = [c for r in c2 for c in r]
        if len(flat1) < 2: return c1
        cut = int(self.rng.integers(1, len(flat1)))
        child_seq = flat1[:cut]
        for c in flat2:
            if c not in child_seq:
                child_seq.append(c)
        # Rebuild routes greedily
        return self._seq_to_routes(child_seq)

    def _seq_to_routes(self, seq):
        routes = []; route = []; cap = self.inst.capacity
        for c in seq:
            if inst_demand := self.inst.demand[c]:
                if cap >= inst_demand:
                    route.append(c); cap -= inst_demand
                else:
                    if route: routes.append(route)
                    route = [c]; cap = self.inst.capacity - inst_demand
        if route: routes.append(route)
        return routes

    def run(self):
        pop    = self._init_pop()
        t_start = time.time()
        archive = []

        for gen in range(self.n_gen):
            fronts, rank = self._fast_non_dominated_sort(pop)

            # Build offspring
            offspring = []
            while len(offspring) < self.pop_size:
                (_, r1), (_, r2) = self._select(pop, fronts, rank)
                child_routes = self._crossover(r1, r2)
                child_routes = perturb_route(self.inst, child_routes, self.rng)
                child_f = evaluate(self.inst, child_routes)
                offspring.append((child_f, child_routes))

            # Combine + select next generation
            combined = pop + offspring
            fronts2, rank2 = self._fast_non_dominated_sort(combined)
            new_pop = []
            for front in fronts2:
                if len(new_pop) + len(front) <= self.pop_size:
                    new_pop.extend([combined[i] for i in front])
                else:
                    needed = self.pop_size - len(new_pop)
                    front_objs = [combined[i][0] for i in front]
                    cd = crowding_distance(front_objs)
                    sorted_front = sorted(zip(cd, front), reverse=True)
                    new_pop.extend([combined[j] for _, j in sorted_front[:needed]])
                    break
            pop = new_pop

            # Update archive (Pareto front of pop)
            archive = [pop[i] for i in pareto_filter([p for p in pop])]

        return archive, time.time() - t_start


# ─────────────────────────────────────────────────────────────────────────────
# MOEA/D
# ─────────────────────────────────────────────────────────────────────────────

class MOEAD:
    """
    Multi-Objective Evolutionary Algorithm based on Decomposition (Zhang & Li, 2007).
    Decomposes 3-objective problem into H scalar subproblems via weight vectors.
    Uses Tchebycheff (Chebyshev) scalarisation — handles non-convex fronts.
    """
    def __init__(self, inst, H=20, n_gen=200, T=5, seed=1):
        self.inst  = inst
        self.n_gen = n_gen
        self.T     = T      # neighbourhood size
        self.rng   = np.random.default_rng(seed)

        # Generate weight vectors on 3D simplex
        self.weights = self._gen_weights(H)
        self.H       = len(self.weights)

    def _gen_weights(self, H):
        """Uniform weight vectors on 3-objective simplex."""
        weights = []
        for i in range(H+1):
            for j in range(H+1-i):
                k = H - i - j
                weights.append((i/H, j/H, k/H))
        return np.array(weights)

    def _tchebycheff(self, f, w, z_star):
        """Tchebycheff scalarisation (maximisation form)."""
        return max(w[m] * abs(f[m] - z_star[m]) for m in range(3))

    def _neighbourhood(self):
        """T nearest neighbours per weight vector (by Euclidean distance)."""
        nbhd = []
        for i in range(self.H):
            dists = [np.linalg.norm(self.weights[i] - self.weights[j])
                     for j in range(self.H)]
            nbhd.append(np.argsort(dists)[:self.T])
        return nbhd

    def run(self):
        H    = self.H
        nbhd = self._neighbourhood()

        # Initialise population
        base = nearest_neighbour(self.inst)
        pop  = []
        for _ in range(H):
            r = perturb_route(self.inst, base, self.rng)
            f = evaluate(self.inst, r)
            pop.append((f, r))

        # Ideal point z* (maximisation: highest f achieved so far)
        z_star = [max(pop[i][0][m] for i in range(H)) for m in range(3)]

        # External Pareto archive
        archive = list(pop)
        t_start = time.time()

        for gen in range(self.n_gen):
            for i in range(H):
                # Select two neighbours for crossover
                nb = nbhd[i]
                j, k = self.rng.choice(nb, size=2, replace=False)
                _, r1 = pop[j]; _, r2 = pop[k]

                # Produce child via segment crossover + Or-opt perturbation
                flat1 = [c for r in r1 for c in r]
                flat2 = [c for r in r2 for c in r]
                if flat1:
                    cut = int(self.rng.integers(1, max(2, len(flat1))))
                    child_seq = flat1[:cut] + [c for c in flat2 if c not in flat1[:cut]]
                    child_r   = _seq_to_routes_inst(child_seq, self.inst)
                else:
                    child_r = [list(r) for r in r1]
                child_r = perturb_route(self.inst, child_r, self.rng)
                child_f = evaluate(self.inst, child_r)

                # Update ideal point
                for m in range(3):
                    if child_f[m] > z_star[m]:
                        z_star[m] = child_f[m]

                # Update neighbourhood solutions
                for nb_idx in nbhd[i]:
                    w = self.weights[nb_idx]
                    current_scal = self._tchebycheff(pop[nb_idx][0], w, z_star)
                    child_scal   = self._tchebycheff(child_f, w, z_star)
                    if child_scal <= current_scal:
                        pop[nb_idx] = (child_f, child_r)

                # Update archive
                archive_objs = [a[0] for a in archive]
                if not any(dominates(ao, child_f) for ao in archive_objs):
                    archive = [(f, r) for f, r in archive
                               if not dominates(child_f, f)]
                    archive.append((child_f, child_r))

        return archive, time.time() - t_start


def _seq_to_routes_inst(seq, inst):
    routes = []; route = []; cap = inst.capacity
    for c in seq:
        d = inst.demand[c]
        if cap >= d:
            route.append(c); cap -= d
        else:
            if route: routes.append(route)
            route = [c]; cap = inst.capacity - d
    if route: routes.append(route)
    return routes


# ─────────────────────────────────────────────────────────────────────────────
# MOPSO
# ─────────────────────────────────────────────────────────────────────────────

class MOPSO:
    """
    Multi-Objective Particle Swarm Optimisation with external Pareto archive.
    Each particle has a position (route permutation) and velocity (swap sequence).
    Leader selection: random from archive (crowding-distance-weighted).
    """
    def __init__(self, inst, swarm_size=60, n_iter=200, seed=1):
        self.inst       = inst
        self.swarm_size = swarm_size
        self.n_iter     = n_iter
        self.rng        = np.random.default_rng(seed)
        self.w          = 0.70
        self.c1         = 1.50
        self.c2         = 1.50
        self.archive_max = 100

    def _init_swarm(self):
        base = nearest_neighbour(self.inst)
        swarm = []
        for _ in range(self.swarm_size):
            r  = perturb_route(self.inst, base, self.rng)
            f  = evaluate(self.inst, r)
            swarm.append({"pos": r, "f": f, "pbest_r": [list(x) for x in r], "pbest_f": f})
        return swarm

    def _select_leader(self, archive):
        """Crowding-distance weighted random leader from archive."""
        if len(archive) == 1:
            return archive[0]
        archive_objs = [a[0] for a in archive]
        cd = crowding_distance(archive_objs)
        total = sum(cd) if sum(cd) > 0 else len(cd)
        weights = [c/total if total > 0 else 1/len(cd) for c in cd]
        idx = self.rng.choice(len(archive), p=weights)
        return archive[idx]

    def _move(self, particle, leader_r):
        """Apply velocity update (random swaps toward pbest and leader)."""
        current_r = particle["pos"]
        pbest_r   = particle["pbest_r"]
        flat_cur  = [c for r in current_r  for c in r]
        flat_pb   = [c for r in pbest_r    for c in r]
        flat_ld   = [c for r in leader_r   for c in r]
        if not flat_cur:
            return current_r

        # Cognitive: some swaps toward personal best
        new_seq = list(flat_cur)
        n_cog = max(1, int(self.c1 * self.rng.random() * len(new_seq) * 0.1))
        for _ in range(n_cog):
            if flat_pb:
                target_pos = int(self.rng.integers(0, len(flat_pb)))
                target_val = flat_pb[target_pos]
                if target_val in new_seq:
                    cur_pos = new_seq.index(target_val)
                    if cur_pos != target_pos % len(new_seq):
                        other = new_seq[target_pos % len(new_seq)]
                        new_seq[cur_pos] = other
                        new_seq[target_pos % len(new_seq)] = target_val

        # Social: some swaps toward leader
        n_soc = max(1, int(self.c2 * self.rng.random() * len(new_seq) * 0.1))
        for _ in range(n_soc):
            if flat_ld:
                target_pos = int(self.rng.integers(0, len(flat_ld)))
                target_val = flat_ld[target_pos]
                if target_val in new_seq:
                    cur_pos = new_seq.index(target_val)
                    if cur_pos != target_pos % len(new_seq):
                        other = new_seq[target_pos % len(new_seq)]
                        new_seq[cur_pos] = other
                        new_seq[target_pos % len(new_seq)] = target_val

        return _seq_to_routes_inst(new_seq, self.inst)

    def _update_archive(self, archive, new_f, new_r):
        """Maintain external Pareto archive."""
        archive_objs = [a[0] for a in archive]
        if any(dominates(ao, new_f) for ao in archive_objs):
            return archive
        archive = [(f, r) for f, r in archive if not dominates(new_f, f)]
        archive.append((new_f, new_r))
        # Trim to archive_max using crowding distance
        if len(archive) > self.archive_max:
            objs = [a[0] for a in archive]
            cd   = crowding_distance(objs)
            archive = [archive[i] for i in np.argsort(cd)[::-1][:self.archive_max]]
        return archive

    def run(self):
        swarm   = self._init_swarm()
        archive = [(p["f"], p["pos"]) for p in swarm]
        archive_objs = [a[0] for a in archive]
        nd_idx  = pareto_filter([(f, None) for f in archive_objs])
        archive = [archive[i] for i in nd_idx]
        t_start = time.time()

        for _ in range(self.n_iter):
            for particle in swarm:
                leader_f, leader_r = self._select_leader(archive)
                new_r = self._move(particle, leader_r)
                new_r = perturb_route(self.inst, new_r, self.rng)
                new_f = evaluate(self.inst, new_r)

                particle["pos"] = new_r
                particle["f"]   = new_f

                # Update personal best (dominance-based)
                if dominates(new_f, particle["pbest_f"]):
                    particle["pbest_f"] = new_f
                    particle["pbest_r"] = [list(r) for r in new_r]

                archive = self._update_archive(archive, new_f, new_r)

        return archive, time.time() - t_start


# ─────────────────────────────────────────────────────────────────────────────
# MO-ALNS  (Multi-Objective ALNS with Pareto acceptance)
# ─────────────────────────────────────────────────────────────────────────────

class MOALNS:
    """
    Multi-Objective Adaptive Large Neighbourhood Search.
    Extends ALNS with Pareto-based acceptance: a new solution is accepted if it
    is non-dominated w.r.t. the current solution (on any objective dimension).
    External archive maintains non-dominated set throughout.
    """
    def __init__(self, inst, n_iter=300, seed=1):
        self.inst   = inst
        self.n_iter = n_iter
        self.rng    = np.random.default_rng(seed)
        self.q_min  = max(1, int(0.1 * inst.n))
        self.q_max  = max(2, int(0.4 * inst.n))
        self.rho    = 0.80
        self.sigma  = [33, 9, 13]    # rewards: new_archive_member, accepted, better_one_obj
        self.w_destroy = np.ones(4)
        self.w_repair  = np.ones(3)

    def _destroy(self, routes, op):
        """Remove q customers from routes."""
        all_custs = [c for r in routes for c in r]
        if not all_custs: return routes, []
        q = int(self.rng.integers(self.q_min, self.q_max+1))
        q = min(q, len(all_custs))

        if op == 0:   # random removal
            removed = list(self.rng.choice(all_custs, q, replace=False))
        elif op == 1: # worst removal (highest demand / lowest priority)
            scores = sorted(all_custs, key=lambda c: self.inst.demand[c] / self.inst.priority[c])
            removed = scores[:q]
        elif op == 2: # time-window removal (cluster by early time)
            sorted_c = sorted(all_custs, key=lambda c: self.inst.early[c])
            start = int(self.rng.integers(0, max(1, len(sorted_c)-q)))
            removed = sorted_c[start:start+q]
        else:         # proximity removal (geographic cluster)
            seed_c  = all_custs[int(self.rng.integers(0, len(all_custs)))]
            seed_loc= self.inst.locs[seed_c]
            dists   = [(np.linalg.norm(self.inst.locs[c]-seed_loc), c) for c in all_custs]
            removed = [c for _, c in sorted(dists)[:q]]

        removed_set = set(removed)
        new_routes  = [[c for c in r if c not in removed_set] for r in routes]
        new_routes  = [r for r in new_routes if r]
        return new_routes, removed

    def _repair(self, routes, removed, op):
        """Re-insert removed customers using greedy or regret insertion."""
        if not removed: return routes
        unserved = list(removed)
        current  = [list(r) for r in routes]

        def insertion_cost(r, pos, c):
            prev = self.inst.n if pos == 0 else r[pos-1]
            next_ = self.inst.n if pos == len(r) else r[pos]
            return (self.inst.dist[prev, c] + self.inst.dist[c, next_]
                    - self.inst.dist[prev, next_]) * 50

        def best_insert(c, routes):
            best_cost, best_v, best_p = float('inf'), -1, -1
            for vi, r in enumerate(routes):
                cap = sum(self.inst.demand[x] for x in r)
                if cap + self.inst.demand[c] > self.inst.capacity:
                    continue
                for p in range(len(r)+1):
                    cost = insertion_cost(r, p, c)
                    if cost < best_cost:
                        best_cost, best_v, best_p = cost, vi, p
            if best_v == -1:
                current.append([c])
                return current, 0
            current[best_v].insert(best_p, c)
            return current, best_cost

        if op == 0:  # greedy
            for c in unserved:
                current, _ = best_insert(c, current)
        else:        # regret-k (op=1 -> k=2, op=2 -> k=3)
            k = op + 1
            while unserved:
                regrets = []
                for c in unserved:
                    costs = []
                    for vi, r in enumerate(current):
                        cap = sum(self.inst.demand[x] for x in r)
                        if cap + self.inst.demand[c] > self.inst.capacity:
                            continue
                        for p in range(len(r)+1):
                            costs.append(insertion_cost(r, p, c))
                    costs.sort()
                    if len(costs) >= k:
                        regrets.append((costs[k-1]-costs[0], c))
                    elif len(costs) >= 1:
                        regrets.append((costs[-1], c))
                    else:
                        regrets.append((float('inf'), c))
                regrets.sort(reverse=True)
                best_c = regrets[0][1]
                unserved.remove(best_c)
                current, _ = best_insert(best_c, current)

        return current

    def run(self):
        routes  = nearest_neighbour(self.inst)
        current_f = evaluate(self.inst, routes)
        archive = [(current_f, [list(r) for r in routes])]
        t_start = time.time()

        for it in range(self.n_iter):
            # Select operators via roulette
            d_probs = self.w_destroy / self.w_destroy.sum()
            r_probs = self.w_repair  / self.w_repair.sum()
            d_op = int(self.rng.choice(4, p=d_probs))
            r_op = int(self.rng.choice(3, p=r_probs))

            new_routes, removed = self._destroy(routes, d_op)
            new_routes = self._repair(new_routes, removed, r_op)
            new_f = evaluate(self.inst, new_routes)

            # Pareto-based acceptance: accept if not dominated by current
            reward = 0
            archive_objs = [a[0] for a in archive]
            if not any(dominates(ao, new_f) for ao in archive_objs):
                # New solution joins archive
                archive = [(f, r) for f, r in archive if not dominates(new_f, f)]
                archive.append((new_f, [list(r) for r in new_routes]))
                reward = self.sigma[0]
                routes = new_routes; current_f = new_f
            elif not dominates(current_f, new_f):
                # Doesn't dominate archive but doesn't dominate current either
                routes = new_routes; current_f = new_f
                reward = self.sigma[1]
            elif any(new_f[m] > current_f[m] for m in range(3)):
                reward = self.sigma[2]

            # Update weights
            self.w_destroy[d_op] = self.rho*self.w_destroy[d_op] + (1-self.rho)*reward
            self.w_repair[r_op]  = self.rho*self.w_repair[r_op]  + (1-self.rho)*reward

        return archive, time.time() - t_start


# ─────────────────────────────────────────────────────────────────────────────
# COMPARISON EXPERIMENT + FIGURES
# ─────────────────────────────────────────────────────────────────────────────

MOO_ALGOS  = ["NSGA-II", "MOEA/D", "MOPSO", "MO-ALNS"]
MOO_COLORS = ["#1565C0", "#2E7D32", "#E53935", "#7B1FA2"]

def run_moo_comparison(n=50, phi_min=0.85, n_seeds=5):
    """Run all 4 MOO algorithms and record archive quality metrics."""
    print(f"\n  Running MOO comparison (n={n}, phi_min={phi_min})...")
    rows = []

    for seed in range(1, n_seeds+1):
        inst = CVRPTWInstance(n, phi_min=phi_min, seed=seed)
        algos = [
            ("NSGA-II", NSGAII(inst, pop_size=60, n_gen=150, seed=seed)),
            ("MOEA/D",  MOEAD(inst,  H=15,         n_gen=150, seed=seed)),
            ("MOPSO",   MOPSO(inst,  swarm_size=60, n_iter=150, seed=seed)),
            ("MO-ALNS", MOALNS(inst, n_iter=300,   seed=seed)),
        ]
        # Reference front = union of all archives
        all_archives = []
        for name, algo in algos:
            archive, ct = algo.run()
            all_archives.extend(archive)
            rows.append(dict(algo=name, seed=seed, phi_min=phi_min, n=n,
                             n_pareto=len(archive), CT=round(ct,3),
                             f1_mean=round(np.mean([a[0][0] for a in archive]),4) if archive else 0,
                             f2_mean=round(np.mean([a[0][1] for a in archive]),4) if archive else 0,
                             f3_mean=round(np.mean([a[0][2] for a in archive]),4) if archive else 0))
            print(f"    {name}: |Pareto|={len(archive)}, CT={ct:.1f}s")

    return pd.DataFrame(rows)


def _compute_hv_2d(front_objs, ref=(0.0, 0.0)):
    """2D HV on (f1,f3) projection."""
    pts = sorted([(f[0], f[2]) for f in front_objs], key=lambda p: -p[0])
    hv = 0.0
    prev_f3 = ref[1]
    for f1, f3 in pts:
        if f1 > ref[0] and f3 > prev_f3:
            hv += (f1 - ref[0]) * (f3 - prev_f3)
            prev_f3 = max(prev_f3, f3)
    return hv


def plot_moo_comparison(df):
    """Generate figures comparing the 4 MOO algorithms."""
    print("\n  Generating MOO comparison figures...")

    # Figure 1: Pareto front scatter (f1 vs f3, f1 vs -f2)
    rng_vis = np.random.default_rng(42)
    inst_vis = CVRPTWInstance(50, phi_min=0.85, seed=1)

    algos_vis = [
        ("NSGA-II",  NSGAII(inst_vis,  pop_size=60, n_gen=150, seed=1)),
        ("MOEA/D",   MOEAD(inst_vis,   H=15,         n_gen=150, seed=1)),
        ("MOPSO",    MOPSO(inst_vis,   swarm_size=60, n_iter=150, seed=1)),
        ("MO-ALNS",  MOALNS(inst_vis,  n_iter=300,   seed=1)),
    ]
    archives = {}
    for name, algo in algos_vis:
        archive, _ = algo.run()
        archives[name] = archive

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for name, col in zip(MOO_ALGOS, MOO_COLORS):
        arch = archives.get(name, [])
        if not arch: continue
        f1v = [a[0][0] for a in arch]
        f2v = [-a[0][1] for a in arch]   # back to positive distance
        f3v = [a[0][2] for a in arch]
        axes[0].scatter(f1v, f3v, s=40, c=col, alpha=0.75, edgecolors="white",
                        lw=0.4, label=name)
        axes[1].scatter(f1v, f2v, s=40, c=col, alpha=0.75, edgecolors="white",
                        lw=0.4, label=name)

    for ax, xl, yl, title in [
        (axes[0], "f₁: Satisfaction (higher=better)", "f₃: Reliability (higher=better)",
         "Pareto Projection: f₁ × f₃"),
        (axes[1], "f₁: Satisfaction (higher=better)", "f₂: Distance km (lower=better, shown +ve)",
         "Pareto Projection: f₁ × f₂"),
    ]:
        ax.set_xlabel(xl); ax.set_ylabel(yl)
        ax.set_title(title, fontweight="bold"); ax.legend(fontsize=9); ax.grid(alpha=0.25)

    fig.suptitle("MOO-NEW-1  Pareto Front Comparison: NSGA-II vs MOEA/D vs MOPSO vs MO-ALNS\n"
                 "(n=50, φ_min=0.85, seed=1) — these replace scalarised GA and PSO",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO_NEW1_pareto_comparison")
    plt.close(fig)

    # Figure 2: Bar chart — Pareto front size and CT
    summary = df.groupby("algo")[["n_pareto","CT","f1_mean","f3_mean"]].mean().round(3)
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    for ax, col, ylabel, title in [
        (axes[0],"n_pareto","Pareto Front Size |F|","Archive Size"),
        (axes[1],"CT","Computation Time (s)","Computation Time"),
        (axes[2],"f1_mean","Mean f₁ in Archive","Mean Satisfaction in Archive"),
    ]:
        vals = [summary.loc[a, col] if a in summary.index else 0 for a in MOO_ALGOS]
        bars = ax.bar(MOO_ALGOS, vals, color=MOO_COLORS, alpha=0.82)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x()+bar.get_width()/2, v+v*0.02,
                    f"{v:.2f}", ha="center", fontsize=9, fontweight="bold")
        ax.set_ylabel(ylabel); ax.set_title(title, fontweight="bold")
        ax.set_xticklabels(MOO_ALGOS, rotation=15); ax.grid(axis="y", alpha=0.25)

    fig.suptitle("MOO-NEW-2  Algorithm Performance Metrics: Archive Quality and Speed\n"
                 "(n=50, φ_min=0.85, mean over 5 seeds)",
                 fontsize=11, fontweight="bold")
    fig.tight_layout()
    savefig(fig, FIG_NEW, "MOO_NEW2_algo_metrics")
    plt.close(fig)

    # Figure 3: Performance across phi_min levels
    if "phi_min" in df.columns and df["phi_min"].nunique() > 1:
        phi_u = sorted(df["phi_min"].unique(), reverse=True)
        fig, ax = plt.subplots(figsize=(9, 5.5))
        for name, col in zip(MOO_ALGOS, MOO_COLORS):
            sub = df[df["algo"]==name]
            n_p = [sub.loc[sub["phi_min"]==p,"n_pareto"].mean() for p in phi_u]
            ax.plot(phi_u, n_p, "o-", color=col, lw=2.2, ms=7, label=name)
        ax.set_xlabel("φ_min"); ax.set_ylabel("Mean Pareto Front Size |F|")
        ax.set_title("MOO-NEW-3  Pareto Archive Size vs φ_min\n"
                     "Smaller A(φ_min) → fewer non-dominated solutions",
                     fontweight="bold")
        ax.invert_xaxis(); ax.legend(fontsize=9); ax.grid(alpha=0.25)
        fig.tight_layout()
        savefig(fig, FIG_NEW, "MOO_NEW3_archive_vs_phi")
        plt.close(fig)

    print("  MOO figures saved.")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def run_all():
    print("=" * 60)
    print("Multi-Objective Algorithm Comparison")
    print("NSGA-II | MOEA/D | MOPSO | MO-ALNS")
    print("=" * 60)

    # Run comparison at phi=0.85 (primary) and phi=0.70 (stress)
    dfs = []
    for phi in [1.00, 0.85, 0.70]:
        df = run_moo_comparison(n=50, phi_min=phi, n_seeds=5)
        dfs.append(df)
    df_all = pd.concat(dfs, ignore_index=True)

    path = os.path.join(TABLES, "moo_comparison.csv")
    df_all.to_csv(path, index=False)
    print(f"\n  Saved: moo_comparison.csv ({len(df_all)} rows)")

    # Summary table
    print("\n  Summary (mean over seeds, phi=0.85):")
    sub = df_all[abs(df_all["phi_min"]-0.85)<1e-9]
    print(sub.groupby("algo")[["n_pareto","CT","f1_mean","f3_mean"]].mean().round(3).to_string())

    # Figures
    plot_moo_comparison(df_all)

    print("\n  Done. Figures in:", FIG_NEW)
    return df_all


if __name__ == "__main__":
    run_all()
