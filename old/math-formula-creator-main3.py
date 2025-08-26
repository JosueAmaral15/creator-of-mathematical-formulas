from functools import reduce
from sympy import sympify, simplify, N
import re

# ------------------- Funções auxiliares -------------------
def logical_and_mathematical_operation(number, choices):
    bits = [int(i) for i in bin(number)[2:].zfill(len(choices))]
    return reduce(lambda a, b: a * b, [v for bit, v in zip(bits, choices) if bit], 1)

def choice_enabler(number, choices):
    bits = [int(i) for i in bin(number)[2:].zfill(len(choices))]
    return [v for bit, v in zip(bits, choices) if bit]

def binary_search_miniterm(wanted, dictionary):
    items = sorted(dictionary.items(), key=lambda x: x[1])
    values = [v for _, v in items]
    keys = [k for k, _ in items]
    l, r = 0, len(values) - 1
    while l <= r:
        mid = (l + r) // 2
        if values[mid] == wanted:
            return values[mid], keys[mid]
        elif values[mid] < wanted:
            l = mid + 1
        else:
            r = mid - 1
    idx = min(max(l, 0), len(values) - 1)
    return values[idx], keys[idx]

def safe_eval(expr):
    """Avaliação segura de expressões numéricas."""
    return eval(compile(expr, "", "eval"), {"__builtins__": None}, {})

# ------------------- Função Principal -------------------
def generate_optimized_expression(data, expected_result, tol=1e-9, max_iter=1000):
    values = list(data.values())
    truth_table = {i: logical_and_mathematical_operation(i, values) for i in range(2 ** len(values))}

    result = 0
    terms = []
    used_literals = set()
    count = 0

    # Construção da expressão com aproximação iterativa
    while abs(expected_result - result) > tol and count < max_iter:
        approx, idx = binary_search_miniterm(expected_result - result, truth_table)
        literals = choice_enabler(idx, list(data.keys()))
        coef = "1*" if literals else "1"
        sign = "+" if result < expected_result else "-"
        terms.append(f"{sign}{coef}{'*'.join(literals) if literals else '1'}")
        used_literals.update(literals)
        result += approx if result < expected_result else -approx
        count += 1

    # Monta expressão bruta
    raw_expr = "".join(terms).lstrip("+")

    # 🔹 Substitui todos os nomes de variáveis por seus valores numéricos (escapando caracteres especiais)
    numeric_expr = raw_expr
    for k, v in data.items():
        pattern = r"\b" + re.escape(k) + r"\b"
        numeric_expr = re.sub(pattern, f"({v})", numeric_expr)

    # 🔹 Corrige potências para formato Python/Sympy
    numeric_expr = numeric_expr.replace("^", "**")

    # 🔹 Avaliação segura
    try:
        # Tenta Sympy
        sym_expr = sympify(numeric_expr, evaluate=True)
        simplified_expr = simplify(sym_expr)
        evaluated = float(N(simplified_expr))
    except Exception:
        # Fallback: usa safe_eval diretamente
        try:
            evaluated = float(safe_eval(numeric_expr))
            simplified_expr = numeric_expr
        except Exception:
            evaluated = None
            simplified_expr = "Erro ao avaliar"

    inconsistency = evaluated is None or abs(evaluated - expected_result) > tol

    return {
        "raw_expression": raw_expr,
        "numeric_expression": numeric_expr,
        "simplified_expression": str(simplified_expr),
        "calculated": evaluated,
        "expected": expected_result,
        "inconsistency": inconsistency,
        "variables_used": used_literals,
        "usage_percent": round(100 * len(used_literals) / len(data), 2)
    }

# ------------------- Execução -------------------
if __name__ == "__main__":
    data = {
        "min_qty_inverse": 10,
        "min_qty": 0.1,
        "cos_brl_inverse(brl_cos)": 44.451936077,
        "cos_brl": 0.022496208,
        "cos_usdt_inverse(usdt_cos)": 258.999999,
        "cos_usdt": 0.003864,
        "usdt_brl_inverse(brl_usdt)": 0.192307692,
        "usdt_brl": 5.2,
    }
    
    expected = 120.59
    result = generate_optimized_expression(data, expected)

    # --- Saída final ---
    print("\n📌 Expressão Original:", result["raw_expression"])
    print("📌 Expressão Numérica:", result["numeric_expression"])
    print("📌 Expressão Simplificada:", result["simplified_expression"])
    print(f"📌 Resultado Calculado: {result['calculated']}")
    print(f"📌 Resultado Esperado: {result['expected']}")
    print(f"📌 Variáveis Usadas ({result['usage_percent']}%): {', '.join(result['variables_used'])}")
    print("⚠️ Inconsistência detectada!" if result["inconsistency"] else "✅ Prova real confirmada.")