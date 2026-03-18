import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

USER = os.getenv('DB_USER')
PASSWORD = os.getenv('DB_PASSWORD')
HOST = os.getenv('DB_HOST')
PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

conn_string = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}'

def extrair_dados(caminho_posicoes, caminho_fluxo):
    if not os.path.exists(caminho_posicoes) or not os.path.exists(caminho_fluxo):
        print("ERRO: Arquivos de entrada não encontrados!")
        sys.exit()

    print("Iniciando a leitura dos arquivos...")
    df_posicoes = pd.read_csv(caminho_posicoes)
    df_fluxo = pd.read_csv(caminho_fluxo)
    
    return df_posicoes, df_fluxo

def transformar_dados(df_posicoes, df_fluxo):
    print("Processando e calculando os KPIs...")
    
    df_posicoes['Mes_Ref'] = pd.to_datetime(df_posicoes['Dia']).dt.to_period('M')
    df_fluxo['Mes_Ref'] = pd.to_datetime(df_fluxo['Mês']).dt.to_period('M')

    df_fluxo['Captação_Liquida'] = df_fluxo['Aportes'] - df_fluxo['Resgates']
    kpi_captacao = df_fluxo.groupby(['Mes_Ref', 'cnpj_do_fundo'])[['Aportes', 'Resgates', 'Captação_Liquida']].sum().reset_index()

    kpi_aum = df_posicoes.groupby(['Mes_Ref', 'cnpj_do_fundo', 'nome_fundo'])['PL_Investido'].sum().reset_index()
    kpi_aum = kpi_aum.rename(columns={'PL_Investido': 'AUM_Total'})

    exposicao_mercado = df_posicoes.groupby(['Mes_Ref', 'cnpj_do_fundo', 'mercado_ativo_investido'])['PL_Investido'].sum().reset_index()
    kpi_exposicao = pd.merge(exposicao_mercado, kpi_aum[['Mes_Ref', 'cnpj_do_fundo', 'AUM_Total']], on=['Mes_Ref', 'cnpj_do_fundo'], how='left')
    kpi_exposicao['Percentual_Exposicao'] = (kpi_exposicao['PL_Investido'] / kpi_exposicao['AUM_Total']) * 100

    ativos_agrupados = df_posicoes.groupby(['Mes_Ref', 'cnpj_do_fundo', 'Symbol_Ativo_Investido'])['PL_Investido'].sum().reset_index()
    ativos_agrupados = pd.merge(ativos_agrupados, kpi_aum[['Mes_Ref', 'cnpj_do_fundo', 'AUM_Total']], on=['Mes_Ref', 'cnpj_do_fundo'], how='left')
    ativos_agrupados['Peso_Ativo_%'] = (ativos_agrupados['PL_Investido'] / ativos_agrupados['AUM_Total']) * 100

    ativos_ordenados = ativos_agrupados.sort_values(by=['Mes_Ref', 'cnpj_do_fundo', 'Peso_Ativo_%'], ascending=[True, True, False])
    top_5_ativos = ativos_ordenados.groupby(['Mes_Ref', 'cnpj_do_fundo']).head(5)

    kpi_concentracao = top_5_ativos.groupby(['Mes_Ref', 'cnpj_do_fundo'])['Peso_Ativo_%'].sum().reset_index()
    kpi_concentracao = kpi_concentracao.rename(columns={'Peso_Ativo_%': 'Concentracao_Top5_%'})

    df_rentabilidade = pd.merge(kpi_aum, kpi_captacao[['Mes_Ref', 'cnpj_do_fundo', 'Captação_Liquida']], on=['Mes_Ref', 'cnpj_do_fundo'], how='left')
    df_rentabilidade['Captação_Liquida'] = df_rentabilidade['Captação_Liquida'].fillna(0)
    df_rentabilidade = df_rentabilidade.sort_values(by=['cnpj_do_fundo', 'Mes_Ref'])
    df_rentabilidade['PL_Mes_Anterior'] = df_rentabilidade.groupby('cnpj_do_fundo')['AUM_Total'].shift(1)
    df_rentabilidade['Lucro_Mensal'] = df_rentabilidade['AUM_Total'] - df_rentabilidade['PL_Mes_Anterior'] - df_rentabilidade['Captação_Liquida']
    df_rentabilidade['Rentabilidade_Mensal_%'] = (df_rentabilidade['Lucro_Mensal'] / df_rentabilidade['PL_Mes_Anterior']) * 100
    df_rentabilidade['Rentabilidade_Media_3M_%'] = df_rentabilidade.groupby('cnpj_do_fundo')['Rentabilidade_Mensal_%'].transform(lambda x: x.rolling(window=3, min_periods=1).mean())

    ultimo_mes = df_rentabilidade['Mes_Ref'].max()
    kpi_top3 = df_rentabilidade[df_rentabilidade['Mes_Ref'] == ultimo_mes].sort_values(by='Rentabilidade_Media_3M_%', ascending=False).head(3)

    tabelas_kpi = {
        'kpi_captacao_mensal': kpi_captacao,
        'kpi_aum_total': kpi_aum,
        'kpi_exposicao_classe': kpi_exposicao,
        'kpi_risco_concentracao': kpi_concentracao,
        'kpi_top3_recomendados': kpi_top3
    }

    for nome_tabela, df in tabelas_kpi.items():
        if 'Mes_Ref' in df.columns:
            df['Mes_Ref'] = df['Mes_Ref'].dt.to_timestamp()
            
    return tabelas_kpi

def carregar_dados(tabelas_kpi, str_conexao):
    print("Enviando dados para o PostgreSQL...")
    try:
        engine = create_engine(str_conexao)
        
        for nome_tabela, df in tabelas_kpi.items():
            df.to_sql(nome_tabela, con=engine, if_exists='replace', index=False)
            print(f" - Tabela '{nome_tabela}' criada/atualizada.")

        print("\nSucesso! Pipeline ETL concluído e dados gravados no banco.")
    except Exception as e:
        print(f"Erro ao conectar ou salvar no PostgreSQL: {e}")

def main():
    pasta_entrada = 'Arquivos_CSV'
    caminho_posicoes = f'{pasta_entrada}/amw_monthly_positions.csv'
    caminho_fluxo = f'{pasta_entrada}/amw_inflows_outflows.csv'

    df_pos, df_flux = extrair_dados(caminho_posicoes, caminho_fluxo)
    kpis = transformar_dados(df_pos, df_flux)
    carregar_dados(kpis, conn_string)

if __name__ == "__main__":
    main()