import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import io
import numpy as np

ARQUIVO_DADOS = 'dados_quebras.csv'
ARQUIVO_PRECOS = 'precos.csv'

st.set_page_config(page_title="Controle de Quebras", layout="wide")
st.title("📉 Controle de Quebras de Salgados")

menu = st.sidebar.selectbox("Menu", ["Registrar Quebra", "Relatório", "Análise", "Importar Planilha", "Preços"])

# Carrega dados principais
if os.path.exists(ARQUIVO_DADOS):
    df = pd.read_csv(ARQUIVO_DADOS, parse_dates=['Data'])
    # Tratar NaN na coluna 'Filial'
    df['Filial'] = df['Filial'].fillna('Desconhecida')
    # Garantir que a coluna 'Data' está no formato datetime
    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
else:
    df = pd.DataFrame(columns=[
        'Data', 'Produto', 'Vendidos', 'Quebra', '% Quebra',
        'Filial', 'Lucro Bruto'
    ])

# Carrega dados de preços
if os.path.exists(ARQUIVO_PRECOS):
    df_precos = pd.read_csv(ARQUIVO_PRECOS)
    # Tratar NaN na coluna 'Produto'
    df_precos['Produto'] = df_precos['Produto'].fillna('Desconhecido')
else:
    df_precos = pd.DataFrame(columns=['COD VIP', 'Produto', 'Custo Unitário', 'Preço Venda Unitário'])

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
                    st.success("Registro atualizado com sucesso!")

    elif modo == "Excluir Registro" and not df.empty:
        df_sorted = df.sort_values(by="Data", ascending=False)
        df_sorted['Resumo'] = df_sorted.apply(lambda x: f"{x['Data'].date()} | {x['Produto']} | {x['Filial']}", axis=1)
        selecao = st.selectbox("Selecione um registro para excluir", df_sorted['Resumo'])

        idx = df_sorted[df_sorted['Resumo'] == selecao].index[0]
        st.write("Registro selecionado:")
        st.dataframe(df.loc[[idx]])

        if st.button("Confirmar Exclusão"):
            df = df.drop(idx).reset_index(drop=True)
            df.to_csv(ARQUIVO_DADOS, index=False)
            st.success("Registro excluído com sucesso!")

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

        # Filtros
        filial = st.multiselect("Filial", df['Filial'].unique(), default=list(df['Filial'].unique()))
        produtos = st.multiselect("Produto", df['Produto'].unique(), default=list(df['Produto'].unique()))
        ano = st.selectbox("Ano", sorted(df['Data'].dt.year.unique()), index=len(sorted(df['Data'].dt.year.unique()))-1)

        df_filt = df[
            (df['Filial'].isin(filial)) &
            (df['Produto'].isin(produtos)) &
            (df['Data'].dt.year == ano)
        ].copy()

        if not df_filt.empty:
            # Preparar dados para o dashboard
            df_filt['Mês'] = df_filt['Data'].dt.month
            meses = {1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
                     7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez'}

            # Pivot para % Quebra por filial e mês
            pivot_quebra = df_filt.pivot_table(
                values='% Quebra',
                index='Filial',
                columns='Mês',
                aggfunc='mean'
            ).fillna(0).round(2)
            pivot_quebra.columns = [meses[m] for m in pivot_quebra.columns]

            # Pivot para Quebra Ponderada (soma de quebras)
            pivot_quebra_pond = df_filt.pivot_table(
                values='Quebra',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).astype(int)
            pivot_quebra_pond.columns = [meses[m] for m in pivot_quebra_pond.columns]

            # Pivot para Venda Ponderada (soma de vendidos)
            pivot_venda_pond = df_filt.pivot_table(
                values='Vendidos',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).astype(int)
            pivot_venda_pond.columns = [meses[m] for m in pivot_venda_pond.columns]

            # Pivot para Margem Bruta Após Quebra
            pivot_margem = df_filt.pivot_table(
                values='Lucro Bruto',
                index='Filial',
                columns='Mês',
                aggfunc='sum'
            ).fillna(0).round(2)
            pivot_margem.columns = [meses[m] for m in pivot_margem.columns]

            # Totais do grupo
            total_quebra_pond = pivot_quebra_pond.sum()
            total_venda_pond = pivot_venda_pond.sum()
            total_margem = pivot_margem.sum()

            # Média de % Quebra por mês (para o grupo)
            grupo_quebra = df_filt.groupby('Mês')['% Quebra'].mean().round(2)
            grupo_quebra.index = [meses[m] for m in grupo_quebra.index]
            grupo_quebra = grupo_quebra.reindex(list(meses.values()), fill_value=0)

            # Criar DataFrame consolidado para exibição
            consolidated_data = []
            for filial in pivot_quebra.index:
                row = {'Filial': filial}
                for mes in meses.values():
                    row[f'% Quebra ({mes})'] = pivot_quebra.loc[filial, mes] if mes in pivot_quebra.columns else 0
                    row[f'Pond. Quebra ({mes})'] = pivot_quebra_pond.loc[filial, mes] if mes in pivot_quebra_pond.columns else 0
                    row[f'Pond. Venda ({mes})'] = pivot_venda_pond.loc[filial, mes] if mes in pivot_venda_pond.columns else 0
                    row[f'Margem Bruta ({mes})'] = pivot_margem.loc[filial, mes] if mes in pivot_margem.columns else 0
                consolidated_data.append(row)

            # Adicionar linha de totais (Grupo)
            grupo_row = {'Filial': 'Grupo'}
            for mes in meses.values():
                grupo_row[f'% Quebra ({mes})'] = grupo_quebra[mes]
                grupo_row[f'Pond. Quebra ({mes})'] = total_quebra_pond[mes] if mes in total_quebra_pond.index else 0
                grupo_row[f'Pond. Venda ({mes})'] = total_venda_pond[mes] if mes in total_venda_pond.index else 0
                grupo_row[f'Margem Bruta ({mes})'] = total_margem[mes] if mes in total_margem.index else 0
            consolidated_data.append(grupo_row)

            df_consolidated = pd.DataFrame(consolidated_data)

            # Estilizar % Quebra (vermelho se > 81%, verde se <= 81%)
            def highlight_quebra(val):
                color = 'red' if val > 81 else 'green'
                return f'background-color: {color}'

            styled_df = df_consolidated.style.applymap(highlight_quebra, subset=[col for col in df_consolidated.columns if '% Quebra' in col])
            st.dataframe(styled_df, use_container_width=True)

            # Exibir métricas totais
            st.subheader("Totais do Grupo")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Ponderado Quebra", total_quebra_pond.sum())
            col2.metric("Total Ponderado Venda", total_venda_pond.sum())
            col3.metric("Total Margem Bruta", f"R$ {total_margem.sum():,.2f}")
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
                # Log: Exibir o estado inicial do DataFrame df
                st.write(f"Total de registros antes da importação: {len(df)}")
                st.dataframe(df)

                # Ler a planilha
                df_planilha = pd.read_excel(arquivo)
                df_planilha.columns = df_planilha.columns.str.strip()
                st.write(f"Total de linhas na planilha importada: {len(df_planilha)}")
                st.dataframe(df_planilha)

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
                    st.write(f"Total de linhas após agrupamento: {len(df_filtrado)}")
                    st.dataframe(df_filtrado)

                    # Calcular % Quebra
                    df_filtrado['% Quebra'] = (df_filtrado['Quebra'] / (df_filtrado['Vendidos'] + df_filtrado['Quebra'])) * 100
                    df_filtrado['% Quebra'] = df_filtrado['% Quebra'].fillna(0).round(2)
                    df_filtrado['Data'] = pd.to_datetime(f"{ano}-{mes:02d}-01")
                    df_filtrado['Filial'] = filial

                    # Mesclar com preços
                    st.write("Conteúdo do df_precos:")
                    st.dataframe(df_precos)
                    df_merge = pd.merge(df_filtrado, df_precos, on=['COD VIP', 'Produto'], how='left')
                    st.write(f"Total de linhas após mesclagem com preços: {len(df_merge)}")
                    st.dataframe(df_merge)

                    # Identificar produtos sem preço
                    produtos_sem_preco = df_merge[df_merge['Preço Venda Unitário'].isna()]['Produto'].unique()
                    if len(produtos_sem_preco) > 0:
                        st.warning(f"Os seguintes produtos estão sem preço cadastrado e não foram importados: {', '.join(produtos_sem_preco)}")
                        df_merge = df_merge[~df_merge['Produto'].isin(produtos_sem_preco)]
                        st.write(f"Total de linhas após remover produtos sem preço: {len(df_merge)}")
                        st.dataframe(df_merge)

                    if not df_merge.empty:
                        # Calcular Lucro Bruto
                        df_merge['Lucro Bruto'] = (df_merge['Preço Venda Unitário'] * df_merge['Vendidos']) - (df_merge['Custo Unitário'] * (df_merge['Vendidos'] + df_merge['Quebra']))
                        colunas_df = ['Data', 'Produto', 'Vendidos', 'Quebra', '% Quebra', 'Filial', 'Lucro Bruto']
                        df_novo = df_merge[colunas_df]
                        st.write(f"Total de linhas a serem adicionadas: {len(df_novo)}")
                        st.dataframe(df_novo)

                        # Adicionar ao DataFrame principal
                        df = pd.concat([df, df_novo], ignore_index=True)
                        st.write(f"Total de registros após adicionar novos dados: {len(df)}")
                        st.dataframe(df)

                        # Salvar no arquivo
                        df.to_csv(ARQUIVO_DADOS, index=False)
                        st.success(f"Importação realizada com sucesso! {len(df_novo)} registros adicionados.")
                    else:
                        st.warning("Nenhum dado foi importado pois todos os produtos estavam sem preço.")
            except Exception as e:
                st.error(f"Erro ao importar: {e}")

elif menu == "Preços":
    st.header("💰 Cadastro e Edição de Preços")

    modo_preco = st.radio("Modo", ["Cadastrar Novo Preço", "Editar Preço Existente"])

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

    st.subheader("📋 Tabela de Preços Cadastrados")
    st.dataframe(df_precos)