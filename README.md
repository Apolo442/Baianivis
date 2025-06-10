# Linguagem Baianivis

Baianivis é uma linguagem procedural fictícia desenvolvida como parte do Trabalho Discente Efetivo (TDE) da disciplina de Compiladores, no Centro Universitário Nobre (UNIFAN). A linguagem foi projetada para ser simples, expressiva e didática, com suporte a variáveis, expressões, estruturas de controle de fluxo, procedimentos e funções.

---

## Equipe
- Mateus Sampaio  
- Rebeca Bellini  
- Gustavo Neri  
- Kauan Leão  

---

## Objetivo

Implementar um compilador que inclui:

- Analisador léxico (scanner)
- Analisador sintático + semântico (parser)
- Geração da Árvore Sintática Abstrata (AST) em JSON

---

## Estrutura da Linguagem

### Tipos de Dados

| Palavra-chave | Tipo                     |
| ------------- | ------------------------ |
| `inteirivis`  | Inteiro                  |
| `realzivis`   | Real                     |
| `textivis`    | Texto                    |
| `vazivis`     | Sem tipo (procedimentos) |

---

### Operadores

#### aritméticos

| Operador | Significado      |
| -------- | ---------------- |
| `+`      | Soma             |
| `-`      | Subtração        |
| `*`      | Multiplicação    |
| `/`      | Divisão          |
| `%`      | Resto da divisão |

#### comparação

| Operador | Significado    |
| -------- | -------------- |
| `>`      | Maior          |
| `<`      | Menor          |
| `>=`     | Maior ou igual |
| `<=`     | Menor ou igual |
| `!=`     | Diferente      |
| `?=`     | Igual          |

#### lógicos

| Operador | Significado |
| -------- | ----------- |
| `&&`     | E lógico    |
| `<>`     | OU lógico   |
| `!`      | Negação     |

---

## Estruturas da Linguagem

### Declaração de Variáveis

inteirivis idade;
realzivis preco;
textivis nome;

### Atribuição de VALOR

idade = 25;
preco = 12.5;
nome = "João";

### Procedimentos

procedimentivis saudacao(textivis nome) {
    // Não retorna valor
    // necessário `retornivis;` mesmo retornando vazio
    retornivis;
}

### Funções

funcaozivis somar(inteirivis a, inteirivis b) retornivis inteirivis {
    retornivis a + b;
}

// Importante: Sempre use `retornivis <tipo>` após os parênteses da função para indicar o tipo de retorno.

### Estrutura de repetição

inteirivis i;
i = 0;

enquantivis (i < 5) {
    i = i + 1;
}


### Estrutura condicional

sevis (x > 10) {
    // bloco verdadeiro
} senivis {
    // bloco falso
}


### Comentários
// etc etc etc bla bla bla


### Como utilizar
1- Instale o ply

- pip install ply

2- Crie um arquivo (nome_do_arquivo.bai) na pasta 'exemplos'

3- Abra o terminal na raiz do projeto

4- Execute: python main.py .\exemplos\nome_do_arquivo.bai
