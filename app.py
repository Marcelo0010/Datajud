import requests
import pandas as pd
import plotly.express as px
import streamlit as st
import time
from datetime import datetime

# === 1. CONFIGURAÇÕES ===
API_KEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": API_KEY
}
# Aqui você pode definir o tamanho da página e o número máximo de documentos por estado
# para evitar sobrecarga na coleta de dados
PAGE_SIZE = 10000
MAX_DOCS_PER_STATE = 1000

TRIBUNAIS = {
    'Acre': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjac/_search',
    'Alagoas': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjal/_search',
    'Amazonas': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjam/_search',
    'Amapá': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjap/_search',
    'Bahia': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjba/_search',
    'Ceará': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjce/_search',
    'Distrito Federal': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjdft/_search',
    'Espírito Santo': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjes/_search',
    'Goiás': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjgo/_search',
    'Maranhão': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjma/_search',
    'Minas Gerais': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjmg/_search',
    'Mato Grosso do Sul': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjms/_search',
    'Mato Grosso': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjmt/_search',
    'Pará': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjpa/_search',
    'Paraíba': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjpb/_search',
    'Pernambuco': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjpe/_search',
    'Piauí': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjpi/_search',
    'Paraná': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjpr/_search',
    'Rio de Janeiro': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjrj/_search',
    'Rio Grande do Norte': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search',
    'Rondônia': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjro/_search',
    'Roraima': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjrr/_search',
    'Rio Grande do Sul': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjrs/_search',
    'Santa Catarina': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjsc/_search',
    'Sergipe': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjse/_search',
    'São Paulo': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjsp/_search',
    'Tocantins': 'https://api-publica.datajud.cnj.jus.br/api_publica_tjto/_search',
}

# intervalos de data para filtro
DATA_INICIO = "2024-01-01T00:00:00.000Z"
DATA_FIM = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")

# === 2. FUNÇÕES DE PADRONIZAÇÃO E COLETA ===
def padronizar_doc(doc, estado):
    src = doc.get('_source', {})
    src['estado'] = estado
    for campo in ['movimentos', 'assuntos', 'partes', 'magistrado']:
        v = src.get(campo, [])
        if isinstance(v, dict):
            src[campo] = [v]
        elif not isinstance(v, list):
            src[campo] = []
    return src

def coletar(estado, url):
    # monta query para filtrar dataAjuizamento no intervalo desejado
    payload = {
        "size": PAGE_SIZE,
        "query": {
            "range": {
                "dataAjuizamento": {
                    "gte": DATA_INICIO,
                    "lte": DATA_FIM
                }
            }
        }
    }
    try:
        r = requests.post(f"{url}?scroll=1m", headers=HEADERS, json=payload)
        r.raise_for_status()
        hits = r.json().get('hits', {}).get('hits', [])
        docs = [padronizar_doc(h, estado) for h in hits]
        return docs[:MAX_DOCS_PER_STATE]
    except Exception as e:
        print(f"Erro ao coletar {estado}: {e}")
        return []

# === 3. CARREGAMENTO CACHÊ (Streamlit) ===
@st.cache_data(ttl=600)
def load_data():
    arr = []
    for sigla, url in TRIBUNAIS.items():
        arr.extend(coletar(sigla, url))
        time.sleep(0.2)
    df = pd.DataFrame(arr)
    # Garante listas antes de len()
    for campo in ['movimentos','assuntos']:
        df[campo] = df[campo].apply(lambda x: x if isinstance(x, list) else [])
    # Métricas derivadas
    df['num_mov'] = df['movimentos'].apply(len)
    df['num_assuntos'] = df['assuntos'].apply(len)
    df['dataAjuizamento'] = pd.to_datetime(df['dataAjuizamento'], errors='coerce')
    df['dataHoraUltimaAtualizacao'] = pd.to_datetime(df['dataHoraUltimaAtualizacao'], errors='coerce')
    df['duracao_dias'] = (
        df['dataHoraUltimaAtualizacao'] - df['dataAjuizamento']
    ).dt.days.clip(lower=0)
    df['assunto_principal'] = df['assuntos'].apply(
        lambda l: l[0].get('nome') if l and isinstance(l[0], dict) else None
    )
    return df

# === 4. DASHBOARD ===
st.title("📊 Monitor DataJud — Janeiro/2024 até hoje")

df = load_data()

# filtros
estados = st.multiselect(
    "Estados:", options=df['estado'].unique(), default=list(TRIBUNAIS.keys())
)
df = df[df['estado'].isin(estados)]

st.markdown(f"**Total de processos (jan/2024 até agora):** {len(df)}")

# 4.1 Top 20 Assuntos
st.subheader("Top 20 Assuntos Principais")
top_assuntos = (
    df['assunto_principal']
      .value_counts()
      .head(20)
      .rename_axis('assunto')
      .reset_index(name='quantidade')
)
fig1 = px.bar(
    top_assuntos, x='quantidade', y='assunto', orientation='h',
    title="Assuntos mais frequentes"
)
st.plotly_chart(fig1, use_container_width=True)

# 4.2 Duração média por estado
st.subheader("Duração Média dos Processos (dias) por Estado")
dur_estado = df.groupby('estado')['duracao_dias'].mean().reset_index()
fig2 = px.bar(
    dur_estado, x='estado', y='duracao_dias',
    labels={'duracao_dias':'Duração média (dias)'},
    title="Duração média por estado"
)
st.plotly_chart(fig2, use_container_width=True)

# 4.3 Movimentações médias por estado
st.subheader("Movimentações Média por Estado")
mov_estado = df.groupby('estado')['num_mov'].mean().reset_index()
fig3 = px.bar(
    mov_estado, x='estado', y='num_mov',
    labels={'num_mov':'Movimentações médias'},
    title="Movimentações médias por estado"
)
st.plotly_chart(fig3, use_container_width=True)

# 4.4 Série mensal de ajuizamento por estado
st.subheader("Processos por Mês de Ajuizamento (por Estado)")
df['mes_ajuiz'] = df['dataAjuizamento'].dt.to_period('M').astype(str)

serie_estados = (
    df.groupby(['mes_ajuiz', 'estado'])
      .size()
      .reset_index(name='quantidade')
)

fig4 = px.line(
    serie_estados,
    x='mes_ajuiz',
    y='quantidade',
    color='estado',
    markers=True,
    title="Processos ajuizados por mês (por Estado)"
)
fig4.update_layout(xaxis_title="Mês", yaxis_title="Quantidade de Processos")
st.plotly_chart(fig4, use_container_width=True)

# 4.5 Última atualização do dashboard
st.markdown(f"*Dados coletados até:* {df['dataHoraUltimaAtualizacao'].max()}")

