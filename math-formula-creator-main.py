from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional
from bisect import bisect_right
from itertools import combinations
import re


@dataclass(frozen=True)
class Item:
    value: float                 # numeric value of the minterm
    literals: Tuple[str, ...]    # e.g., ('usdt_brl', 'inv:cos_usdt')
    idx: int


@dataclass
class Term:
    literals: Tuple[str, ...]
    coeff: int = 1
    def key(self) -> Tuple[str, ...]:
        return self.literals


class GreedyExpressionApproximator:
    """
    Build minterms with exponents in {-1, 0, +1} per base variable (inv:x means 1/x).
    Select a subset (no repeats) whose sum is the best <= target.
    Factor recursively by common subsets and render products as num/(den) safely,
    avoiding precedence bugs when parentheses are omitted in 1/x.
    """
    def __init__(self, data: Dict[str, float], target: float, tolerance: float = 1e-9):
        self.data = data
        self.target = target
        self.tolerance = tolerance
        self.items: List[Item] = []
        self.terms: List[Term] = []
        self.factored_expr: str = ""
        self.final_value: float = 0.0

    # ---------- Build minterms with {-1,0,+1} exponents ----------
    def build_items(self):
        keys = list(self.data.keys())
        vals = list(self.data.values())
        n = len(keys)
        uid = 0

        def enumerate_trits(n: int):
            """Yield vectors of length n with entries in {-1,0,1}, excluding the all-zero vector."""
            total = 3 ** n
            for m in range(total):
                vec = []
                tmp = m
                all_zero = True
                for _ in range(n):
                    d = tmp % 3  # 0,1,2
                    tmp //= 3
                    e = -1 if d == 0 else (0 if d == 1 else 1)
                    vec.append(e)
                    if e != 0:
                        all_zero = False
                if not all_zero:
                    yield vec

        for evec in enumerate_trits(n):
            v = 1.0
            lits: List[str] = []
            for i, e in enumerate(evec):
                if e == 1:
                    v *= vals[i]
                    lits.append(keys[i])
                elif e == -1:
                    v /= vals[i]
                    lits.append(f"inv:{keys[i]}")  # inverse token
            if v <= 0:
                continue
            if v <= self.target + self.tolerance:
                self.items.append(Item(value=v, literals=tuple(sorted(lits)), idx=uid))
                uid += 1

        self.items.sort(key=lambda it: it.value)
        print(f"[INFO] Generated {len(self.items)} valid minterms (with inverses).")

    # ---------- Selection (best <= target) ----------
    def select_items(self):
        values_sorted = [it.value for it in self.items]
        selected: List[int] = []
        selected_set = set()
        total = 0.0

        def take_largest_not_exceeding(gap: float, banned: set) -> Optional[int]:
            if gap <= 0:
                return None
            pos = bisect_right(values_sorted, gap) - 1
            while pos >= 0:
                if self.items[pos].idx not in banned:
                    return pos
                pos -= 1
            return None

        # Greedy fill
        while True:
            gap = self.target - total
            pos = take_largest_not_exceeding(gap, selected_set)
            if pos is None:
                break
            it = self.items[pos]
            total += it.value
            selected.append(pos)
            selected_set.add(it.idx)

        # Pair fill improvement
        def best_pair_under_gap(gap: float, banned: set) -> Optional[Tuple[int, int, float]]:
            lo, hi = 0, len(self.items) - 1
            best = None
            best_sum = -1.0
            while lo < hi:
                a, b = self.items[lo], self.items[hi]
                if a.idx in banned:
                    lo += 1
                    continue
                if b.idx in banned:
                    hi -= 1
                    continue
                s = a.value + b.value
                if s > gap + self.tolerance:
                    hi -= 1
                else:
                    if s > best_sum:
                        best_sum = s
                        best = (lo, hi, s)
                    lo += 1
            return best

        improved = True
        while improved:
            improved = False
            gap = self.target - total
            pair = best_pair_under_gap(gap, selected_set)
            if pair:
                i, j, s = pair
                total += s
                selected.extend([i, j])
                selected_set.add(self.items[i].idx)
                selected_set.add(self.items[j].idx)
                improved = True

        # Safety
        assert total <= self.target + self.tolerance
        self.final_value = total

        # Build unique terms list
        self.terms = [Term(self.items[p].literals, 1) for p in selected]
        self.terms = self._simplify_terms(self.terms)

    # ---------- Factorization ----------
    def _simplify_terms(self, terms: List[Term]) -> List[Term]:
        c = Counter()
        for t in terms:
            c[t.key()] += t.coeff
        return [Term(lits, coeff) for lits, coeff in c.items() if coeff != 0]

    def _find_best_common_subset(self, tlist: List[Term]) -> Optional[Tuple[Tuple[str, ...], List[int]]]:
        index_by_subset: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
        for idx, t in enumerate(tlist):
            lits = list(t.literals)
            if len(lits) >= 2:
                for sub in combinations(lits, 2):
                    index_by_subset[tuple(sorted(sub))].append(idx)
            for sub in combinations(lits, 1):
                index_by_subset[(sub[0],)].append(idx)
        best, best_sc = None, (0, 0)
        for sub, idxs in index_by_subset.items():
            if len(idxs) < 2:
                continue
            sc = (len(sub), len(idxs))  # prefer larger subset, then more hits
            if sc > best_sc:
                best_sc = sc
                best = (sub, idxs)
        return best

    # ---- NEW: robust product rendering (no ambiguous 1/x) ----
    def _render_product(self, lits: Tuple[str, ...]) -> str:
        """
        Render a product of tokens where tokens can be 'var' or 'inv:var' (meaning 1/var).
        Returns a string like:
          'a*b/c'                 (1 denominator)
          'a*b/(c*d)'             (>=2 denominators)
          '1/c'                   (no numerator)
        """
        nums: List[str] = []
        dens: List[str] = []
        for tok in lits:
            if tok.startswith("inv:"):
                dens.append(tok[4:])
            else:
                nums.append(tok)
        if not nums:
            nums = ["1"]
        num = "*".join(nums)
        if not dens:
            return num
        if len(dens) == 1:
            return f"{num}/{dens[0]}"
        den = "*".join(dens)
        return f"{num}/({den})"

    def _render_sum(self, tlist: List[Term]) -> str:
        if not tlist:
            return "0"
        parts = []
        for t in tlist:
            if len(t.literals) == 0:
                parts.append(str(t.coeff))
            else:
                parts.append(self._render_product(t.literals))
        return " + ".join(parts)

    def _factor_recursive(self, tlist: List[Term]) -> str:
        tlist = self._simplify_terms(tlist)
        best = self._find_best_common_subset(tlist)
        if not best:
            return self._render_sum(tlist)
        sub, idxs = best
        sub_set = set(sub)
        inside, outside = [], []
        for i, t in enumerate(tlist):
            if i in idxs:
                remain = tuple(sorted(x for x in t.literals if x not in sub_set))
                inside.append(Term(remain, t.coeff))
            else:
                outside.append(t)
        inside_str = self._factor_recursive(inside)
        outside_str = self._factor_recursive(outside) if outside else ""
        factor_str = self._render_product(sub)
        if outside_str and outside_str != "0":
            return f"{factor_str}*({inside_str}) + {outside_str}"
        else:
            return f"{factor_str}*({inside_str})"

    # ---------- Evaluate ----------
    def evaluate_expression(self, expr: str) -> float:
        expr_eval = expr
        # Replace longer keys first & use word boundaries to avoid partial matches
        for k in sorted(self.data.keys(), key=len, reverse=True):
            expr_eval = re.sub(rf'\b{k}\b', str(self.data[k]), expr_eval)
        return eval(expr_eval, {"__builtins__": {}})

    # ---------- Run ----------
    def run(self):
        self.build_items()
        self.select_items()
        expr = self._factor_recursive(self.terms)
        self.factored_expr = expr
        numeric_result = self.evaluate_expression(expr)
        return {
            "used_literals": sorted({l for t in self.terms for l in t.literals}),
            "final_sum": self.final_value,
            "expression": self.factored_expr,
            "numeric_result": numeric_result,
        }


# ------------------ Example ------------------
if __name__ == "__main__":
    data = {
        "min_qty": 0.1,
        "cos_brl": 0.022496208,
        "cos_usdt": 0.003864,
        "usdt_brl": 5.2,
    }
    target = 159.2

    approximator = GreedyExpressionApproximator(data, target)
    result = approximator.run()

    print("Used variables:", ", ".join(result["used_literals"]))
    print(f"Final sum (≤ target): {result['final_sum']:.12f} | Target: {target}")
    print("Factored expression (recursive):")
    print(result["expression"])
    print("Numeric check (substitution):")
    print(result["numeric_result"])