import sys
from lex_baianivis import lexer
from parser_baianivis import parser, tabela_simbolos

def main():
    
    if len(sys.argv) != 2:
        print("Uso: python main.py <arquivo_fonte.bai>")
        sys.exit(1)

    filepath = sys.argv[1]

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            source_code = file.read()
            print(f"--- Iniciando compilação de ", filepath, " ---")
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado: ", filepath)
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo ", filepath, ": ", e)
        sys.exit(1)

    # vai limpar erros semanticos de execucoes anteriores ( se tiver alguns)
    tabela_simbolos.errors.clear()

    print("--- Análise Léxica e Sintática ---")
    try:
    
        # o parser chama o lexer de maneira implicitta
        result = parser.parse(source_code, lexer=lexer)

        
        # a analise semantica(erros) é verificada dentro da regra p_programa no parser
        # a ast e a tabela de simbolos sao salva pelo parser se nao tiver erros semanticos
        
        if not tabela_simbolos.get_errors():
             if result is not None: # verifica se o parsing teve sucesso (sem erros de sintaxe )
                 print("\nCompilação (análise léxica, sintática e semântica básica) concluída com sucesso.")
             else:
                 # erro de sintaxe ja foi impressso pelo p_error
                 print("\nCompilação falhou devido a erros de sintaxe.")
        else:
            # erro semantico ja foi impresso pelo parser
            print("\nCompilação falhou devido a erros semânticos.")

    except Exception as e:
        # pega excecoes inesperadas durante o parsing
        print(f"\nErro inesperado durante a compilação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

