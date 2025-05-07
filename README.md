# DataJud Analytics

Este repositório demonstra duas abordagens para explorar a **API pública DataJud** do CNJ:

## 1. Processamento em Larga Escala com Apache Spark

* Consulta *range* por data (janeiro/2024 até hoje) e paginação via *scroll*.
* Coleta de centenas de milhares de processos de PB, PE e RN sem estourar memória local.
* Transformação em DataFrame Spark, com cálculo de métricas: duração média dos processos, contagem por classe, assunto, juízo e estado.
* Geração de tabelas e gráficos estáticos via Plotly para análise offline.

## 2. Dashboard Interativo com Streamlit + Pandas

* Coleta dinâmica com cache (`@st.cache_data`) para “quase real-time”.
* Filtros por estado, visualização de Top 20 Assuntos, Duração Média, Movimentações Médias e Séries Temporais.
* Fácil de compartilhar com equipes ou publicar resultados em relatórios.

## Sobre a API DataJud

A API DataJud disponibiliza metadados processuais de tribunais estaduais (classe, assunto, juízo, datas, movimentações), permitindo:

* **Match all** ou **range queries** por campo de data (`dataAjuizamento`).
* **Scroll pagination** para percorrer toda a base.
* Filtragem em campos como sistema, formato e grau.

Economistas, cientistas de dados e gestores públicos podem usar esses dados para:

* Avaliar **eficiência** dos tribunais (duração média, número de movimentações).
* Identificar **tendências de litígio** (assuntos e classes dominantes).
* Monitorar **fluxo de casos** ao longo do tempo.

## Estrutura do Repositório

* **analysis.py**: pipeline PySpark para coleta e análise offline.
* **app.py**: dashboard Streamlit para interação em tempo quase real.
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
* **Reprodutibilidade**: basta ajustar a `API_KEY` para replicar em qualquer máquina.

---

*Exploração de dados judiciais em Spark e Streamlit — insights para áreas de economia do crime, políticas públicas e gestão judicial.*

* **Análises temporais mais refinadas** (tendências semanais, sazonalidade).
* **Modelagem preditiva** para estimar prazos de julgamento.

---

*Desenvolvido em PySpark e Plotly — insights judiciais para informar gestores, advogados e pesquisadores.*
