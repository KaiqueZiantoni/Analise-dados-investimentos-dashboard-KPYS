# Dashboard de investimentos: </br>

**Funções**

1. Analisar os arquivos CSV presentes no projeto
2. Gerar diretamente em postgreSQL o resultado das 5 KPIs definidas como 
importantes para uma análise minuciosa dos gestores de investimento.
3. Criar um Dashboard de fácil interpretação do usuário
4. O README.MD esta divido em duas partes:

º Parte 1 - Execução do projeto;

º Parte 2- Justificativa de decisões e explicação das KPIs;
# Pré-requisitos

- Python 3.11.2  instalado.
- PostgreSQL configurado e rodando

# Iniciando o projeto:

**1.  Inicie seu ambiente virtual (VENV):**

***(Linux // Mac)***
```
    python -m venv venv
    source venv/bin/activate
```


ou

***(Windows)***
```
    venv\scripts\activate
```


**2. Instale as dependências necessárias**

```
    pip install -r requirements.txt
```
**3. Crie um arquivo .env na raiz do projeto:**

-  Crie um arquivo ".env" na raiz do seu projeto, e adicione as informações para conectar em seu banco de dados 
```
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nome_do_banco
```
**4. Execute o arquivo main.py**
```
    (Linux)
    python3 main.py
```
ou
```
    (Windows)
    python main.py
```
*Presente na raiz do projeto*

As tabelas que darão origem aos gráficos serão criadas diretamente no PostgreSQL.

**4.Iniciando o dashboard:**

Para iniciar no seu navegador a apresentação do seu Dashboard, siga esse passo-a-passo:

1. execute o arquivo "dashboard.py": 
``` 
    streamlit run dashboard.py
    (Ele irá oferecer para receber ofertas e informações por e-mail sobre essa extensão do python, caso queira pular, apenas clique ENTER, caso queira receber, digite seu e-mail.)
```
*Presente na raiz do projeto*

_____________________________________________________________________________________________________________________________________________________________
# Escolhas técnicas
O projeto foi desenvolvido utilizando apenas python e postgreSQL, para facilitar o uso, sem que se torne um projeto pesado, cumprindo sua necessidade essencial de analisar - transformar os dados - criar um dashboard de facil entendimento para o responsável.

**"main.py"** 

1. pandas  - 
Essencial para a etapa de ETL, permitindo extrair, limpar e manipular os dados de forma eficiente através de DataFrames.

1. os - 
Utilizado para manipulação dinâmica de caminhos de diretórios, garantindo que o script acesse as pastas e os arquivos de dados corretamente em qualquer sistema operacional.

1. sys - 
Permite interagir com o interpretador Python, sendo útil para ajustar rotas de execução ou interromper o script com segurança em caso de falhas críticas no processamento.

1. sqlalchemy / create_engine - 
Estabelece a conexão direta entre o Python e o banco de dados SQL, permitindo persistir e consultar os dados que já foram processados.

1. dotenv /  load_dotenv - 
Carrega variáveis de ambiente de um arquivo .env, ocultando e protegendo informações sensíveis do projeto, como as credenciais de acesso ao banco de dados.

**"dashboard.py"**

1.  streamlit - 
Framework principal usado para construir a interface web interativa do seu painel de forma rápida, estruturando tudo apenas com Python.

2.  pandas - 
Estrutura e manipula os dados retornados do banco, permitindo filtrar, agregar e preparar as informações antes de enviá-las aos gráficos.

3.  sqlalchemy /  create_engine, text - 
Estabelece a conexão com o banco de dados SQL (create_engine) e permite executar queries diretas e seguras (text) para alimentar o dashboard.

4.  plotly.express - 
Gera os gráficos interativos de forma ágil, permitindo construir visualizações de dados eficientes com poucas linhas de código.

5.  plotly.graph_objects - 
Utilizado para criar visualizações mais complexas ou customizadas, dando controle total sobre cada detalhe e camada dos seus gráficos.

6.  os - 
Garante a leitura correta de caminhos e diretórios no sistema, evitando que o dashboard quebre ao ser executado em ambientes diferentes.

7.  dotenv /  load_dotenv - 
Carrega as credenciais sensíveis (como as senhas de acesso ao banco) do arquivo .env, garantindo que a segurança do projeto não seja exposta.

# Escolhas de KPIs:

(Para visualizar as fórmulas pelo VScode, recomendo a instalação da extensão Markdown+Math )
```
    Cntrl + Shift + x
    Busque a opção Markdown+Math
    Aceite os termos
    Reinicie o VScode
```
## 1. Captação Líquida


**Descrição do negócio:**

Atua como termómetro para aquele fundo de investimento, verificando se, em determinado periodo, o fundo atraiu mais investimentos (Aportes), ou se teve mais retiradas (Resgates).

**Fórmula:**

```

$$\text{Captação Líquida} = \sum(\text{Aportes}) - \sum(\text{Resgates})$$

ou

Sum(Aportes) - Sum(Resgates)

```

*(Agrupado por mês e por fundo).*

## 2. Patrimônio Líquido Total

**Descrição do negócio:**

Representa o tamanho total do fundo sob gestão em um determinado momento. É a métrica central para a receita da gestora, visto que as taxas de administração são aplicadas sobre esse montante.

**Fórmula:**
```
$$\text{PL Total} = \sum(\text{PL Investido})$$

ou

Soma(PL Investido) 
```

## 3. Classes de ativo no fundo

**Descrição do negócio:**

Mostra como o patrimônio está distribuído (ex: Renda Fixa, Renda Variável,etc.). Importante para garantir que o fundo está respeitando seu mandato de investimento e para apresentar o nível de risco macro aos clientes.

**Fórmula:**
```

$$\text{\% Classe} = \left( \frac{\sum \text{PL na Classe}}{\text{Patrimônio Líquido Total}} \right) \times 100$$

ou

(Soma(PL Investido na Classe) / Patrimônio Líquido Total do Fundo) * 100
```

## 4. Risco de Concentração (Top 5 Ativos)

**Descrição do negócio:**

Métrica fundamental para a gestão de riscos e compliance. Destaca a importância dos maiores investimentos individuais na carteira. Contribui para evitar que o fundo fique excessivamente vulnerável à falência ou desvalorização de um único emissor.

**Fórmula:**
```

$$\text{Concentração} (\%) = \left( \frac{\sum \text{PL Investido do Ativo}}{\text{Patrimônio Líquido Total}} \right) \times 100$$

ou 

(Sum(PL Investido do Ativo Específico) / Patrimônio Líquido Total) * 100
```
*(Filtrando os 5 maiores percentuais de cada fundo)*

## 5. Top 3 Fundos Recomendados (Rentabilidade Trimestral)

**Descrição do negócio:**

Um ranking estratégico voltado para o time de vendas. Identifica os fundos que apresentaram a melhor performance real (desconsiderando o impacto de novos investimentos) de maneira consistente nos últimos três meses. Essa janela temporal elimina distorções de um mês atípico, garantindo aos clientes indicações mais confiáveis.

**Fórmula:**
```

$$\text{Rentabilidade Média} = \frac{\text{Rent}_{m} + \text{Rent}_{m-1} + \text{Rent}_{m-2}}{3}$$

ou

Média da Rentabilidade(Mês Atual, Mês -1, Mês -2).
(Onde o Lucro Mensal = PL Atual - PL Anterior - Captação Líquida. 
E a Rentabilidade = Lucro Mensal / PL Anterior)
```
