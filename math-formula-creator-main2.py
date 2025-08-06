from functools import reduce
from math import sqrt, log
from re import findall

# --- Funções auxiliares ---
logical_and_mathematical_operation = lambda number, choices: reduce(
    lambda a, b: a * b,
    [j for i, j in zip([int(i) for i in bin(number)[2:][::-1]], choices[::-1]) if i],
    1
)

choice_enabler = lambda number, choices: [
    j for i, j in zip([int(i) for i in bin(number)[2:][::-1]], choices[::-1]) if i
]

# --- Busca Binária para Minitermos ---
def binary_search_to_find_miniterm_from_dict(wanted_number, array_dict):
    array_dict = dict(sorted(array_dict.items(), key=lambda x: x[1]))
    arr = list(array_dict.values())
    keys = list(array_dict.keys())
    l, r = 0, len(arr) - 1
    while l <= r:
        mid = (l + r) // 2
        if arr[mid] == wanted_number:
            return arr[mid], keys[mid]
        elif arr[mid] < wanted_number:
            l = mid + 1
        else:
            r = mid - 1
    idx = min(max(l, 0), len(arr) - 1)
    return arr[idx], keys[idx]

# --- Dados de entrada ---
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

expected_result = 120.59
values = list(data.values())
truth_table = {i: logical_and_mathematical_operation(i, values) for i in range(2 ** len(data))}

# --- Construção da expressão ---
final_result = 0
expression_terms = []
used_literals = set()

while abs(expected_result - final_result) > 1e-9:
    approx, idx = binary_search_to_find_miniterm_from_dict(expected_result - final_result, truth_table)
    term_literals = choice_enabler(idx, list(data.keys()))
    used_literals.update(term_literals)
    coef = 1 if not term_literals else ""
    sign = "+" if final_result < expected_result else "-"
    expression_terms.append(f"{sign}{coef}{'*'.join(term_literals) if term_literals else '1'}")
    final_result += approx if final_result < expected_result else -approx

# --- Geração da expressão ---
expression = "".join(expression_terms).lstrip('+')

# --- Substituir variáveis pelos valores ---
for k, v in data.items():
    expression = expression.replace(k, f"({v})")

# --- Simplificação usando regras básicas ---
def simplify(expr):
    expr = expr.replace("**0.5", "√")  # radiciação
    expr = expr.replace("*1", "")      # remover multiplicações por 1
    expr = expr.replace("1*", "")      # idem
    # regra simples de potências repetidas
    for base in data.keys():
        expr = expr.replace(f"({data[base]})*({data[base]})", f"({data[base]}^2)")
    return expr

simplified_expr = simplify(expression)

# --- Prova real ---
evaluated = eval(expression)

# --- Saídas ---
print(f"Expressão Algébrica: {simplified_expr}")
print(f"Resultado Calculado: {evaluated}")
print(f"Resultado Esperado: {expected_result}")
if abs(evaluated - expected_result) > 1e-6:
    print("⚠️ Inconsistência detectada na prova real!")