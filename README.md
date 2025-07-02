# 🧾 Sistema de Controle de Quebras

Desenvolvido em **Streamlit** para controle de perdas (quebras) em lojas de conveniência. Automatiza a importação de dados de perda e venda, aplica os preços cadastrados e gera relatórios com análise de lucro bruto por unidade, item e período.

---

## 📌 Funcionalidades

✅ Importação de planilhas `.csv` com dados de perda e venda  
✅ Cadastro de preços (custo e venda) por item  
✅ Cálculo automático de lucro bruto após perdas  
✅ Filtros por filial, data e item  
✅ Visualizações em tabela e gráficos interativos  
✅ Armazenamento local em arquivos `.csv` por mês/filial  

---

## 🧠 Lógica de Funcionamento

1. O usuário importa uma planilha com os dados de quebra e venda (`CÓD. VIP`, `DESCRIÇÃO`, `QUEBRA`, `VENDA`)
2. Informa a **filial**, **mês** e **ano** para registrar os dados
3. O sistema armazena os dados em um arquivo `.csv` por período
4. Os preços cadastrados em outra aba (custo e venda) são usados para calcular:
   - Valor perdido (QUEBRA × Custo)
   - Lucro bruto = (VENDA × Preço de venda) - (QUEBRA × Custo)
5. O relatório permite análise detalhada por item, data ou unidade

---


