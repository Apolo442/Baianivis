import ply.yacc as yacc
from lex_baianivis import tokens, lexer, find_column
import json
import html

# --- Gerenciador de escopo ---
class TabelaSimbolos:
    def __init__(self):
        self.scopes = [{}]
        self.errors = []
        self.current_function_type = None

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def add_symbol(self, name, symbol_type, data_type=None, params=None, lineno=None, lexpos=None):
        current_scope = self.scopes[-1]
        if name in current_scope:
            col = find_column(lexer.lexdata, lexpos) if lexpos and hasattr(lexer, 'lexdata') else 'N/A'
            self.log_error(f"Erro semântico: Símbolo '{name}' já declarado neste escopo.", lineno, col)
            return False
        current_scope[name] = {
            "tipo": symbol_type,
            "tipo_dado": data_type,
            "parametros": params,
            "escopo": len(self.scopes) - 1
        }
        return True

    def lookup(self, name, lineno=None, lexpos=None):
        for i in range(len(self.scopes) - 1, -1, -1):
            if name in self.scopes[i]:
                return self.scopes[i][name]
        col = find_column(lexer.lexdata, lexpos) if lexpos and hasattr(lexer, 'lexdata') else 'N/A'
        self.log_error(f"Erro semântico: Símbolo '{name}' não declarado.", lineno, col)
        return None

    def log_error(self, message, lineno=None, column=None):
        location = f" (Linha: {lineno}, Coluna: {column})" if lineno is not None else ""
        error_msg = f"{message}{location}"
        if error_msg not in self.errors:
             self.errors.append(error_msg)

    def get_errors(self):
        return self.errors

    def set_current_function_type(self, type_name):
        self.current_function_type = type_name

    def get_current_function_type(self):
        return self.current_function_type

tabela_simbolos = TabelaSimbolos()

# Precedência dos operadores
precedence = (
    ("left", "OU_LOGICO"),
    ("left", "E_LOGICO"),
    ("right", "NEGACAO"),
    ("left", "IGUALDADE", "DIFERENTE", "MAIOR", "MENOR", "MAIOR_IGUAL", "MENOR_IGUAL"),
    ("left", "MAIS", "MENOS"),
    ("left", "MULT", "DIV", "RESTO"),
    ("right", "UMINUS"), # pra negacao se precisar
)

# --- Regra Inicial --- 
def p_programa(p):
    "programa : declaracoes_globais comandos FIM"
    p[0] = {
        "tipo_nodo": "programa",
        "declaracoes": p[1],
        "comandos": p[2]
    }
    errors = tabela_simbolos.get_errors()
    if errors:
        print("\n--- Erros Semânticos Detectados ---")
        for error in errors:
            print(error)
        print("-----------------------------------")
    else:
        print("\nAnálise semântica concluída sem erros.")
        salvar_ast(p[0])

# --- Declarações Globais --- 
def p_declaracoes_globais(p):
    """declaracoes_globais : declaracoes_globais declaracao_global
                           | empty"""
    if len(p) == 3:
        p[0] = p[1] + ([p[2]] if p[2] else [])
    else:
        p[0] = []

def p_declaracao_global(p):
    """declaracao_global : declaracao_variavel
                         | declaracao_funcao
                         | declaracao_procedimento"""
    p[0] = p[1]

def p_declaracao_variavel(p):
    "declaracao_variavel : tipo ID PONTO_VIRGULA"
    var_name = p[2]
    var_type = p[1]
    lineno = p.lineno(2)
    lexpos = p.lexpos(2)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if var_type == 'vazivis':
        tabela_simbolos.log_error(f"Erro semântico: Variável '{var_name}' não pode ser do tipo 'vazivis'.", lineno, col)
        p[0] = None
    else:
        added = tabela_simbolos.add_symbol(var_name, 'variavel', data_type=var_type, lineno=lineno, lexpos=lexpos)
        if added:
            p[0] = {"tipo_nodo": "declaracao_variavel", "nome": var_name, "tipo_dado": var_type}
        else:
            p[0] = None

def p_tipo(p):
    """tipo : INTEIRO
            | REAL
            | TIPO_TEXTO"""
    p[0] = p[1]

# --- Comandos --- 
def p_comandos(p):
    """comandos : comandos comando
                | empty"""
    if len(p) == 3:
        p[0] = p[1] + ([p[2]] if p[2] else [])
    else:
        p[0] = []

def p_comando(p):
    """comando : atribuicao
               | condicional
               | comando_repeticao
               | chamada_procedimento_stmt
               | comando_retorno
               | bloco_comandos
               """
    p[0] = p[1]

def p_bloco_comandos(p):
    "bloco_comandos : ABRE_CHAVE comandos FECHA_CHAVE"
    p[0] = {"tipo_nodo": "bloco", "comandos": p[2]}

def p_comando_repeticao(p):
    "comando_repeticao : ENQUANTO ABRE_PAREN expressao FECHA_PAREN bloco_comandos"
    cond_node = p[3]
    cond_type = cond_node.get('tipo_dado', 'desconhecido')
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if cond_type != 'inteirivis':
        tabela_simbolos.log_error(f"Erro de tipo: Condição do 'enquantivis' deve ser inteira (booleana), mas é '{cond_type}'.", lineno, col)

    p[0] = {
        "tipo_nodo": "repeticao",
        "condicao": cond_node,
        "bloco": p[5]
    }

def p_atribuicao(p):
    "atribuicao : ID IGUAL expressao PONTO_VIRGULA"
    var_name = p[1]
    expr_node = p[3]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    symbol_info = tabela_simbolos.lookup(var_name, lineno=lineno, lexpos=lexpos)

    if symbol_info:
        if symbol_info['tipo'] != 'variavel':
            tabela_simbolos.log_error(f"Erro semântico: Símbolo '{var_name}' não é uma variável.", lineno, col)
            p[0] = None
        else:
            var_type = symbol_info['tipo_dado']
            expr_type = expr_node.get('tipo_dado', 'desconhecido')

            if expr_type == 'desconhecido':
                 p[0] = None
            elif var_type != expr_type:
                if not (var_type == 'realzivis' and expr_type == 'inteirivis'):
                    tabela_simbolos.log_error(f"Erro de tipo: Não é possível atribuir tipo '{expr_type}' à variável '{var_name}' do tipo '{var_type}'.", lineno, col)
                    p[0] = None
                else:
                     p[0] = {"tipo_nodo": "atribuicao", "id": var_name, "expressao": expr_node}
            else:
                 p[0] = {"tipo_nodo": "atribuicao", "id": var_name, "expressao": expr_node}
    else:
        p[0] = None

def p_condicional(p):
    """condicional : SE ABRE_PAREN expressao FECHA_PAREN bloco_comandos
                   | SE ABRE_PAREN expressao FECHA_PAREN bloco_comandos SENAO bloco_comandos"""
    cond_node = p[3]
    cond_type = cond_node.get('tipo_dado', 'desconhecido')
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if cond_type != 'inteirivis':
        tabela_simbolos.log_error(f"Erro de tipo: Condição do 'sevis' deve ser inteira (booleana), mas é '{cond_type}'.", lineno, col)

    if len(p) == 6:
        p[0] = {"tipo_nodo": "condicional", "condicao": cond_node, "bloco_verdadeiro": p[5]}
    else:
        p[0] = {"tipo_nodo": "condicional", "condicao": cond_node, "bloco_verdadeiro": p[5], "bloco_falso": p[7]}

# --- Expressões --- 
def p_expressao_binaria(p):
    """expressao : expressao MAIS expressao
                 | expressao MENOS expressao
                 | expressao MULT expressao
                 | expressao DIV expressao
                 | expressao RESTO expressao
                 | expressao MAIOR expressao
                 | expressao MENOR expressao
                 | expressao MAIOR_IGUAL expressao
                 | expressao MENOR_IGUAL expressao
                 | expressao IGUALDADE expressao
                 | expressao DIFERENTE expressao"""
    op = p[2]
    left_node = p[1]
    right_node = p[3]
    left_type = left_node.get('tipo_dado', 'desconhecido')
    right_type = right_node.get('tipo_dado', 'desconhecido')
    result_type = 'desconhecido'
    lineno = p.lineno(2)
    lexpos = p.lexpos(2)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if left_type == 'desconhecido' or right_type == 'desconhecido':
        result_type = 'desconhecido'

    elif op in ['+', '-', '*', '/', '%']:
        if left_type == 'textivis' or right_type == 'textivis':
            if op == '+' and left_type == 'textivis' and right_type == 'textivis':
                result_type = 'textivis'
            else:
                tabela_simbolos.log_error(f"Erro de tipo: Operador '{op}' inválido para os tipos '{left_type}' e '{right_type}'.", lineno, col)
        elif left_type == 'realzivis' or right_type == 'realzivis':
            if left_type in ['inteirivis', 'realzivis'] and right_type in ['inteirivis', 'realzivis']:
                 result_type = 'realzivis'
            else:
                 tabela_simbolos.log_error(f"Erro de tipo: Operador aritmético '{op}' inválido para os tipos '{left_type}' e '{right_type}'.", lineno, col)
        elif left_type == 'inteirivis' and right_type == 'inteirivis':
            result_type = 'inteirivis'
        else:
             tabela_simbolos.log_error(f"Erro de tipo: Operador aritmético '{op}' inválido para os tipos '{left_type}' e '{right_type}'.", lineno, col)

    elif op in ['>', '<', '>=', '<=', '?=', '!=']:
        is_numeric_comparison = (left_type in ['inteirivis', 'realzivis'] and right_type in ['inteirivis', 'realzivis'])
        is_text_equality_comparison = (left_type == 'textivis' and right_type == 'textivis' and op in ['?=', '!='])

        if is_numeric_comparison or is_text_equality_comparison:
            result_type = 'inteirivis'
        else:
            tabela_simbolos.log_error(f"Erro de tipo: Comparação '{op}' inválida entre os tipos '{left_type}' e '{right_type}'.", lineno, col)

    p[0] = {
        "tipo_nodo": "binaria",
        "operador": op,
        "esquerda": left_node,
        "direita": right_node,
        "tipo_dado": result_type
    }

def p_expressao_logica(p):
    """expressao : expressao E_LOGICO expressao
                 | expressao OU_LOGICO expressao"""
    left_node = p[1]
    right_node = p[3]
    left_type = left_node.get('tipo_dado', 'desconhecido')
    right_type = right_node.get('tipo_dado', 'desconhecido')
    lineno = p.lineno(2)
    lexpos = p.lexpos(2)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if left_type != 'inteirivis' or right_type != 'inteirivis':
        tabela_simbolos.log_error(f"Erro de tipo: Operadores lógicos ('{p[2]}') requerem operandos inteiros (booleanos), recebidos '{left_type}' e '{right_type}'.", lineno, col)

    p[0] = {
        "tipo_nodo": "logica",
        "operador": p[2],
        "esquerda": left_node,
        "direita": right_node,
        "tipo_dado": "inteirivis"
    }

def p_expressao_negacao(p):
    "expressao : NEGACAO expressao %prec UMINUS"
    operand_node = p[2]
    operand_type = operand_node.get('tipo_dado', 'desconhecido')
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if operand_type != 'inteirivis':
         tabela_simbolos.log_error(f"Erro de tipo: Operador de negação (!) requer operando inteiro (booleano), recebido '{operand_type}'.", lineno, col)
    p[0] = {"tipo_nodo": "negacao", "operando": operand_node, "tipo_dado": "inteirivis"}

def p_expressao_fator(p):
    "expressao : fator"
    p[0] = p[1]

# --- Fatores --- 
def p_fator_numero(p):
    "fator : NUMERO"
    tipo = 'inteirivis' if isinstance(p[1], int) else 'realzivis'
    p[0] = {
        "tipo_nodo": "numero",
        "valor": p[1],
        "tipo_dado": tipo
    }

def p_fator_texto(p):
    "fator : LITERAL_TEXTO"
    p[0] = {
        "tipo_nodo": "texto",
        "valor": p[1],
        "tipo_dado": "textivis"
    }

def p_fator_id(p):
    "fator : ID"
    var_name = p[1]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    symbol_info = tabela_simbolos.lookup(var_name, lineno=lineno, lexpos=lexpos)
    if symbol_info:
        if symbol_info['tipo'] != 'variavel':
            tabela_simbolos.log_error(f"Erro semântico: Símbolo '{var_name}' não é uma variável (é '{symbol_info['tipo']}').", lineno, col)
            p[0] = {"tipo_nodo": "variavel", "nome": var_name, "tipo_dado": "desconhecido"}
        else:
            p[0] = {"tipo_nodo": "variavel", "nome": var_name, "tipo_dado": symbol_info['tipo_dado']}
    else:
        p[0] = {"tipo_nodo": "variavel", "nome": var_name, "tipo_dado": "desconhecido"}

def p_fator_chamada_funcao(p):
    "fator : ID ABRE_PAREN lista_argumentos FECHA_PAREN"
    func_name = p[1]
    args_list = p[3]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    symbol_info = tabela_simbolos.lookup(func_name, lineno=lineno, lexpos=lexpos)
    return_type = 'desconhecido'

    if symbol_info:
        if symbol_info['tipo'] != 'funcao':
            tabela_simbolos.log_error(f"Erro semântico: Símbolo '{func_name}' não é uma função.", lineno, col)
        else:
            return_type = symbol_info['tipo_dado']
            expected_params = symbol_info.get('parametros', [])
            if len(args_list) != len(expected_params):
                tabela_simbolos.log_error(f"Erro semântico: Função '{func_name}' espera {len(expected_params)} argumentos, mas recebeu {len(args_list)}.", lineno, col)
            else:
                for i, arg_node in enumerate(args_list):
                    arg_type = arg_node.get('tipo_dado', 'desconhecido')
                    if arg_type == 'desconhecido': continue
                    param_type = expected_params[i]['tipo_dado']
                    if arg_type != param_type:
                        if not (param_type == 'realzivis' and arg_type == 'inteirivis'):
                            tabela_simbolos.log_error(f"Erro de tipo no argumento {i+1} da função '{func_name}': esperado '{param_type}', recebido '{arg_type}'.", lineno, col)

    p[0] = {
        "tipo_nodo": "chamada_funcao",
        "nome": func_name,
        "argumentos": args_list,
        "tipo_dado": return_type
    }

def p_chamada_procedimento_stmt(p):
    "chamada_procedimento_stmt : ID ABRE_PAREN lista_argumentos FECHA_PAREN PONTO_VIRGULA"
    proc_name = p[1]
    args_list = p[3]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    symbol_info = tabela_simbolos.lookup(proc_name, lineno=lineno, lexpos=lexpos)

    if symbol_info:
        if symbol_info['tipo'] != 'procedimento':
            tabela_simbolos.log_error(f"Erro semântico: Símbolo '{proc_name}' não é um procedimento.", lineno, col)
        else:
            expected_params = symbol_info.get('parametros', [])
            if len(args_list) != len(expected_params):
                tabela_simbolos.log_error(f"Erro semântico: Procedimento '{proc_name}' espera {len(expected_params)} argumentos, mas recebeu {len(args_list)}.", lineno, col)
            else:
                for i, arg_node in enumerate(args_list):
                    arg_type = arg_node.get('tipo_dado', 'desconhecido')
                    if arg_type == 'desconhecido': continue
                    param_type = expected_params[i]['tipo_dado']
                    if arg_type != param_type:
                         if not (param_type == 'realzivis' and arg_type == 'inteirivis'):
                            tabela_simbolos.log_error(f"Erro de tipo no argumento {i+1} do procedimento '{proc_name}': esperado '{param_type}', recebido '{arg_type}'.", lineno, col)

    p[0] = {
        "tipo_nodo": "chamada_procedimento",
        "nome": proc_name,
        "argumentos": args_list
    }

def p_lista_argumentos(p):
    """lista_argumentos : argumentos
                       | empty"""
    p[0] = p[1] if p[1] else []

def p_argumentos(p):
    """argumentos : expressao
                  | argumentos VIRGULA expressao"""
    if len(p) == 2:
        p[0] = [p[1]] if p[1] else []
    else:
        prev_args = p[1] if p[1] else []
        current_arg = [p[3]] if p[3] else []
        p[0] = prev_args + current_arg

def p_fator_parenteses(p):
    "fator : ABRE_PAREN expressao FECHA_PAREN"
    p[0] = p[2]

# --- Funções e Procedimentos --- 

def p_declaracao_funcao(p):
    """declaracao_funcao : func_sig marker_enter_scope ABRE_CHAVE comandos_funcao FECHA_CHAVE marker_exit_scope"""
    func_sig_info = p[1]
    func_body = p[4]

    if not func_sig_info:
        p[0] = None
        return

    p[0] = {
        "tipo_nodo": "declaracao_funcao",
        "nome": func_sig_info['nome'],
        "parametros": func_sig_info['params'],
        "retorno": func_sig_info['return'],
        "bloco": func_body
    }

def p_func_sig(p):
    """func_sig : FUNCAO ID ABRE_PAREN lista_parametros FECHA_PAREN RETORNO tipo"""
    func_name = p[2]
    params_list = p[4]
    return_type = p[7]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)

    added_global = tabela_simbolos.add_symbol(func_name, 'funcao', data_type=return_type, params=params_list, lineno=lineno, lexpos=lexpos)

    if added_global:
        p[0] = {'nome': func_name, 'params': params_list, 'return': return_type, 'lineno': lineno, 'valid': True}
    else:
        p[0] = {'valid': False}

def p_marker_enter_scope(p):
    """marker_enter_scope : empty"""
    sig_info = p[-1]

    if sig_info and sig_info.get('valid'):
        tabela_simbolos.enter_scope()
        tabela_simbolos.set_current_function_type(sig_info.get('return', sig_info.get('data_type'))) 

        params_list = sig_info.get('params', [])
        param_names_local = set()
        func_proc_name = sig_info.get('nome', '<?>')
        lineno = sig_info.get('lineno', None)

        for param in params_list:
            param_name = param['nome']
            if param_name in param_names_local:
                 tabela_simbolos.log_error(f"Erro semântico: Parâmetro '{param_name}' duplicado na definição de '{func_proc_name}'.", lineno)
            else:
                 param_names_local.add(param_name)
                 tabela_simbolos.add_symbol(param_name, 'variavel', data_type=param['tipo_dado'], lineno=lineno)

def p_marker_exit_scope(p):
    """marker_exit_scope : empty"""
    if len(tabela_simbolos.scopes) > 1:
         tabela_simbolos.exit_scope()
    tabela_simbolos.set_current_function_type(None)

def p_declaracao_procedimento(p):
     """declaracao_procedimento : proc_sig marker_enter_scope ABRE_CHAVE comandos_funcao FECHA_CHAVE marker_exit_scope"""
     proc_sig_info = p[1]
     proc_body = p[4]

     if not proc_sig_info:
         p[0] = None
         return

     p[0] = {
        "tipo_nodo": "declaracao_procedimento",
        "nome": proc_sig_info['nome'],
        "parametros": proc_sig_info['params'],
        "bloco": proc_body
     }

def p_proc_sig(p):
    """proc_sig : PROCEDIMENTO ID ABRE_PAREN lista_parametros FECHA_PAREN"""
    proc_name = p[2]
    params_list = p[4]
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)

    added_global = tabela_simbolos.add_symbol(proc_name, 'procedimento', data_type='vazivis', params=params_list, lineno=lineno, lexpos=lexpos)

    if added_global:
        p[0] = {'nome': proc_name, 'params': params_list, 'data_type': 'vazivis', 'lineno': lineno, 'valid': True}
    else:
        p[0] = {'valid': False}

def p_comandos_funcao(p):
    """comandos_funcao : comandos_funcao comando_local
                       | empty"""
    # isso aqui é tipo p_comandos, permitindo declaracoes locais
    if len(p) == 3:
        p[0] = p[1] + ([p[2]] if p[2] else [])
    else:
        p[0] = []

def p_comando_local(p):
    """comando_local : declaracao_variavel
                     | comando"""
    p[0] = p[1]

def p_lista_parametros(p):
    """lista_parametros : parametros
                        | empty"""
    p[0] = p[1] if p[1] else []

def p_parametros(p):
    """parametros : parametro
                  | parametros VIRGULA parametro"""
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        param_names = [param['nome'] for param in p[1]]
        if p[3]['nome'] in param_names:
             lineno = p.lineno(3)
             col = find_column(lexer.lexdata, p.lexpos(3)) if hasattr(lexer, 'lexdata') else 'N/A'
        p[0] = p[1] + [p[3]]

def p_parametro(p):
    "parametro : tipo ID"
    p[0] = {"nome": p[2], "tipo_dado": p[1]}

def p_comando_retorno(p):
    """comando_retorno : RETORNO expressao PONTO_VIRGULA
                       | RETORNO PONTO_VIRGULA"""
    expected_type = tabela_simbolos.get_current_function_type()
    lineno = p.lineno(1)
    lexpos = p.lexpos(1)
    col = find_column(lexer.lexdata, lexpos) if hasattr(lexer, 'lexdata') else 'N/A'

    if expected_type is None:
        tabela_simbolos.log_error("Erro semântico: Comando 'retornivis' fora de uma função ou procedimento.", lineno, col)
        p[0] = None
        return

    if len(p) == 4: # RETORNO expressao PONTO_VIRGULA
        returned_expr = p[2]
        if returned_expr is None:
             p[0] = None
             return

        returned_type = returned_expr.get('tipo_dado', 'desconhecido')

        if expected_type == 'vazivis':
            tabela_simbolos.log_error("Erro semântico: Procedimento não deve retornar valor com expressão.", lineno, col)
            p[0] = None
        elif returned_type == 'desconhecido':
             p[0] = None
        elif returned_type != expected_type:
             if not (expected_type == 'realzivis' and returned_type == 'inteirivis'):
                tabela_simbolos.log_error(f"Erro de tipo: Função esperava retorno '{expected_type}', mas expressão retorna '{returned_type}'.", lineno, col)
                p[0] = None
             else:
                 p[0] = {"tipo_nodo": "retorno", "expressao": returned_expr}
        else:
            p[0] = {"tipo_nodo": "retorno", "expressao": returned_expr}

    else: # RETORNO PONTO_VIRGULA
        if expected_type != 'vazivis':
            tabela_simbolos.log_error(f"Erro semântico: Função do tipo '{expected_type}' deve retornar um valor (retorno vazio encontrado).", lineno, col)
            p[0] = None
        else:
            p[0] = {"tipo_nodo": "retorno_vazio"}

# --- Utilitários e Erros --- 
def p_empty(p):
    "empty :"
    pass

def p_error(p):
    # cuida dos erros de sintaxe capturados pelo PLY
    if p:
        col = find_column(lexer.lexdata, p.lexpos) if hasattr(lexer, 'lexdata') and p.lexpos is not None else 'N/A'
        tabela_simbolos.log_error(f"Erro de sintaxe: Token inesperado '{p.value}' (tipo: {p.type})", p.lineno, col)
    else:
        tabela_simbolos.log_error("Erro de sintaxe: Fim inesperado do arquivo (EOF).")

def salvar_ast(ast):
    try:
        with open("ast.json", "w", encoding="utf-8") as f:
            json.dump(ast, f, indent=4, ensure_ascii=False, default=str)
        print("\nAST salva com sucesso em ast.json")
    except Exception as e:
        print(f"\nErro ao salvar AST: {e}")

# constroi o parser
parser = yacc.yacc()
