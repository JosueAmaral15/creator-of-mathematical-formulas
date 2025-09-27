from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple, Iterable, Optional
from bisect import bisect_right
from itertools import combinations


@dataclass(frozen=True)
class Item:
    """A truth-table minterm."""
    value: float
    literals: Tuple[str, ...]
    idx: int


@dataclass
class Term:
    """Symbolic term: coefficient * product(literals)."""
    literals: Tuple[str, ...]
    coeff: int = 1

    def key(self) -> Tuple[str, ...]:
        return self.literals


class GreedyExpressionApproximator:
    def __init__(self, data: Dict[str, float], target: float, tolerance: float = 1e-9):
        self.data = data
        self.target = target
        self.tolerance = tolerance
        self.items: List[Item] = []
        self.terms: List[Term] = []
        self.factored_expr: str = ""
        self.final_value: float = 0.0

    # =========================
    # Utility methods
    # =========================
    def bitmask_pairs(self, n: int, items: List) -> Iterable[Tuple[int, float]]:
        b = bin(n)[2:][::-1]
        for bit, item in zip((int(ch) for ch in b), items[::-1]):
            yield bit, item

    def product_from_mask(self, n: int, values: List[float]) -> float:
        prod = 1.0
        for bit, v in self.bitmask_pairs(n, values):
            if bit:
                prod *= v
        return prod

    def chosen_names_from_mask(self, n: int, keys: List[str]) -> List[str]:
        return [
            name
            for (bit, name) in (
                (int(ch), nm) for ch, nm in zip(bin(n)[2:][::-1], keys[::-1])
            )
            if bit
        ]

    # =========================
    # Build truth table
    # =========================
    def build_items(self):
        keys = list(self.data.keys())
        vals = list(self.data.values())
        N = 2 ** len(self.data)

        uid = 0
        for i in range(1, N):
            v = self.product_from_mask(i, vals)
            if v <= 0:
                continue
            lits = tuple(sorted(self.chosen_names_from_mask(i, keys)))
            if v <= self.target + self.tolerance:
                self.items.append(Item(value=v, literals=lits, idx=uid))
                uid += 1

        self.items.sort(key=lambda it: it.value)
        print(f"[INFO] Generated {len(self.items)} valid minterms.")

    # =========================
    # Knapsack-like selection (never exceeds target)
    # =========================
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

        # Step 1: Greedy fill
        while True:
            gap = self.target - total
            pos = take_largest_not_exceeding(gap, selected_set)
            if pos is None:
                break
            it = self.items[pos]
            total += it.value
            selected.append(pos)
            selected_set.add(it.idx)

        # Step 2: Pair fill and small improvements
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
                continue

            # Try 1→2 replacement
            chosen_sorted = sorted(selected, key=lambda p: self.items[p].value)
            for rem_pos in chosen_sorted:
                freed = self.items[rem_pos].value
                gap2 = self.target - (total - freed)
                banned = selected_set.copy()
                banned.remove(self.items[rem_pos].idx)
                pair2 = best_pair_under_gap(gap2, banned)
                if pair2:
                    i, j, s = pair2
                    if s > freed + 1e-12:
                        total = total - freed + s
                        selected_set.remove(self.items[rem_pos].idx)
                        selected.remove(rem_pos)
                        if self.items[i].idx not in selected_set:
                            selected.append(i)
                            selected_set.add(self.items[i].idx)
                        if self.items[j].idx not in selected_set:
                            selected.append(j)
                            selected_set.add(self.items[j].idx)
                        improved = True
                        break

        assert total <= self.target + self.tolerance
        self.final_value = total

        # Create terms
        self.terms = [Term(self.items[pos].literals, coeff=1) for pos in selected]
        self.terms = self.simplify_terms(self.terms)

    # =========================
    # Simplify & factorization
    # =========================
    def simplify_terms(self, terms: List[Term]) -> List[Term]:
        c = Counter()
        for t in terms:
            c[t.key()] += t.coeff
        return [Term(lits, coeff) for lits, coeff in c.items() if coeff != 0]

    def score_factor(self, sub: Tuple[str, ...], hits: int) -> Tuple[int, int]:
        return (len(sub), hits)

    def find_best_common_subset(self, tlist: List[Term]) -> Optional[Tuple[Tuple[str, ...], List[int]]]:
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
            sc = self.score_factor(sub, len(idxs))
            if sc > best_sc:
                best_sc = sc
                best = (sub, idxs)
        return best

    def render_sum(self, tlist: List[Term]) -> str:
        if not tlist:
            return "0"
        parts = []
        for t in tlist:
            if len(t.literals) == 0:
                parts.append(str(t.coeff))
            else:
                if t.coeff == 1:
                    parts.append("*".join(t.literals))
                else:
                    parts.append(str(t.coeff) + "*" + "*".join(t.literals))
        return " + ".join(parts)

    def factor_recursive(self, tlist: List[Term]) -> str:
        tlist = self.simplify_terms(tlist)
        best = self.find_best_common_subset(tlist)
        if not best:
            return self.render_sum(tlist)
        sub, idxs = best
        sub_set = set(sub)
        inside, outside = [], []
        for i, t in enumerate(tlist):
            if i in idxs:
                remain = tuple(sorted(x for x in t.literals if x not in sub_set))
                inside.append(Term(remain, t.coeff))
            else:
                outside.append(t)
        inside_str = self.factor_recursive(inside)
        outside_str = self.factor_recursive(outside) if outside else ""
        factor_str = "*".join(sub)
        if outside_str and outside_str != "0":
            return f"{factor_str}*({inside_str}) + {outside_str}"
        else:
            return f"{factor_str}*({inside_str})"

    # =========================
    # Evaluate final expression
    # =========================
    def evaluate_expression(self, expr: str) -> float:
        expr_eval = expr
        for k in sorted(self.data.keys(), key=len, reverse=True):
            expr_eval = expr_eval.replace(k, str(self.data[k]))
        return eval(expr_eval, {"__builtins__": {}})

    # =========================
    # Main workflow
    # =========================
    def run(self):
        self.build_items()
        self.select_items()
        self.factored_expr = self.factor_recursive(self.terms)
        numeric_result = self.evaluate_expression(self.factored_expr)
        return {
            "used_literals": sorted({l for t in self.terms for l in t.literals}),
            "final_sum": self.final_value,
            "expression": self.factored_expr,
            "numeric_result": numeric_result,
        }


# =========================
# Example usage
# =========================
if __name__ == "__main__":
    data = {
        "min_qty_inverse": 10,
        "min_qty": 0.1,
        "cos_brl_inverse(brl_cos)": 44.451936077,
        "cos_brl": 0.022496208,
        "cos_usdt_inverse(usdt_cos)": 258.999999,
        "cos_usdt": 0.003864,
        "usdt_brl_inverse(brl_usdt)" : 0.192307692,
        "usdt_brl" : 5.2,
    }
    target = 159.2

    approximator = GreedyExpressionApproximator(data, target)
    result = approximator.run()

    print("Used variables:", ", ".join(result["used_literals"]))
    print(f"Final sum: {result['final_sum']:.12f} | Target: {target}")
    print("Factored expression (recursive):")
    print(result["expression"])
    print("Numeric check (substitution):")
    print(result["numeric_result"])