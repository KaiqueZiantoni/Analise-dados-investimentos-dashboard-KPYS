import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv

st.set_page_config(page_title="Gestão de Fundos", layout="wide", page_icon="📈")

WARREN_PINK = '#EE2E5D'
WARREN_GREEN = '#10C073'
BG_TRANSPARENT = 'rgba(0,0,0,0)'

def aplicar_tema_warren(fig):
    fig.update_layout(
        plot_bgcolor=BG_TRANSPARENT,
        paper_bgcolor=BG_TRANSPARENT,
        font=dict(color='#FFFFFF', size=14),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, title=""),
        yaxis=dict(showgrid=True, gridcolor='#333333', zeroline=False, title="")
    )
    return fig

load_dotenv()

@st.cache_resource 
def get_connection():
    USER = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    HOST = os.getenv('DB_HOST')
    PORT = os.getenv('DB_PORT')
    DB_NAME = os.getenv('DB_NAME')
    return create_engine(f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}')

engine = get_connection()

st.title("Portfólio de Investimentos")
st.markdown("Visão gerencial de fundos com dados processados em tempo real via PostgreSQL.")
st.divider()

with engine.connect() as conn:
    df_nomes = pd.read_sql('SELECT DISTINCT "nome_fundo" FROM kpi_aum_total', con=conn)

st.sidebar.image('logo_warren.png', use_container_width=True)
st.sidebar.header("Filtros de Análise")
fundo_selecionado = st.sidebar.selectbox("Selecione o Fundo", df_nomes['nome_fundo'])

with engine.connect() as conn:
    query_aum = text('SELECT * FROM kpi_aum_total WHERE "nome_fundo" = :fundo ORDER BY "Mes_Ref"')
    df_aum = pd.read_sql(query_aum, con=conn, params={"fundo": fundo_selecionado})
    
    query_cnpj = text('SELECT "cnpj_do_fundo" FROM kpi_aum_total WHERE "nome_fundo" = :fundo LIMIT 1')
    cnpj_fundo = pd.read_sql(query_cnpj, con=conn, params={"fundo": fundo_selecionado}).iloc[0, 0]
    
    mes_max = df_aum['Mes_Ref'].max()

st.subheader(f"Resumo: {fundo_selecionado}")

if not df_aum.empty:
    aum_atual = df_aum.iloc[-1]['AUM_Total']
    aum_anterior = df_aum.iloc[-2]['AUM_Total'] if len(df_aum) > 1 else aum_atual
    variacao_aum = ((aum_atual / aum_anterior) - 1) * 100 if aum_anterior > 0 else 0
else:
    aum_atual = 0
    variacao_aum = 0

with engine.connect() as conn:
    query_cap = text('SELECT "Captação_Liquida" FROM kpi_captacao_mensal WHERE "cnpj_do_fundo" = :cnpj ORDER BY "Mes_Ref" DESC LIMIT 1')
    res_cap = pd.read_sql(query_cap, con=conn, params={"cnpj": cnpj_fundo})
    captacao_atual = res_cap.iloc[0, 0] if not res_cap.empty else 0

def formatar_valor_curto(valor):
    if abs(valor) >= 1e9:
        return f"R$ {valor/1e9:.2f}B"
    elif abs(valor) >= 1e6:
        return f"R$ {valor/1e6:.2f}M"
    else:
        return f"R$ {valor:,.2f}"

col_m1, col_m2, col_m3 = st.columns(3)

with col_m1:
    st.metric(
        label="Patrimônio Líquido (AUM Atual)", 
        value=formatar_valor_curto(aum_atual), 
        delta=f"{variacao_aum:.2f}% (Último Mês)"
    )

with col_m2:
    st.metric(
        label="Captação Líquida (Último Mês)", 
        value=formatar_valor_curto(captacao_atual),
        delta="Fluxo Positivo" if captacao_atual > 0 else "- Fluxo Negativo",
        delta_color="normal" 
    )

with col_m3:
    st.metric(
        label="Status do Fundo", 
        value="Ativo",
    )

st.divider()

st.subheader("1. Evolução do Patrimônio Líquido (AUM)")
st.markdown("<p style='font-size: 13px; color: #AAAAAA;'>Comparação entre aportes e resgates</p>", unsafe_allow_html=True)

fig_aum = px.area(df_aum, x='Mes_Ref', y='AUM_Total', markers=True)

fig_aum.update_traces(
    line_color=WARREN_PINK, 
    fillcolor='rgba(238, 46, 93, 0.15)',
    hovertemplate='<b>Mês:</b> %{x}<br><b>Patrimônio:</b> R$ %{y:,.2f}<extra></extra>'
)

fig_aum = aplicar_tema_warren(fig_aum)
fig_aum.update_layout(yaxis_tickformat="R$ ,.0f", hovermode="x unified")
st.plotly_chart(fig_aum, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("2. Fluxo de Caixa (Captação Líquida)")

    st.markdown("<p style='font-size: 13px; color: #AAAAAA;'>Representa o tamanho total do fundo sob gestão em um determinado momento</p>", unsafe_allow_html=True)

    with engine.connect() as conn:
        query_fluxo = text('SELECT * FROM kpi_captacao_mensal WHERE "cnpj_do_fundo" = :cnpj ORDER BY "Mes_Ref"')
        df_fluxo = pd.read_sql(query_fluxo, con=conn, params={"cnpj": cnpj_fundo})

    cores = [WARREN_GREEN if val > 0 else WARREN_PINK for val in df_fluxo['Captação_Liquida']]
    fig_fluxo = px.bar(df_fluxo, x='Mes_Ref', y='Captação_Liquida', text='Captação_Liquida')
    
    fig_fluxo.update_traces(
        marker_color=cores,
        texttemplate='R$ %{text:,.2s}',
        textposition='outside',
        hovertemplate='<b>Mês:</b> %{x}<br><b>Fluxo:</b> R$ %{y:,.2f}<extra></extra>'
    )
    
    fig_fluxo = aplicar_tema_warren(fig_fluxo)
    fig_fluxo.update_layout(margin=dict(t=30))
    st.plotly_chart(fig_fluxo, use_container_width=True)

with col2:
    st.subheader("3. Exposição por Mercado Ativo")

    st.markdown("<p style='font-size: 13px; color: #AAAAAA;'>Grafico responsável por informar como o patrimônio está distribuido</p>", unsafe_allow_html=True)

    with engine.connect() as conn:
        query_exp = text('SELECT * FROM kpi_exposicao_classe WHERE "cnpj_do_fundo" = :cnpj AND "Mes_Ref" = :mes')
        df_exp = pd.read_sql(query_exp, con=conn, params={"cnpj": cnpj_fundo, "mes": mes_max})
    
    coluna_fatia = 'mercado_ativo_investido' if 'mercado_ativo_investido' in df_exp.columns else 'classe_do_fundo'
    
    fig_pie = px.pie(df_exp, values='Percentual_Exposicao', names=coluna_fatia, hole=0.6)
    
    fig_pie.update_traces(
        textposition='inside', 
        textinfo='percent+label', 
        marker=dict(colors=['#10C073', '#EE2E5D', '#4A4A4A', '#FFFFFF']),
        hovertemplate='<b>%{label}</b><br>Exposição: %{percent}<extra></extra>'
    )
    
    fig_pie.update_layout(
        showlegend=False, 
        plot_bgcolor=BG_TRANSPARENT, 
        paper_bgcolor=BG_TRANSPARENT, 
        font=dict(color='#FFFFFF'), 
        margin=dict(t=10, b=10)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

col3, col4 = st.columns(2)

with col3:
    st.subheader("4. Risco: Concentração (Top 5)")
    
    st.markdown("<p style='font-size: 13px; color: #AAAAAA;'>Se o ponteiro estiver no vermelho, o fundo depende demais de apenas 5 investimentos. Se um deles quebrar, o fundo sofre muito.</p>", unsafe_allow_html=True)
    
    with engine.connect() as conn:
        query_risk = text('SELECT * FROM kpi_risco_concentracao WHERE "cnpj_do_fundo" = :cnpj AND "Mes_Ref" = :mes')
        df_risk = pd.read_sql(query_risk, con=conn, params={"cnpj": cnpj_fundo, "mes": mes_max})
    
    concentracao = df_risk['Concentracao_Top5_%'].iloc[0] if not df_risk.empty else 0
    
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = concentracao,
        number = {'suffix': "%", 'font': {'color': 'white', 'size': 45}},
        gauge = {
            'axis': {
                'range': [0, 100], 
                'tickvals': [0, 100], 
                'ticktext': ['Seguro', 'Perigo'], 
                'tickfont': {'size': 16, 'color': 'white', 'family': 'Arial Black'}
            },
            'bar': {'color': 'white', 'thickness': 0.15},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 40], 'color': '#10C073'},
                {'range': [40, 70], 'color': '#F39C12'},
                {'range': [70, 100], 'color': '#EE2E5D'}
            ],
        }
    ))
    
    fig_gauge.update_layout(
        paper_bgcolor=BG_TRANSPARENT, 
        font={'color': 'white'}, 
        height=260,
        margin=dict(t=20, b=10, l=30, r=30)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col4:
    st.subheader("5. Top 3 Alternativas")
    
    st.markdown("<p style='font-size: 13px; color: #AAAAAA;'>Opções de diversificação com os maiores ganhos acumulados nos últimos meses.</p>", unsafe_allow_html=True)
    
    with engine.connect() as conn:
        df_top3 = pd.read_sql("SELECT * FROM kpi_top3_recomendados", con=conn)

    df_top3 = df_top3.sort_values(by='Rentabilidade_Media_3M_%', ascending=False).head(3).reset_index(drop=True)
    
    medalhas = ['🥇 1º', '🥈 2º', '🥉 3º']
    df_top3['Fundo_Com_Medalha'] = [f"{medalhas[i]} - {nome}" for i, nome in enumerate(df_top3['nome_fundo'][:len(medalhas)])]
    
    df_top3 = df_top3.sort_values(by='Rentabilidade_Media_3M_%', ascending=True)

    fig_rank = px.bar(
        df_top3, 
        x='Rentabilidade_Media_3M_%', 
        y='Fundo_Com_Medalha', 
        orientation='h', 
        text='Rentabilidade_Media_3M_%'
    )
    
    cores_podio = [WARREN_GREEN, WARREN_GREEN, WARREN_GREEN] 
    
    fig_rank.update_traces(
        marker_color=cores_podio[:len(df_top3)],
        texttemplate='<b>+%{text:.2f}%</b>',
        textposition='outside',
        hovertemplate='<b>%{y}</b><br><b>Ganho de:</b> +%{x:.2f}%<extra></extra>'
    )
    
    fig_rank = aplicar_tema_warren(fig_rank)
    fig_rank.update_layout(
        yaxis_title="", 
        xaxis_title="", 
        xaxis_showticklabels=False, 
        height=260,
        margin=dict(l=10, r=60, t=20, b=10)
    )
    st.plotly_chart(fig_rank, use_container_width=True)