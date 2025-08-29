'''
[] colocar o número 1 como valor unitário sempre quando a substituição de partes literais implicar em desaparecimento de termos. Além disso, somar esses valores unitários para definir constantes dentro de parênteses
[] Sempre verificar o que está fora dos parênteses para não substituir partes literais de termos fora de parênteses;
[] Inserir e tratar os coeficientes na fórmula de forma que a equação seja sempre válida.
[] entender o motivo de não haver operação de subtração na fórmula;
[] compreender inconsistências de resultados da prova real;
[] verificar a possibilidade de reduzir ainda mais a fórmula com a utilização de operações de exponenciação, radiciação e logaritmo;

'''

from functools import reduce
from re import escape, findall
from math import isfinite
from binary_search import BinarySearch



if __name__ == '__main__':
    array_tuples_choice_pair = lambda number, choices: [(i,j) for i,j in zip([int(i) for i in str(bin(number))[2:][::-1]], choices[::-1])]
    truth_table_combination_multiplication = lambda number, choices: reduce(lambda a, b: a * b, list(map(lambda x: x[1], list(filter(lambda a: a[0] * a[1], array_tuples_choice_pair(number,choices))))),1)
    truth_table_combination_list = lambda number, choices: list(map(lambda a: a[1], list(filter(lambda a: a[0], array_tuples_choice_pair(number, choices)))))
    binary_search = BinarySearch()
    
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
    truth_table_product_list = dict()
    expected_result = 120.59
    number_of_rows_in_the_truth_table = 2**len(data)
    
    for i in range(number_of_rows_in_the_truth_table):
        result = truth_table_combination_multiplication(i,values) # Calcula os resultados de multiplicação e de divisão com influência de uma tabela verdade
        truth_table_product_list[i] = result # Os resultados são armazenados em um dicionário ordenado pelas chaves com influência do número binário definido pela variável de iteração i.
        
    ENABLE_OPERATION_LIMIT = True
    SUM_SIGNAL = " + "
    MINUS_SIGNAL = " - "
    MUL_SIGNAL = " * "
    final_result = 0
    margin_of_error_difference = expected_result
    operation_limit = number_of_rows_in_the_truth_table # Para não acontecer loops infinitos, se coloca uma restrição de iteração:
    truth_table_product_list = sorted(truth_table_product_list.items(), key=lambda x: x[1]) # O dicionário passa a ser ordenado pelos valores e não mais pelas chaves.
    truth_table_product_list = dict(truth_table_product_list)
    list_of_terms_of_algebraic_expressions  = list()
    set_of_terms_of_algebraic_expressions = set()
    used_literal_parts = set()
    tolerance = 0.000000001
    count = 0
    print(truth_table_product_list)
    approximate_value, index_expected = binary_search.binary_search_to_find_miniterm_from_dict(margin_of_error_difference, truth_table_product_list) # Achamos o minitermo, que seria a seleção de variáveis que devem ser operandos de uma operação de multiplicação.
    final_result += approximate_value
    list_of_algebraic_literal_parts = truth_table_combination_list(index_expected, list(data.keys()))
    used_literal_parts.update(list_of_algebraic_literal_parts)
    previous_signal = ""
    previous_approximate_value = 0    
    
    while abs(expected_result -final_result) > tolerance and (count < operation_limit or not ENABLE_OPERATION_LIMIT): #and final_result + approximate_value < expected_result
        
        margin_of_error_difference = abs(expected_result -final_result)
        
        # With this code scope, we want to create the polynomial algebraic expression without redundancies.
        insert_new_one = True
        #if tuple(list_of_algebraic_literal_parts) in set_of_terms_of_algebraic_expressions and len(list_of_terms_of_algebraic_expressions) > 0:
        # for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions:
        #     if list_of_algebraic_literal_parts == data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]:
        #         if data_dict_of_algebraic_terms["signal"] == SUM_SIGNAL:
        #             if not final_result < expected_result:
        #                 insert_new_one = False
        #                 break
        #         elif data_dict_of_algebraic_terms["signal"] == MINUS_SIGNAL:
        #             if final_result < expected_result:
        #                 insert_new_one = False
        #                 break
        
        # In this code scope, the coeficient of each term is calculated.
        # if insert_new_one:
        #     for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions[::-1]:
        #         if list_of_algebraic_literal_parts == data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]:
        #                 data_dict_of_algebraic_terms["terms_quantity"] += 1
        #                 break
                
        if insert_new_one:
            list_of_terms_of_algebraic_expressions.append({"terms_quantity" : 1, "signal":  SUM_SIGNAL if final_result < expected_result else MINUS_SIGNAL, "list_of_algebraic_literal_parts": list_of_algebraic_literal_parts})
            
        set_of_terms_of_algebraic_expressions.add(tuple(list_of_algebraic_literal_parts)) # with this, we avoid repetition of the same variables in the same equation.
        
        previous_approximate_value = approximate_value
        approximate_value, index_expected = binary_search.binary_search_to_find_miniterm_from_dict(margin_of_error_difference, truth_table_product_list) # Achamos o minitermo, que seria a seleção de variáveis que devem ser operandos de uma operação de multiplicação.
        
        if count +1 < operation_limit or not ENABLE_OPERATION_LIMIT:
            if final_result < expected_result:
                #if final_result + approximate_value < expected_result:
                final_result += approximate_value
                previous_signal = SUM_SIGNAL
            else:
                final_result -= approximate_value
                if previous_approximate_value == approximate_value and previous_signal == SUM_SIGNAL:
                    break
                previous_signal = MINUS_SIGNAL
                
            list_of_algebraic_literal_parts = truth_table_combination_list(index_expected, list(data.keys()))
            used_literal_parts.update(list_of_algebraic_literal_parts)
        count += 1
    
    count_variables = dict()
    terms_quantity = 0
    
    # In this code scope, we calculate the coeficient of each term.
    for term_of_algebraic_expression in set_of_terms_of_algebraic_expressions:
        for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions:
            if term_of_algebraic_expression == tuple(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]):
                terms_quantity += 1 # Counting how many times each term appears in the equation to calculate coefficients.
        for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions:
            if term_of_algebraic_expression == tuple(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]):
                data_dict_of_algebraic_terms["terms_quantity"] = terms_quantity
    
    # Now, identifying the variables that are most used in the algebraic expression.
    for used_literal_part in used_literal_parts:  # In this algorithm scope, we want to discover which variable is more frequently used in the equation.
        count_variables[used_literal_part] = 0 # The counter is initialized to zero.
        for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions: # We iterate over the list of tuples that contains the variables used in the equation.
            for literal_part in data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]: # We iterate over the variables used in the equatio and we want to count how many times each literal_part appears in neighboring equations to determine nesting by isolating these variables.
                if literal_part == used_literal_part:
                    count_variables[used_literal_part] +=1 # it may be unnecessary if this logic is placed during the construction of the variable list up there.
                    break
    
    count_variables = sorted(count_variables.items(), key=lambda x: x[1], reverse=True)
    count_variables = dict(count_variables)
    
    terms_hierarchy_structure = list()
    literal_parts_to_be_removed = set()
    dont_insert_anything = False
    
    # identifying the structure of the algebraic expression.
    for variable_name, count in count_variables.items():
        terms_inserted_into_parentesis = list()
        terms_out_from_parentesis = list()
        if count > 1:
            for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions: # Determining which terms are inside the parenthesis and also out of the parenthesis.
                found_variable = False
                for literal_part in data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]:
                    if literal_part == variable_name:
                        if data_dict_of_algebraic_terms["terms_quantity"] == 1:
                            literal_parts_to_be_removed.add(literal_part)
                            found_variable = True
                            break
                        else:
                            dont_insert_anything = True
                            
                    
                data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"] = [i for i in data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"] if i not in literal_parts_to_be_removed]
                if not dont_insert_anything:
                    if found_variable:
                        terms_inserted_into_parentesis.append(dict(data_dict_of_algebraic_terms))
                    else:
                        terms_out_from_parentesis.append(dict(data_dict_of_algebraic_terms))
                else:
                    dont_insert_anything = False
    
        if terms_inserted_into_parentesis or terms_out_from_parentesis:
            terms_hierarchy_structure.append({"variable_name" : variable_name, "terms_inserted_into_parentesis": terms_inserted_into_parentesis, "terms_out_from_parentesis": terms_out_from_parentesis})
    
    # Were we able to shorten the equation
    #count_variables = sorted(count_variables.items(), key=lambda x: x[1])
    #count_variables = dict(count_variables)
    del count_variables
    first_iteration = True
    term_string = str()
    
    if terms_hierarchy_structure:
        terms_hierarchy_structure = terms_hierarchy_structure[::-1]
        for term_hierarchy_structure in terms_hierarchy_structure:
            if not first_iteration:
                term_list_out = list(filter(lambda x: x, [MUL_SIGNAL.join(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]) for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_out_from_parentesis"]]))
                polynomial = "".join([ signal+term for signal, term in zip([data_dict_of_algebraic_terms["signal"] for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_out_from_parentesis"]], term_list_out)])
                if sub_term_string[len(sub_term_string)-1:] != ')':
                    term_string = f"{term_hierarchy_structure['variable_name']}{MUL_SIGNAL}({sub_term_string})"
                else:
                    term_string = f"{term_hierarchy_structure['variable_name']}{MUL_SIGNAL}{sub_term_string}"
                term_string += polynomial
                sub_term_string = term_string
            else:
                term_list_in = list(filter(lambda x: x, [MUL_SIGNAL.join(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]) for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_inserted_into_parentesis"]]))
                term_list_out = list(filter(lambda x: x, [MUL_SIGNAL.join(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"]) for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_out_from_parentesis"]]))
                if any(term_list_in):
                    sub_term_string = f"{term_hierarchy_structure['variable_name']}{MUL_SIGNAL}("
                    polynomial = "".join([signal+term for signal, term in zip([data_dict_of_algebraic_terms["signal"] for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_inserted_into_parentesis"]], term_list_in)])
                    if polynomial[:len(SUM_SIGNAL)] != MINUS_SIGNAL:
                        polynomial = polynomial[len(SUM_SIGNAL):]
                    sub_term_string += polynomial + ")"
                    if any(term_list_out):
                        polynomial = "".join([signal+term for signal, term in zip([data_dict_of_algebraic_terms["signal"] for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_out_from_parentesis"]], term_list_out)])
                        sub_term_string += polynomial                    
                else:
                    print("ERROR 221 : term_list_in is empty and unknown error occurred!!!")
                    if any(term_list_out):
                        print("ERROR 223 : this command must not be executed, because not make sense!!!")
                        sub_term_string = term_hierarchy_structure['variable_name']
                        polynomial = "".join([signal+term for signal, term in zip([data_dict_of_algebraic_terms["signal"] for data_dict_of_algebraic_terms in term_hierarchy_structure["terms_out_from_parentesis"]], term_list_out)])
                        sub_term_string += polynomial
                    else:
                        sub_term_string = term_hierarchy_structure['variable_name']
                    
                first_iteration = False
    else:
        for data_dict_of_algebraic_terms in list_of_terms_of_algebraic_expressions:
            sub_term_string = MUL_SIGNAL.join(data_dict_of_algebraic_terms["list_of_algebraic_literal_parts"])
            if first_iteration:
                if data_dict_of_algebraic_terms["signal"] == MINUS_SIGNAL:
                    term_string += data_dict_of_algebraic_terms["signal"] + sub_term_string
                else:
                    term_string += sub_term_string
                first_iteration = False
                
    resulting_algebraic_expression = term_string
    used_variables_str = ", ".join(used_literal_parts)
    used_variables_quantity = len(used_literal_parts)
    total_variables_quantity = len(values)
    
    print(f"The following variables were used: {used_variables_str}. In total, {used_variables_quantity} variables out a total of {total_variables_quantity} were used ({round((used_variables_quantity/total_variables_quantity)*100, 2)}%).")
    if resulting_algebraic_expression:
        print(f"To the approximate value: {final_result}, the variables used for the multiplication operation that most closely approximate the desired value are: {resulting_algebraic_expression}")
    else:
        print("Unfortunately, there are no terms in the equation.")
    
    for key, value in data.items():
        resulting_algebraic_expression = resulting_algebraic_expression.replace(key, str(value))
    
    expression_result = eval(resulting_algebraic_expression)
    
    print(f"actual proof of the mathematical terms found: {expression_result}")