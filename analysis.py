# === 0. IMPORTS ===
import requests, time
from datetime import datetime
from pyspark.sql import SparkSession, Row
from pyspark.sql.functions import to_date, datediff, col, explode, count, avg
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
import plotly.express as px

# DICA: USE O GOOGLE COLAB SE NUNCA USOU O SPARK

# === 1. INICIA A SPARK SESSION ===
# == Voce pode mudar para 4g-6g a depender do hardware do seu PC == 
spark = SparkSession.builder \
    .appName("DataJud_Analise_Completo") \
    .config("spark.executor.memory","8g") \
    .config("spark.driver.memory","4g") \
    .config("spark.sql.shuffle.partitions","200") \
    .getOrCreate()


# === 2. CONFIG API & CONSTS ===
API_KEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
HEADERS = {"Content-Type":"application/json","Authorization":API_KEY}
PAGE_SIZE = 1000
SCROLL_TTL = "2m"
SCROLL_URL = "https://api-publica.datajud.cnj.jus.br/_search/scroll"

TRIBUNAIS = {
    'PB':'https://api-publica.datajud.cnj.jus.br/api_publica_tjpb/_search',
    'PE':'https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search',
    'RN':'https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search'
}

DATA_INICIO="2024-01-01T00:00:00.000Z"
DATA_FIM = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
MAX_DOCS=100000000  # None = para ilimitado ou diminua para mil ou dez mil a fim de uma análise mais tranquila

# === 3. FLATTEN sem listas ===
def flatten_hit(hit, estado):
    src = hit.get("_source",{})
    dt_aju = src.get("dataAjuizamento")
    dt_upd = src.get("dataHoraUltimaAtualizacao")
    # contagens
    movs = src.get("movimentos") or []
    movs = movs if isinstance(movs,list) else []
    ass = src.get("assuntos") or []
    ass = ass if isinstance(ass,list) else []
    # juiz
    juiz = None
    og = src.get("orgaoJulgador")
    if isinstance(og,dict): juiz = og.get("nome")
    # classe
    classe = src.get("classe",{}).get("nome")
    # grau
    grau = src.get("grau")
    # assunto principal
    ap = None
    if ass and isinstance(ass[0],dict): ap=ass[0].get("nome")
    return Row(
        estado=estado,
        dataAjuizamento=dt_aju,
        dataAtualizacao=dt_upd,
        movimentos_count=len(movs),
        assuntos_count=len(ass),
        classe=classe,
        grau=grau,
        juiz=juiz,
        assunto_principal=ap
    )

# === 4. EXTRAI APELAÇÕES em (estado,hora) ===
def extract_apel(hit, estado):
    src = hit.get("_source",{})
    movs = src.get("movimentos") or []
    movs = movs if isinstance(movs,list) else []
    rows=[]
    for m in movs:
        nome = (m.get("nome") or "").lower()
        if "apela" in nome:
            dt = m.get("dataHora")
            if dt and len(dt)>=13:
                hora = int(dt[11:13])
                rows.append(Row(estado=estado, hora=hora))
    return rows

# === 5. PAGINAÇÃO + COLETA ===
def collect_for(sigla,url):
    prots=[]    # para processos
    apeos=[]    # para apelações
    payload={"size":PAGE_SIZE,"query":{"range":{"dataAjuizamento":{"gte":DATA_INICIO,"lte":DATA_FIM}}}}
    r=requests.post(f"{url}?scroll={SCROLL_TTL}",headers=HEADERS,json=payload)
    r.raise_for_status()
    data=r.json()
    scroll_id=data.get("_scroll_id")
    hits=data.get("hits",{}).get("hits",[])
    while hits and (MAX_DOCS is None or len(prots)<MAX_DOCS):
        for h in hits:
            prots.append(flatten_hit(h,sigla))
            apeos.extend(extract_apel(h,sigla))
            if MAX_DOCS and len(prots)>=MAX_DOCS: break
        if not hits or (MAX_DOCS and len(prots)>=MAX_DOCS): break
        r=requests.post(SCROLL_URL,headers=HEADERS,json={"scroll":SCROLL_TTL,"scroll_id":scroll_id})
        r.raise_for_status()
        data=r.json()
        scroll_id=data.get("_scroll_id")
        hits=data.get("hits",{}).get("hits",[])
    return prots,apeos

# === 6. COLETA DOS DADOS  -  PODE DEMORAR 5, 10, 20 MINUTOS A DEPENDER DO SEU PC ===
all_prots=[]
all_ape=[]
for sig,url in TRIBUNAIS.items():
    print("Buscando",sig)
    p,a = collect_for(sig,url)
    all_prots.extend(p)
    all_ape.extend(a)
    time.sleep(0.2)

print(f"Total de processos lidos: {len(all_prots)}")

# === 7. CRIA RDDs + DF SPARK ===
rdd_pro = spark.sparkContext.parallelize(all_prots)
df_pro = spark.createDataFrame(rdd_pro) \
    .withColumn("dt_aju", to_date("dataAjuizamento")) \
    .withColumn("dt_upd", to_date("dataAtualizacao")) \
    .withColumn("duracao_dias", datediff("dt_upd","dt_aju"))

# Definição de schema para as apelações
schema_ape = StructType([
    StructField("estado", StringType(), True),
    StructField("hora", IntegerType(), True)
])

if all_ape:
    rdd_ape = spark.sparkContext.parallelize(all_ape)
    df_ape = spark.createDataFrame(rdd_ape)
else:
    # cria DataFrame vazio com schema
    df_ape = spark.createDataFrame([], schema_ape)

df_pro.cache()
df_ape.cache()

# === 8. VISUALIZAÇÕES PANDAS/Plotly ===

# Converte o DataFrame Spark principal para Pandas (será usado em vários gráficos)
pdf_pro = df_pro.toPandas()

# 8.1 EFICIÊNCIA DOS JUÍZES
df_eff = df_pro.groupBy("estado", "juiz") \
    .agg(
        avg("duracao_dias").alias("dur_media"),
        count("*").alias("n_proc")
    ) \
    .filter(col("n_proc") >= 20) \
    .orderBy("estado", "dur_media")

pdf_eff = df_eff.toPandas()
fig1 = px.bar(
    pdf_eff,
    x="dur_media",
    y="juiz",
    color="estado",
    orientation="h",
    title="Juízes com ≥20 processos: duração média"
)
fig1.show()


# 8.2 TOP ASSUNTOS POR ESTADO
df_ass_est = df_pro.groupBy("estado", "assunto_principal") \
    .count() \
    .orderBy("estado", col("count").desc())

pdf_ass_est = df_ass_est.toPandas()
fig2 = px.bar(
    pdf_ass_est,
    x="count",
    y="assunto_principal",
    color="assunto_principal",
    facet_col="estado",
    facet_col_wrap=3,
    category_orders={
        "estado": sorted(df_pro.select("estado").distinct().rdd.flatMap(lambda x: x).collect())
    },
    title="Top Assuntos por Estado",
    height=400
)
fig2.update_layout(showlegend=False)
fig2.show()


# 8.3 CLASSES PROCESSUAIS POR ESTADO (TOP >50)
df_cls_est = df_pro.groupBy("estado", "classe") \
    .count() \
    .filter(col("count") > 50) \
    .orderBy("estado", col("count").desc())

pdf_cls_est = df_cls_est.toPandas()
fig3 = px.bar(
    pdf_cls_est,
    x="count",
    y="classe",
    color="estado",
    facet_col="estado",
    facet_col_wrap=3,
    title="Classes Processuais (>50 processos) por Estado",
    height=800
)
fig3.update_layout(showlegend=False)
fig3.show()


# 8.4 HISTOGRAMA DA DURAÇÃO DOS PROCESSOS POR ESTADO
fig4 = px.histogram(
    pdf_pro,
    x="duracao_dias",
    facet_col="estado",
    facet_col_wrap=3,
    nbins=50,
    title="Distribuição da Duração dos Processos (dias) por Estado",
    labels={"duracao_dias": "Duração (dias)", "count": "Número de Processos"}
)
fig4.update_layout(
    height=1000,
    showlegend=False
)
# Desacopla eixos X para cada faceta
fig4.for_each_xaxis(lambda ax: ax.update(matches=None))
fig4.show()


# 8.5 QUANTIDADE DE PROCESSOS POR GRAU E ESTADO
df_grau_est = df_pro.groupBy("estado", "grau") \
    .count() \
    .orderBy("estado", col("count").desc())

pdf_grau_est = df_grau_est.toPandas()
fig5 = px.bar(
    pdf_grau_est,
    x="grau",
    y="count",
    color="estado",
    barmode="group",
    title="Quantidade de Processos por Grau e Estado"
)
fig5.show()


# === 9. TABELAS RESUMO ===

# === 9.1.  CONTAGEM DE PROCESSOS POR ESTADO  POR ASSUNTO  ===

df_pro.groupBy("estado", "assunto_principal") \
    .count() \
    .orderBy("estado", col("count").desc()) \
    .show(100, truncate=False)

# === 9.2.  MÉDIA DE DIAS POR PROCESSO  ===
df_pro.groupBy("estado") \
    .agg({"duracao_dias": "avg"}) \
    .withColumnRenamed("avg(duracao_dias)", "duracao_media_dias") \
    .orderBy("estado") \
    .show()

# === 9.3. CONTAGEM DE PROCESSOS POR GRAU POR ESTADO  ===
df_pro.groupBy("grau") \
    .count() \
    .orderBy(col("count").desc()) \
    .show()

spark.stop()
