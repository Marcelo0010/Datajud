
# DataJud Spark Analysis

Este repositório apresenta um **pipeline de análise de processos judiciais** utilizando dados do **DataJud** (API pública do Conselho Nacional de Justiça) para os Tribunais de Justiça da Paraíba (PB), Pernambuco (PE) e Rio Grande do Norte (RN).

## Sobre o DataJud

O DataJud é uma iniciativa do CNJ que fornece acesso aberto a informações processuais de diversos tribunais brasileiros. A API pública do DataJud permite consultar **metadados de processos** (classe, assunto, juízo, movimentações, datas de ajuizamento e atualização, etc.), possibilitando análises agregadas e também estudos de eficiência e desempenho dos tribunais.

## Objetivos deste projeto

1. **Quantificar** o volume de casos ajuizados de janeiro/2024 até o presente.
2. **Comparar** a distribuição de assuntos e classes processuais entre PB, PE e RN.
3. **Avaliar a eficiência** dos juízos por meio da duração média dos processos.
4. **Visualizar** padrões temporais (mensal, horário) e características estruturais (grau, movimentações).

## Estrutura

* **analysis.py**
  Script principal em PySpark que:

  * Coleta e limpa dados via API DataJud (scroll + *range* em `dataAjuizamento`).
  * Transforma registros em DataFrame Spark e calcula métricas (duração, contagens).
  * Gera tabelas Spark e exporta para gráficos com Plotly.

* **requirements.txt**
  Lista de dependências para instalar via pip.

## Como executar

1. Clone o repositório:

   ```bash
   git clone <URL_DO_REPO>
   cd datajud-spark-analysis
   ```
2. Crie um ambiente virtual e instale as dependências:

   ```bash
   python -m venv venv
   source venv/bin/activate  # ou `venv\Scripts\activate` no Windows
   pip install -r requirements.txt
   ```
3. Ajuste a variável `API_KEY` em `analysis.py` (substitua pela sua chave se necessário).
4. Execute com Spark:

   ```bash
   spark-submit analysis.py
   ```

   ou, em um notebook:

   ```bash
   python analysis.py
   ```

## Principais Insights

* **Processos por Estado**: mostra o volume real de casos (muito abaixo dos limites solicitados), refletindo o fluxo de janeiro/2024 até hoje.
* **Top 10 Assuntos por Estado**: facetas destacam as áreas de litígio predominantes em cada tribunal.
* **Classes Processuais**: comparação das classes que superaram 50 processos em cada jurisdição.
* **Duração Média**: indicador de eficiência, revelando quais juízos finalizam mais rapidamente.

## Próximos passos

* **Escalar** para outros tribunais estaduais e federais.
* **Análises temporais mais refinadas** (tendências semanais, sazonalidade).
* **Modelagem preditiva** para estimar prazos de julgamento.

---

*Desenvolvido em PySpark e Plotly — insights judiciais para informar gestores, advogados e pesquisadores.*
