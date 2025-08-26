from functools import reduce
from re import escape, findall
logical_and_mathematical_operation = lambda number, choices: reduce(lambda a, b: a * b, list(map(lambda x: x[1], list(filter(lambda a: a[0] * a[1], [(i,j) for i,j in zip([int(i) for i in str(bin(number))[2:][::-1]], choices[::-1])])))),1)
choice_enabler = lambda number, choices: list(map(lambda a: a[1], list(filter(lambda a: a[0], [(i,j) for i,j in zip([int(i) for i in str(bin(number))[2:][::-1]], choices[::-1])]))))

def binary_search_to_find_miniterm_from_dict (wanted_number, array_dict):
    determine_the_most_approximate_value = False # booleano que indica se deve acontecer o deslocamento em um determinado index
    array_dict_length = len(array_dict)-1 # Seria o tamanho ou o comprimento da lista, ou seja, quantos elementos tem a lista.
    factor_binary_search = (array_dict_length)//2 if array_dict_length % 2 != 0 else (array_dict_length+1)//2
    factor_is_zero = False # Verifica se a variável factor_binary_search tem valor zero
    first_iteration = True # Indica a primeira iteração do algoritmo.
    index_middle = array_dict_length # Seria uma variável que aponta para o meio entre o intervalo dos limites superior e inferior da lista através do valor da média entre o limite superior com o inferior. Seria a mesma coisa que mk.
    index_middle_result = index_middle # Guarda o valor da média (que aponta para o índice entre o limite inferior do intervalo com o limite superior do intervalo) com um número natural.
    lower_limit = 0 # Trata-se do limite inferior do intervalo. Seria equivalente a lk.
    average = lambda a, b: (a+b)/2 # função que calcula a média entre dois valores. Seria equivalente a mk+1
    upper_limit = array_dict_length # Limite superior do intervalo. Seria equivalente a uk.
    array_list = list(array_dict.values()) # array_list contém os resultados das operações da tabela verdade.
    
    while not determine_the_most_approximate_value:

        if wanted_number == array_list[index_middle]:
            determine_the_most_approximate_value = True
                                                        
        elif wanted_number > array_list[index_middle]: # Se o número à esquerda for maior que o número da busca binária:
            if index_middle < array_dict_length: # Se o número verificado à direita não tiver o mesmo índice referente ao maior índice do vetor aberto (overflow):
                
                lower_limit = index_middle_result
                index_middle_result = average(lower_limit, upper_limit)
                index_middle = int(index_middle_result)                
                
            else: # Do contrário, se os índices forem iguais, então devemos fazer a inserção à direita do número encontrado
                determine_the_most_approximate_value = True                
        else:
            if not first_iteration:
                upper_limit = index_middle_result
            else:
                first_iteration = False
                
            index_middle_result = average(lower_limit, upper_limit)
            index_middle = int(index_middle_result)
        
        if factor_is_zero:
            determine_the_most_approximate_value = True
        
        if not determine_the_most_approximate_value and not factor_is_zero:
            factor_binary_search = factor_binary_search / 2
            if int(factor_binary_search) == 0:
                factor_is_zero = True
    
    if index_middle > 0: # Se a distância entre o valor do índice encontrado for maior que o valor do índice anterior, então desejamos aquele valor com a menor distância ou com a menor diferença com o valor desejado.
        if abs(wanted_number -array_list[index_middle]) > abs(wanted_number - array_list[index_middle-1]):
            index_middle -= 1
            
    groups = dict()
    for key, value in array_dict.items():
        groups[value] = key # Valor é o resultado das operações, e key seria o índice desses resultados.
    
    #print(f"groups: {groups}")
    
    return array_list[index_middle], groups[array_list[index_middle]]

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

values = list(data.values())
results = dict()
expected_result = 120.59
number_of_rows_in_the_truth_table = 2**len(data)

for i in range(number_of_rows_in_the_truth_table):
    result = logical_and_mathematical_operation(i,values) # Calcula os resultados de multiplicação e de divisão com influência de uma tabela verdade
    results[i] = result # Os resultados são armazenados em um dicionário ordenado pelas chaves com influência do número binário definido pela variável de iteração i.
    
ENABLE_OPERATION_LIMIT = True
final_result = 0
margin_of_error_difference = expected_result
operation_limit = number_of_rows_in_the_truth_table # Para não acontecer loops infinitos, se coloca uma restrição de iteração:
results = sorted(results.items(), key=lambda x: x[1]) # O dicionário passa a ser ordenado pelos valores e não mais pelas chaves.
results = dict(results)
used_variables = set()
total_variables_str = ""
#tolerance = 0.000000001
tolerance = 0.00001
count = 0

approximate_value, index_expected = binary_search_to_find_miniterm_from_dict(margin_of_error_difference, results) # Achamos o minitermo, que seria a seleção de variáveis que devem ser operandos de uma operação de multiplicação.
final_result += approximate_value

while abs(expected_result -final_result) > tolerance and (count < operation_limit or not ENABLE_OPERATION_LIMIT): #and final_result + approximate_value < expected_result
    variables_list = choice_enabler(index_expected, list(data.keys()))
    used_variables.update(variables_list)
    variables_str = " * ".join(variables_list)
    total_variables_str += variables_str
    
    if final_result < expected_result:
        margin_of_error_difference = expected_result -final_result
        total_variables_str+= " + "
    else:
        margin_of_error_difference = final_result - expected_result
        total_variables_str+= " - "
        
    approximate_value, index_expected = binary_search_to_find_miniterm_from_dict(margin_of_error_difference, results) # Achamos o minitermo, que seria a seleção de variáveis que devem ser operandos de uma operação de multiplicação.
    
    if count +1 < operation_limit or not ENABLE_OPERATION_LIMIT:
        if final_result < expected_result:
            final_result += approximate_value
        else:
            final_result -= approximate_value
            
    count += 1
    #print(f"DEBUG: count: {count} expected_result: {expected_result}, final_result: {final_result}, tolerance: {tolerance}, abs(expected_result -final_result): {abs(expected_result -final_result)} abs(expected_result -final_result) > tolerance: {abs(expected_result -final_result) > tolerance}")

total_variables_str = total_variables_str[:-len(" + ")]
used_variables_str = ", ".join(used_variables)
used_variables_quantity = len(used_variables)
total_variables_quantity = len(values)

print(f"The following variables were used: {used_variables_str}. In total, {used_variables_quantity} variables out a total of {total_variables_quantity} were used ({round((used_variables_quantity/total_variables_quantity)*100, 2)}%).")
print(f"To the approximate value: {final_result}, the variables used for the multiplication operation that most closely approximate the desired value are: {total_variables_str}")

for key, value in data.items():
    total_variables_str = total_variables_str.replace(key, str(value))

expression_result = eval(total_variables_str)

print(f"actual proof of the mathematical terms found: {expression_result}")