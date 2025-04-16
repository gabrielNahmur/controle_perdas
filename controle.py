import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io
import numpy as np
import shutil

ARQUIVO_DADOS = 'dados_quebras.csv'
ARQUIVO_PRECOS = 'precos.csv'

# Inicializar o estado da sessão
if 'df' not in st.session_state:
    try:
        st.session_state.df = pd.read_csv(ARQUIVO_DADOS, dtype={'Filial': str})
        st.session_state.df['Data'] = pd.to_datetime(st.session_state.df['Data'], errors='coerce')
        
        # Verificar datas inválidas
        if st.session_state.df['Data'].isna().any():
            st.error("Existem datas inválidas no arquivo CSV. Corrija antes de continuar.")
            st.stop()
    except FileNotFoundError:
        st.error(f"Arquivo {ARQUIVO_DADOS} não encontrado.")
        st.stop()

# Carrega dados de preços
if os.path.exists(ARQUIVO_PRECOS):
    df_precos = pd.read_csv(ARQUIVO_PRECOS)
    # Tratar NaN na coluna 'Produto'
    df_precos['Produto'] = df_precos['Produto'].fillna('Desconhecido')
else:
    df_precos = pd.DataFrame(columns=['COD VIP', 'Produto', 'Custo Unitário', 'Preço Venda Unitário'])

st.set_page_config(page_title="Controle de Quebras", layout="wide")
st.title("📉 Controle de Quebras de Salgados")

menu = st.sidebar.selectbox("Menu", ["Registrar Quebra", "Relatório", "Análise", "Importar Planilha", "Preços"])

# Atualizar o DataFrame global
df = st.session_state.df

if menu == "Registrar Quebra":
    st.header("➕ Registrar, Editar ou Excluir Quebra")

    modo = st.radio("Modo", ["Novo Registro", "Editar Registro Existente", "Excluir Registro"])

    if modo == "Novo Registro":
        with st.form("form_quebra"):
            data = st.date_input("Data", value=datetime.today())
            produto = st.selectbox("Produto", options=[""] + list(df_precos['Produto'].unique()), help="Selecione um produto ou digite um novo")
            if not produto:
                produto_novo = st.text_input("Novo Produto (se não listado)")
            else:
                produto_novo = produto
            vendidos = st.number_input("Vendidos", min_value=0, step=1)
            quebra = st.number_input("Quebra", min_value=0, step=1)
            filial = st.selectbox("Filial", options=[""] + list(df['Filial'].unique()), help="Selecione uma filial ou digite uma nova")
            if not filial:
                filial_nova = st.text_input("Nova Filial (se não listada)")
            else:
                filial_nova = filial
            submit = st.form_submit_button("Registrar")

            if submit:
                if not produto_novo:
                    st.error("O campo Produto é obrigatório.")
                elif not filial_nova:
                    st.error("O campo Filial é obrigatório.")
                else:
                    total = vendidos + quebra
                    perc_quebra = (quebra / total) * 100 if total > 0 else 0

                    # Calcular Lucro Bruto
                    preco_info = df_precos[df_precos['Produto'] == produto_novo]
                    if not preco_info.empty:
                        custo_unit = preco_info['Custo Unitário'].iloc[0]
                        preco_venda = preco_info['Preço Venda Unitário'].iloc[0]
                        lucro_bruto = (preco_venda * vendidos) - (custo_unit * (vendidos + quebra))
                    else:
                        st.warning(f"Produto {produto_novo} sem preço cadastrado. Lucro Bruto será None.")
                        lucro_bruto = None

                    novo_registro = pd.DataFrame([{
                        'Data': data,
                        'Produto': produto_novo,
                        'Vendidos': vendidos,
                        'Quebra': quebra,
                        '% Quebra': round(perc_quebra, 2),
                        'Filial': filial_nova,
                        'Lucro Bruto': lucro_bruto
                    }])

                    df = pd.concat([df, novo_registro], ignore_index=True)
                    df.to_csv(ARQUIVO_DADOS, index=False)
                    st.success("Registro adicionado com sucesso!")

    elif modo == "Editar Registro Existente" and not df.empty:
        df_sorted = df.sort_values(by="Data", ascending=False)
        df_sorted['Resumo'] = df_sorted.apply(lambda x: f"{x['Data'].date()} | {x['Produto']} | {x['Filial']}", axis=1)
        selecao = st.selectbox("Selecione um registro para editar", df_sorted['Resumo'])

        idx = df_sorted[df_sorted['Resumo'] == selecao].index[0]
        registro = df.loc[idx]

        with st.form("form_editar_quebra"):
            data = st.date_input("Data", value=pd.to_datetime(registro['Data']))
            produto = st.selectbox("Produto", options=[""] + list(df_precos['Produto'].unique()), index=0 if registro['Produto'] not in df_precos['Produto'].unique() else list(df_precos['Produto'].unique()).index(registro['Produto']) + 1)
            if not produto:
                produto_novo = st.text_input("Novo Produto (se não listado)", value=registro['Produto'])
            else:
                produto_novo = produto
            vendidos = st.number_input("Vendidos", min_value=0, step=1, value=int(registro['Vendidos']))
            quebra = st.number_input("Quebra", min_value=0, step=1, value=int(registro['Quebra']))
            filial = st.selectbox("Filial", options=[""] + list(df['Filial'].unique()), index=0 if registro['Filial'] not in df['Filial'].unique() else list(df['Filial'].unique()).index(registro['Filial']) + 1)
            if not filial:
                filial_nova = st.text_input("Nova Filial (se não listada)", value=registro['Filial'])
            else:
                filial_nova = filial
            submit = st.form_submit_button("Salvar Alterações")

            if submit:
                try:
                    if not produto_novo:
                        st.error("O campo Produto é obrigatório.")
                    elif not filial_nova:
                        st.error("O campo Filial é obrigatório.")
                    else:
                        total = vendidos + quebra
                        perc_quebra = (quebra / total) * 100 if total > 0 else 0

                        # Calcular Lucro Bruto
                        preco_info = df_precos[df_precos['Produto'] == produto_novo]
                        if not preco_info.empty:
                            custo_unit = preco_info['Custo Unitário'].iloc[0]
                            preco_venda = preco_info['Preço Venda Unitário'].iloc[0]
                            lucro_bruto = (preco_venda * vendidos) - (custo_unit * (vendidos + quebra))
                        else:
                            st.warning(f"Produto {produto_novo} sem preço cadastrado. Lucro Bruto será None.")
                            lucro_bruto = None

                        df.loc[idx, :] = {
                            'Data': data,
                            'Produto': produto_novo,
                            'Vendidos': vendidos,
                            'Quebra': quebra,
                            '% Quebra': round(perc_quebra, 2),
                            'Filial': filial_nova,
                            'Lucro Bruto': lucro_bruto
                        }

                        df.to_csv(ARQUIVO_DADOS, index=False)
                        st.session_state.df = df
                        st.success("Registro atualizado com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar registro: {str(e)}")

    elif modo == "Excluir Registro" and not df.empty:
        st.header("🗑️ Excluir Registros")
        
        # Opções de exclusão
        tipo_exclusao = st.radio("Selecione o tipo de exclusão:", 
                                ["Excluir Registro Individual", "Excluir por Período e Filial"])
        
        if tipo_exclusao == "Excluir Registro Individual":
            # Ordenar registros por data (mais recentes primeiro)
            df_sorted = df.sort_values(by="Data", ascending=False)
            
            # Criar resumo para exibição
            df_sorted['Resumo'] = df_sorted.apply(
                lambda x: f"{x['Data'].date()} | {x['Produto']} | {x['Filial']} | {x['Vendidos']} vendidos | {x['Quebra']} quebras",
                axis=1
            )
            
            # Selecionar registro
            selecao = st.selectbox("Selecione um registro para excluir:", df_sorted['Resumo'])
            
            # Encontrar índice do registro selecionado
            idx = df_sorted[df_sorted['Resumo'] == selecao].index[0]
            
            # Exibir detalhes do registro
            st.subheader("Detalhes do Registro Selecionado:")
            st.dataframe(df.loc[[idx]])
            
            # Botão de confirmação
            if st.button("Confirmar Exclusão do Registro"):
                try:
                    # Criar backup
                    shutil.copy(ARQUIVO_DADOS, ARQUIVO_DADOS + ".backup")
                    
                    # Excluir registro
                    df_novo = df.drop(idx).reset_index(drop=True)
                    
                    # Salvar alterações
                    df_novo.to_csv(ARQUIVO_DADOS, index=False)
                    
                    # Atualizar o DataFrame na sessão
                    st.session_state.df = df_novo
                    
                    st.success("Registro excluído com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao excluir registro: {e}")
        
        else:  # Excluir por Período e Filial
            st.subheader("Excluir Registros por Período e Filial")
            
            # Seleção de período
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data Inicial", value=df['Data'].min())
            with col2:
                data_fim = st.date_input("Data Final", value=df['Data'].max())
            
            # Seleção de filiais
            filiais = st.multiselect(
                "Selecione as Filiais:",
                options=df['Filial'].unique(),
                default=df['Filial'].unique()
            )
            
            # Converter datas para datetime
            inicio = pd.to_datetime(data_inicio)
            fim = pd.to_datetime(data_fim)
            
            # Criar máscara de filtro
            mask = (df['Data'] >= inicio) & (df['Data'] <= fim) & (df['Filial'].isin(filiais))
            registros_filtrados = df[mask]
            
            if not registros_filtrados.empty:
                st.subheader("Registros Encontrados:")
                st.write(f"Total de registros: {len(registros_filtrados)}")
                st.dataframe(registros_filtrados)
                
                # Botão de confirmação
                if st.button("Confirmar Exclusão dos Registros"):
                    try:
                        # Excluir registros
                        df_novo = df[~mask].copy()
                        
                        # Salvar alterações
                        df_novo.to_csv(ARQUIVO_DADOS, index=False)
                        
                        # Atualizar o DataFrame na sessão
                        st.session_state.df = df_novo
                        
                        st.success(f"{len(registros_filtrados)} registros excluídos com sucesso!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao excluir registros: {str(e)}")
            else:
                st.warning("Nenhum registro encontrado para os critérios selecionados.")

elif menu == "Relatório":
    st.header("📊 Relatório de Quebras")

    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])

        filial = st.multiselect("Filial", df['Filial'].unique(), default=list(df['Filial'].unique()))
        produtos = st.multiselect("Produto", df['Produto'].unique(), default=list(df['Produto'].unique()))
        datas = st.date_input("Período", [df['Data'].min(), df['Data'].max()])

        if len(datas) == 2:
            df_filt = df[
                (df['Filial'].isin(filial)) &
                (df['Produto'].isin(produtos)) &
                (df['Data'] >= pd.to_datetime(datas[0])) &
                (df['Data'] <= pd.to_datetime(datas[1]))
            ].copy()

            if not df_filt.empty:
                df_relatorio = pd.merge(df_filt, df_precos[['Produto', 'Custo Unitário', 'Preço Venda Unitário']],
                                        on='Produto', how='left')
                colunas_para_remover = ['Inicial', 'Estoque Final']
                df_relatorio.drop(columns=[col for col in colunas_para_remover if col in df_relatorio.columns], inplace=True)

                st.dataframe(df_relatorio)

                # Exportar como CSV
                csv = df_relatorio.to_csv(index=False)
                st.download_button(
                    label="Exportar como CSV",
                    data=csv,
                    file_name="relatorio_quebras.csv",
                    mime="text/csv"
                )

                # Exportar como Excel
                excel_buffer = io.BytesIO()
                df_relatorio.to_excel(excel_buffer, index=False, engine='openpyxl')
                st.download_button(
                    label="Exportar como Excel",
                    data=excel_buffer,
                    file_name="relatorio_quebras.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                total_lucro = df_relatorio['Lucro Bruto'].sum()
                st.metric("Lucro Bruto Total", f"R$ {total_lucro:,.2f}")
            else:
                st.warning("Nenhum dado disponível para o filtro selecionado.")
        else:
            st.error("Selecione um período válido.")
    else:
        st.warning("Nenhum dado disponível para exibir.")

elif menu == "Análise":
    st.header("📈 Análise de Quebras - Dashboard")

    if not df.empty:
        df['Data'] = pd.to_datetime(df['Data'])

        # Filtros em uma única linha
        col1, col2, col3 = st.columns(3)
        with col1:
            filial = st.multiselect("Filial", df['Filial'].unique(), default=list(df['Filial'].unique()))
        with col2:
            produtos = st.multiselect("Produto", df['Produto'].unique(), default=list(df['Produto'].unique()))
        with col3:
            ano = st.selectbox("Ano", sorted(df['Data'].dt.year.unique()), index=len(sorted(df['Data'].dt.year.unique()))-1)

        df_filt = df[
            (df['Filial'].isin(filial)) &
            (df['Produto'].isin(produtos)) &
            (df['Data'].dt.year == ano)
        ].copy()

        if not df_filt.empty:
            # Preparar dados
            df_filt['Mês'] = df_filt['Data'].dt.month
            meses = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                     7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}

            # Criar DataFrames separados para cada métrica
            quebras_df = df_filt.pivot_table(
                values='Quebra',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).astype(int)

            vendas_df = df_filt.pivot_table(
                values='Vendidos',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).astype(int)

            # Corrigindo o cálculo da porcentagem
            perc_quebra_df = (quebras_df / vendas_df * 100).fillna(0).round(1)

            margem_df = df_filt.pivot_table(
                values='Lucro Bruto',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).round(2)

            # Renomear colunas com nomes dos meses
            for df_temp in [quebras_df, vendas_df, perc_quebra_df, margem_df]:
                df_temp.columns = [meses[m] for m in df_temp.columns]

            # Criar abas para diferentes visualizações
            tab1, tab2, tab3 = st.tabs(["Quebras e Vendas", "% Quebra", "Margem Bruta"])

            with tab1:
                # Quebras
                st.subheader("Quebras")
                st.dataframe(
                    quebras_df.style.format("{:,.0f}")
                        .applymap(lambda x: f'background-color: {"#ffcccc" if x > 0 else "white"}; color: black'),
                    use_container_width=True
                )

                # Vendas
                st.subheader("Vendas")
                st.dataframe(
                    vendas_df.style.format("{:,.0f}")
                        .applymap(lambda x: f'background-color: {"#cce5ff" if x > 0 else "white"}; color: black'),
                    use_container_width=True
                )

            with tab2:
                # % Quebra
                st.subheader("% Quebra sobre Venda")
                st.dataframe(
                    perc_quebra_df.style.format("{:.1f}%")
                        .applymap(lambda x: f'background-color: {"#ffcccc" if x > 8 else "#ccffcc"}; color: {"red" if x > 8 else "darkgreen"}'),
                    use_container_width=True
                )

            with tab3:
                # Margem Bruta
                st.subheader("Margem Bruta")
                st.dataframe(
                    margem_df.style.format("R$ {:,.2f}")
                        .applymap(lambda x: f'background-color: {"#ccffcc" if x > 0 else "#ffcccc"}; color: {"darkgreen" if x > 0 else "red"}'),
                    use_container_width=True
                )

            # Totais
            st.subheader("Totais do Período")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_quebras = quebras_df.sum().sum()
                st.metric("Total Quebras", f"{total_quebras:,.0f}")
            
            with col2:
                total_vendas = vendas_df.sum().sum()
                st.metric("Total Vendas", f"{total_vendas:,.0f}")
            
            with col3:
                perc_total = (total_quebras / total_vendas * 100)
                st.metric("% Quebra Média", f"{perc_total:.1f}%")
            
            with col4:
                total_margem = margem_df.sum().sum()
                st.metric("Margem Bruta Total", f"R$ {total_margem:,.2f}")

        else:
            st.warning("Nenhum dado disponível para o filtro selecionado.")
    else:
        st.warning("Nenhum dado disponível para análise.")

elif menu == "Importar Planilha":
    st.header("📥 Importar Planilha de Quebras")

    filial = st.text_input("Filial")
    mes = st.selectbox("Mês da quebra", list(range(1, 13)))
    ano = st.selectbox("Ano da quebra", list(range(2023, datetime.today().year + 1)))
    arquivo = st.file_uploader("Selecione a planilha Excel", type=[".xls", ".xlsx"])
    confirmar = st.button("Confirmar e Importar")

    if confirmar:
        if not filial or filial.strip() == "":
            st.error("O campo Filial é obrigatório. Por favor, informe a filial antes de importar a planilha.")
        elif not arquivo:
            st.error("Por favor, selecione uma planilha para importar.")
        else:
            try:
                # Ler a planilha
                df_planilha = pd.read_excel(arquivo)
                df_planilha.columns = df_planilha.columns.str.strip()

                if "DESCRIÇÃO" not in df_planilha.columns:
                    st.error("A planilha deve conter a coluna 'DESCRIÇÃO'.")
                else:
                    df_filtrado = df_planilha[["CÓD. VIP", "DESCRIÇÃO", "QUEBRA", "VENDA"]].copy()
                    df_filtrado.rename(columns={
                        "CÓD. VIP": "COD VIP",
                        "DESCRIÇÃO": "Produto",
                        "QUEBRA": "Quebra",
                        "VENDA": "Vendidos"
                    }, inplace=True)

                    # Garantir que 'Quebra' e 'Vendidos' sejam numéricos
                    df_filtrado['Quebra'] = pd.to_numeric(df_filtrado['Quebra'], errors='coerce').fillna(0)
                    df_filtrado['Vendidos'] = pd.to_numeric(df_filtrado['Vendidos'], errors='coerce').fillna(0)

                    # Agrupar por COD VIP e Produto
                    df_filtrado = df_filtrado.groupby(["COD VIP", "Produto"], as_index=False).agg({
                        "Quebra": "sum",
                        "Vendidos": "sum"
                    })

                    # Calcular % Quebra
                    df_filtrado['% Quebra'] = (df_filtrado['Quebra'] / (df_filtrado['Vendidos'] + df_filtrado['Quebra'])) * 100
                    df_filtrado['% Quebra'] = df_filtrado['% Quebra'].fillna(0).round(2)
                    df_filtrado['Data'] = pd.to_datetime(f"{ano}-{mes:02d}-01")
                    df_filtrado['Filial'] = filial

                    # Mesclar com preços
                    df_merge = pd.merge(df_filtrado, df_precos, on=['COD VIP', 'Produto'], how='left')

                    # Identificar produtos sem preço
                    produtos_sem_preco = df_merge[df_merge['Preço Venda Unitário'].isna()]['Produto'].unique()
                    if len(produtos_sem_preco) > 0:
                        st.warning(f"Os seguintes produtos estão sem preço cadastrado e não foram importados: {', '.join(produtos_sem_preco)}")
                        df_merge = df_merge[~df_merge['Produto'].isin(produtos_sem_preco)]

                    if not df_merge.empty:
                        # Calcular Lucro Bruto
                        df_merge['Lucro Bruto'] = (df_merge['Preço Venda Unitário'] * df_merge['Vendidos']) - (df_merge['Custo Unitário'] * (df_merge['Vendidos'] + df_merge['Quebra']))
                        colunas_df = ['Data', 'Produto', 'Vendidos', 'Quebra', '% Quebra', 'Filial', 'Lucro Bruto']
                        df_novo = df_merge[colunas_df]

                        # Adicionar ao DataFrame principal
                        df = pd.concat([df, df_novo], ignore_index=True)

                        # Salvar no arquivo
                        df.to_csv(ARQUIVO_DADOS, index=False)
                        st.session_state.df = df
                        st.success(f"Importação realizada com sucesso! {len(df_novo)} registros adicionados.")
                        st.rerun()
                    else:
                        st.warning("Nenhum dado foi importado pois todos os produtos estavam sem preço.")
            except Exception as e:
                st.error(f"Erro ao importar: {str(e)}")

elif menu == "Preços":
    st.header("💰 Cadastro e Edição de Preços")

    modo_preco = st.radio("Modo", ["Cadastrar Novo Preço", "Editar Preço Existente", "Excluir Preço"])

    if modo_preco == "Cadastrar Novo Preço":
        with st.form("form_precos"):
            cod_vip = st.text_input("Código VIP")
            produto = st.text_input("Nome do Produto")
            custo = st.number_input("Custo Unitário", min_value=0.0, format="%.2f")
            preco_venda = st.number_input("Preço Venda Unitário", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("Salvar")

            if submit:
                if preco_venda <= custo:
                    st.error("O Preço Venda Unitário deve ser maior que o Custo Unitário.")
                else:
                    novo_preco = pd.DataFrame([{
                        "COD VIP": cod_vip,
                        "Produto": produto,
                        "Custo Unitário": custo,
                        "Preço Venda Unitário": preco_venda
                    }])
                    df_precos = df_precos[~((df_precos["COD VIP"] == cod_vip) & (df_precos["Produto"] == produto))]
                    df_precos = pd.concat([df_precos, novo_preco], ignore_index=True)
                    df_precos.to_csv(ARQUIVO_PRECOS, index=False)
                    st.success("Preço salvo com sucesso!")
                    st.rerun()

    elif modo_preco == "Editar Preço Existente" and not df_precos.empty:
        produto_selecionado = st.selectbox("Selecione o Produto", df_precos['Produto'])
        preco_info = df_precos[df_precos['Produto'] == produto_selecionado].iloc[0]

        with st.form("form_editar_precos"):
            cod_vip = st.text_input("Código VIP", value=preco_info['COD VIP'])
            produto = st.text_input("Nome do Produto", value=preco_info['Produto'])
            custo = st.number_input("Custo Unitário", min_value=0.0, format="%.2f", value=float(preco_info['Custo Unitário']))
            preco_venda = st.number_input("Preço Venda Unitário", min_value=0.0, format="%.2f", value=float(preco_info['Preço Venda Unitário']))
            submit = st.form_submit_button("Salvar Alterações")

            if submit:
                if preco_venda <= custo:
                    st.error("O Preço Venda Unitário deve ser maior que o Custo Unitário.")
                else:
                    idx = df_precos[df_precos['Produto'] == produto_selecionado].index[0]
                    df_precos.loc[idx, :] = {
                        "COD VIP": cod_vip,
                        "Produto": produto,
                        "Custo Unitário": custo,
                        "Preço Venda Unitário": preco_venda
                    }
                    df_precos.to_csv(ARQUIVO_PRECOS, index=False)
                    st.success("Preço atualizado com sucesso!")
                    st.rerun()

    elif modo_preco == "Excluir Preço" and not df_precos.empty:
        st.subheader("🗑️ Excluir Preço")
        
        # Selecionar produto para excluir
        produto_selecionado = st.selectbox("Selecione o Produto para Excluir", df_precos['Produto'])
        
        if produto_selecionado:
            # Mostrar informações do produto
            preco_info = df_precos[df_precos['Produto'] == produto_selecionado].iloc[0]
            
            st.write("### Informações do Produto")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Código VIP:** {preco_info['COD VIP']}")
                st.write(f"**Produto:** {preco_info['Produto']}")
            with col2:
                st.write(f"**Custo Unitário:** R$ {preco_info['Custo Unitário']:.2f}")
                st.write(f"**Preço Venda:** R$ {preco_info['Preço Venda Unitário']:.2f}")
            
            # Botão de confirmação
            if st.button("Confirmar Exclusão do Preço"):
                try:
                    # Remover o produto do DataFrame
                    df_precos = df_precos[df_precos['Produto'] != produto_selecionado]
                    
                    # Salvar alterações
                    df_precos.to_csv(ARQUIVO_PRECOS, index=False)
                    
                    st.success(f"Preço do produto '{produto_selecionado}' excluído com sucesso!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao excluir preço: {str(e)}")

    st.subheader("📋 Tabela de Preços Cadastrados")
    st.dataframe(df_precos.style.format({
        'Custo Unitário': 'R$ {:.2f}',
        'Preço Venda Unitário': 'R$ {:.2f}'
    }), use_container_width=True)