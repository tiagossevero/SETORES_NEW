# ============================================================
# COLE ESTE CÓDIGO NO INÍCIO DE CADA ARQUIVO .PY
# ============================================================

import streamlit as st
import hashlib

# DEFINA A SENHA AQUI
SENHA = "tsevero852"  # ← TROQUE para cada projeto

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("<div style='text-align: center; padding: 50px;'><h1>🔐 Acesso Restrito</h1></div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            senha_input = st.text_input("Digite a senha:", type="password", key="pwd_input")
            if st.button("Entrar", use_container_width=True):
                if senha_input == SENHA:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Senha incorreta")
        st.stop()

check_password()

"""
Sistema SETORES - Análise Tributária Setorial v4.0
Receita Estadual de Santa Catarina
Dashboard interativo para análise de comportamento tributário por setor
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
import warnings
import ssl

# =============================================================================
# 1. CONFIGURAÇÕES INICIAIS
# =============================================================================

# Hack SSL
try:
    createunverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = createunverified_https_context

warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="ARGOS Setores - Análise Tributária",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com estilos para tooltips e melhorias de UX
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }

    /* ESTILO DOS KPIs - BORDA PRETA */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 2px solid #2c3e50;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }

    /* Título do métrica */
    div[data-testid="stMetric"] > label {
        font-weight: 600;
        color: #2c3e50;
    }

    /* Valor do métrica */
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: bold;
        color: #1f77b4;
    }

    /* Delta (variação) */
    div[data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }

    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }

    .alert-critico {
        background-color: #ffebee;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #d32f2f;
    }

    .alert-alto {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f57c00;
    }

    /* Estilos para tooltips customizados */
    .tooltip-container {
        position: relative;
        display: inline-block;
    }

    .tooltip-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        background-color: #e3f2fd;
        color: #1976d2;
        border-radius: 50%;
        font-size: 12px;
        font-weight: bold;
        cursor: help;
        margin-left: 5px;
        border: 1px solid #1976d2;
        transition: all 0.2s ease;
    }

    .tooltip-icon:hover {
        background-color: #1976d2;
        color: white;
    }

    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
        transition: all 0.3s ease;
    }

    .kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }

    .kpi-title {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 5px;
    }

    .kpi-help {
        font-size: 0.75rem;
        color: #888;
        font-style: italic;
        line-height: 1.3;
        padding: 8px;
        background-color: #f5f5f5;
        border-radius: 6px;
        margin-top: 8px;
    }

    .kpi-delta-positive {
        color: #2e7d32;
        font-size: 0.9rem;
    }

    .kpi-delta-negative {
        color: #c62828;
        font-size: 0.9rem;
    }

    /* Legenda de ajuda */
    .help-section {
        background-color: #e3f2fd;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        border-left: 4px solid #1976d2;
    }

    .help-section h4 {
        color: #1565c0;
        margin-bottom: 10px;
    }

    .help-item {
        display: flex;
        align-items: flex-start;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }

    .help-icon {
        margin-right: 8px;
        min-width: 20px;
    }

    /* Indicadores de status */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .status-critico { background-color: #ffcdd2; color: #c62828; }
    .status-alto { background-color: #ffe0b2; color: #e65100; }
    .status-medio { background-color: #fff9c4; color: #f9a825; }
    .status-baixo { background-color: #c8e6c9; color: #2e7d32; }
    .status-normal { background-color: #e8f5e9; color: #388e3c; }

    /* Expander customizado */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 2. CREDENCIAIS E CONEXÃO
# =============================================================================

IMPALA_HOST = 'bdaworkernode02.sef.sc.gov.br'
IMPALA_PORT = 21050
DATABASE = 'niat'

try:
    IMPALA_USER = st.secrets["impala_credentials"]["user"]
    IMPALA_PASSWORD = st.secrets["impala_credentials"]["password"]
except:
    st.error("⚠️ Credenciais não configuradas. Configure o arquivo secrets.toml")
    st.stop()

# =============================================================================
# 3. FUNÇÕES DE CARREGAMENTO - LAZY LOADING (OTIMIZADO)
# =============================================================================

@st.cache_resource
def get_engine():
    """Cria engine de conexão (cached como resource)."""
    try:
        engine = create_engine(
            f'impala://{IMPALA_HOST}:{IMPALA_PORT}/{DATABASE}',
            connect_args={
                'user': IMPALA_USER,
                'password': IMPALA_PASSWORD,
                'auth_mechanism': 'LDAP',
                'use_ssl': True
            }
        )
        return engine
    except Exception as e:
        st.error(f"❌ Erro de conexão: {str(e)[:100]}")
        return None

# -----------------------------------------------------------------------------
# FUNÇÕES AUXILIARES DE CACHE
# -----------------------------------------------------------------------------

@st.cache_data(ttl=14400, show_spinner=False)
def carregar_periodos_disponiveis(_engine):
    """Carrega lista de períodos disponíveis - cache longo (4h)."""
    try:
        query = f"""
            SELECT DISTINCT nu_per_ref 
            FROM {DATABASE}.argos_benchmark_setorial
            ORDER BY nu_per_ref DESC
        """
        df = pd.read_sql(query, _engine)
        return sorted(df['nu_per_ref'].tolist(), reverse=True)
    except:
        return []

@st.cache_data(ttl=14400, show_spinner=False)
def carregar_lista_setores(_engine):
    """Carrega lista de setores - cache longo."""
    try:
        query = f"""
            SELECT DISTINCT cnae_classe, desc_cnae_classe
            FROM {DATABASE}.argos_benchmark_setorial
            WHERE cnae_classe IS NOT NULL AND desc_cnae_classe IS NOT NULL
            ORDER BY desc_cnae_classe
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=14400, show_spinner=False)
def carregar_tipos_alerta(_engine):
    """Carrega tipos de alerta distintos."""
    try:
        query = f"SELECT DISTINCT tipo_alerta FROM {DATABASE}.argos_alertas_empresas WHERE tipo_alerta IS NOT NULL"
        df = pd.read_sql(query, _engine)
        return ['Todos'] + sorted(df['tipo_alerta'].tolist())
    except:
        return ['Todos']

# -----------------------------------------------------------------------------
# BENCHMARK SETORIAL
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_benchmark_setorial(_engine, periodo=None):
    """Carrega benchmark setorial por período."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_benchmark_setorial WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_benchmark_setorial"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except Exception as e:
        st.error(f"Erro benchmark setorial: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_benchmark_setorial_todos_periodos(_engine):
    """Carrega benchmark de todos os períodos (para evolução temporal)."""
    try:
        query = f"SELECT * FROM {DATABASE}.argos_benchmark_setorial ORDER BY nu_per_ref"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# BENCHMARK POR PORTE
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_benchmark_porte(_engine, periodo=None, cnae_classe=None):
    """Carrega benchmark por porte."""
    try:
        conditions = []
        if periodo:
            conditions.append(f"nu_per_ref = {periodo}")
        if cnae_classe:
            conditions.append(f"cnae_classe = '{cnae_classe}'")
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM {DATABASE}.argos_benchmark_setorial_porte {where_clause}"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# EMPRESAS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_empresas(_engine, periodo=None):
    """Carrega dados de empresas."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_empresas WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_empresas"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_empresas_resumo(_engine, periodo=None):
    """Carrega resumo agregado de empresas (leve)."""
    try:
        where = f"WHERE nu_per_ref = {periodo}" if periodo else ""
        query = f"""
            SELECT 
                nu_per_ref,
                porte_empresa,
                COUNT(DISTINCT nu_cnpj) as qtd_empresas,
                SUM(vl_faturamento) as faturamento_total,
                SUM(icms_devido) as icms_total,
                AVG(aliq_efetiva) as aliq_media
            FROM {DATABASE}.argos_empresas
            {where}
            GROUP BY nu_per_ref, porte_empresa
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# EMPRESA VS BENCHMARK
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_empresa_vs_benchmark(_engine, periodo=None):
    """Carrega comparação empresa vs benchmark."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_empresa_vs_benchmark WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_empresa_vs_benchmark"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False)
def buscar_empresa_por_cnpj(_engine, cnpj, periodo=None):
    """Busca empresa específica por CNPJ."""
    try:
        cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
        periodo_cond = f"AND nu_per_ref = {periodo}" if periodo else ""
        
        query = f"""
            SELECT * FROM {DATABASE}.argos_empresa_vs_benchmark
            WHERE REGEXP_REPLACE(CAST(nu_cnpj AS STRING), '[^0-9]', '') = '{cnpj_limpo}'
            {periodo_cond}
            ORDER BY nu_per_ref DESC
        """
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# EVOLUÇÃO TEMPORAL
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_evolucao_setor(_engine, cnae_classe=None):
    """Carrega evolução temporal de setores."""
    try:
        if cnae_classe:
            query = f"SELECT * FROM {DATABASE}.argos_evolucao_temporal_setor WHERE cnae_classe = '{cnae_classe}'"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_evolucao_temporal_setor"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_evolucao_empresa(_engine, cnpj=None):
    """Carrega evolução temporal de empresas."""
    try:
        if cnpj:
            cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
            query = f"""
                SELECT * FROM {DATABASE}.argos_evolucao_temporal_empresa
                WHERE REGEXP_REPLACE(CAST(nu_cnpj AS STRING), '[^0-9]', '') = '{cnpj_limpo}'
            """
        else:
            query = f"SELECT * FROM {DATABASE}.argos_evolucao_temporal_empresa"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# ALERTAS E ANOMALIAS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_alertas(_engine, periodo=None):
    """Carrega alertas de empresas."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_alertas_empresas WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_alertas_empresas"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_anomalias(_engine, periodo=None):
    """Carrega anomalias setoriais."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_anomalias_setoriais WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_anomalias_setoriais"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# -----------------------------------------------------------------------------
# PAGAMENTOS
# -----------------------------------------------------------------------------

@st.cache_data(ttl=7200, show_spinner=False)
def carregar_pagamentos(_engine, periodo=None):
    """Carrega dados de pagamentos."""
    try:
        if periodo:
            query = f"SELECT * FROM {DATABASE}.argos_pagamentos_empresa WHERE nu_per_ref = {periodo}"
        else:
            query = f"SELECT * FROM {DATABASE}.argos_pagamentos_empresa"
        df = pd.read_sql(query, _engine)
        df.columns = [col.lower() for col in df.columns]
        for col in df.select_dtypes(include=['object']).columns:
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        return df
    except:
        return pd.DataFrame()

# =============================================================================
# 4. FUNÇÕES AUXILIARES
# =============================================================================

def formatar_moeda(valor):
    """Formata valor em moeda brasileira."""
    if pd.isna(valor):
        return "R$ 0,00"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_percentual(valor):
    """Formata valor como percentual."""
    if pd.isna(valor):
        return "0,00%"
    return f"{valor*100:.2f}%".replace(".", ",")

def criar_grafico_evolucao(df, x_col, y_col, color_col=None, title=""):
    """Cria gráfico de linha temporal."""
    fig = px.line(
        df, x=x_col, y=y_col, color=color_col,
        title=title,
        labels={x_col: 'Período', y_col: 'Valor'}
    )
    fig.update_layout(hovermode='x unified', height=400)
    return fig

def criar_mapa_calor(df, index_col, columns_col, values_col, title=""):
    """Cria mapa de calor."""
    pivot = df.pivot_table(
        index=index_col, 
        columns=columns_col, 
        values=values_col
    )
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn_r',
        text=pivot.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10}
    ))
    fig.update_layout(title=title, height=600)
    return fig

def criar_gauge_aliquota(aliq_mediana, aliq_p25, aliq_p75):
    """Cria gráfico de velocímetro para alíquota."""
    aliq_mediana_pct = aliq_mediana * 100
    aliq_p25_pct = aliq_p25 * 100
    aliq_p75_pct = aliq_p75 * 100
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = aliq_mediana_pct,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Alíquota Mediana (%)"},
        delta = {'reference': (aliq_p25_pct + aliq_p75_pct) / 2},
        gauge = {
            'axis': {'range': [None, max(aliq_p75_pct * 1.2, 20)]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, aliq_p25_pct], 'color': "#e8f5e9"},
                {'range': [aliq_p25_pct, aliq_p75_pct], 'color': "#c8e6c9"},
                {'range': [aliq_p75_pct, max(aliq_p75_pct * 1.2, 20)], 'color': "#fff3e0"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': aliq_p75_pct
            }
        }
    ))
    
    fig.add_annotation(
        x=0.5, y=0.15,
        text=f"P25: {aliq_p25_pct:.2f}%",
        showarrow=False,
        font=dict(size=12)
    )
    
    fig.add_annotation(
        x=0.5, y=0.05,
        text=f"P75: {aliq_p75_pct:.2f}%",
        showarrow=False,
        font=dict(size=12)
    )
    
    fig.update_layout(height=300)
    return fig

def metric_with_tooltip(label, value, tooltip, delta=None, delta_color="normal"):
    """
    Exibe uma métrica com tooltip explicativo.

    Args:
        label: Título do KPI
        value: Valor a ser exibido
        tooltip: Texto explicativo do indicador
        delta: Valor de variação (opcional)
        delta_color: Cor do delta - "normal", "inverse", ou "off"
    """
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color,
              help=tooltip)

def render_kpi_card(icon, title, value, tooltip, color="#1f77b4"):
    """
    Renderiza um card KPI customizado com tooltip.

    Args:
        icon: Emoji ou ícone
        title: Título do KPI
        value: Valor formatado
        tooltip: Texto explicativo
        color: Cor do valor
    """
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{icon} {title}</div>
        <div class="kpi-value" style="color: {color};">{value}</div>
        <div class="kpi-help">{tooltip}</div>
    </div>
    """, unsafe_allow_html=True)

def render_help_section(title, items):
    """
    Renderiza uma seção de ajuda com explicações dos indicadores.

    Args:
        title: Título da seção
        items: Lista de tuplas (ícone, texto)
    """
    items_html = ""
    for icon, text in items:
        items_html += f'<div class="help-item"><span class="help-icon">{icon}</span>{text}</div>'

    st.markdown(f"""
    <div class="help-section">
        <h4>{title}</h4>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

# Dicionário centralizado de tooltips para reutilização
TOOLTIPS = {
    # Visão Geral
    "setores_monitorados": "Total de setores econômicos (CNAE) sendo monitorados no período. Cada setor representa um grupo de empresas com atividade econômica similar.",
    "empresas": "Quantidade total de empresas ativas no período selecionado, identificadas por CNPJ único.",
    "faturamento_total": "Soma do faturamento declarado por todas as empresas no período. Valores em bilhões de reais (B).",
    "aliquota_media": "Média ponderada das alíquotas efetivas de ICMS praticadas por todas as empresas. Indica a carga tributária média do estado.",

    # Análise Setorial
    "empresas_setor": "Número de empresas ativas no setor selecionado durante o período de referência.",
    "faturamento_setor": "Faturamento total declarado pelas empresas do setor. Valores em milhões (M) ou bilhões (B).",
    "aliquota_mediana": "Valor central das alíquotas efetivas do setor. 50% das empresas têm alíquota abaixo e 50% acima deste valor. Mais robusto que a média.",
    "coef_variacao": "Coeficiente de Variação - mede a dispersão das alíquotas no setor. Valores > 0.3 indicam alta heterogeneidade fiscal.",
    "categoria_volatilidade": "Classificação da estabilidade do setor: BAIXA (estável), MÉDIA (moderada) ou ALTA (instável).",
    "tendencia_aliquota": "Direção da variação da alíquota nos últimos períodos: CRESCENTE, ESTÁVEL ou DECRESCENTE.",
    "aliquota_media_8m": "Média da alíquota efetiva mediana nos últimos 8 meses. Útil para identificar padrões de longo prazo.",

    # Análise Empresarial
    "faturamento_empresa": "Valor total das vendas/receitas declaradas pela empresa no período.",
    "icms_devido": "Valor do ICMS calculado como devido pela empresa, baseado nas operações declaradas.",
    "aliquota_empresa": "Taxa efetiva de ICMS da empresa = (ICMS Devido / Faturamento) x 100. Indica a carga tributária real.",
    "aliquota_setor_ref": "Alíquota mediana do setor de atuação da empresa. Serve como referência para comparação.",
    "indice_vs_setor": "Relação entre alíquota da empresa e do setor. Valores < 1 indicam tributação abaixo do esperado.",
    "status_vs_setor": "Classificação comparativa: MUITO_ABAIXO (<50% da mediana), ABAIXO (50-80%), NORMAL (80-120%), ACIMA (>120%).",

    # Volatilidade
    "alta_volatilidade": "Empresas com Coeficiente de Variação > 0.5 nos últimos 8 meses. Alto risco de comportamento fiscal irregular.",
    "media_volatilidade": "Empresas com CV entre 0.2 e 0.5. Requerem monitoramento preventivo.",
    "baixa_volatilidade": "Empresas com CV < 0.2. Comportamento fiscal estável e previsível.",
    "cv_medio": "Média do Coeficiente de Variação de todas as empresas. Quanto maior, mais instável o universo fiscal.",

    # Alertas
    "total_alertas": "Quantidade total de situações anômalas identificadas pelo sistema no período.",
    "alertas_criticos": "Alertas de maior gravidade que requerem ação imediata. Score de risco > 80.",
    "alertas_altos": "Alertas importantes que devem ser priorizados. Score de risco entre 60-80.",
    "alertas_medios": "Alertas que requerem atenção mas não são urgentes. Score de risco entre 40-60.",
    "score_risco": "Pontuação de 0 a 100 que indica a probabilidade de irregularidade fiscal. Calculado com base em múltiplos fatores.",

    # Pagamentos
    "total_pago": "Soma de todos os pagamentos de ICMS realizados no período.",
    "qtd_pagamentos": "Número total de guias de pagamento processadas no período.",
    "empresas_pagantes": "Quantidade de empresas distintas que realizaram pelo menos um pagamento.",
    "ticket_medio": "Valor médio por pagamento = Total Pago / Quantidade de Pagamentos.",
    "divergencia_pagamento": "Diferença significativa (>30%) entre ICMS declarado como devido e valor efetivamente pago.",

    # Machine Learning
    "acuracia": "Percentual de previsões corretas do modelo. Quanto maior, melhor a performance geral.",
    "precisao": "Dos casos previstos como problemáticos, quantos realmente são. Evita falsos positivos.",
    "recall": "Dos casos realmente problemáticos, quantos foram identificados. Evita falsos negativos.",
    "f1_score": "Média harmônica entre Precisão e Recall. Melhor métrica para dados desbalanceados.",
    "prob_risco": "Probabilidade (0-100%) de uma empresa apresentar comportamento fiscal problemático.",

    # Evolução Temporal
    "periodos_analisados": "Quantidade de meses com dados disponíveis para o setor/empresa selecionado.",
    "desvio_padrao": "Medida de dispersão das alíquotas ao longo do tempo. Valores altos indicam instabilidade.",
    "amplitude": "Diferença entre a maior e menor alíquota observada no período. Mede a variação extrema.",
    "tendencia_percentual": "Variação percentual entre o primeiro e último período analisado."
}

# =============================================================================
# 5. INTERFACE PRINCIPAL (OTIMIZADA)
# =============================================================================

def main():
    # Header
    st.markdown('<p class="main-header">📊 ARGOS SETORES - Análise Tributária Setorial</p>', 
                unsafe_allow_html=True)
    st.markdown("**Receita Estadual de Santa Catarina** | Sistema de Análise v4.1 (Otimizado)")
    st.markdown("---")
    
    # Conectar ao banco (cached)
    engine = get_engine()
    
    if engine is None:
        st.error("❌ Não foi possível conectar ao banco de dados. Verifique as credenciais.")
        return
    
    # Carregar apenas períodos (consulta leve)
    with st.spinner("Carregando períodos disponíveis..."):
        periodos = carregar_periodos_disponiveis(engine)
    
    if not periodos:
        st.error("❌ Não foi possível carregar os períodos disponíveis.")
        return
    
    # Sidebar - Navegação
    st.sidebar.title("🔐 Navegação")
    st.sidebar.success("✅ Conexão estabelecida!")

    # Guia rápido de navegação
    with st.sidebar.expander("❓ Guia Rápido", expanded=False):
        st.markdown("""
        **Como usar o sistema:**

        1. **Visão Geral**: Panorama rápido do período
        2. **Análise Setorial**: Detalhes por setor econômico
        3. **Análise Empresarial**: Busca e análise por CNPJ
        4. **Alertas**: Empresas com comportamento atípico
        5. **Evolução**: Tendências históricas
        6. **Volatilidade**: Estabilidade fiscal
        7. **Pagamentos**: ICMS declarado vs pago
        8. **ML**: Modelos preditivos de risco
        9. **Avançadas**: Análises complementares
        10. **Relatórios**: Resumos executivos

        💡 **Dica**: Passe o mouse sobre os indicadores (?) para ver explicações detalhadas.
        """)

    secao = st.sidebar.radio(
        "Escolha a análise:",
        [
            "📈 Visão Geral",
            "🏭 Análise Setorial",
            "🏢 Análise Empresarial",
            "⚠️ Alertas e Anomalias",
            "⏱️ Evolução Temporal",
            "📉 Análise de Volatilidade",
            "💰 Análise de Pagamentos",
            "🤖 Machine Learning",
            "📊 Análises Avançadas",
            "📋 Relatórios"
        ],
        help="Selecione a seção do dashboard que deseja visualizar."
    )

    # Info na sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(f"📅 {len(periodos)} períodos disponíveis")

    # Legenda de cores
    with st.sidebar.expander("🎨 Legenda de Cores", expanded=False):
        st.markdown("""
        **Indicadores de Status:**
        - 🟢 **Verde**: Normal / Bom / Baixo risco
        - 🟡 **Amarelo**: Atenção / Médio
        - 🟠 **Laranja**: Alto / Importante
        - 🔴 **Vermelho**: Crítico / Urgente

        **Tendências:**
        - 📈 Crescente
        - 📉 Decrescente
        - ➡️ Estável
        """)

    # Botão para limpar cache
    if st.sidebar.button("🔄 Limpar Cache", help="Recarrega todos os dados do banco de dados."):
        st.cache_data.clear()
        st.rerun()

    # Versão do sistema
    st.sidebar.markdown("---")
    st.sidebar.caption("ARGOS Setores v4.1 | SEF/SC")
    
    # Período padrão (mais recente)
    periodo_padrao = periodos[0] if periodos else None
    
    # Renderizar seção selecionada
    if secao == "📈 Visão Geral":
        render_visao_geral_v2(engine, periodos, periodo_padrao)
    elif secao == "🏭 Análise Setorial":
        render_analise_setorial_v2(engine, periodos, periodo_padrao)
    elif secao == "🏢 Análise Empresarial":
        render_analise_empresarial_v2(engine, periodos, periodo_padrao)
    elif secao == "⚠️ Alertas e Anomalias":
        render_alertas_anomalias_v2(engine, periodos, periodo_padrao)
    elif secao == "⏱️ Evolução Temporal":
        render_evolucao_temporal_v2(engine, periodos)
    elif secao == "📉 Análise de Volatilidade":
        render_analise_volatilidade_v2(engine, periodos, periodo_padrao)
    elif secao == "💰 Análise de Pagamentos":
        render_analise_pagamentos_v2(engine, periodos, periodo_padrao)
    elif secao == "🤖 Machine Learning":
        render_machine_learning_v2(engine, periodos, periodo_padrao)
    elif secao == "📊 Análises Avançadas":
        render_analises_avancadas_v2(engine, periodos, periodo_padrao)
    elif secao == "📋 Relatórios":
        render_relatorios_v2(engine, periodos, periodo_padrao)

# =============================================================================
# 6. SEÇÃO: VISÃO GERAL (OTIMIZADA)
# =============================================================================

def render_visao_geral_v2(engine, periodos, periodo_padrao):
    st.header("📈 Visão Geral do Sistema")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores Principais", [
            ("🏭", "**Setores Monitorados**: Total de classificações CNAE (atividades econômicas) presentes na base."),
            ("🏢", "**Empresas**: Quantidade de CNPJs únicos com movimentação no período."),
            ("💰", "**Faturamento Total**: Soma das receitas declaradas por todas as empresas (em bilhões)."),
            ("📊", "**Alíquota Média**: Média das taxas efetivas de ICMS - indica a carga tributária média.")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Selecione o mês/ano para análise. Dados são atualizados mensalmente.")

    # Carregar dados do período selecionado
    with st.spinner("Carregando dados do período..."):
        df_periodo = carregar_benchmark_setorial(engine, periodo)
        df_empresas = carregar_empresas(engine, periodo)
        df_alertas = carregar_alertas(engine, periodo)

    # KPIs principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏭 Setores Monitorados",
            f"{len(df_periodo):,}" if not df_periodo.empty else "0",
            help=TOOLTIPS["setores_monitorados"]
        )

    with col2:
        st.metric(
            "🏢 Empresas",
            f"{df_empresas['nu_cnpj'].nunique():,}" if not df_empresas.empty else "0",
            help=TOOLTIPS["empresas"]
        )

    with col3:
        fat_total = df_periodo['faturamento_total'].sum() / 1e9 if not df_periodo.empty else 0
        st.metric(
            "💰 Faturamento Total",
            f"R$ {fat_total:.2f}B",
            help=TOOLTIPS["faturamento_total"]
        )

    with col4:
        aliq_media = df_periodo['aliq_efetiva_mediana'].mean() * 100 if not df_periodo.empty else 0
        st.metric(
            "📊 Alíquota Média",
            f"{aliq_media:.2f}%",
            help=TOOLTIPS["aliquota_media"]
        )
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuição por Porte")
        if not df_empresas.empty:
            porte_dist = df_empresas.groupby('porte_empresa').size().reset_index(name='quantidade')
            fig = px.pie(
                porte_dist, 
                values='quantidade', 
                names='porte_empresa',
                title="Empresas por Porte"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("⚠️ Status de Alertas")
        if not df_alertas.empty:
            alertas_dist = df_alertas.groupby('severidade').size().reset_index(name='quantidade')
            fig = px.bar(
                alertas_dist,
                x='severidade',
                y='quantidade',
                title="Alertas por Severidade",
                color='severidade',
                color_discrete_map={
                    'CRITICO': '#d32f2f',
                    'ALTO': '#f57c00',
                    'MEDIO': '#fbc02d',
                    'BAIXO': '#388e3c'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Top setores
    st.markdown("---")
    st.subheader("🏆 Top 10 Setores por Faturamento")
    if not df_periodo.empty:
        top_setores = df_periodo.nlargest(10, 'faturamento_total')[
            ['cnae_classe', 'desc_cnae_classe', 'faturamento_total', 
             'qtd_empresas_total', 'aliq_efetiva_mediana']
        ].copy()
        
        top_setores['faturamento_milhoes'] = top_setores['faturamento_total'] / 1e6
        top_setores['aliq_mediana_pct'] = top_setores['aliq_efetiva_mediana'] * 100
        
        st.dataframe(
            top_setores[['cnae_classe', 'desc_cnae_classe', 'faturamento_milhoes', 
                        'qtd_empresas_total', 'aliq_mediana_pct']],
            hide_index=True,
            column_config={
                'cnae_classe': 'CNAE',
                'desc_cnae_classe': 'Descrição',
                'faturamento_milhoes': st.column_config.NumberColumn(
                    'Faturamento (R$ Milhões)',
                    format="%.2f"
                ),
                'qtd_empresas_total': 'Empresas',
                'aliq_mediana_pct': st.column_config.NumberColumn(
                    'Alíquota Mediana (%)',
                    format="%.2f"
                )
            }
        )
        
# =============================================================================
# 7. SEÇÃO: ANÁLISE SETORIAL (OTIMIZADA)
# =============================================================================

def render_analise_setorial_v2(engine, periodos, periodo_padrao):
    st.header("🏭 Análise Setorial Detalhada")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores Setoriais", [
            ("🏢", "**Empresas**: Quantidade de empresas ativas no setor durante o período."),
            ("💰", "**Faturamento**: Total de receitas declaradas por todas as empresas do setor."),
            ("📊", "**Alíquota Mediana**: Valor central da distribuição de alíquotas - metade das empresas está acima, metade abaixo."),
            ("📈", "**Coef. Variação**: Mede a dispersão das alíquotas. CV > 0.3 indica alta heterogeneidade no setor."),
            ("🎯", "**P25/P75**: Percentis 25 e 75 - definem a faixa onde estão 50% das empresas centrais.")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Selecione o período para análise setorial detalhada.")

    # Carregar dados do período
    with st.spinner("Carregando dados setoriais..."):
        df_setor = carregar_benchmark_setorial(engine, periodo)
        df_evolucao = carregar_evolucao_setor(engine)

    if df_setor.empty:
        st.warning("⚠️ Sem dados para o período selecionado")
        return

    # Seletor de setor
    setores = sorted([s for s in df_setor['desc_cnae_classe'].unique() if s is not None and pd.notna(s)])
    if not setores:
        st.warning("Sem setores disponíveis para o período")
        return
    setor_selecionado = st.selectbox("🔍 Selecione um setor:", setores,
                                     help="Escolha o setor econômico (CNAE) para análise detalhada.")

    # Filtrar dados do setor
    setor_data = df_setor[df_setor['desc_cnae_classe'] == setor_selecionado].iloc[0]
    cnae_classe = setor_data['cnae_classe']

    # KPIs do setor
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "🏢 Empresas",
            f"{int(setor_data['qtd_empresas_total']):,}",
            help=TOOLTIPS["empresas_setor"]
        )

    with col2:
        fat = setor_data['faturamento_total'] / 1e6
        st.metric(
            "💰 Faturamento",
            f"R$ {fat:.2f}M",
            help=TOOLTIPS["faturamento_setor"]
        )

    with col3:
        aliq = setor_data['aliq_efetiva_mediana'] * 100
        st.metric(
            "📊 Alíquota Mediana",
            f"{aliq:.2f}%",
            help=TOOLTIPS["aliquota_mediana"]
        )

    with col4:
        cv = setor_data['aliq_coef_variacao']
        cv_status = "🔴 Alto" if cv > 0.3 else ("🟡 Médio" if cv > 0.15 else "🟢 Baixo")
        st.metric(
            "📈 Coef. Variação",
            f"{cv:.3f}",
            delta=cv_status,
            delta_color="off",
            help=TOOLTIPS["coef_variacao"]
        )
    
    st.markdown("---")
    
    # Gráfico de velocímetro
    st.subheader("🎯 Gráfico de Alíquota")
    fig_gauge = criar_gauge_aliquota(
        setor_data['aliq_efetiva_mediana'],
        setor_data['aliq_efetiva_p25'],
        setor_data['aliq_efetiva_p75']
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    st.markdown("---")
    
    # Evolução temporal
    if not df_evolucao.empty:
        setor_evolucao = df_evolucao[df_evolucao['cnae_classe'] == cnae_classe]
        if not setor_evolucao.empty:
            st.subheader("📈 Evolução Temporal (8 meses)")
            
            # Buscar dados mensais - carrega sob demanda
            with st.spinner("Carregando histórico..."):
                df_benchmark_todos = carregar_benchmark_setorial_todos_periodos(engine)
            
            df_mensal = df_benchmark_todos[
                df_benchmark_todos['cnae_classe'] == cnae_classe
            ].sort_values('nu_per_ref')
            
            if not df_mensal.empty:
                df_mensal['aliq_pct'] = df_mensal['aliq_efetiva_mediana'] * 100
                df_mensal['periodo_str'] = df_mensal['nu_per_ref'].astype(str)
                
                fig = px.line(
                    df_mensal,
                    x='periodo_str',
                    y='aliq_pct',
                    title="Evolução da Alíquota Mediana",
                    labels={'periodo_str': 'Período', 'aliq_pct': 'Alíquota (%)'}
                )
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig, use_container_width=True)
            
            # Métricas de evolução
            col1, col2, col3 = st.columns(3)
            with col1:
                volatilidade = setor_evolucao.iloc[0]['categoria_volatilidade_temporal']
                vol_icon = "🔴" if volatilidade == "ALTA" else ("🟡" if volatilidade == "MEDIA" else "🟢")
                st.metric(
                    "🎯 Categoria Volatilidade",
                    f"{vol_icon} {volatilidade}",
                    help=TOOLTIPS["categoria_volatilidade"]
                )
            with col2:
                tendencia = setor_evolucao.iloc[0]['tendencia_aliquota']
                tend_icon = "📈" if tendencia == "CRESCENTE" else ("📉" if tendencia == "DECRESCENTE" else "➡️")
                st.metric(
                    "📊 Tendência",
                    f"{tend_icon} {tendencia}",
                    help=TOOLTIPS["tendencia_aliquota"]
                )
            with col3:
                aliq_8m = setor_evolucao.iloc[0]['aliq_mediana_media_8m'] * 100
                st.metric(
                    "📈 Alíquota Média 8m",
                    f"{aliq_8m:.2f}%",
                    help=TOOLTIPS["aliquota_media_8m"]
                )
    
    # Distribuição por porte
    st.markdown("---")
    st.subheader("📊 Distribuição por Porte Empresarial")
    
    with st.spinner("Carregando dados por porte..."):
        df_porte = carregar_benchmark_porte(engine, periodo, cnae_classe)
    
    if not df_porte.empty:
        df_porte['aliq_mediana_pct'] = df_porte['aliq_efetiva_mediana'] * 100
        
        fig = px.bar(
            df_porte,
            x='porte_empresa',
            y='aliq_mediana_pct',
            title="Alíquota Mediana por Porte",
            labels={'porte_empresa': 'Porte', 'aliq_mediana_pct': 'Alíquota (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(
            df_porte[['porte_empresa', 'qtd_empresas', 'aliq_mediana_pct']],
            hide_index=True,
            column_config={
                'porte_empresa': 'Porte',
                'qtd_empresas': 'Qtd Empresas',
                'aliq_mediana_pct': st.column_config.NumberColumn(
                    'Alíquota Mediana (%)',
                    format="%.2f"
                )
            }
        )

# =============================================================================
# 8. SEÇÃO: ANÁLISE EMPRESARIAL (OTIMIZADA)
# =============================================================================

def render_analise_empresarial_v2(engine, periodos, periodo_padrao):
    st.header("🏢 Análise Empresarial")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores Empresariais", [
            ("💰", "**Faturamento**: Receita bruta declarada pela empresa no período."),
            ("💵", "**ICMS Devido**: Valor calculado de ICMS a pagar com base nas operações."),
            ("📊", "**Alíquota Empresa**: Taxa efetiva = (ICMS / Faturamento) x 100."),
            ("📈", "**Alíquota Setor**: Mediana do setor - referência para comparação."),
            ("🎯", "**Índice vs Setor**: Razão entre alíquota da empresa e do setor. < 1 = abaixo da média."),
            ("⚠️", "**Status**: Classificação comparativa (MUITO_ABAIXO, ABAIXO, NORMAL, ACIMA).")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Período para consulta dos dados da empresa.")

    # Busca de empresa - NÃO carrega dados automaticamente
    cnpj_busca = st.text_input("🔍 Buscar CNPJ (apenas números):", max_chars=14,
                               help="Digite o CNPJ completo sem pontuação para buscar os dados da empresa.")
    
    if cnpj_busca:
        # Busca específica por CNPJ
        with st.spinner("Buscando empresa..."):
            empresa_data = buscar_empresa_por_cnpj(engine, cnpj_busca, periodo)
        
        if empresa_data.empty:
            st.warning(f"❌ CNPJ {cnpj_busca} não encontrado no período")
            # Mostrar total de empresas
            with st.spinner("Verificando base..."):
                df_empresas = carregar_empresa_vs_benchmark(engine, periodo)
            st.info(f"Total de empresas no período: {df_empresas['nu_cnpj'].nunique():,}" if not df_empresas.empty else "")
        else:
            emp = empresa_data.iloc[0]
            
            st.success(f"✅ Empresa encontrada: **{emp['nm_razao_social']}**")
            
            # Informações principais
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.info(f"**CNAE:** {emp['cnae_classe']}")
                st.info(f"**Setor:** {str(emp['desc_cnae_classe'])[:50]}")
                st.info(f"**Porte:** {emp['porte_empresa']}")
            
            with col2:
                st.metric("💰 Faturamento", formatar_moeda(emp['vl_faturamento']),
                         help=TOOLTIPS["faturamento_empresa"])
                st.metric("💵 ICMS Devido", formatar_moeda(emp['icms_devido']),
                         help=TOOLTIPS["icms_devido"])

            with col3:
                aliq_emp = emp['aliq_efetiva_empresa'] * 100 if pd.notna(emp['aliq_efetiva_empresa']) else 0
                aliq_setor = emp['aliq_setor_mediana'] * 100 if pd.notna(emp['aliq_setor_mediana']) else 0

                st.metric("📊 Alíquota Empresa", f"{aliq_emp:.2f}%",
                         help=TOOLTIPS["aliquota_empresa"])
                st.metric("📊 Alíquota Setor", f"{aliq_setor:.2f}%",
                         help=TOOLTIPS["aliquota_setor_ref"])
            
            # Status comparativo
            st.markdown("---")
            st.subheader("📊 Status Comparativo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                status_color = {
                    'MUITO_ABAIXO': '🔴',
                    'ABAIXO': '🟠',
                    'NORMAL': '🟢',
                    'ACIMA': '🟡',
                    'MUITO_ACIMA': '🔴'
                }
                
                st.info(f"{status_color.get(emp['status_vs_setor'], '⚪')} Status: **{emp['status_vs_setor']}**")
                st.caption(TOOLTIPS["status_vs_setor"])

                if pd.notna(emp['indice_vs_mediana_setor']):
                    indice = emp['indice_vs_mediana_setor']
                    delta_pct = (indice - 1) * 100
                    st.metric(
                        "Índice vs Setor",
                        f"{indice:.2f}",
                        delta=f"{delta_pct:+.1f}%",
                        delta_color="normal" if delta_pct >= 0 else "inverse",
                        help=TOOLTIPS["indice_vs_setor"]
                    )
            
            with col2:
                # Gráfico comparativo de alíquotas
                if pd.notna(emp['aliq_efetiva_empresa']) and pd.notna(emp['aliq_setor_mediana']):
                    dados_comp = pd.DataFrame({
                        'Tipo': ['Empresa', 'Setor (Mediana)', 'Setor (P25)', 'Setor (P75)'],
                        'Alíquota': [
                            emp['aliq_efetiva_empresa'] * 100,
                            emp['aliq_setor_mediana'] * 100,
                            emp['aliq_setor_p25'] * 100 if pd.notna(emp.get('aliq_setor_p25')) else 0,
                            emp['aliq_setor_p75'] * 100 if pd.notna(emp.get('aliq_setor_p75')) else 0
                        ]
                    })
                    
                    fig = px.bar(
                        dados_comp,
                        x='Tipo',
                        y='Alíquota',
                        title="Comparação de Alíquotas (%)",
                        color='Tipo',
                        color_discrete_sequence=['#d32f2f', '#1f77b4', '#2ca02c', '#ff7f0e']
                    )
                    fig.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig, use_container_width=True)
            
            # Evolução temporal da empresa vs setor
            st.markdown("---")
            st.subheader("📈 Evolução Temporal: Empresa vs Setor")
            
            # Buscar dados históricos da empresa (todos os períodos)
            with st.spinner("Carregando histórico..."):
                df_hist_empresa = buscar_empresa_por_cnpj(engine, cnpj_busca, None)
                df_benchmark_todos = carregar_benchmark_setorial_todos_periodos(engine)
            
            df_hist_setor = df_benchmark_todos[
                df_benchmark_todos['cnae_classe'] == emp['cnae_classe']
            ].sort_values('nu_per_ref')
            
            if not df_hist_empresa.empty and not df_hist_setor.empty:
                df_hist_empresa = df_hist_empresa.sort_values('nu_per_ref')
                
                # Preparar dados
                df_hist_empresa['periodo_str'] = df_hist_empresa['nu_per_ref'].astype(str)
                df_hist_empresa['aliq_empresa_pct'] = df_hist_empresa['aliq_efetiva_empresa'] * 100
                
                df_hist_setor['periodo_str'] = df_hist_setor['nu_per_ref'].astype(str)
                df_hist_setor['aliq_setor_pct'] = df_hist_setor['aliq_efetiva_mediana'] * 100
                
                # Criar gráfico de linhas
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_hist_empresa['periodo_str'],
                    y=df_hist_empresa['aliq_empresa_pct'],
                    mode='lines+markers',
                    name='Empresa',
                    line=dict(color='#d32f2f', width=3),
                    marker=dict(size=8)
                ))
                
                fig.add_trace(go.Scatter(
                    x=df_hist_setor['periodo_str'],
                    y=df_hist_setor['aliq_setor_pct'],
                    mode='lines+markers',
                    name='Setor (Mediana)',
                    line=dict(color='#1f77b4', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title="Evolução da Alíquota Efetiva: Empresa vs Setor",
                    xaxis_title="Período",
                    yaxis_title="Alíquota (%)",
                    hovermode='x unified',
                    height=400,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.3,
                        xanchor="center",
                        x=0.5
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados históricos insuficientes para comparação temporal")
    
    # Top empresas por score - carregado sob demanda
    st.markdown("---")
    st.subheader("🎯 Top Empresas para Fiscalização")
    
    if st.button("🔄 Carregar Top Empresas"):
        with st.spinner("Carregando alertas..."):
            df_alertas = carregar_alertas(engine, periodo)
        
        if not df_alertas.empty:
            top_empresas = df_alertas.nlargest(20, 'score_risco')[
                ['nu_cnpj', 'nm_razao_social', 'cnae_classe', 'porte_empresa', 
                 'tipo_alerta', 'severidade', 'score_risco']
            ]
            
            st.dataframe(
                top_empresas,
                hide_index=True,
                column_config={
                    'nu_cnpj': 'CNPJ',
                    'nm_razao_social': 'Razão Social',
                    'cnae_classe': 'CNAE',
                    'porte_empresa': 'Porte',
                    'tipo_alerta': 'Tipo Alerta',
                    'severidade': 'Severidade',
                    'score_risco': st.column_config.NumberColumn(
                        'Score Risco',
                        format="%.1f"
                    )
                }
            )
        else:
            st.info("Nenhum alerta encontrado no período")

# =============================================================================
# 9. SEÇÃO: EVOLUÇÃO TEMPORAL (OTIMIZADA)
# =============================================================================

def render_evolucao_temporal_v2(engine, periodos):
    st.header("⏱️ Evolução Temporal por CNAE")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores de Evolução Temporal", [
            ("📊", "**Períodos Analisados**: Quantidade de meses com dados disponíveis para análise histórica."),
            ("🏢", "**Empresas (Média)**: Média de empresas ativas ao longo de todos os períodos."),
            ("💰", "**Faturamento Total**: Soma acumulada do faturamento em todos os períodos."),
            ("📈", "**Mediana/Média**: A mediana é mais robusta a outliers; a média considera todos os valores."),
            ("📉", "**Amplitude**: Diferença entre maior e menor alíquota - indica a variação extrema."),
            ("🔄", "**Tendência**: Variação percentual entre primeiro e último período analisado.")
        ])

    # Carregar dados de benchmark de todos os períodos
    with st.spinner("Carregando dados de benchmark..."):
        df_benchmark = carregar_benchmark_setorial_todos_periodos(engine)

    if df_benchmark.empty:
        st.warning("Sem dados de benchmark disponíveis")
        return

    # Seletor de CNAE
    cnaes_raw = [
        (cnae, desc) for cnae, desc in
        zip(df_benchmark['cnae_classe'], df_benchmark['desc_cnae_classe'])
        if cnae is not None and pd.notna(cnae) and desc is not None and pd.notna(desc)
    ]

    if not cnaes_raw:
        st.warning("Sem CNAEs disponíveis")
        return

    # Ordenar e remover duplicados
    try:
        cnaes = sorted(list(set(cnaes_raw)), key=lambda x: str(x[1]))
    except:
        cnaes = list(set(cnaes_raw))

    # Criar dicionário para o selectbox
    cnae_dict = {f"{cnae} - {desc}": cnae for cnae, desc in cnaes}

    cnae_selecionado_str = st.selectbox(
        "🔍 Selecione o CNAE:",
        list(cnae_dict.keys()),
        help="Escolha um setor para visualizar sua evolução histórica de indicadores."
    )
    
    cnae_selecionado = cnae_dict[cnae_selecionado_str]
    
    # Filtrar dados do CNAE
    df_cnae = df_benchmark[df_benchmark['cnae_classe'] == cnae_selecionado].copy()
    
    if df_cnae.empty:
        st.warning(f"Sem dados para o CNAE {cnae_selecionado}")
        return
    
    # Ordenar por período
    df_cnae = df_cnae.sort_values('nu_per_ref')
    
    # Preparar dados para visualização
    df_cnae['periodo_str'] = df_cnae['nu_per_ref'].astype(str)
    df_cnae['aliq_media_pct'] = df_cnae['aliq_efetiva_media'] * 100
    df_cnae['aliq_mediana_pct'] = df_cnae['aliq_efetiva_mediana'] * 100
    df_cnae['aliq_p25_pct'] = df_cnae['aliq_efetiva_p25'] * 100
    df_cnae['aliq_p75_pct'] = df_cnae['aliq_efetiva_p75'] * 100
    
    # Informações gerais
    st.info(f"**Setor:** {df_cnae.iloc[0]['desc_cnae_classe']}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Períodos Analisados", len(df_cnae),
                 help=TOOLTIPS["periodos_analisados"])
    with col2:
        st.metric("🏢 Empresas (Média)", f"{df_cnae['qtd_empresas_total'].mean():.0f}",
                 help="Média de empresas ativas por período no setor selecionado.")
    with col3:
        fat_total = df_cnae['faturamento_total'].sum() / 1e9
        st.metric("💰 Faturamento Total", f"R$ {fat_total:.2f}B",
                 help="Soma acumulada do faturamento de todas as empresas em todos os períodos.")
    
    # Gráfico principal - Evolução da Alíquota
    st.markdown("---")
    st.subheader("📈 Evolução da Alíquota Efetiva")
    
    fig = go.Figure()
    
    # Adicionar área entre P25 e P75
    fig.add_trace(go.Scatter(
        x=df_cnae['periodo_str'],
        y=df_cnae['aliq_p75_pct'],
        fill=None,
        mode='lines',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatter(
        x=df_cnae['periodo_str'],
        y=df_cnae['aliq_p25_pct'],
        fill='tonexty',
        mode='lines',
        line=dict(width=0),
        name='Intervalo P25-P75',
        fillcolor='rgba(68, 68, 68, 0.1)',
        hoverinfo='skip'
    ))
    
    # Linha da mediana
    fig.add_trace(go.Scatter(
        x=df_cnae['periodo_str'],
        y=df_cnae['aliq_mediana_pct'],
        mode='lines+markers',
        name='Mediana',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Linha da média
    fig.add_trace(go.Scatter(
        x=df_cnae['periodo_str'],
        y=df_cnae['aliq_media_pct'],
        mode='lines+markers',
        name='Média',
        line=dict(color='#ff7f0e', width=2, dash='dash'),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=f"Evolução da Alíquota - {df_cnae.iloc[0]['desc_cnae_classe'][:60]}",
        xaxis_title="Período",
        yaxis_title="Alíquota (%)",
        hovermode='x unified',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de faturamento
    st.markdown("---")
    st.subheader("💰 Evolução do Faturamento")
    
    df_cnae['faturamento_milhoes'] = df_cnae['faturamento_total'] / 1e6
    
    fig2 = px.bar(
        df_cnae,
        x='periodo_str',
        y='faturamento_milhoes',
        title="Faturamento Total por Período",
        labels={'periodo_str': 'Período', 'faturamento_milhoes': 'Faturamento (R$ Milhões)'}
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)
    
    # Tabela de dados
    st.markdown("---")
    st.subheader("📋 Dados Detalhados")
    
    df_exibir = df_cnae[[
        'nu_per_ref', 'qtd_empresas_total', 'qtd_empresas_ativas',
        'aliq_mediana_pct', 'aliq_media_pct', 'aliq_coef_variacao',
        'faturamento_milhoes'
    ]].copy()
    
    st.dataframe(
        df_exibir,
        hide_index=True,
        column_config={
            'nu_per_ref': 'Período',
            'qtd_empresas_total': 'Total Empresas',
            'qtd_empresas_ativas': 'Empresas Ativas',
            'aliq_mediana_pct': st.column_config.NumberColumn(
                'Alíq. Mediana (%)',
                format="%.2f"
            ),
            'aliq_media_pct': st.column_config.NumberColumn(
                'Alíq. Média (%)',
                format="%.2f"
            ),
            'aliq_coef_variacao': st.column_config.NumberColumn(
                'Coef. Variação',
                format="%.3f"
            ),
            'faturamento_milhoes': st.column_config.NumberColumn(
                'Faturamento (R$ Mi)',
                format="%.2f"
            )
        }
    )
    
    # Estatísticas resumidas
    st.markdown("---")
    st.subheader("📊 Estatísticas do Período")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Alíquota Média",
            f"{df_cnae['aliq_mediana_pct'].mean():.2f}%",
            help="Média aritmética das alíquotas medianas ao longo de todos os períodos analisados."
        )

    with col2:
        variacao = df_cnae['aliq_mediana_pct'].std()
        st.metric(
            "Desvio Padrão",
            f"{variacao:.2f} p.p.",
            help=TOOLTIPS["desvio_padrao"]
        )

    with col3:
        aliq_min = df_cnae['aliq_mediana_pct'].min()
        aliq_max = df_cnae['aliq_mediana_pct'].max()
        st.metric(
            "Amplitude",
            f"{aliq_max - aliq_min:.2f} p.p.",
            help=TOOLTIPS["amplitude"]
        )

    with col4:
        # Tendência (primeiro vs último)
        if len(df_cnae) >= 2:
            primeiro = df_cnae.iloc[0]['aliq_mediana_pct']
            ultimo = df_cnae.iloc[-1]['aliq_mediana_pct']
            tendencia = ((ultimo - primeiro) / primeiro * 100) if primeiro > 0 else 0
            tend_icon = "📈" if tendencia > 0 else ("📉" if tendencia < 0 else "➡️")
            st.metric(
                "Tendência",
                f"{tend_icon} {tendencia:+.1f}%",
                delta=f"{ultimo - primeiro:+.2f} p.p.",
                help=TOOLTIPS["tendencia_percentual"]
            )
    
    # Nova seção: Setores Normais e Anormais
    st.markdown("---")
    st.subheader("🎯 Análise de Normalidade dos Setores")
    
    with st.spinner("Carregando análise de volatilidade..."):
        df_evolucao_setor = carregar_evolucao_setor(engine)
    
    if not df_evolucao_setor.empty:
        # Calcular score de anormalidade baseado em volatilidade e tendência
        df_analise = df_evolucao_setor.copy()
        
        # Criar score de anormalidade
        df_analise['score_anormalidade'] = (
            df_analise['coef_variacao_temporal'] * 100 +
            (df_analise['categoria_volatilidade_temporal'].map({
                'BAIXA': 0, 'MEDIA': 50, 'ALTA': 100
            }).fillna(50))
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Setores Mais Normais (Estáveis)**")
            setores_normais = df_analise.nsmallest(10, 'score_anormalidade')[
                ['cnae_classe', 'desc_cnae_classe', 'coef_variacao_temporal', 
                 'categoria_volatilidade_temporal', 'score_anormalidade']
            ]
            
            st.dataframe(
                setores_normais,
                hide_index=True,
                column_config={
                    'cnae_classe': 'CNAE',
                    'desc_cnae_classe': 'Descrição',
                    'coef_variacao_temporal': st.column_config.NumberColumn(
                        'CV',
                        format="%.3f"
                    ),
                    'categoria_volatilidade_temporal': 'Volatilidade',
                    'score_anormalidade': st.column_config.NumberColumn(
                        'Score',
                        format="%.1f"
                    )
                },
                height=400
            )
        
        with col2:
            st.markdown("**🔴 Setores Mais Anormais (Instáveis)**")
            setores_anormais = df_analise.nlargest(10, 'score_anormalidade')[
                ['cnae_classe', 'desc_cnae_classe', 'coef_variacao_temporal', 
                 'categoria_volatilidade_temporal', 'score_anormalidade']
            ]
            
            st.dataframe(
                setores_anormais,
                hide_index=True,
                column_config={
                    'cnae_classe': 'CNAE',
                    'desc_cnae_classe': 'Descrição',
                    'coef_variacao_temporal': st.column_config.NumberColumn(
                        'CV',
                        format="%.3f"
                    ),
                    'categoria_volatilidade_temporal': 'Volatilidade',
                    'score_anormalidade': st.column_config.NumberColumn(
                        'Score',
                        format="%.1f"
                    )
                },
                height=400
            )
        
        # Seleção de setor para análise de empresas
        st.markdown("---")
        st.subheader("🔍 Empresas Anormais por Setor")
        
        setores_disponiveis = df_analise.nlargest(20, 'score_anormalidade')
        setor_dict = {f"{row['cnae_classe']} - {row['desc_cnae_classe']}": row['cnae_classe'] 
                      for _, row in setores_disponiveis.iterrows()}
        
        setor_analise = st.selectbox(
            "Selecione um setor anormal para análise:",
            list(setor_dict.keys())
        )
        
        if setor_analise and st.button("🔍 Carregar Empresas do Setor"):
            cnae_analise = setor_dict[setor_analise]
            
            # Buscar empresas do setor com alertas
            with st.spinner("Carregando alertas do setor..."):
                df_alertas = carregar_alertas(engine)
            
            if not df_alertas.empty:
                # Empresas com alertas no setor
                empresas_anormais = df_alertas[
                    df_alertas['cnae_classe'] == cnae_analise
                ].nlargest(15, 'score_risco')
                
                if not empresas_anormais.empty:
                    st.warning(f"⚠️ {len(empresas_anormais)} empresas anormais identificadas para fiscalização")
                    
                    st.dataframe(
                        empresas_anormais[[
                            'nu_cnpj', 'nm_razao_social', 'porte_empresa',
                            'tipo_alerta', 'severidade', 'score_risco'
                        ]],
                        hide_index=True,
                        column_config={
                            'nu_cnpj': 'CNPJ',
                            'nm_razao_social': 'Razão Social',
                            'porte_empresa': 'Porte',
                            'tipo_alerta': 'Tipo Alerta',
                            'severidade': 'Severidade',
                            'score_risco': st.column_config.NumberColumn(
                                'Score Risco',
                                format="%.1f"
                            )
                        },
                        height=400
                    )
                    
                    # Download
                    csv = empresas_anormais.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "📥 Download Empresas para Fiscalização",
                        csv,
                        f"empresas_anormais_{cnae_analise}.csv",
                        "text/csv"
                    )
                else:
                    st.info("✅ Nenhuma empresa anormal identificada neste setor")

# =============================================================================
# 10. SEÇÃO: ANÁLISE DE VOLATILIDADE (OTIMIZADA)
# =============================================================================

def render_analise_volatilidade_v2(engine, periodos, periodo_padrao):
    st.header("📉 Análise de Volatilidade Empresarial")
    st.markdown("Identifique empresas e setores com comportamento fiscal instável ao longo do tempo.")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores de Volatilidade", [
            ("🔴", "**Alta Volatilidade**: Empresas com CV > 0.5 - comportamento muito instável, alto risco."),
            ("🟡", "**Média Volatilidade**: Empresas com CV entre 0.2 e 0.5 - requerem monitoramento."),
            ("🟢", "**Baixa Volatilidade**: Empresas com CV < 0.2 - comportamento estável e previsível."),
            ("📊", "**CV (Coef. Variação)**: Razão entre desvio padrão e média. Quanto maior, mais instável."),
            ("⚠️", "Empresas com alta volatilidade podem indicar planejamento tributário agressivo ou irregularidades.")
        ])

    # Carregar dados de evolução de empresas
    with st.spinner("Carregando dados de volatilidade..."):
        df_evolucao = carregar_evolucao_empresa(engine)

    if df_evolucao.empty:
        st.warning("⚠️ Dados de evolução temporal não disponíveis")
        return

    # Métricas gerais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        alta_vol = len(df_evolucao[df_evolucao['categoria_volatilidade'] == 'ALTA'])
        st.metric("🔴 Alta Volatilidade", f"{alta_vol:,}",
                 help=TOOLTIPS["alta_volatilidade"])

    with col2:
        media_vol = len(df_evolucao[df_evolucao['categoria_volatilidade'] == 'MEDIA'])
        st.metric("🟡 Média Volatilidade", f"{media_vol:,}",
                 help=TOOLTIPS["media_volatilidade"])

    with col3:
        baixa_vol = len(df_evolucao[df_evolucao['categoria_volatilidade'] == 'BAIXA'])
        st.metric("🟢 Baixa Volatilidade", f"{baixa_vol:,}",
                 help=TOOLTIPS["baixa_volatilidade"])

    with col4:
        cv_medio = df_evolucao['aliq_coef_variacao_8m'].mean() if 'aliq_coef_variacao_8m' in df_evolucao.columns else 0
        cv_status = "🔴 Alto" if cv_medio > 0.3 else ("🟡 Médio" if cv_medio > 0.15 else "🟢 Baixo")
        st.metric("📊 CV Médio", f"{cv_medio:.3f}",
                 delta=cv_status,
                 delta_color="off",
                 help=TOOLTIPS["cv_medio"])
    
    # Distribuição por categoria
    st.markdown("---")
    st.subheader("📊 Distribuição de Volatilidade")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vol_counts = df_evolucao['categoria_volatilidade'].value_counts()
        fig = px.pie(
            vol_counts,
            values=vol_counts.values,
            names=vol_counts.index,
            title="Distribuição por Categoria de Volatilidade",
            color=vol_counts.index,
            color_discrete_map={
                'ALTA': '#d32f2f',
                'MEDIA': '#fbc02d',
                'BAIXA': '#388e3c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Volatilidade por setor
        vol_setor = df_evolucao.groupby('cnae_classe').agg({
            'categoria_volatilidade': lambda x: (x == 'ALTA').sum() / len(x) * 100
        }).nlargest(10, 'categoria_volatilidade').sort_values('categoria_volatilidade')
        
        fig = px.bar(
            vol_setor,
            x='categoria_volatilidade',
            y=vol_setor.index,
            orientation='h',
            title="Top 10 Setores com Maior % de Alta Volatilidade",
            labels={'categoria_volatilidade': '% Alta Volatilidade', 'y': 'CNAE'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top empresas mais voláteis
    st.markdown("---")
    st.subheader("🎯 Empresas Mais Voláteis")
    
    df_alta_vol = df_evolucao[
        df_evolucao['categoria_volatilidade'] == 'ALTA'
    ].nlargest(20, 'aliq_coef_variacao_8m')
    
    if not df_alta_vol.empty:
        st.dataframe(
            df_alta_vol[[
                'nm_razao_social', 'cnae_classe', 'porte_predominante',
                'aliq_coef_variacao_8m', 'aliq_media_8m', 'meses_com_declaracao'
            ]],
            hide_index=True,
            column_config={
                'nm_razao_social': 'Razão Social',
                'cnae_classe': 'CNAE',
                'porte_predominante': 'Porte',
                'aliq_coef_variacao_8m': st.column_config.NumberColumn(
                    'Coef. Variação',
                    format="%.3f"
                ),
                'aliq_media_8m': st.column_config.NumberColumn(
                    'Alíq. Média (%)',
                    format="%.2f"
                ),
                'meses_com_declaracao': 'Meses'
            }
        )
    
    # Análise de volatilidade vs faturamento
    st.markdown("---")
    st.subheader("📈 Volatilidade vs Faturamento")
    
    if 'faturamento_total_8m' in df_evolucao.columns:
        df_scatter = df_evolucao[df_evolucao['faturamento_total_8m'] > 0].copy()
        df_scatter['fat_milhoes'] = df_scatter['faturamento_total_8m'] / 1e6
        
        fig = px.scatter(
            df_scatter,
            x='fat_milhoes',
            y='aliq_coef_variacao_8m',
            color='categoria_volatilidade',
            size='meses_com_declaracao',
            hover_data=['nm_razao_social', 'cnae_classe'],
            title="Volatilidade vs Faturamento",
            labels={
                'fat_milhoes': 'Faturamento Total (R$ Milhões)',
                'aliq_coef_variacao_8m': 'Coeficiente de Variação'
            },
            color_discrete_map={
                'ALTA': '#d32f2f',
                'MEDIA': '#fbc02d',
                'BAIXA': '#388e3c'
            }
        )
        fig.update_xaxes(type='log')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# 11. SEÇÃO: ALERTAS E ANOMALIAS
# =============================================================================
# =============================================================================
# 11. SEÇÃO: ALERTAS E ANOMALIAS (OTIMIZADA)
# =============================================================================

def render_alertas_anomalias_v2(engine, periodos, periodo_padrao):
    st.header("⚠️ Alertas e Anomalias")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Sistema de Alertas", [
            ("🔴", "**CRÍTICO**: Situações que requerem ação imediata. Score > 80. Alta probabilidade de irregularidade."),
            ("🟠", "**ALTO**: Alertas importantes para priorização. Score 60-80. Monitoramento intensivo."),
            ("🟡", "**MÉDIO**: Alertas que requerem atenção. Score 40-60. Acompanhamento preventivo."),
            ("🟢", "**BAIXO**: Alertas informativos. Score < 40. Verificação quando possível."),
            ("📊", "**Score de Risco**: Pontuação 0-100 baseada em múltiplos fatores (desvio da mediana, volatilidade, divergências).")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Selecione o período para visualizar os alertas gerados.")

    # Carregar dados
    with st.spinner("Carregando alertas..."):
        df_alertas = carregar_alertas(engine, periodo)
        df_anomalias = carregar_anomalias(engine, periodo)

    # Resumo de alertas
    col1, col2, col3, col4 = st.columns(4)

    if not df_alertas.empty:
        with col1:
            total = len(df_alertas)
            st.metric("📋 Total Alertas", f"{total:,}",
                     help=TOOLTIPS["total_alertas"])

        with col2:
            criticos = len(df_alertas[df_alertas['severidade'] == 'CRITICO'])
            st.metric("🔴 Críticos", f"{criticos:,}",
                     help=TOOLTIPS["alertas_criticos"])

        with col3:
            altos = len(df_alertas[df_alertas['severidade'] == 'ALTO'])
            st.metric("🟠 Altos", f"{altos:,}",
                     help=TOOLTIPS["alertas_altos"])

        with col4:
            medios = len(df_alertas[df_alertas['severidade'] == 'MEDIO'])
            st.metric("🟡 Médios", f"{medios:,}",
                     help=TOOLTIPS["alertas_medios"])
    
    # Filtro de alertas
    st.markdown("---")
    st.subheader("🔍 Filtrar Alertas")
    
    if not df_alertas.empty:
        tipos_alerta = ['Todos'] + sorted(df_alertas['tipo_alerta'].dropna().unique().tolist())
        tipo_selecionado = st.selectbox("Selecione o tipo de alerta:", tipos_alerta)
        
        if tipo_selecionado != 'Todos':
            df_filtrado = df_alertas[df_alertas['tipo_alerta'] == tipo_selecionado].copy()
        else:
            df_filtrado = df_alertas.copy()
        
        if not df_filtrado.empty:
            st.info(f"📊 {len(df_filtrado):,} empresa(s) encontrada(s)")
            
            # Preparar dados para exibição
            colunas_disponiveis = ['nu_cnpj', 'nm_razao_social', 'cnae_classe', 'desc_cnae_classe',
                                   'porte_empresa', 'tipo_alerta', 'severidade', 'score_risco',
                                   'vl_faturamento', 'aliq_efetiva_empresa', 'aliq_setor_mediana']
            colunas_exibir = [c for c in colunas_disponiveis if c in df_filtrado.columns]
            df_exibir = df_filtrado[colunas_exibir].copy()
            
            # Formatar colunas
            if 'aliq_efetiva_empresa' in df_exibir.columns:
                df_exibir['aliq_empresa_pct'] = df_exibir['aliq_efetiva_empresa'] * 100
            if 'aliq_setor_mediana' in df_exibir.columns:
                df_exibir['aliq_setor_pct'] = df_exibir['aliq_setor_mediana'] * 100
            
            # Ordenar por score
            df_exibir = df_exibir.sort_values('score_risco', ascending=False)
            
            colunas_tabela = ['nu_cnpj', 'nm_razao_social', 'cnae_classe', 'porte_empresa',
                              'tipo_alerta', 'severidade', 'score_risco', 'vl_faturamento']
            if 'aliq_empresa_pct' in df_exibir.columns:
                colunas_tabela.append('aliq_empresa_pct')
            if 'aliq_setor_pct' in df_exibir.columns:
                colunas_tabela.append('aliq_setor_pct')
            
            colunas_tabela = [c for c in colunas_tabela if c in df_exibir.columns]
            
            st.dataframe(
                df_exibir[colunas_tabela],
                hide_index=True,
                column_config={
                    'nu_cnpj': 'CNPJ',
                    'nm_razao_social': 'Razão Social',
                    'cnae_classe': 'CNAE',
                    'porte_empresa': 'Porte',
                    'tipo_alerta': 'Tipo Alerta',
                    'severidade': 'Severidade',
                    'score_risco': st.column_config.NumberColumn('Score Risco', format="%.1f"),
                    'vl_faturamento': st.column_config.NumberColumn('Faturamento', format="R$ %.2f"),
                    'aliq_empresa_pct': st.column_config.NumberColumn('Alíq. Empresa (%)', format="%.2f"),
                    'aliq_setor_pct': st.column_config.NumberColumn('Alíq. Setor (%)', format="%.2f")
                },
                height=400
            )
            
            # Opção de download
            csv = df_exibir.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"alertas_{tipo_selecionado}_{periodo}.csv",
                mime="text/csv"
            )
    
    # Distribuição de alertas
    if not df_alertas.empty:
        st.markdown("---")
        st.subheader("📊 Distribuição de Alertas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_dist = df_alertas.groupby('tipo_alerta').size().reset_index(name='quantidade')
            fig = px.bar(
                tipo_dist,
                x='quantidade',
                y='tipo_alerta',
                orientation='h',
                title="Alertas por Tipo"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            sev_dist = df_alertas.groupby('severidade').size().reset_index(name='quantidade')
            fig = px.pie(
                sev_dist,
                values='quantidade',
                names='severidade',
                title="Alertas por Severidade",
                color='severidade',
                color_discrete_map={
                    'CRITICO': '#d32f2f',
                    'ALTO': '#f57c00',
                    'MEDIO': '#fbc02d',
                    'BAIXO': '#388e3c'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Anomalias setoriais
    if not df_anomalias.empty:
        st.markdown("---")
        st.subheader("🏭 Anomalias Setoriais")
        
        top_anomalias = df_anomalias.nlargest(15, 'score_relevancia')
        colunas_anomalias = ['cnae_classe', 'desc_cnae_classe', 'tipo_anomalia', 
                            'severidade', 'score_relevancia', 'qtd_empresas_total']
        colunas_anomalias = [c for c in colunas_anomalias if c in top_anomalias.columns]
        
        st.dataframe(
            top_anomalias[colunas_anomalias],
            hide_index=True,
            column_config={
                'cnae_classe': 'CNAE',
                'desc_cnae_classe': 'Descrição',
                'tipo_anomalia': 'Tipo',
                'severidade': 'Severidade',
                'score_relevancia': st.column_config.NumberColumn('Score', format="%.1f"),
                'qtd_empresas_total': 'Empresas'
            }
        )

# =============================================================================
# 12. SEÇÃO: ANÁLISE DE PAGAMENTOS (OTIMIZADA)
# =============================================================================

def render_analise_pagamentos_v2(engine, periodos, periodo_padrao):
    st.header("💰 Análise de Pagamentos")
    st.markdown("Explore os dados de pagamentos de ICMS, tendências temporais e empresas com maiores contribuições.")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Indicadores de Pagamentos", [
            ("💵", "**Total Pago**: Soma de todos os pagamentos de ICMS realizados no período."),
            ("📋", "**Qtd Pagamentos**: Número total de guias/documentos de pagamento processados."),
            ("🏢", "**Empresas Pagantes**: CNPJs distintos que realizaram pelo menos um pagamento."),
            ("💳", "**Ticket Médio**: Valor médio por pagamento (Total / Quantidade)."),
            ("⚠️", "**Divergência**: Diferença > 30% entre ICMS declarado e valor pago indica possível inadimplência.")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Selecione o período para análise dos pagamentos de ICMS.")

    # Carregar dados de pagamentos
    with st.spinner("Carregando dados de pagamentos..."):
        df_pagamentos = carregar_pagamentos(engine, periodo)
        df_empresas = carregar_empresa_vs_benchmark(engine, periodo)

    if df_pagamentos.empty:
        st.warning("⚠️ Dados de pagamentos não disponíveis")
        return

    # Métricas principais
    st.subheader("📊 Indicadores Gerais")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_pago = df_pagamentos['valor_total_pago'].sum() if 'valor_total_pago' in df_pagamentos.columns else 0
        st.metric("💵 Total Pago", f"R$ {total_pago/1e9:.2f}B",
                 help=TOOLTIPS["total_pago"])

    with col2:
        total_pagamentos = df_pagamentos['qtd_pagamentos'].sum() if 'qtd_pagamentos' in df_pagamentos.columns else 0
        st.metric("📋 Qtd Pagamentos", f"{total_pagamentos:,.0f}",
                 help=TOOLTIPS["qtd_pagamentos"])

    with col3:
        empresas_pagantes = df_pagamentos[df_pagamentos['valor_total_pago'] > 0]['nu_cnpj'].nunique() if 'valor_total_pago' in df_pagamentos.columns else 0
        st.metric("🏢 Empresas Pagantes", f"{empresas_pagantes:,}",
                 help=TOOLTIPS["empresas_pagantes"])

    with col4:
        ticket_medio = total_pago / total_pagamentos if total_pagamentos > 0 else 0
        st.metric("💳 Ticket Médio", f"R$ {ticket_medio:,.2f}",
                 help=TOOLTIPS["ticket_medio"])
    
    # Evolução temporal
    st.markdown("---")
    st.subheader("📈 Evolução Temporal dos Pagamentos")
    
    # Carregar pagamentos de todos os períodos para evolução
    with st.spinner("Carregando histórico de pagamentos..."):
        df_pagamentos_todos = carregar_pagamentos(engine, None)
    
    if not df_pagamentos_todos.empty and 'nu_per_ref' in df_pagamentos_todos.columns:
        evolucao = df_pagamentos_todos.groupby('nu_per_ref').agg({
            'valor_total_pago': 'sum',
            'qtd_pagamentos': 'sum'
        }).reset_index()
        
        evolucao['periodo_str'] = evolucao['nu_per_ref'].astype(str)
        evolucao['valor_milhoes'] = evolucao['valor_total_pago'] / 1e6
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig.add_trace(
            go.Bar(
                x=evolucao['periodo_str'],
                y=evolucao['valor_milhoes'],
                name='Valor Pago (R$ Mi)',
                marker_color='#1f77b4'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=evolucao['periodo_str'],
                y=evolucao['qtd_pagamentos'],
                name='Quantidade',
                line=dict(color='#ff7f0e', width=3),
                mode='lines+markers'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            title="Evolução do Valor e Quantidade de Pagamentos",
            hovermode='x unified',
            height=400
        )
        fig.update_xaxes(title_text="Período")
        fig.update_yaxes(title_text="Valor (R$ Milhões)", secondary_y=False)
        fig.update_yaxes(title_text="Quantidade", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Top empresas
    st.markdown("---")
    st.subheader("🏆 Ranking de Empresas")
    
    col1, col2 = st.columns(2)
    
    # Merge com dados de empresas para pegar nomes
    if not df_empresas.empty:
        df_pag_com_nome = df_pagamentos.merge(
            df_empresas[['nu_cnpj', 'nm_razao_social']].drop_duplicates(),
            on='nu_cnpj',
            how='left'
        )
        df_pag_com_nome['nm_razao_social'] = df_pag_com_nome['nm_razao_social'].fillna('Não identificado')
    else:
        df_pag_com_nome = df_pagamentos.copy()
        df_pag_com_nome['nm_razao_social'] = 'Não identificado'
    
    with col1:
        st.markdown("**Top 10 por Valor Pago**")
        if 'valor_total_pago' in df_pag_com_nome.columns:
            top_valor = df_pag_com_nome.nlargest(10, 'valor_total_pago')
            top_valor['valor_milhoes'] = top_valor['valor_total_pago'] / 1e6
            
            fig = px.bar(
                top_valor,
                x='valor_milhoes',
                y='nm_razao_social',
                orientation='h',
                title="Maiores Pagadores",
                labels={'valor_milhoes': 'Valor (R$ Mi)', 'nm_razao_social': ''}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Top 10 por Quantidade**")
        if 'qtd_pagamentos' in df_pag_com_nome.columns:
            top_qtd = df_pag_com_nome.nlargest(10, 'qtd_pagamentos')
            
            fig = px.bar(
                top_qtd,
                x='qtd_pagamentos',
                y='nm_razao_social',
                orientation='h',
                title="Maior Frequência de Pagamentos",
                labels={'qtd_pagamentos': 'Quantidade', 'nm_razao_social': ''}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Análise de divergências
    st.markdown("---")
    st.subheader("⚠️ Divergências ICMS x Pagamentos")
    
    if not df_empresas.empty and not df_pagamentos.empty:
        # Preparar dados de pagamentos
        if 'valor_total_pago' in df_pagamentos.columns:
            df_pag_merge = df_pagamentos[['nu_cnpj', 'valor_total_pago']].drop_duplicates()
            
            # Comparar com ICMS devido
            df_comp = df_empresas.merge(
                df_pag_merge,
                on='nu_cnpj',
                how='left',
                suffixes=('', '_pag')
            )
            
            # Garantir que a coluna existe
            if 'valor_total_pago' in df_comp.columns and 'icms_recolher' in df_comp.columns:
                df_comp['valor_total_pago'] = df_comp['valor_total_pago'].fillna(0)
                
                # Calcular divergências
                df_comp['diferenca'] = df_comp['icms_recolher'] - df_comp['valor_total_pago']
                df_comp['perc_divergencia'] = np.where(
                    df_comp['icms_recolher'] > 0,
                    (df_comp['diferenca'] / df_comp['icms_recolher'] * 100),
                    0
                )
                
                # Filtrar divergências significativas
                df_div = df_comp[
                    (np.abs(df_comp['perc_divergencia']) > 30) & 
                    (df_comp['icms_recolher'] > 1000)
                ].copy()
                
                if not df_div.empty:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric(
                            "🔴 Empresas com Divergência > 30%",
                            f"{len(df_div):,}",
                            help=TOOLTIPS["divergencia_pagamento"]
                        )

                    with col2:
                        dif_total = df_div['diferenca'].sum()
                        st.metric(
                            "💰 Diferença Total",
                            f"R$ {dif_total/1e6:.2f}M",
                            help="Soma das diferenças entre ICMS declarado e valor efetivamente pago para todas as empresas com divergência significativa."
                        )
                    
                    # Tabela de divergências
                    st.markdown("**Maiores Divergências:**")
                    df_div_top = df_div.nlargest(15, 'diferenca')[
                        ['nm_razao_social', 'icms_recolher', 'valor_total_pago', 
                         'diferenca', 'perc_divergencia']
                    ]
                    
                    st.dataframe(
                        df_div_top,
                        hide_index=True,
                        column_config={
                            'nm_razao_social': 'Razão Social',
                            'icms_recolher': st.column_config.NumberColumn(
                                'ICMS a Recolher',
                                format="R$ %.2f"
                            ),
                            'valor_total_pago': st.column_config.NumberColumn(
                                'Valor Pago',
                                format="R$ %.2f"
                            ),
                            'diferenca': st.column_config.NumberColumn(
                                'Diferença',
                                format="R$ %.2f"
                            ),
                            'perc_divergencia': st.column_config.NumberColumn(
                                'Divergência (%)',
                                format="%.1f"
                            )
                        }
                    )
                else:
                    st.success("✅ Não há divergências significativas no período")
            else:
                st.info("ℹ️ Colunas necessárias não disponíveis para análise de divergências")
        else:
            st.info("ℹ️ Coluna valor_total_pago não encontrada nos dados de pagamentos")
    else:
        st.info("ℹ️ Dados insuficientes para análise de divergências")

# =============================================================================
# 13. SEÇÃO: MACHINE LEARNING (OTIMIZADA)
# =============================================================================

def render_machine_learning_v2(engine, periodos, periodo_padrao):
    st.header("🤖 Modelos Preditivos (Machine Learning)")
    st.markdown("Utilize modelos de ML para identificar padrões e prever comportamentos de risco fiscal.")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Entenda os indicadores desta seção", expanded=False):
        render_help_section("📊 Métricas de Machine Learning", [
            ("🎯", "**Acurácia**: % de previsões corretas. Boa métrica geral, mas pode ser enganosa com dados desbalanceados."),
            ("✅", "**Precisão**: Dos previstos como problemáticos, quantos realmente são. Evita falsos positivos."),
            ("🔍", "**Recall**: Dos realmente problemáticos, quantos foram identificados. Evita falsos negativos."),
            ("⚖️", "**F1-Score**: Média harmônica entre Precisão e Recall. Melhor métrica para dados desbalanceados."),
            ("📈", "**Prob. Risco**: Probabilidade (0-100%) calculada pelo modelo de uma empresa ser problemática.")
        ])
        st.info("💡 O modelo utiliza features como alíquota, faturamento, porte e flags de divergência para prever o risco.")

    from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
    from sklearn.preprocessing import StandardScaler

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Período dos dados para treinar e aplicar o modelo preditivo.")

    # NÃO carrega dados automaticamente - apenas sob demanda
    st.info("💡 Clique no botão abaixo para carregar os dados e treinar o modelo")
    
    # Abas para diferentes análises
    tabs = st.tabs(["🎯 Modelo Preditivo", "🔍 Empresas em Risco", "📊 Análise de Features"])
    
    with tabs[0]:
        st.subheader("🎯 Treinamento do Modelo")
        
        modelo_escolhido = st.selectbox(
            "Escolha o algoritmo:",
            ["Gradient Boosting", "Random Forest"]
        )
        
        if st.button("🚀 Carregar Dados e Treinar Modelo", type="primary"):
            with st.spinner("Carregando dados para ML..."):
                df_empresas = carregar_empresa_vs_benchmark(engine, periodo)
                df_evolucao = carregar_evolucao_empresa(engine)
            
            if df_empresas.empty:
                st.warning("⚠️ Dados insuficientes para análise preditiva")
                return
            
            # Preparar dados
            df_ml = df_empresas.copy()
            
            # Criar variável target: empresa problemática
            df_ml['empresa_problematica'] = (
                (df_ml['status_vs_setor'].isin(['MUITO_ABAIXO', 'ABAIXO'])) |
                (df_ml['flag_divergencia_pagamento'] == 1 if 'flag_divergencia_pagamento' in df_ml.columns else False)
            ).astype(int)
            
            # Features
            features = []
            
            # Adicionar features numéricas básicas
            if 'vl_faturamento' in df_ml.columns:
                df_ml['log_faturamento'] = np.log1p(df_ml['vl_faturamento'].fillna(0))
                features.append('log_faturamento')
            
            if 'aliq_efetiva_empresa' in df_ml.columns:
                df_ml['aliq_empresa'] = df_ml['aliq_efetiva_empresa'].fillna(0)
                features.append('aliq_empresa')
            
            if 'indice_vs_mediana_setor' in df_ml.columns:
                df_ml['indice_setor'] = df_ml['indice_vs_mediana_setor'].fillna(1)
                features.append('indice_setor')
            
            # One-hot encoding para porte
            if 'porte_empresa' in df_ml.columns:
                porte_dummies = pd.get_dummies(df_ml['porte_empresa'], prefix='porte')
                df_ml = pd.concat([df_ml, porte_dummies], axis=1)
                features.extend(porte_dummies.columns.tolist())
            
            # Flags
            if 'flag_divergencia_pagamento' in df_ml.columns:
                features.append('flag_divergencia_pagamento')
            
            if 'sn_omisso' in df_ml.columns:
                df_ml['sn_omisso'] = df_ml['sn_omisso'].fillna(0)
                features.append('sn_omisso')
            
            # Verificar se temos features suficientes
            if len(features) < 3:
                st.error("❌ Features insuficientes para treinar o modelo")
                return
            
            # Preparar datasets
            X = df_ml[features].fillna(0)
            y = df_ml['empresa_problematica']
            
            if y.nunique() < 2 or len(df_ml) < 100:
                st.warning("⚠️ Dados insuficientes ou sem variação na variável alvo")
                return
            
            # Split treino/teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )
            
            with st.spinner("Treinando modelo..."):
                if modelo_escolhido == "Gradient Boosting":
                    modelo = GradientBoostingClassifier(n_estimators=100, random_state=42)
                else:
                    modelo = RandomForestClassifier(n_estimators=100, random_state=42)
                
                modelo.fit(X_train, y_train)
                y_pred = modelo.predict(X_test)
                y_pred_proba = modelo.predict_proba(X_test)[:, 1]
                
                # Métricas
                st.markdown("### 📈 Performance do Modelo")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    acc = accuracy_score(y_test, y_pred)
                    acc_status = "🟢 Bom" if acc >= 0.8 else ("🟡 Regular" if acc >= 0.6 else "🔴 Baixo")
                    st.metric("Acurácia", f"{acc:.2%}",
                             delta=acc_status,
                             delta_color="off",
                             help=TOOLTIPS["acuracia"])

                with col2:
                    prec = precision_score(y_test, y_pred, zero_division=0)
                    prec_status = "🟢 Bom" if prec >= 0.7 else ("🟡 Regular" if prec >= 0.5 else "🔴 Baixo")
                    st.metric("Precisão", f"{prec:.2%}",
                             delta=prec_status,
                             delta_color="off",
                             help=TOOLTIPS["precisao"])

                with col3:
                    rec = recall_score(y_test, y_pred, zero_division=0)
                    rec_status = "🟢 Bom" if rec >= 0.7 else ("🟡 Regular" if rec >= 0.5 else "🔴 Baixo")
                    st.metric("Recall", f"{rec:.2%}",
                             delta=rec_status,
                             delta_color="off",
                             help=TOOLTIPS["recall"])

                with col4:
                    f1 = f1_score(y_test, y_pred, zero_division=0)
                    f1_status = "🟢 Bom" if f1 >= 0.7 else ("🟡 Regular" if f1 >= 0.5 else "🔴 Baixo")
                    st.metric("F1-Score", f"{f1:.2%}",
                             delta=f1_status,
                             delta_color="off",
                             help=TOOLTIPS["f1_score"])
                
                # Matriz de confusão
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🎲 Matriz de Confusão")
                    cm = confusion_matrix(y_test, y_pred)
                    fig = px.imshow(
                        cm,
                        labels=dict(x="Predito", y="Real"),
                        x=['Normal', 'Problemática'],
                        y=['Normal', 'Problemática'],
                        text_auto=True,
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.markdown("### 🔥 Features Mais Importantes")
                    importancias = pd.DataFrame({
                        'feature': features,
                        'importancia': modelo.feature_importances_
                    }).sort_values('importancia', ascending=False).head(10)
                    
                    fig = px.bar(
                        importancias,
                        x='importancia',
                        y='feature',
                        orientation='h',
                        title="Top 10 Features"
                    )
                    fig.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig, use_container_width=True)
                
                # Salvar modelo em session_state
                st.session_state['modelo_ml'] = modelo
                st.session_state['features_ml'] = features
                st.session_state['df_ml'] = df_ml
                st.success("✅ Modelo treinado com sucesso!")
    
    with tabs[1]:
        st.subheader("🔍 Empresas em Alto Risco")
        
        if 'modelo_ml' in st.session_state:
            modelo = st.session_state['modelo_ml']
            features_usadas = st.session_state['features_ml']
            df_ml = st.session_state['df_ml']
            
            # Prever para todas as empresas
            X_all = df_ml[features_usadas].fillna(0)
            df_ml['prob_risco'] = modelo.predict_proba(X_all)[:, 1]
            
            # Filtrar empresas em risco (não problemáticas atualmente)
            df_risco = df_ml[
                (df_ml['empresa_problematica'] == 0) &
                (df_ml['prob_risco'] > 0.5)
            ].nlargest(30, 'prob_risco')
            
            if not df_risco.empty:
                st.warning(f"⚠️ {len(df_risco)} empresas identificadas com alto risco")
                
                colunas_exibir = ['nm_razao_social', 'cnae_classe', 'porte_empresa',
                                  'prob_risco', 'vl_faturamento', 'aliq_efetiva_empresa']
                colunas_exibir = [c for c in colunas_exibir if c in df_risco.columns]
                
                st.dataframe(
                    df_risco[colunas_exibir],
                    hide_index=True,
                    column_config={
                        'nm_razao_social': 'Razão Social',
                        'cnae_classe': 'CNAE',
                        'porte_empresa': 'Porte',
                        'prob_risco': st.column_config.NumberColumn(
                            'Prob. Risco',
                            format="%.2%"
                        ),
                        'vl_faturamento': st.column_config.NumberColumn(
                            'Faturamento',
                            format="R$ %.2f"
                        ),
                        'aliq_efetiva_empresa': st.column_config.NumberColumn(
                            'Alíquota',
                            format="%.2%"
                        )
                    },
                    height=500
                )
                
                # Download
                csv = df_risco.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 Download Lista de Risco",
                    csv,
                    f"empresas_alto_risco_{periodo}.csv",
                    "text/csv"
                )
            else:
                st.success("✅ Nenhuma empresa em alto risco identificada")
        else:
            st.info("👆 Treine o modelo na aba anterior para ver esta análise")
    
    with tabs[2]:
        st.subheader("📊 Análise Detalhada de Features")
        
        if 'modelo_ml' in st.session_state and 'df_ml' in st.session_state:
            df_ml = st.session_state['df_ml']
            features = st.session_state['features_ml']
            
            # Distribuição das features por classe
            col1, col2 = st.columns(2)
            
            with col1:
                features_numericas = [f for f in features if not f.startswith('porte_')]
                if features_numericas:
                    feature_analise = st.selectbox(
                        "Selecione uma feature para análise:",
                        features_numericas
                    )
                    
                    fig = px.box(
                        df_ml,
                        x='empresa_problematica',
                        y=feature_analise,
                        color='empresa_problematica',
                        title=f"Distribuição de {feature_analise}",
                        labels={'empresa_problematica': 'Tipo', feature_analise: 'Valor'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if 'prob_risco' in df_ml.columns:
                    fig = px.histogram(
                        df_ml,
                        x='prob_risco',
                        color='empresa_problematica',
                        title="Distribuição de Probabilidades",
                        labels={'prob_risco': 'Probabilidade de Risco'},
                        nbins=50
                    )
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("👆 Treine o modelo primeiro")

# =============================================================================
# 14. SEÇÃO: ANÁLISES AVANÇADAS (OTIMIZADA)
# =============================================================================

def render_analises_avancadas_v2(engine, periodos, periodo_padrao):
    st.header("📊 Análises Avançadas")

    # Seção de ajuda expandível
    with st.expander("ℹ️ Sobre as Análises Avançadas", expanded=False):
        render_help_section("📊 Análises Disponíveis", [
            ("📈", "**Evolução Temporal**: Acompanhe a variação dos indicadores ao longo do tempo para os principais setores."),
            ("🎯", "**Volatilidade**: Identifique setores com comportamento instável que podem indicar riscos."),
            ("💰", "**ICMS vs Pagamentos**: Compare valores declarados e pagos para detectar divergências."),
            ("🔍", "**Comparações**: Compare métricas entre diferentes setores para identificar outliers.")
        ])

    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0,
                          help="Período base para as análises avançadas.")

    tabs = st.tabs([
        "📈 Evolução Temporal",
        "🎯 Volatilidade",
        "💰 ICMS vs Pagamentos",
        "🔍 Comparações"
    ])
    
    # Tab 1: Evolução Temporal
    with tabs[0]:
        st.subheader("📈 Evolução Temporal dos Setores")
        
        if st.button("🔄 Carregar Evolução Temporal"):
            with st.spinner("Carregando dados..."):
                df_benchmark = carregar_benchmark_setorial_todos_periodos(engine)
            
            if not df_benchmark.empty:
                # Top 10 setores
                top_setores_cnae = df_benchmark.groupby('cnae_classe')['faturamento_total'].sum().nlargest(10).index
                df_top = df_benchmark[df_benchmark['cnae_classe'].isin(top_setores_cnae)].copy()
                
                df_top['aliq_pct'] = df_top['aliq_efetiva_mediana'] * 100
                df_top['periodo_str'] = df_top['nu_per_ref'].astype(str)
                
                fig = px.line(
                    df_top,
                    x='periodo_str',
                    y='aliq_pct',
                    color='desc_cnae_classe',
                    title="Evolução da Alíquota Mediana - Top 10 Setores",
                    labels={'periodo_str': 'Período', 'aliq_pct': 'Alíquota (%)'}
                )
                fig.update_layout(hovermode='x unified', height=500, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Sem dados disponíveis")
    
    # Tab 2: Volatilidade
    with tabs[1]:
        st.subheader("🎯 Análise de Volatilidade")
        
        if st.button("🔄 Carregar Análise de Volatilidade"):
            with st.spinner("Carregando dados..."):
                df_evolucao = carregar_evolucao_setor(engine)
            
            if not df_evolucao.empty:
                df_vol = df_evolucao[df_evolucao['categoria_volatilidade_temporal'].isin(['ALTA', 'MEDIA'])].copy()
                
                if not df_vol.empty:
                    df_vol['aliq_media_pct'] = df_vol['aliq_mediana_media_8m'] * 100
                    df_vol['fat_milhoes'] = df_vol['faturamento_acumulado_8m'] / 1e6
                    
                    fig = px.scatter(
                        df_vol,
                        x='coef_variacao_temporal',
                        y='aliq_media_pct',
                        size='fat_milhoes',
                        color='categoria_volatilidade_temporal',
                        hover_data=['desc_cnae_classe'],
                        title="Volatilidade vs Alíquota Média",
                        labels={
                            'coef_variacao_temporal': 'Coeficiente de Variação',
                            'aliq_media_pct': 'Alíquota Média (%)'
                        }
                    )
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Nenhum setor com volatilidade alta ou média encontrado")
            else:
                st.warning("Sem dados disponíveis")
    
    # Tab 3: ICMS vs Pagamentos
    with tabs[2]:
        st.subheader("💰 Divergências ICMS vs Pagamentos")
        
        if st.button("🔄 Carregar Análise de Divergências"):
            with st.spinner("Carregando dados..."):
                df_empresas = carregar_empresa_vs_benchmark(engine, periodo)
            
            if not df_empresas.empty:
                if 'flag_divergencia_pagamento' in df_empresas.columns:
                    df_div = df_empresas[df_empresas['flag_divergencia_pagamento'] == 1].copy()
                    
                    if not df_div.empty:
                        st.warning(f"⚠️ {len(df_div):,} empresas com divergências detectadas")
                        
                        if 'icms_recolher' in df_div.columns and 'valor_total_pago' in df_div.columns:
                            df_div['diferenca'] = df_div['icms_recolher'] - df_div['valor_total_pago']
                            df_div_top = df_div.nlargest(20, 'diferenca')
                            
                            colunas_exibir = ['nu_cnpj', 'nm_razao_social', 'icms_recolher', 
                                             'valor_total_pago', 'diferenca']
                            colunas_exibir = [c for c in colunas_exibir if c in df_div_top.columns]
                            
                            st.dataframe(
                                df_div_top[colunas_exibir],
                                hide_index=True,
                                column_config={
                                    'nu_cnpj': 'CNPJ',
                                    'nm_razao_social': 'Razão Social',
                                    'icms_recolher': st.column_config.NumberColumn(
                                        'ICMS a Recolher',
                                        format="R$ %.2f"
                                    ),
                                    'valor_total_pago': st.column_config.NumberColumn(
                                        'Valor Pago',
                                        format="R$ %.2f"
                                    ),
                                    'diferenca': st.column_config.NumberColumn(
                                        'Diferença',
                                        format="R$ %.2f"
                                    )
                                }
                            )
                        else:
                            st.info("Colunas de valores não disponíveis para análise detalhada")
                    else:
                        st.success("✅ Nenhuma divergência encontrada")
                else:
                    st.info("Coluna de flag de divergência não disponível")
            else:
                st.warning("Sem dados disponíveis")
    
    # Tab 4: Comparações
    with tabs[3]:
        st.subheader("🔍 Comparações Setoriais")
        
        if st.button("🔄 Carregar Comparações"):
            with st.spinner("Carregando dados..."):
                df_benchmark = carregar_benchmark_setorial(engine, periodo)
            
            if not df_benchmark.empty:
                df_comp = df_benchmark.nlargest(20, 'faturamento_total').copy()
                df_comp['aliq_pct'] = df_comp['aliq_efetiva_mediana'] * 100
                df_comp['fat_milhoes'] = df_comp['faturamento_total'] / 1e6
                
                fig = px.bar(
                    df_comp,
                    x='desc_cnae_classe',
                    y='aliq_pct',
                    title="Alíquota Mediana - Top 20 Setores",
                    labels={'desc_cnae_classe': 'Setor', 'aliq_pct': 'Alíquota (%)'}
                )
                fig.update_xaxes(tickangle=-45)
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela adicional
                st.markdown("### 📋 Detalhamento")
                st.dataframe(
                    df_comp[['cnae_classe', 'desc_cnae_classe', 'qtd_empresas_total', 'fat_milhoes', 'aliq_pct']],
                    hide_index=True,
                    column_config={
                        'cnae_classe': 'CNAE',
                        'desc_cnae_classe': 'Descrição',
                        'qtd_empresas_total': 'Empresas',
                        'fat_milhoes': st.column_config.NumberColumn(
                            'Faturamento (R$ Mi)',
                            format="%.2f"
                        ),
                        'aliq_pct': st.column_config.NumberColumn(
                            'Alíquota (%)',
                            format="%.2f"
                        )
                    }
                )
            else:
                st.warning("Sem dados disponíveis")

# =============================================================================
# 15. SEÇÃO: RELATÓRIOS (OTIMIZADA)
# =============================================================================

def render_relatorios_v2(engine, periodos, periodo_padrao):
    st.header("📋 Relatórios Gerenciais")
    st.markdown("Gere resumos executivos e insights automáticos a partir dos dados analisados.")
    
    # Filtro de período
    periodo = st.selectbox("📅 Período de Referência", periodos, index=0)
    
    # Relatório Executivo
    st.markdown("### 🎯 Relatório Executivo - Sistema ARGOS Setores")
    
    if st.button("📊 Gerar Relatório Executivo", type="primary"):
        # Carregar dados necessários
        with st.spinner("Carregando dados para o relatório..."):
            df_empresas = carregar_empresas(engine, periodo)
            df_alertas = carregar_alertas(engine, periodo)
            df_benchmark = carregar_benchmark_setorial(engine, periodo)
            df_anomalias = carregar_anomalias(engine, periodo)
        
        # Resumo do período
        st.subheader(f"📊 Período de Referência: {periodo}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📈 Volumes Gerais**")
            if not df_empresas.empty:
                st.write(f"• **Empresas:** {df_empresas['nu_cnpj'].nunique():,}")
                st.write(f"• **Setores:** {df_empresas['cnae_classe'].nunique():,}")
                fat_total = df_empresas['vl_faturamento'].sum() / 1e12
                st.write(f"• **Faturamento:** R$ {fat_total:.2f} Tri")
            else:
                st.write("• Dados não disponíveis")
        
        with col2:
            st.markdown("**⚠️ Alertas e Riscos**")
            if not df_alertas.empty:
                st.write(f"• **Total Alertas:** {len(df_alertas):,}")
                criticos = len(df_alertas[df_alertas['severidade'] == 'CRITICO'])
                st.write(f"• **Críticos:** {criticos:,}")
                st.write(f"• **Empresas:** {df_alertas['nu_cnpj'].nunique():,}")
            else:
                st.write("• Nenhum alerta no período")
        
        with col3:
            st.markdown("**🏭 Anomalias Setoriais**")
            if not df_anomalias.empty:
                st.write(f"• **Setores:** {len(df_anomalias):,}")
                alta_sev = len(df_anomalias[df_anomalias['severidade'] == 'ALTA'])
                st.write(f"• **Alta Severidade:** {alta_sev:,}")
            else:
                st.write("• Nenhuma anomalia detectada")
        
        # Principais achados
        st.markdown("---")
        st.subheader("🔍 Principais Achados")
        
        achados = []
        
        if not df_alertas.empty:
            tipo_mais_comum = df_alertas['tipo_alerta'].mode()
            if not tipo_mais_comum.empty:
                tipo_mais_comum = tipo_mais_comum.iloc[0]
                qtd_tipo = len(df_alertas[df_alertas['tipo_alerta'] == tipo_mais_comum])
                achados.append(
                    f"• O tipo de alerta mais frequente é **{tipo_mais_comum}** com {qtd_tipo:,} ocorrências"
                )
        
        if not df_anomalias.empty:
            setor_maior_score = df_anomalias.nlargest(1, 'score_relevancia')
            if not setor_maior_score.empty:
                setor_maior_score = setor_maior_score.iloc[0]
                achados.append(
                    f"• Setor **{setor_maior_score['desc_cnae_classe']}** apresenta maior score de relevância ({setor_maior_score['score_relevancia']:.1f})"
                )
        
        if not df_empresas.empty:
            porte_dist = df_empresas['porte_empresa'].value_counts()
            if not porte_dist.empty:
                porte_predominante = porte_dist.index[0]
                pct_porte = (porte_dist.iloc[0] / len(df_empresas)) * 100
                achados.append(
                    f"• **{pct_porte:.1f}%** das empresas são de porte **{porte_predominante}**"
                )
        
        if achados:
            for achado in achados:
                st.markdown(achado)
        else:
            st.info("Nenhum achado relevante identificado")
        
        # Recomendações
        st.markdown("---")
        st.subheader("💡 Recomendações Estratégicas")
        
        st.markdown("""
        **1. Priorização de Fiscalização**
        - Focar em empresas com alertas críticos e alto score de risco
        - Priorizar setores com anomalias de alta severidade
        
        **2. Monitoramento Contínuo**
        - Acompanhar empresas com alta volatilidade fiscal
        - Monitorar divergências entre ICMS devido e pagamentos realizados
        
        **3. Ações Preventivas**
        - Desenvolver orientações específicas para setores problemáticos
        - Implementar comunicação preventiva com empresas em risco
        
        **4. Otimização de Processos**
        - Utilizar modelos preditivos para seleção de alvos
        - Automatizar identificação de padrões anômalos
        
        **5. Análise Setorial**
        - Investigar setores com alta concentração de alertas
        - Desenvolver benchmarks específicos por porte e setor
        """)
        
        # Tabelas de suporte
        st.markdown("---")
        st.subheader("📊 Tabelas de Suporte")
        
        tab1, tab2, tab3 = st.tabs(["Top Setores", "Evolução Temporal", "Distribuições"])
        
        with tab1:
            if not df_benchmark.empty:
                top_setores = df_benchmark.nlargest(10, 'faturamento_total')
                
                st.dataframe(
                    top_setores[[
                        'cnae_classe', 'desc_cnae_classe', 'faturamento_total',
                        'qtd_empresas_total', 'aliq_efetiva_mediana'
                    ]],
                    hide_index=True,
                    column_config={
                        'cnae_classe': 'CNAE',
                        'desc_cnae_classe': 'Descrição',
                        'faturamento_total': st.column_config.NumberColumn(
                            'Faturamento',
                            format="R$ %.2f"
                        ),
                        'qtd_empresas_total': 'Empresas',
                        'aliq_efetiva_mediana': st.column_config.NumberColumn(
                            'Alíq. Mediana',
                            format="%.2%"
                        )
                    }
                )
            else:
                st.info("Dados de benchmark não disponíveis")
        
        with tab2:
            st.markdown("**Evolução do Faturamento Total**")
            
            # Carregar todos os períodos para evolução
            with st.spinner("Carregando evolução..."):
                df_empresas_todos = carregar_empresas(engine, None)
            
            if not df_empresas_todos.empty:
                evolucao = df_empresas_todos.groupby('nu_per_ref').agg({
                    'nu_cnpj': 'nunique',
                    'vl_faturamento': 'sum',
                    'icms_devido': 'sum'
                }).reset_index()
                
                evolucao['periodo_str'] = evolucao['nu_per_ref'].astype(str)
                evolucao['fat_bilhoes'] = evolucao['vl_faturamento'] / 1e9
                
                fig = px.line(
                    evolucao,
                    x='periodo_str',
                    y='fat_bilhoes',
                    title="Evolução do Faturamento Total",
                    labels={'periodo_str': 'Período', 'fat_bilhoes': 'Faturamento (R$ Bi)'},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela de evolução
                st.dataframe(
                    evolucao[['periodo_str', 'nu_cnpj', 'fat_bilhoes']],
                    hide_index=True,
                    column_config={
                        'periodo_str': 'Período',
                        'nu_cnpj': 'Empresas',
                        'fat_bilhoes': st.column_config.NumberColumn(
                            'Faturamento (R$ Bi)',
                            format="%.2f"
                        )
                    }
                )
            else:
                st.info("Dados de evolução não disponíveis")
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Alertas por Severidade**")
                if not df_alertas.empty:
                    sev_dist = df_alertas['severidade'].value_counts()
                    
                    fig = px.pie(
                        sev_dist,
                        values=sev_dist.values,
                        names=sev_dist.index,
                        title="Distribuição de Alertas",
                        color=sev_dist.index,
                        color_discrete_map={
                            'CRITICO': '#d32f2f',
                            'ALTO': '#f57c00',
                            'MEDIO': '#fbc02d',
                            'BAIXO': '#388e3c'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem alertas no período")
            
            with col2:
                st.markdown("**Empresas por Porte**")
                if not df_empresas.empty:
                    porte_dist = df_empresas['porte_empresa'].value_counts()
                    
                    fig = px.bar(
                        porte_dist,
                        x=porte_dist.index,
                        y=porte_dist.values,
                        title="Distribuição por Porte",
                        labels={'x': 'Porte', 'y': 'Quantidade'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Sem dados de empresas")
        
        # Opção de exportação
        st.markdown("---")
        st.info("📥 Funcionalidade de exportação em PDF será implementada em breve")
        
        # Download dos dados em CSV
        if not df_alertas.empty:
            csv_alertas = df_alertas.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 Download Alertas (CSV)",
                csv_alertas,
                f"alertas_relatorio_{periodo}.csv",
                "text/csv"
            )

# =============================================================================
# 16. EXECUÇÃO PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    main()