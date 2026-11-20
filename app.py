import streamlit as st
import pandas as pd
import plotly.express as px
import io
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image as RLImage
)

# ---------------------------------------------------------------
# Página e tema
# ---------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Executivo de Marketing Digital",
    page_icon="📈",
    layout="wide",
)

st.markdown("""
<style>

/* Identidade tipográfica: moderna, limpa e corporativa */
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    letter-spacing: -0.01em;
}

.main {
    background-color: #0f172a;
}

/* Títulos e hierarquia visual */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #f8fafc;
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-weight: 700;
    letter-spacing: -0.035em;
    line-height: 1.25;
}

h1, [data-testid="stMarkdownContainer"] h1 {
    font-size: 2.15rem;
}

h2, [data-testid="stMarkdownContainer"] h2 {
    font-size: 1.65rem;
}

h3, [data-testid="stMarkdownContainer"] h3 {
    font-size: 1.25rem;
}

p, label, [data-testid="stCaptionContainer"] {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    line-height: 1.6;
}

/* Cartões de métricas */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 8px 20px rgba(0,0,0,.3);
}

div[data-testid="metric-container"] label {
    color: #cbd5e1;
    font-size: 0.88rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f8fafc;
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.04em;
}

/* Barra lateral e controles */
section[data-testid="stSidebar"] {
    background-color: #111827;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-weight: 700;
}

[data-testid="stWidgetLabel"] p {
    color: #e2e8f0;
    font-size: 0.9rem;
    font-weight: 600;
}

/* Abas e tabelas */
button[data-baseweb="tab"] {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
    font-size: 0.92rem;
    font-weight: 600;
}

div[data-testid="stDataFrame"] {
    font-family: "Inter", "Segoe UI", Arial, sans-serif;
}


/* CORREÇÃO DO FUNDO E DA VISIBILIDADE DOS TEXTOS */

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background-color: #0f172a !important;
}

/* Títulos principais */
h1, h2, h3, h4,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    color: #f8fafc !important;
}

/* Subtítulos e textos */
p,
[data-testid="stMarkdownContainer"] p,
[data-testid="stCaptionContainer"] {
    color: #cbd5e1 !important;
}

/* Textos da área principal */
[data-testid="stMain"] label {
    color: #e2e8f0 !important;
}

/* CORREÇÃO DOS PRINCIPAIS INSIGHTS */
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] li p,
[data-testid="stMarkdownContainer"] ul,
[data-testid="stMarkdownContainer"] ol {
    color: #f1f5f9 !important;
}

/* Garantir boa leitura dos textos dos relatórios */
[data-testid="stMarkdownContainer"] li strong,
[data-testid="stMarkdownContainer"] li span {
    color: #ffffff !important;
}

/* Títulos dos cartões */
.stApp h4 {
    color: #f8fafc !important;
}

/* Números dos cartões */
.stApp h2 {
    color: #ffffff !important;
}

/* Texto geral do relatório executivo */
[data-testid="stVerticalBlock"] p {
    color: #e2e8f0;
}



/* Barra superior */
[data-testid="stHeader"] {
    background-color: #0f172a !important;
}

/* Textos da barra lateral */
section[data-testid="stSidebar"] {
    background-color: #111827 !important;
}

section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #f8fafc !important;
}



</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------
# Cabeçalho com logo fictício
# ---------------------------------------------------------------
st.markdown("""
# Dashboard Executivo de Marketing Digital
### Inteligência de dados para decisões estratégicas
""")
st.info(
    "Projeto demonstrativo: esta versão utiliza uma base de demonstração e não possui "
    "integração direta com contas do Google Ads, Meta Ads ou outras plataformas. "
    "A estrutura foi desenvolvida como modelo aplicável a projetos reais."
)


# ---------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------

def format_pt(value, decimals=2):
    """Formata números no padrão brasileiro, aceitando números e textos numéricos."""
    if value is None:
        return "-"

    try:
        numero = float(value)
    except (TypeError, ValueError):
        return "-"

    if pd.isna(numero):
        return "-"

    texto = f"{numero:,.{decimals}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------
# Carregar dados (cacheado)
# ---------------------------------------------------------------
@st.cache_data
def carregar_dados() -> pd.DataFrame:
    df = pd.read_csv("data.csv")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    num_cols = [
        "impressions", "clicks", "conversions", "cost", "revenue",
        "new_customers", "sales_cost"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].astype(float).round(2)
    return df

# Carrega dados
df = carregar_dados()

# ---------------------------------------------------------------
# Sidebar – filtros avançados
# ---------------------------------------------------------------
st.sidebar.title(" Filtros avançados")

# Checkbox para ocultar valores sensíveis
hide_sensitive = st.sidebar.checkbox("Ocultar valores sensíveis", value=False)

# Intervalo de datas
min_date = df["date"].min()
max_date = df["date"].max()
date_range = st.sidebar.date_input(
    "Selecione o intervalo de datas",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date,
)
if len(date_range) == 2:
    start, end = date_range
    df = df[(df["date"] >= start) & (df["date"] <= end)]

# Seletor de campanhas
campaigns = st.sidebar.multiselect(
    "Campanhas",
    options=df["campaign"].unique(),
    default=df["campaign"].unique(),
)
df = df[df["campaign"].isin(campaigns)]

# Seletor de métricas a exibir
kpi_options = [
    "Impressões",
    "Cliques",
    "Conversões",
    "Investimento",
    "CTR",
    "Taxa de Conversão",
    "CPC",
    "CPM",
    "CPA",
    "CAC simplificado (proxy)",
    "CAC estimado",
]

# Indicadores de retorno financeiro só ficam disponíveis quando a base
# possui a coluna de receita.
if "revenue" in df.columns:
    kpi_options.extend(["Receita", "ROAS", "ROI"])

selected_kpis = st.sidebar.multiselect(
    "Indicadores a exibir",
    options=kpi_options,
    default=kpi_options,
)

# Download dos dados filtrados
csv = df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="📥 Baixar CSV filtrado",
    data=csv,
    file_name="dados_filtrados.csv",
    mime="text/csv",
)

# ---------------------------------------------------------------
# Cálculos de indicadores
# ---------------------------------------------------------------
impressoes = df["impressions"].sum()
cliques = df["clicks"].sum()
conversoes = df["conversions"].sum()
investimento = df["cost"].sum()
# Receita pode não existir na base de dados; tratar normalmente
if "revenue" in df.columns:
    receita = df["revenue"].sum()
else:
    receita = 0.0

ctr = cliques / impressoes * 100 if impressoes else 0
taxa_conversao = conversoes / cliques * 100 if cliques else 0
cpc = investimento / cliques if cliques else 0
cpm = investimento / impressoes * 1000 if impressoes else 0
cpa = investimento / conversoes if conversoes else 0
roas = receita / investimento if investimento > 0 else 0

# CAC simplificado é apenas um proxy quando conversões são usadas como
# aproximação de novos clientes; por isso, coincide matematicamente com o CPA.
cac_simplificado = investimento / conversoes if conversoes > 0 else None

# CAC estimado exige a quantidade de novos clientes. Se houver custos
# comerciais na base, eles também entram no numerador.
cac_estimado = None
if "new_customers" in df.columns:
    total_novos_clientes = df["new_customers"].sum()
    custo_comercial = df["sales_cost"].sum() if "sales_cost" in df.columns else 0
    if total_novos_clientes > 0:
        cac_estimado = (investimento + custo_comercial) / total_novos_clientes

roi = ((receita - investimento) / investimento) * 100 if investimento > 0 else 0

# Função para ocultar valores quando essa opção estiver ativada
def get_value(raw, prefix="", suffix=""):
    if hide_sensitive:
        return "*****"
    return f"{prefix}{format_pt(raw)}{suffix}"

kpi_values = {
    "Impressões": get_value(impressoes),
    "Cliques": get_value(cliques),
    "Conversões": get_value(conversoes),
    "Investimento": get_value(investimento, prefix="R$ "),
    "Receita": get_value(receita, prefix="R$ "),
    "CTR": get_value(ctr, suffix="%"),
    "Taxa de Conversão": get_value(taxa_conversao, suffix="%"),
    "CPC": get_value(cpc, prefix="R$ "),
    "CPM": get_value(cpm, prefix="R$ "),
    "CPA": get_value(cpa, prefix="R$ "),
    "ROAS": get_value(roas),
    "CAC simplificado (proxy)": (
        "N/D" if cac_simplificado is None else get_value(cac_simplificado, prefix="R$ ")
    ),
    "CAC estimado": (
        "N/D" if cac_estimado is None else get_value(cac_estimado, prefix="R$ ")
    ),
    "ROI": get_value(roi, suffix="%"),
}

# ---------------------------------------------------------------
# KPIs executivos principais
# ---------------------------------------------------------------
st.markdown("### Indicadores-chave de desempenho")

kpis_principais = [
    ("Investimento", get_value(investimento, prefix="R$ ")),
    ("Cliques", get_value(cliques)),
    ("CTR", get_value(ctr, suffix="%")),
    ("Conversões", get_value(conversoes)),
    ("CPA médio", get_value(cpa, prefix="R$ ")),
]

cols_kpi = st.columns(5, gap="medium")
for col, (titulo_kpi, valor_kpi) in zip(cols_kpi, kpis_principais):
    with col:
        st.markdown(f"""
        <div style="
            background:linear-gradient(145deg,#1e293b,#111827);
            padding:22px 18px;
            border-radius:16px;
            border:1px solid #334155;
            border-top:4px solid #38bdf8;
            min-height:138px;
            display:flex;
            flex-direction:column;
            justify-content:center;
            box-shadow:0 8px 22px rgba(0,0,0,.22);
            overflow-wrap:anywhere;
        ">
            <div style="font-size:13px;font-weight:600;color:#94a3b8;margin-bottom:12px;">
                {titulo_kpi}
            </div>
            <div style="font-size:clamp(19px,1.8vw,27px);font-weight:750;color:#f8fafc;line-height:1.2;">
                {valor_kpi}
            </div>
        </div>
        """, unsafe_allow_html=True)

# Indicadores adicionais continuam disponíveis no filtro lateral
with st.expander("Ver outros indicadores"):
    cols_extra = st.columns(4, gap="medium")
    extras = [k for k in selected_kpis if k not in
              ["Investimento", "Cliques", "CTR", "Conversões", "CPA"]]
    for i, kpi in enumerate(extras):
        cols_extra[i % 4].metric(kpi, kpi_values[kpi])

# ---------------------------------------------------------------
#  Mostrar Crescimento
# ---------------------------------------------------------------
st.write("")
st.write("")

cliques_por_dia = (
    df.groupby("date")["clicks"]
    .sum()
    .sort_index()
)

if len(cliques_por_dia) >= 2:
    cliques_inicio = cliques_por_dia.iloc[0]
    cliques_fim = cliques_por_dia.iloc[-1]

    if cliques_inicio > 0:
        variacao_cliques_pct = (
            (cliques_fim - cliques_inicio) / cliques_inicio
        ) * 100
        st.metric(
            "Variação de cliques no período",
            f"{variacao_cliques_pct:+.1f}%",
            delta=(
                f"{cliques_por_dia.index[0].strftime('%d/%m')} → "
                f"{cliques_por_dia.index[-1].strftime('%d/%m')}"
            )
        )
    else:
        st.metric(
            "Variação de cliques no período",
            "N/D",
            delta="O primeiro dia teve zero cliques"
        )
else:
    st.metric(
        "Variação de cliques no período",
        "N/D",
        delta="É necessário ter pelo menos duas datas"
    )


# ---------------------------------------------------------------
# 📈 Gráfico de tendência superior
# ---------------------------------------------------------------
st.subheader(" Tendência de Cliques ao longo do tempo")
fig = px.line(
    df,
    x="date",
    y="clicks",
    color="campaign",
    template="plotly_dark",
    labels={
        "date": "Data",
        "clicks": "Cliques",
        "campaign": "Campanha"
    }
)
fig.update_traces(
    line=dict(width=4)
)
st.plotly_chart(
    fig,
    use_container_width=True,
    key="trend_clicks"
)

st.divider()


# ---------------------------------------------------------------
# Distribuição do investimento + leitura executiva
# ---------------------------------------------------------------
st.divider()
st.subheader("Onde está concentrado o investimento?")

col_pizza, col_leitura = st.columns([1.25, 1], gap="large")

investimento_campanha = (
    df.groupby("campaign", as_index=False)["cost"].sum()
    .sort_values("cost", ascending=False)
)
total_investimento_pizza = investimento_campanha["cost"].sum()

with col_pizza:
    if total_investimento_pizza > 0:
        fig_pizza_exec = px.pie(
            investimento_campanha,
            names="campaign",
            values="cost",
            hole=0.48,
            title="Participação no investimento por campanha",
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_pizza_exec.update_traces(
            textposition="inside",
            textinfo="percent",
            textfont_size=14,
            hovertemplate="<b>%{label}</b><br>Investimento: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>",
        )
        fig_pizza_exec.update_layout(
            height=430,
            margin=dict(l=10, r=10, t=65, b=10),
            legend_title_text="Campanhas",
            font=dict(family="Inter, Segoe UI, sans-serif", size=13),
        )
        st.plotly_chart(fig_pizza_exec, use_container_width=True, key="pie_investimento_executivo")
    else:
        st.info("Não há investimento positivo no período selecionado.")

with col_leitura:
    st.markdown("#### Leitura executiva")
    if not investimento_campanha.empty and total_investimento_pizza > 0:
        lider_investimento = investimento_campanha.iloc[0]
        participacao = lider_investimento["cost"] / total_investimento_pizza * 100
        por_campanha = df.groupby("campaign").agg(
            impressoes=("impressions", "sum"),
            conversoes=("conversions", "sum"),
            investimento=("cost", "sum"),
        )
        lider_impressoes = por_campanha["impressoes"].idxmax() if not por_campanha.empty else None
        lider_conversoes = por_campanha["conversoes"].idxmax() if not por_campanha.empty else None

        st.markdown(
            f"**{lider_investimento['campaign']}** concentra "
            f"**{format_pt(participacao, 1)}%** do investimento "
            f"({('valores ocultos' if hide_sensitive else 'R$ ' + format_pt(lider_investimento['cost']) )})."
        )
        st.markdown(
            f"A campanha líder em impressões é **{lider_impressoes}** "
            f"e a líder em conversões é **{lider_conversoes}**."
        )
        st.caption(
            "A concentração de verba, isoladamente, não comprova eficiência. "
            "Compare também CPA, taxa de conversão e qualidade das conversões."
        )
    else:
        st.info("Selecione campanhas com investimento para gerar a leitura executiva.")

# ---------------------------------------------------------------
# Visualizações interativas
# ---------------------------------------------------------------
st.subheader("Visualizações")

aba1, aba2, aba3, aba4 = st.tabs(["Impressões", "Cliques/Conversões", "Investimento", "Evolução ao longo do tempo"])

with aba1:
    fig1 = px.bar(
        df,
        x="campaign",
        y="impressions",
        color="campaign",
        text="impressions",
        title="Impressões por Campanha",
        template="plotly_dark",
        labels={
            "campaign": "Campanha",
            "impressions": "Impressões"
        },
    )
    st.plotly_chart(fig1, use_container_width=True, key="bar_impressions")

with aba2:
    df_long = df.melt(id_vars=["campaign"], value_vars=["clicks", "conversions"], var_name="Indicador", value_name="Quantidade")
    fig2 = px.bar(
        df_long,
        x="campaign",
        y="Quantidade",
        color="Indicador",
        barmode="group",
        title="Cliques e Conversões",
        template="plotly_dark",
        labels={
            "campaign": "Campanha",
            "Quantidade": "Quantidade",
            "Indicador": "Indicador"
        },
    )
    st.plotly_chart(fig2, use_container_width=True, key="bar_clicks_conversions")

with aba3:
    st.markdown("A distribuição do investimento por campanha está apresentada no gráfico executivo acima.")
    st.dataframe(
        investimento_campanha.rename(columns={
            "campaign": "Campanha",
            "cost": "Investimento"
        }).assign(
            **{"Participação": investimento_campanha["cost"].apply(
                lambda valor: format_pt(valor / total_investimento_pizza * 100) + "%"
                if total_investimento_pizza > 0 else "0,00%"
            )}
        ),
        use_container_width=True,
        hide_index=True,
    )

with aba4:
    metric = selected_kpis[0] if selected_kpis else "Impressões"
    metric_col = {
        "Impressões": "impressions",
        "Cliques": "clicks",
        "Conversões": "conversions",
        "Investimento": "cost",
        "Receita": "revenue"
    }.get(metric, "impressions")
    if metric_col not in df.columns:
        metric_col = "impressions"
    fig4 = px.line(
        df.sort_values("date"),
        x="date",
        y=metric_col,
        color="campaign",
        title=f"Evolução dos indicadores ao longo do tempo",
        template="plotly_dark",
        labels={
            "date": "Data",
            metric_col: metric
        }

    )
    st.plotly_chart(fig4, use_container_width=True)

st.divider()


# ---------------------------------------------------------------
# Ranking de campanhas (com CPA)
# ---------------------------------------------------------------
st.subheader("Ranking de Campanhas por Volume de Conversões")

colunas_agg = {
    "clicks": "sum",
    "conversions": "sum",
    "cost": "sum"
}

if "revenue" in df.columns:
    colunas_agg["revenue"] = "sum"

ranking = (
    df.groupby("campaign")
    .agg(colunas_agg)
    .reset_index()
    .sort_values("conversions", ascending=False)
)

# Calcula o CPA antes de formatar os valores
ranking["cpa"] = (
    ranking["cost"] / ranking["conversions"].where(ranking["conversions"] > 0)
).fillna(0)

if "revenue" in ranking.columns:
    ranking["roas"] = (
        ranking["revenue"] / ranking["cost"].where(ranking["cost"] > 0)
    ).fillna(0)

# Renomeia as colunas para português
renomear = {
    "campaign": "Campanha",
    "clicks": "Cliques",
    "conversions": "Conversões",
    "cost": "Investimento",
    "cpa": "CPA",
    "roas": "ROAS"
}

if "revenue" in ranking.columns:
    renomear["revenue"] = "Receita"

ranking = ranking.rename(columns=renomear)

# Formata os valores para exibição
if hide_sensitive:
    ranking["Investimento"] = "Oculto"
    ranking["CPA"] = "Oculto"

    if "Receita" in ranking.columns:
        ranking["Receita"] = "Oculto"
    if "ROAS" in ranking.columns:
        ranking["ROAS"] = "Oculto"
else:
    ranking["Investimento"] = ranking["Investimento"].apply(
        lambda x: "R$ " + format_pt(x)
    )
    ranking["CPA"] = ranking["CPA"].apply(
        lambda x: "R$ " + format_pt(x)
    )

    if "Receita" in ranking.columns:
        ranking["Receita"] = ranking["Receita"].apply(
            lambda x: "R$ " + format_pt(x)
        )
    if "ROAS" in ranking.columns:
        ranking["ROAS"] = ranking["ROAS"].apply(
            lambda x: format_pt(x) + "x"
        )

st.dataframe(ranking, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------
# Relatório executivo: insights automáticos e recomendações
# ---------------------------------------------------------------
def gerar_insights(df_analise, ranking_analise):
    """Gera leituras descritivas sem benchmarks universais fixos."""
    insights = []
    recomendacoes = []

    total_impressoes = df_analise["impressions"].sum()
    total_cliques = df_analise["clicks"].sum()
    total_conversoes = df_analise["conversions"].sum()
    total_investimento = df_analise["cost"].sum()

    ctr_atual = total_cliques / total_impressoes * 100 if total_impressoes else 0
    taxa_conv_atual = total_conversoes / total_cliques * 100 if total_cliques else 0
    cpa_atual = total_investimento / total_conversoes if total_conversoes else 0

    if total_impressoes > 0:
        insights.append(
            f"A taxa de cliques (CTR) consolidada do período foi de {format_pt(ctr_atual)}%."
        )
        recomendacoes.append(
            "Comparar o CTR entre campanhas, públicos e peças criativas, considerando "
            "os objetivos e referências definidos para o negócio."
        )
    else:
        insights.append("Não há impressões no período selecionado para calcular o CTR.")
        recomendacoes.append(
            "Verificar a disponibilidade dos dados de impressões e a configuração dos filtros."
        )

    if total_cliques > 0:
        insights.append(
            f"A taxa de conversão consolidada foi de {format_pt(taxa_conv_atual)}%, "
            "calculada pela relação entre conversões e cliques."
        )
        recomendacoes.append(
            "Analisar a taxa de conversão por campanha em conjunto com a qualidade das "
            "conversões e a experiência da página de destino."
        )
    else:
        insights.append(
            "Não foram registrados cliques no período; não é possível calcular a taxa de conversão."
        )

    if total_conversoes > 0:
        insights.append(
            f"Foram registradas {format_pt(total_conversoes, 0)} conversões, com CPA "
            f"{'oculto' if hide_sensitive else 'de R$ ' + format_pt(cpa_atual)}."
        )
    else:
        insights.append("Não houve conversões registradas no período selecionado.")
        recomendacoes.append(
            "Validar o rastreamento de conversões e revisar o alinhamento entre anúncios, "
            "público, oferta e página de destino."
        )

    if not ranking_analise.empty:
        maior_volume = ranking_analise.iloc[0]
        insights.append(
            f"A campanha com maior volume de conversões foi '{maior_volume['Campanha']}', "
            f"com {format_pt(maior_volume['Conversões'], 0)} conversões."
        )

        campanhas_sem_conv = ranking_analise[
            ranking_analise["Conversões"] == 0
        ]
        if not campanhas_sem_conv.empty:
            nomes = ", ".join(
                str(x) for x in campanhas_sem_conv["Campanha"].head(3)
            )
            insights.append(f"Campanhas sem conversões registradas no período: {nomes}.")
            recomendacoes.append(
                "Investigar individualmente as campanhas sem conversões, verificando "
                "investimento, público, criativos e configuração do acompanhamento."
            )

    # As lideranças são calculadas e apresentadas separadamente.
    if not df_analise.empty:
        resumo_campanhas = df_analise.groupby("campaign").agg(
            investimento=("cost", "sum"),
            impressoes=("impressions", "sum"),
            conversoes=("conversions", "sum"),
        )

        if total_investimento > 0:
            maior_verba = resumo_campanhas["investimento"].idxmax()
            share_verba = (
                resumo_campanhas.loc[maior_verba, "investimento"]
                / total_investimento * 100
            )
            insights.append(
                f"A campanha '{maior_verba}' concentra {format_pt(share_verba, 1)}% do investimento."
            )

        if resumo_campanhas["impressoes"].sum() > 0:
            maior_imp = resumo_campanhas["impressoes"].idxmax()
            insights.append(f"A campanha líder em volume de impressões é '{maior_imp}'.")

        recomendacoes.append(
            "Comparar CPA, taxa de conversão, volume e qualidade das conversões antes "
            "de redistribuir o orçamento entre campanhas."
        )

    if "revenue" in df_analise.columns:
        receita_total = df_analise["revenue"].sum()
        if receita_total > 0 and total_investimento > 0:
            roas_atual = receita_total / total_investimento
            roi_atual = ((receita_total - total_investimento) / total_investimento) * 100
            insights.append(
                f"O ROAS consolidado foi de {format_pt(roas_atual)}x, com base na receita registrada."
            )
            insights.append(
                f"O ROI simplificado foi de {format_pt(roi_atual)}%, considerando apenas "
                "receita registrada e investimento em mídia; não representa necessariamente lucro líquido."
            )
            recomendacoes.append(
                "Considerar margens, custos operacionais, impostos e demais despesas para "
                "avaliar a rentabilidade efetiva."
            )
        else:
            insights.append(
                "A base contém uma coluna de receita, mas não há valores positivos suficientes "
                "para uma leitura consolidada de ROAS e ROI."
            )
    else:
        insights.append(
            "A base não contém a coluna de receita; ROAS e ROI não podem ser calculados "
            "de forma confiável nesta análise."
        )
        recomendacoes.append(
            "Incluir receita atribuída por campanha caso a análise de retorno financeiro "
            "faça parte dos objetivos do dashboard."
        )

    if not recomendacoes:
        recomendacoes.append(
            "Manter o monitoramento periódico e comparar os resultados com períodos "
            "equivalentes, considerando os objetivos do negócio."
        )

    return insights, list(dict.fromkeys(recomendacoes))


st.subheader(" Relatório Executivo — Insights e Recomendações")
st.caption(
    "Insights automatizados baseados em regras de negócio e nos indicadores disponíveis. "
    "As recomendações são indicativas e devem ser avaliadas conforme o contexto do negócio."
)

insights_exec, recomendacoes_exec = gerar_insights(df, ranking)

with st.container(border=True):
    st.markdown("###  Resumo executivo")
    if hide_sensitive:
        st.write(
            f"No período selecionado, foram registradas {format_pt(impressoes, 0)} impressões, "
            f"{format_pt(cliques, 0)} cliques e {format_pt(conversoes, 0)} conversões. "
            "Os valores financeiros estão ocultos conforme a configuração de privacidade."
        )
    else:
        st.write(
            f"No período selecionado, as campanhas somaram {format_pt(impressoes, 0)} impressões, "
            f"{format_pt(cliques, 0)} cliques e {format_pt(conversoes, 0)} conversões, "
            f"com investimento total de R$ {format_pt(investimento)}."
        )

    st.markdown("###  Principais insights")
    for item in insights_exec:
        st.markdown(f"- {item}")

    st.markdown("###  Recomendações estratégicas")
    for item in recomendacoes_exec:
        st.markdown(f" {item}")


# ---------------------------------------------------------------
# Geração do relatório executivo completo em PDF
# ---------------------------------------------------------------
def gerar_relatorio_pdf():

    buffer = io.BytesIO()

    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm
    )

    estilos = getSampleStyleSheet()

    estilos.add(ParagraphStyle(
        name="TituloMarketing",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=26,
        textColor=colors.HexColor("#17365D"),
        spaceAfter=12
    ))

    estilos.add(ParagraphStyle(
        name="SecaoMarketing",
        parent=estilos["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#17365D"),
        spaceBefore=12,
        spaceAfter=7
    ))

    estilos.add(ParagraphStyle(
        name="TextoMarketing",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6
    ))

    estilos.add(ParagraphStyle(
        name="CelulaMarketing",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155")
    ))

    estilos.add(ParagraphStyle(
        name="CabecalhoMarketing",
        parent=estilos["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    ))

    elementos = []

    # -----------------------------------------------------------
    # Dados do período filtrado
    # -----------------------------------------------------------
    total_impressoes = df["impressions"].sum()
    total_cliques = df["clicks"].sum()
    total_conversoes = df["conversions"].sum()
    total_investimento = df["cost"].sum()

    ctr_pdf = (
        total_cliques / total_impressoes * 100
        if total_impressoes else 0
    )

    taxa_conv_pdf = (
        total_conversoes / total_cliques * 100
        if total_cliques else 0
    )

    cpc_pdf = (
        total_investimento / total_cliques
        if total_cliques else 0
    )

    cpa_pdf = (
        total_investimento / total_conversoes
        if total_conversoes else 0
    )

    tem_receita = "revenue" in df.columns
    receita_pdf = df["revenue"].sum() if tem_receita else 0

    roas_pdf = (
        receita_pdf / total_investimento
        if total_investimento > 0 else 0
    )

    roi_pdf = (
        ((receita_pdf - total_investimento) / total_investimento) * 100
        if total_investimento > 0 else 0
    )

    inicio = min(df["date"]) if not df.empty else None
    fim = max(df["date"]) if not df.empty else None
    inicio_formatado = inicio.strftime("%d/%m/%Y") if inicio else "-"
    fim_formatado = fim.strftime("%d/%m/%Y") if fim else "-"

    # Tabela de campanhas com valores numéricos originais
    ranking_pdf = (
        df.groupby("campaign")
        .agg({
            "clicks": "sum",
            "conversions": "sum",
            "cost": "sum"
        })
        .reset_index()
    )

    ranking_pdf["cpa"] = (
        ranking_pdf["cost"] /
        ranking_pdf["conversions"].where(
            ranking_pdf["conversions"] > 0
        )
    ).fillna(0)

    ranking_pdf = ranking_pdf.sort_values(
        "conversions",
        ascending=False
    )

    # Função auxiliar para textos
    def paragrafo(texto):
        return Paragraph(
            escape(str(texto)),
            estilos["TextoMarketing"]
        )

    def secao(titulo):
        elementos.append(
            Paragraph(titulo, estilos["SecaoMarketing"])
        )

    # -----------------------------------------------------------
    # CAPA
    # -----------------------------------------------------------
    # Logo oficial: manter logo.png na mesma pasta deste app.py.
    caminho_logo = Path(__file__).with_name("logo.png")
    if caminho_logo.exists():
        logo_pdf = RLImage(str(caminho_logo), width=7.0 * cm, height=1.97 * cm)
        logo_pdf.hAlign = "CENTER"
        elementos.append(logo_pdf)
        elementos.append(Spacer(1, 0.6 * cm))
    else:
        elementos.append(Spacer(1, 2 * cm))

    elementos.append(Paragraph(
        "DASHBOARD EXECUTIVO<br/>DE MARKETING DIGITAL",
        estilos["TituloMarketing"]
    ))

    elementos.append(Paragraph(
        "Análise executiva das campanhas digitais",
        estilos["Heading3"]
    ))

    elementos.append(Spacer(1, 1.5 * cm))

    estilo_rotulo_capa = ParagraphStyle(
        name="RotuloCapaMarketing",
        parent=estilos["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )
    estilo_valor_capa = ParagraphStyle(
        name="ValorCapaMarketing",
        parent=estilos["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155")
    )

    dados_capa_brutos = [
        ("Período analisado", f"{inicio_formatado} a {fim_formatado}"),
        ("Data de emissão", datetime.now().strftime("%d/%m/%Y")),
        ("Responsável", "Agta Pereira"),
        ("Site", "agtapereira.com.br"),
        ("Tecnologias", "Python + Streamlit + Plotly"),
        ("Origem dos dados", "Base demonstrativa; sem conexão direta com plataformas de anúncios")
    ]
    dados_capa = [
        [Paragraph(escape(rotulo), estilo_rotulo_capa),
         Paragraph(escape(valor), estilo_valor_capa)]
        for rotulo, valor in dados_capa_brutos
    ]

    tabela_capa = Table(
        dados_capa,
        colWidths=[4.2 * cm, 13.2 * cm],
        hAlign="LEFT"
    )

    tabela_capa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elementos.append(tabela_capa)
    elementos.append(Spacer(1, 1 * cm))

    # -----------------------------------------------------------
    # 1. RESUMO EXECUTIVO
    # -----------------------------------------------------------
    secao("1. RESUMO EXECUTIVO")

    elementos.append(paragrafo(
        f"No período analisado, as campanhas registraram "
        f"{format_pt(total_impressoes, 0)} impressões, "
        f"{format_pt(total_cliques, 0)} cliques e "
        f"{format_pt(total_conversoes, 0)} conversões, "
        f"com investimento total de "
        f"{'valor oculto' if hide_sensitive else 'R$ ' + format_pt(total_investimento)}."
    ))

    dados_kpi = [
        ["INDICADOR", "RESULTADO", "INDICADOR", "RESULTADO"],
        ["Impressões", format_pt(total_impressoes, 0),
         "Cliques", format_pt(total_cliques, 0)],
        ["Conversões", format_pt(total_conversoes, 0),
         "Investimento",
         "Oculto" if hide_sensitive else "R$ " + format_pt(total_investimento)],
        ["CTR", format_pt(ctr_pdf) + "%",
         "Taxa de conversão", format_pt(taxa_conv_pdf) + "%"],
        ["CPC médio",
         "Oculto" if hide_sensitive else "R$ " + format_pt(cpc_pdf),
         "CPA médio",
         "Oculto" if hide_sensitive else "R$ " + format_pt(cpa_pdf)]
    ]

    tabela_kpi = Table(
        dados_kpi,
        colWidths=[3.3 * cm, 4.4 * cm, 3.3 * cm, 4.4 * cm]
    )

    tabela_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1F5F9")]),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elementos.append(tabela_kpi)

    secao("Síntese executiva")

    for item in insights_exec:
        elementos.append(paragrafo("• " + item))

    # -----------------------------------------------------------
    # 2. METODOLOGIA E QUALIDADE DOS DADOS
    # -----------------------------------------------------------
    texto_metodologia_intro = paragrafo(
        "Este é um projeto demonstrativo, desenvolvido como modelo de uma solução "
        "aplicável a cenários reais. A versão utiliza uma base de demonstração e não "
        "possui integração direta com contas do Google Ads, Meta Ads ou outras plataformas. "
        "Os indicadores são calculados a partir dos registros disponíveis na base carregada."
    )

    dados_metodologia_brutos = [
        ("INDICADOR", "CRITÉRIO UTILIZADO"),
        ("CTR", "Cliques ÷ impressões × 100"),
        ("Taxa de conversão", "Conversões ÷ cliques × 100"),
        ("CPC médio", "Investimento ÷ cliques"),
        ("CPA médio", "Investimento em mídia ÷ conversões"),
        ("CAC simplificado (proxy)", "Investimento em mídia ÷ conversões; coincide com o CPA quando conversões são usadas como aproximação de clientes"),
        ("CAC estimado", "(Investimento em mídia + custos comerciais disponíveis) ÷ novos clientes; requer a coluna new_customers"),
        ("ROAS", "Receita atribuída ÷ investimento"),
        ("ROI simplificado", "(Receita - investimento) ÷ investimento × 100")
    ]
    dados_metodologia = []
    for indice, (indicador, criterio) in enumerate(dados_metodologia_brutos):
        estilo_celula = estilos["CabecalhoMarketing"] if indice == 0 else estilos["CelulaMarketing"]
        dados_metodologia.append([
            Paragraph(escape(indicador), estilo_celula),
            Paragraph(escape(criterio), estilo_celula)
        ])

    tabela_metodologia = Table(
        dados_metodologia,
        colWidths=[5.0 * cm, 12.0 * cm],
        repeatRows=1,
        hAlign="LEFT"
    )

    tabela_metodologia.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1F5F9")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elementos.append(KeepTogether([
        Paragraph("2. METODOLOGIA E QUALIDADE DOS DADOS", estilos["SecaoMarketing"]),
        texto_metodologia_intro,
        tabela_metodologia
    ]))

    secao("Limitações identificadas")

    limitacoes = [
        "Alcance único não está disponível; impressões não representam pessoas únicas.",
        "A base atual não contém novos clientes nem custos comerciais; por isso, não permite calcular o CAC estimado. O CAC simplificado usa conversões como proxy e coincide com o CPA.",
        "Não há histórico completo para comparação com períodos anteriores.",
        "Não há dados de margem, custos operacionais ou impostos.",
        "A qualidade das conversões deve ser validada com CRM ou plataforma de vendas."
    ]

    if not tem_receita or receita_pdf <= 0:
        limitacoes.append(
            "Não há receita positiva atribuída às campanhas; ROAS e ROI "
            "não podem ser avaliados de forma confiável."
        )

    for item in limitacoes:
        elementos.append(paragrafo("• " + item))

    # -----------------------------------------------------------
    # 3. ANÁLISE DE NEGÓCIO
    # -----------------------------------------------------------
    secao("3. ANÁLISE DE NEGÓCIO")

    perguntas = [
        (
            "Pergunta 1 - Estamos tendo resultados com o marketing?",
            f"Foram registradas {format_pt(total_impressoes, 0)} impressões, "
            f"{format_pt(total_cliques, 0)} cliques e "
            f"{format_pt(total_conversoes, 0)} conversões. "
            "É necessário validar se as conversões representam clientes ou vendas reais."
        ),
        (
            "Pergunta 2 - Onde estamos investindo nosso dinheiro?",
            "A distribuição do investimento por campanha está apresentada "
            "na seção de desempenho por campanha. O valor investido deve ser "
            "analisado em conjunto com conversões, CPA e qualidade dos resultados."
        ),
        (
            "Pergunta 3 - Quais campanhas apresentam melhor desempenho?",
            "A comparação considera volume de conversões e custo por aquisição. "
            "A campanha com maior volume não é necessariamente a mais eficiente."
        ),
        (
            "Pergunta 4 - Estamos atraindo clientes com eficiência?",
            f"O CPC médio calculado foi de "
            f"{'oculto' if hide_sensitive else 'R$ ' + format_pt(cpc_pdf)} "
            f"e a taxa de conversão foi de {format_pt(taxa_conv_pdf)}%. "
            "Esses números não comprovam, isoladamente, a aquisição de clientes pagantes."
        ),
        (
            "Pergunta 5 - O marketing está trazendo retorno financeiro?",
            (
                f"O ROAS calculado foi de {format_pt(roas_pdf)} e o ROI simplificado "
                f"foi de {format_pt(roi_pdf)}%."
                if tem_receita and receita_pdf > 0 and not hide_sensitive
                else "Não há dados suficientes de receita atribuída para calcular "
                     "o retorno financeiro de forma confiável."
            )
        )
    ]

    for pergunta, resposta in perguntas:
        elementos.append(Paragraph(
            escape(pergunta),
            estilos["Heading3"]
        ))
        elementos.append(paragrafo(resposta))

    # -----------------------------------------------------------
    # 4. DESEMPENHO POR CAMPANHA
    # -----------------------------------------------------------
    texto_desempenho_intro = paragrafo(
        "A tabela reúne os resultados das campanhas presentes no período selecionado."
    )

    dados_campanhas = [[
        "CAMPANHA", "CLIQUES", "CONVERSÕES", "CPA", "INVESTIMENTO"
    ]]

    for _, linha in ranking_pdf.iterrows():
        dados_campanhas.append([
            Paragraph(escape(str(linha["campaign"])), estilos["CelulaMarketing"]),
            Paragraph(format_pt(linha["clicks"], 0), estilos["CelulaMarketing"]),
            Paragraph(format_pt(linha["conversions"], 0), estilos["CelulaMarketing"]),
            Paragraph("Oculto" if hide_sensitive else "R$ " + format_pt(linha["cpa"]), estilos["CelulaMarketing"]),
            Paragraph("Oculto" if hide_sensitive else "R$ " + format_pt(linha["cost"]), estilos["CelulaMarketing"])
        ])

    if len(dados_campanhas) == 1:
        dados_campanhas.append(["Sem campanhas", "-", "-", "-", "-"])

    tabela_campanhas = Table(
        dados_campanhas,
        colWidths=[
            4.2 * cm, 2.2 * cm, 2.4 * cm, 3.2 * cm, 5.0 * cm
        ],
        repeatRows=1
    )

    tabela_campanhas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1F5F9")]),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elementos.append(KeepTogether([
        Paragraph("4. DESEMPENHO POR CAMPANHA", estilos["SecaoMarketing"]),
        texto_desempenho_intro,
        tabela_campanhas
    ]))

    if not ranking_pdf.empty:
        campanhas_com_conv = ranking_pdf[
            ranking_pdf["conversions"] > 0
        ]

        if not campanhas_com_conv.empty:
            maior_volume = campanhas_com_conv.loc[
                campanhas_com_conv["conversions"].idxmax()
            ]
            menor_cpa = campanhas_com_conv.loc[
                campanhas_com_conv["cpa"].idxmin()
            ]

            if maior_volume["campaign"] != menor_cpa["campaign"]:
                valor_menor_cpa = (
                    "valor oculto" if hide_sensitive
                    else "R$ " + format_pt(menor_cpa["cpa"])
                )
                elementos.append(paragrafo(
                    f"Embora {maior_volume['campaign']} tenha apresentado o maior volume "
                    f"de conversões ({format_pt(maior_volume['conversions'], 0)}), "
                    f"{menor_cpa['campaign']} registrou o menor CPA do período, no valor "
                    f"de {valor_menor_cpa}, indicando potencial eficiência na aquisição."
                ))
            else:
                elementos.append(paragrafo(
                    f"{maior_volume['campaign']} apresentou simultaneamente o maior volume "
                    f"de conversões ({format_pt(maior_volume['conversions'], 0)}) e o menor "
                    f"CPA do período ({'valor oculto' if hide_sensitive else 'R$ ' + format_pt(menor_cpa['cpa'])})."
                ))

    # -----------------------------------------------------------
    # 5. RETORNO FINANCEIRO E OPORTUNIDADES
    # -----------------------------------------------------------
    secao("5. RETORNO FINANCEIRO E OPORTUNIDADES")

    elementos.append(paragrafo(
        f"Investimento em mídia: "
        f"{'valor oculto' if hide_sensitive else 'R$ ' + format_pt(total_investimento)}."
    ))

    if tem_receita and receita_pdf > 0:
        elementos.append(paragrafo(
            f"Receita registrada: "
            f"{'valor oculto' if hide_sensitive else 'R$ ' + format_pt(receita_pdf)}."
        ))

        if not hide_sensitive:
            elementos.append(paragrafo(
                f"ROAS: {format_pt(roas_pdf)}. "
                f"ROI simplificado: {format_pt(roi_pdf)}%."
            ))

        elementos.append(paragrafo(
            "Os indicadores devem ser interpretados considerando margens, "
            "impostos e demais custos da empresa."
        ))
    else:
        elementos.append(paragrafo(
            "A base não apresenta receita positiva atribuída às campanhas. "
            "Por isso, ROAS e ROI não podem ser calculados com confiabilidade."
        ))

    secao("Oportunidades identificadas")

    for item in recomendacoes_exec:
        elementos.append(paragrafo("• " + item))

    # -----------------------------------------------------------
    # 6. PLANO DE AÇÃO
    # -----------------------------------------------------------
    secao("6. PLANO DE AÇÃO")

    elementos.append(paragrafo(
        "As ações abaixo são propostas com base nos indicadores disponíveis. "
        "Responsáveis e prazos devem ser definidos pela empresa."
    ))

    acoes = [
        ("ALTA",
         "Validar o rastreamento das conversões com CRM ou sistema de vendas e definir o que caracteriza uma conversão qualificada."),
        ("ALTA",
         "Analisar as campanhas com maior CPA e investigar investimento, público, criativos e página de destino."),
        ("ALTA",
         "Incluir receita atribuída por campanha caso seja necessária a análise de ROAS e retorno financeiro."),
        ("MÉDIA",
         "Comparar volume, CTR, taxa de conversão e CPA entre campanhas antes de redistribuir o orçamento."),
        ("MÉDIA",
         "Acompanhar periodicamente os indicadores e registrar as alterações realizadas."),
        ("BAIXA",
         "Documentar a origem dos dados, o período analisado e as regras de atribuição.")
    ]

    dados_acoes = [[
        Paragraph("PRIORIDADE", estilos["CabecalhoMarketing"]),
        Paragraph("AÇÃO PROPOSTA", estilos["CabecalhoMarketing"])
    ]]

    for prioridade, acao in acoes:
        dados_acoes.append([
            Paragraph(escape(prioridade), estilos["CelulaMarketing"]),
            Paragraph(escape(acao), estilos["CelulaMarketing"])
        ])

    tabela_acoes = Table(
        dados_acoes,
        colWidths=[2.8 * cm, 13.2 * cm],
        repeatRows=1,
        hAlign="LEFT"
    )

    tabela_acoes.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F1F5F9")]),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elementos.append(tabela_acoes)

    secao("Critério de acompanhamento")

    elementos.append(paragrafo(
        "Em cada revisão, comparar os indicadores com o período anterior "
        "equivalente, registrar alterações realizadas e verificar se houve "
        "impacto em conversões qualificadas, CPA e receita atribuída."
    ))

    # -----------------------------------------------------------
    # 7. CONCLUSÃO EXECUTIVA
    # -----------------------------------------------------------
    secao("7. CONCLUSÃO EXECUTIVA")

    elementos.append(Paragraph(
        "O que funcionou",
        estilos["Heading3"]
    ))

    conclusoes_positivas = [
        f"As campanhas geraram {format_pt(total_cliques, 0)} cliques "
        f"e {format_pt(total_conversoes, 0)} conversões registradas."
    ]

    for item in conclusoes_positivas:
        elementos.append(paragrafo("• " + item))

    elementos.append(Paragraph(
        "O que precisa melhorar",
        estilos["Heading3"]
    ))

    for item in recomendacoes_exec[:3]:
        elementos.append(paragrafo("• " + item))

    elementos.append(Paragraph(
        "Próximos passos",
        estilos["Heading3"]
    ))

    proximos_passos = [
        "Validar os dados com CRM e plataforma de vendas.",
        "Executar as ações de alta prioridade do plano de ação.",
        "Revisar semanalmente os indicadores e documentar as decisões."
    ]

    for item in proximos_passos:
        elementos.append(paragrafo("• " + item))

    elementos.append(paragrafo(
        "Conclusão: os dados demonstram geração de tráfego e conversões. "
        "As decisões de investimento devem considerar também a qualidade "
        "das conversões e o retorno comercial."
    ))

    # -----------------------------------------------------------
    # 8. CONSIDERAÇÕES FINAIS
    # -----------------------------------------------------------
    secao("8. CONSIDERAÇÕES FINAIS")

    elementos.append(paragrafo(
        "Este relatório apresenta uma análise descritiva dos dados disponíveis "
        "na base utilizada pelo dashboard, considerando os filtros selecionados. "
        "A inclusão de receita atribuída, histórico comparativo e dados de vendas "
        "permitirá análises mais completas e decisões de investimento mais seguras."
    ))

    elementos.append(Spacer(1, 12))

    elementos.append(paragrafo(
        "Os resultados devem ser interpretados considerando as limitações "
        "registradas neste documento. As recomendações são indicativas e "
        "devem ser avaliadas conforme a realidade do negócio."
    ))

    # Numeração das páginas
    def numerar_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawRightString(
            A4[0] - 1.7 * cm,
            0.8 * cm,
            f"Página {doc.page}"
        )
        canvas.restoreState()

    documento.build(
        elementos,
        onFirstPage=numerar_pagina,
        onLaterPages=numerar_pagina
    )

    buffer.seek(0)
    return buffer.getvalue()

nome_pdf = "relatorio_executivo_marketing.pdf"
st.download_button(
    label=" Baixar Relatório Executivo em PDF",
    data=gerar_relatorio_pdf(),
    file_name=nome_pdf,
    mime="application/pdf",
    use_container_width=True,
)


# ---------------------------------------------------------------
# Dados completos (expander)
# ---------------------------------------------------------------
with st.expander(" Visualizar dados completos"):

    if hide_sensitive:
        st.write("Valores sensíveis foram ocultados.")

    else:
        # Cria uma cópia para exibição em português
        df_exibicao = df.rename(columns={
            "date": "Data",
            "campaign": "Campanha",
            "impressions": "Impressões",
            "clicks": "Cliques",
            "conversions": "Conversões",
            "cost": "Investimento",
            "revenue": "Receita",
            "new_customers": "Novos clientes",
            "sales_cost": "Custos comerciais"
        })

        st.dataframe(
            df_exibicao,
            use_container_width=True,
            hide_index=True
        )



# ---------------------------------------------------------------
# Assinatura e créditos do projeto
# ---------------------------------------------------------------
st.divider()
st.markdown(
    "<div style='text-align:center;color:#94a3b8;font-size:12px;padding:14px 0;'>"
    "<strong style='color:#e2e8f0;'>Desenvolvido por Agta Pereira</strong>"
    " &nbsp;|&nbsp; Python + Streamlit + Plotly"
    "</div>",
    unsafe_allow_html=True,
)
