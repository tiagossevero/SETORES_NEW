# ARGOS SETORES v4.1

**Análise Tributária Setorial** - Sistema de Inteligência Tributária

Dashboard interativo para análise de comportamento tributário setorial da Receita Estadual de Santa Catarina.

---

## Sobre o Projeto

O ARGOS SETORES é um sistema de inteligência tributária desenvolvido para analisar e monitorar o comportamento de conformidade fiscal de diferentes setores econômicos em Santa Catarina, Brasil. A ferramenta oferece análises estatísticas avançadas, detecção de anomalias e modelos de Machine Learning para identificação de riscos.

### Principais Funcionalidades

- **Visão Geral**: KPIs do sistema, distribuição por porte e status de alertas
- **Análise Setorial**: Métricas detalhadas por código CNAE e benchmarks setoriais
- **Análise Empresarial**: Busca e análise individual de empresas por CNPJ
- **Alertas e Anomalias**: Detecção de comportamentos atípicos e classificação de severidade
- **Evolução Temporal**: Acompanhamento histórico de 8 meses
- **Análise de Volatilidade**: Avaliação de estabilidade e coeficiente de variação
- **Análise de Pagamentos**: Comparativo entre ICMS devido e pagamentos realizados
- **Machine Learning**: Modelos preditivos de risco (Gradient Boosting, Random Forest)
- **Análises Avançadas**: Comparativos temporais e análises multi-setoriais
- **Relatórios**: Geração de sumários executivos e exportação de dados

---

## Tecnologias Utilizadas

### Frontend/Framework
- **Streamlit** - Framework de interface web
- **Plotly** - Visualizações interativas (plotly.express, plotly.graph_objects)
- **CSS customizado** - Estilização e UX aprimorada

### Backend/Processamento de Dados
- **Python 3.7+** - Linguagem principal
- **Pandas** - Manipulação e análise de dados
- **NumPy** - Computações numéricas
- **SQLAlchemy** - ORM e conectividade com banco de dados

### Banco de Dados
- **Apache Impala** - Banco de dados analítico (database: `niat`)
- **LDAP** - Autenticação corporativa
- **SSL/TLS** - Criptografia de conexão

### Machine Learning
- **Scikit-learn**
  - GradientBoostingClassifier
  - RandomForestClassifier
  - Métricas: accuracy, precision, recall, F1-score
  - Matriz de confusão

---

## Estrutura do Projeto

```
SETORES_NEW/
├── SETORES (5).py    # Aplicação principal (3.152 linhas)
├── SETORES.json      # Arquivo de dados/configuração
├── README.md         # Documentação do projeto
└── .git/             # Controle de versão
```

---

## Instalação

### Pré-requisitos

- Python 3.7 ou superior
- Acesso de rede ao servidor Impala: `bdaworkernode02.sef.sc.gov.br:21050`
- Credenciais LDAP/Impala válidas

### Instalação de Dependências

```bash
pip install streamlit pandas numpy plotly sqlalchemy scikit-learn
```

### Configuração de Credenciais

Crie o arquivo de secrets do Streamlit:

```bash
mkdir -p ~/.streamlit
```

Crie o arquivo `~/.streamlit/secrets.toml` com o seguinte conteúdo:

```toml
[impala_credentials]
user = "seu_usuario"
password = "sua_senha"
```

---

## Como Executar

### Execução Local

```bash
streamlit run "SETORES (5).py"
```

A aplicação estará disponível em: `http://localhost:8501`

### Autenticação

Ao iniciar, o sistema solicitará uma senha de acesso para proteção da sessão.

---

## Módulos e Funcionalidades

### 1. Visão Geral
- KPIs principais do sistema
- Quantidade de setores monitorados
- Total de empresas e faturamento agregado
- Alíquotas médias efetivas
- Distribuição por porte empresarial
- Status de alertas
- Top 10 setores por receita

### 2. Análise Setorial
- Análise detalhada por código CNAE
- Métricas setoriais:
  - Quantidade de empresas (total, ativas, relevantes)
  - Faturamento agregado
  - Estatísticas de alíquota efetiva (mediana, média, desvio padrão, P25/P75)
  - Coeficiente de variação
- Gráficos gauge para visualização de alíquotas
- Análise de distribuição por porte (MICRO, PEQUENO, MÉDIO, GRANDE)
- Evolução temporal (8 meses)
- Classificação de volatilidade

### 3. Análise Empresarial
- Busca de empresas por CNPJ
- Métricas individuais:
  - Faturamento, ICMS devido, alíquota efetiva
  - Comparação com benchmarks setoriais
  - Classificação de status (MUITO_ABAIXO, ABAIXO, NORMAL, ACIMA, MUITO_ACIMA)
  - Índice vs mediana do setor
- Gráficos de evolução empresa vs setor
- Dados históricos de todos os períodos

### 4. Alertas e Anomalias
- Múltiplos tipos de alertas
- Níveis de severidade (CRÍTICO, ALTO, MÉDIO, BAIXO)
- Detecção de anomalias:
  - Alta volatilidade interna
  - Alíquotas significativamente acima/abaixo da média econômica
  - Identificação de outliers
- Scoring de severidade baseado em desvios estatísticos
- Scoring de relevância incorporando volume de faturamento

### 5. Evolução Temporal
- Acompanhamento histórico de 8 meses
- Evolução setorial:
  - Métricas médias ao longo do tempo
  - Classificação de volatilidade
  - Análise de tendência (CRESCENTE, DECRESCENTE, ESTÁVEL)
- Evolução empresarial:
  - Dados históricos de declarações
  - Rastreamento de movimentações/omissões
  - Métricas de volatilidade
  - Flags de divergência (ICMS vs pagamentos)

### 6. Análise de Volatilidade
- Análise do coeficiente de variação
- Avaliação de estabilidade setorial
- Comparação setor vs economia
- Scatter plots: volatilidade vs alíquota
- Indicadores de estabilidade institucional

### 7. Análise de Pagamentos
- Comparativo ICMS devido vs pagamentos realizados
- Detecção de divergências
- Análise de frequência de pagamentos
- Top empresas com gaps de pagamento
- Rastreamento acumulado de pagamentos

### 8. Machine Learning
- **Aba de Treinamento:**
  - Seleção de modelo (Gradient Boosting vs Random Forest)
  - Engenharia de features
  - Split treino/teste (70/30)
  - Métricas de performance (Accuracy, Precision, Recall, F1-Score)
  - Visualização de matriz de confusão
  - Análise de importância de features

- **Aba de Predição de Risco:**
  - Identificação de empresas de alto risco
  - Scoring de probabilidade (0-100%)
  - Exportação para CSV

- **Aba de Análise de Features:**
  - Distribuição de features por tipo de empresa
  - Histogramas de distribuição de probabilidade

### 9. Análises Avançadas
- Evolução temporal comparativa
- Análise de tendência de volatilidade
- Análise de divergência ICMS vs pagamento
- Comparações multi-setoriais
- Análise top 20 setores

### 10. Relatórios
- Geração de sumário executivo
- Agregação de métricas de volume
- Resumos de alertas/anomalias
- Extração de principais achados
- Recomendações estratégicas
- Exportação CSV de alertas

---

## Esquema de Banco de Dados

O sistema utiliza as seguintes tabelas no banco `niat`:

| Tabela | Descrição |
|--------|-----------|
| `argos_benchmark_setorial` | Benchmarks mensais setoriais |
| `argos_benchmark_setorial_porte` | Benchmarks por porte empresarial |
| `argos_empresas` | Dados individuais de empresas |
| `argos_pagamentos_empresa` | Agregados mensais de pagamentos |
| `argos_empresa_vs_benchmark` | Comparações empresa vs setor |
| `argos_evolucao_temporal_setor` | Tendências temporais setoriais |
| `argos_evolucao_temporal_empresa` | Tendências temporais de empresas |
| `argos_anomalias_setoriais` | Anomalias detectadas |
| `argos_alertas_empresas` | Alertas gerados |

### Tabelas Fonte
- `usr_sat_ods.vw_ods_decl_dime` - Views de dimensão de declarações
- `usr_sat_ods.vw_ods_contrib` - Dados de contribuintes
- `usr_sat_ods.vw_ods_pagamento` - Registros de pagamentos

---

## Métricas Principais

### Métricas Financeiras
- Faturamento
- Receita bruta
- ICMS devido
- ICMS a recolher
- Valores de entrada/saída

### Métricas Tributárias
- Alíquota efetiva
- Alíquota efetiva mediana
- Coeficiente de variação
- Percentis (P25, P75)
- Desvio padrão

### Métricas Operacionais
- Quantidade de empresas
- Empresas ativas
- Empresas relevantes
- Quantidade de funcionários
- Contagens e valores de pagamentos

### Métricas de Risco
- Tipos e scores de severidade de anomalias
- Classificação e scoring de alertas
- Flags de divergência (pagamento vs declaração)
- Categorias de volatilidade (ALTA, MÉDIA, BAIXA)
- Probabilidade de risco ML (0-100%)

---

## Performance e Otimizações

- **Cache de longa duração (4 horas)**: Listas de períodos, listas de setores, tipos de alertas
- **Cache de média duração (2 horas)**: Dados de benchmark, dados de empresas, evolução temporal
- **Cache de curta duração**: Renderização de gráficos
- **Carregamento sob demanda**: Lazy loading de dados
- **Botão de limpeza de cache**: Disponível na barra lateral

---

## Considerações e Limitações

1. **Requisitos de Dados:**
   - Mínimo de 3 registros por grupo para cálculos estatísticos
   - Mínimo de 5 empresas por setor para benchmarking
   - Janela de dados históricos de 8 meses

2. **Escopo Geográfico:**
   - Apenas estado de Santa Catarina
   - Interface em português brasileiro

3. **Performance:**
   - Queries grandes podem timeout em redes lentas
   - Modelos de ML treinados sob demanda (não persistidos)

---

## Contribuição

Este é um projeto interno da Receita Estadual de Santa Catarina. Para contribuições ou sugestões, entre em contato com a equipe de desenvolvimento.

---

## Changelog

### v4.1 (Versão Atual)
- Tooltips aprimorados com explicações detalhadas de métricas
- Melhorias de UX com badges de status e codificação por cores
- Capacidades expandidas de ML com predição de risco
- Detecção avançada de anomalias
- Funcionalidade de geração de relatórios

---

## Licença

Projeto de uso interno da Secretaria da Fazenda do Estado de Santa Catarina (SEF/SC).

---

## Contato

**Organização:** Receita Estadual de Santa Catarina
**Sistema:** ARGOS SETORES - Análise Tributária Setorial
