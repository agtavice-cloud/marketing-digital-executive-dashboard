
import streamlit as st
import pandas as pd
import plotly.express as px

# CONFIGURAÇÃO
st.set_page_config(
    page_title="Marketing Performance",
    page_icon="📊",
    layout="wide"
)

# DESIGN PERSONALIZADO
st.markdown("""
<style>
.stApp {
    background-color: #F4F6FA;
}

[data-testid="stSidebar"] {
    background-color: #172554;
}

[data-testid="stSidebar"] * {
    color: white !important;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

h1 {
    color: #172554;
    font-weight: 700;
}

h2, h3 {
    color: #1E293B;
}

</style>
""", unsafe_allow_html=True)

# CARREGAR DADOS
@st.cache_data
def carregar_dados():
    dados = pd.read_csv("data.csv")
    dados["date"] = pd.to_datetime(dados["date"])
    return dados

df = carregar_dados()

# CABEÇALHO
st.title("📊 Marketing Performance Dashboard")
st.caption("Painel de inteligência e desempenho de campanhas digitais")

# FILTROS
st.sidebar.title("⚙️ Painel de Filtros")
st.sidebar.markdown("---")

campanhas = st.sidebar.multiselect(
    "Selecione as campanhas",
    options=df["campaign"].unique(),
    default=df["campaign"].unique()
)

df_filtrado = df[df["campaign"].isin(campanhas)]

if df_filtrado.empty:
    st.warning("Selecione pelo menos uma campanha.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.caption("Marketing Analytics | Dashboard")

# CÁLCULOS
impressoes = df_filtrado["impressions"].sum()
cliques = df_filtrado["clicks"].sum()
conversoes = df_filtrado["conversions"].sum()
investimento = df_filtrado["cost"].sum()

ctr = cliques / impressoes * 100 if impressoes else 0
taxa_conversao = conversoes / cliques * 100 if cliques else 0
cpa = investimento / conversoes if conversoes else 0
cpc = investimento / cliques if cliques else 0
cpm = investimento / impressoes * 1000 if impressoes else 0

# ROI: somente se houver receita
if "revenue" in df_filtrado.columns and investimento > 0:
    receita = df_filtrado["revenue"].sum()
    roi = ((receita - investimento) / investimento) * 100
else:
    roi = None

# KPIs PRINCIPAIS
st.subheader("📈 Indicadores de Performance")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Impressões", f"{impressoes:,.0f}")
col2.metric("Cliques", f"{cliques:,.0f}")
col3.metric("Conversões", f"{conversoes:,.0f}")
col4.metric("Investimento", f"R$ {investimento:,.2f}")

st.divider()

# KPIs SECUNDÁRIOS
col5, col6, col7, col8 = st.columns(4)

col5.metric("CTR", f"{ctr:.2f}%")
col6.metric("Taxa de Conversão", f"{taxa_conversao:.2f}%")
col7.metric("CPC", f"R$ {cpc:.2f}")
col8.metric("CPM", f"R$ {cpm:.2f}")

col9, col10 = st.columns(2)

col9.metric("CPA", f"R$ {cpa:.2f}")

if roi is not None:
    col10.metric("ROI", f"{roi:.2f}%")
else:
    col10.metric("ROI", "Não disponível")
    st.caption(
        "Para calcular o ROI, adicione a coluna revenue "
        "com a receita de cada campanha no data.csv."
    )

st.divider()

# GRÁFICOS
st.subheader("📊 Análise das Campanhas")

aba1, aba2, aba3 = st.tabs([
    "Impressões",
    "Cliques e Conversões",
    "Investimento"
])

with aba1:
    fig1 = px.bar(
        df_filtrado,
        x="campaign",
        y="impressions",
        color="campaign",
        text="impressions",
        title="Impressões por Campanha",
        template="plotly_white"
    )
    st.plotly_chart(fig1, use_container_width=True)

with aba2:
    df_grafico = df_filtrado.melt(
        id_vars="campaign",
        value_vars=["clicks", "conversions"],
        var_name="Indicador",
        value_name="Quantidade"
    )

    fig2 = px.bar(
        df_grafico,
        x="campaign",
        y="Quantidade",
        color="Indicador",
        barmode="group",
        template="plotly_white",
        title="Cliques e Conversões"
    )
    st.plotly_chart(fig2, use_container_width=True)

with aba3:
    fig3 = px.pie(
        df_filtrado,
        names="campaign",
        values="cost",
        hole=0.5,
        title="Distribuição do Investimento",
        template="plotly_white"
    )
    st.plotly_chart(fig3, use_container_width=True)

# RANKING
st.divider()
st.subheader("🏆 Ranking de Campanhas")

ranking = df_filtrado.sort_values(
    by="conversions",
    ascending=False
)[["campaign", "clicks", "conversions", "cost"]].copy()

ranking.columns = [
    "Campanha",
    "Cliques",
    "Conversões",
    "Investimento"
]

st.dataframe(
    ranking,
    use_container_width=True,
    hide_index=True
)

# DADOS
with st.expander("Visualizar dados completos"):
    st.dataframe(df_filtrado, use_container_width=True)

st.success("Dashboard atualizado com sucesso!")
