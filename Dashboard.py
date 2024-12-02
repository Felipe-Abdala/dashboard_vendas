import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(layout= 'wide')

#Função de formatar número
def formata_numero(valor, prefixo = ''):
	for unidade in ['', 'mil']:
		if valor < 1000:
			return f'{prefixo} {valor: .2f} {unidade}'
		valor /= 1000
	return f'{prefixo} {valor: .2f} milhões'



st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)
    
#Precisamos usar o "lower", pois a API não interpreta caracteres maiúsculos.
query_string = {'regiao':regiao.lower(), 'ano':ano}


# Requisção
response = requests.get(url)

# 1.Transformação da Requisição em JSON (via response.json)
# 2. Transformação do JSON em Dataframe
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')


#Filtro Vendedores
filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
#Opção para que caso não haja a marcação de nenhuma opção no Multiselect, que seja selecionado tudo
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]


## Tabelas
### Tabelas de receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum() #o right_index abaixo é devido ao "Local da compra" ter se tornado a única coluna.
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra','lat','lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending=False)


receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].sum().reset_index() # reset_index, pois as informações de Data que foram agrupadas se tornam automaticamente em Índices.
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)

### Tabelas de quantidade de vendas

### Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))


## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados,
								  lat = 'lat',
								  lon = 'lon',
								  scope = 'south america',
								  size = 'Preço',
								  template = 'seaborn',
								  hover_name = 'Local da compra',
								  hover_data = {'lat': False, 'lon': False},
								  title = 'Receita por estado')


fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = True,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')


fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True, # inputaremos o valor sobre cada coluna
                             title = 'Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title = 'Receita')

#Não precisamos atribuir o eixo X e Y no gráfico abaixo, pois ela só tem as infos que já de adequam automaticamente
fig_receita_categorias = px.bar(receita_categorias,
                                text_auto = True,
                                title = 'Receita por categoria')
fig_receita_categorias.update_layout(yaxis_title = 'Receita')



## Visualização no Streamlit
# Abas ('Tabs')
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])
# aba1
with aba1:
	coluna1, coluna2 = st.columns(2)
	with coluna1:
		st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
		st.plotly_chart(fig_mapa_receita, use_container_width= True)
		st.plotly_chart(fig_receita_estados, use_container_width= True)
	with coluna2:
		st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
		st.plotly_chart(fig_receita_mensal, use_container_width= True)
		st.plotly_chart(fig_receita_categorias, use_container_width= True)

# aba2
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))

# aba3
with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2, 10, 5)

    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                        x = 'sum',
                                        y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                        x = 'count',
                                        y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                        text_auto = True,
                                        title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width = True)
         
# Visualização de TABELA
#st.dataframe(dados)












#Desafio
#Em uma dessas abas, foi deixado o desafio de colocar gráficos relacionados a quantidade de vendas. Chegou o momento de praticar e resolver esse desafio, que pode ser dividido em 4 partes:
#
#    Construir um gráfico de mapa com a quantidade de vendas por estado.
#    Construir um gráfico de linhas com a quantidade de vendas mensal.
#    Construir um gráfico de barras com os 5 estados com maior quantidade de vendas.
#    Construir um gráfico de barras com a quantidade de vendas por categoria de produto. 
#
#Opinião do instrutor
#
#Tabelas
#
#Para resolver esse desafio, vamos primeiro construir as tabelas que servirão como fonte de dados para os gráficos, utilizando a biblioteca Pandas.
#
#Tabela de quantidade de vendas por estado:
#
#vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
#vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
#
#Tabela de quantidade de vendas mensal:
#
#vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
#vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
#vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()
#
#Tabela de quantidade de vendas por categoria de produtos:
#
#vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))
#
#Gráficos
#
#Agora, vamos criar os gráficos usando a biblioteca Plotly.
#
#Gráfico de mapa de quantidade de vendas por estado:
#
#fig_mapa_vendas = px.scatter_geo(vendas_estados, 
#                     lat = 'lat', 
#                     lon= 'lon', 
#                     scope = 'south america', 
#                     #fitbounds = 'locations', 
#                     template='seaborn', 
#                     size = 'Preço', 
#                     hover_name ='Local da compra', 
#                     hover_data = {'lat':False,'lon':False},
#                     title = 'Vendas por estado',
#                     )
#
#Gráfico de quantidade de vendas mensal:
#
#fig_vendas_mensal = px.line(vendas_mensal, 
#              x = 'Mes',
#              y='Preço',
#              markers = True, 
#              range_y = (0,vendas_mensal.max()), 
#              color = 'Ano', 
#              line_dash = 'Ano',
#              title = 'Quantidade de vendas mensal')
#
#fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')
#
#Gráfico dos 5 estados com maior quantidade de vendas:
#
#fig_vendas_estados = px.bar(vendas_estados.head(),
#                             x ='Local da compra',
#                             y = 'Preço',
#                             text_auto = True,
#                             title = 'Top 5 estados'
#)
#
#fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')
#
#Gráfico da quantidade de vendas por categoria de produto:
#
#fig_vendas_categorias = px.bar(vendas_categorias, 
#                                text_auto = True,
#                                title = 'Vendas por categoria')
#fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')
#
#Inserir elementos no Streamlit
#
#Por fim, vamos inserir os elementos gráficos na 2ª aba do nosso aplicativo, referente a quantidade de vendas:
#
#with aba2:
#    coluna1, coluna2 = st.columns(2)
#    with coluna1:
#        st.metric('Receita', formatar_numero(dados['Preço'].sum(), 'R$'))
#        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
#        st.plotly_chart(fig_vendas_estados, use_container_width = True)
#
#    with coluna2:
#        st.metric('Quantidade de vendas', formatar_numero(dados.shape[0]))
#        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
#        st.plotly_chart(fig_vendas_categorias, use_container_width = True)