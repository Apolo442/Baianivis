import ply.lex as lex

# calcular o numero da coluna baseada na posicao do token
def find_column(input_text, token_pos):
    
    last_cr = input_text.rfind('\n', 0, token_pos)
    if last_cr < 0:
        column = token_pos + 1
    else:
        column = token_pos - last_cr
    return column

tokens = (
    'ID', 'NUMERO', 'LITERAL_TEXTO',
    'IGUAL', 'MAIS', 'MENOS', 'MULT', 'DIV', 'RESTO',
    'MAIOR', 'MENOR', 'MAIOR_IGUAL', 'MENOR_IGUAL', 'DIFERENTE', 'IGUALDADE',
    'E_LOGICO', 'OU_LOGICO', 'NEGACAO',
    'ABRE_PAREN', 'FECHA_PAREN',
    'ABRE_CHAVE', 'FECHA_CHAVE',
    'PONTO_VIRGULA', 'VIRGULA'
)

# palavras reservadas e mapeadas pra seus tipos de token
reserved = {
    'inteirivis': 'INTEIRO',
    'realzivis': 'REAL',
    'textivis': 'TIPO_TEXTO',
    'vazivis': 'VAZIO',
    'sevis': 'SE',
    'senivis': 'SENAO',
    'enquantivis': 'ENQUANTO',
    'procedimentivis': 'PROCEDIMENTO',
    'funcaozivis': 'FUNCAO',
    'retornivis': 'RETORNO',
    'finivis': 'FIM'
}


# adiciona os tokens das palavras resevadas na lista de tokens
tokens += tuple(reserved.values())

# expressoes regulares para tokens simples
t_IGUAL         = r'='
t_MAIS          = r'\+'
t_MENOS         = r'-'
t_MULT          = r'\*'
t_DIV           = r'/'
t_RESTO         = r'%'

t_MAIOR         = r'>'
t_MENOR         = r'<'
t_MAIOR_IGUAL   = r'>='
t_MENOR_IGUAL   = r'<='
t_DIFERENTE     = r'!='
t_IGUALDADE     = r'\?='

t_E_LOGICO      = r'&&'
t_OU_LOGICO     = r'<>'
t_NEGACAO       = r'!'

t_ABRE_PAREN    = r'\('
t_FECHA_PAREN   = r'\)'
t_ABRE_CHAVE    = r'\{'
t_FECHA_CHAVE   = r'\}'
t_PONTO_VIRGULA = r';'
t_VIRGULA       = r','

t_ignore = ' \t'

# ignorar comentarios
def t_COMENTARIO(t):
    r'//.*'
    pass

# regra para literais de texto ( "bla+bla+bla" ) ""
def t_LITERAL_TEXTO(t):
    r'"[^\"]*"'
    t.value = t.value[1:-1]
    return t

# regra para numeros
def t_NUMERO(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# regra para identificadores e palavras reservadas
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# regra para contagem de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# regra pra tratamento de erros lexicos
def t_error(t):

    col = find_column(t.lexer.lexdata, t.lexer.lexpos)
    print(f"Erro léxico: Símbolo inválido '{t.value[0]}' na linha {t.lexer.lineno}, coluna {col}")
    t.lexer.skip(1)

# gera o analisador lexico
lexer = lex.lex()
