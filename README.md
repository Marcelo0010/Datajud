# DataJud Analytics

Este repositório demonstra duas abordagens para explorar a **API pública DataJud** do CNJ:

## 1. Processamento em Larga Escala com Apache Spark

* Consulta *range* por data (janeiro/2024 até hoje) e paginação via *scroll*.
* Coleta de centenas de milhares de processos de PB, PE e RN sem estourar memória local.
* Transformação em DataFrame Spark, com cálculo de métricas: duração média dos processos, contagem por classe, assunto, juízo e estado.
* Geração de tabelas e gráficos estáticos via Plotly para análise offline.

## 2. Dashboard Interativo com Streamlit + Pandas

* Coleta dinâmica com cache (`@st.cache_data`) para “bom para dados quase real-time”.
* Filtros por estado, visualização de Top 20 Assuntos, Duração Média, Movimentações Médias e Séries Temporais.
* Fácil de compartilhar com equipes ou publicar resultados em relatórios.

## O que é a API DataJud?

A API pública **DataJud**, mantida pelo Conselho Nacional de Justiça (CNJ), disponibiliza **metadados processuais** de tribunais estaduais de forma aberta:

* **Estrutura RESTful** com endpoints para cada tribunal, seguindo `https://api-publica.datajud.cnj.jus.br/api_publica_<sigla>/_search`. 
* **Filtros** por campos como `dataAjuizamento`, `classe`, `assuntos`, `grau`.
* **Paginação via scroll** para percorrer toda a base.

**Observação**: há uma **defasagem** na atualização dos dados (em geral algumas dias), pois a API sincroniza periodicamente com os sistemas internos dos tribunais.

## O que é o Apache Spark?

[Apache Spark](https://spark.apache.org/) é uma **engine de processamento distribuído** projetada para:

* **Processar grandes volumes** de dados em memória sem sobrecarregar recursos locais.
* Definir **pipelines** de transformação de dados (ETL) de forma declarativa via DataFrame API.
* Realizar **agregações**, **joindas** e **cálculos estatísticos** de maneira escalável.

No `analysis.py`, usamos Spark para:

1. **Coletar** centenas de milhares de registros da API sem estourar memória.
2. **Filtrar** por intervalo de datas no próprio cluster.
3. **Calcular** métricas como duração média, contagens por assunto/classe/estado.
4. **Exportar** resultados para gráficos estáticos com Plotly.

## Estrutura do Repositório do Repositório

* **analysis.py**: pipeline PySpark para coleta e análise offline.
* **app.py**: dashboard Streamlit para interação
* **requirements.txt**: dependências necessárias.

## Como Executar

### Análise em Spark

1. Instale dependências:

   ```bash
   pip install -r requirements.txt
   ```
2. Execute:

   ```bash
   spark-submit analysis.py
   ```

### Dashboard Streamlit

1. Instale dependências (se ainda não instalou):

   ```bash
   pip install -r requirements.txt
   ```
2. Rode:

   ```bash
   streamlit run app.py
   ```
3. Abra a URL exibida no terminal.

## Por que usar estas ferramentas?

* **Desempenho**: Spark processa grandes volumes sem overcommit de RAM.
* **Velocidade**: filtros na API e cache no Streamlit mantêm a análise responsiva.
* **Flexibilidade**: combine análises offline e dashboards interativos com o mesmo fluxo de dados.
* **Reprodutibilidade**: basta usar a `API_KEY` para replicar em qualquer máquina.

---

