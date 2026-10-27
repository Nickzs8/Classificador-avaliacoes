import sys
from pathlib import Path

# Ensure the 'src' directory is in sys.path when launched directly via streamlit
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from analytics import carregar_analises

st.set_page_config(page_title="Análise de Avaliações", layout="wide")
st.title("Análise de sentimento das avaliações")


@st.cache_data(ttl=60)  # guarda o resultado por 60s, para não repetir as agregações
def carregar():
    return carregar_analises()


analises = carregar()

# indicadores no topo
col1, col2, col3 = st.columns(3)
col1.metric("Total de avaliações", analises["total"])

acerto = analises["taxa_acerto"]
if not acerto.empty:
    col2.metric("Taxa de acerto (dados novos)", f"{acerto.loc[0, 'taxa_acerto']}%")
    col3.metric("Predições avaliadas", int(acerto.loc[0, "total"]))

# tabelas e gráfico
st.subheader("Produtos com mais avaliações negativas")
st.dataframe(analises["negativas_por_produto"], hide_index=True)

st.subheader("Evolução por mês")
if not analises["evolucao_por_mes"].empty:
    st.bar_chart(analises["evolucao_por_mes"])

st.subheader("Confiança média por classe prevista")
st.dataframe(analises["confianca_media"], hide_index=True)

st.subheader("Últimas avaliações registradas")
if not analises["recentes"].empty:
    st.dataframe(analises["recentes"], hide_index=True, use_container_width=True)