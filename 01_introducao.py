import pandas as pd

#Armazena a string do camnho
caminho = 'C:/Users/integral/Desktop/Python2_Joao/01_base_vendas.xlsx'

df1 = pd.read_excel(caminho, sheet_name='Relatório de Vendas')
df2 = pd.read_excel(caminho, sheet_name='Relatório de Vendas1')

print('Primeiro relatorio de venda')
print(df1.head())

print('Segundo relatorio de venda')
print(df2.head())


#juntar os dois dataframes em um unico dataframe consolidado
#o ignore index vai garantir qye o indice seja reordenado apos a juncao
dfConsolidado = pd.concat([df1,df2], ignore_index=True)

print('\n-----------------------------------------------------------------\n')
print('Consolidado')
print(dfConsolidado)
print('\n-----------------------------------------------------------------\n')
print('Consolidado Duplicado.')
print(dfConsolidado.duplicated().sum())

print('')
#verifica quantos registros duplicados existem no relatorio - usando sum para fazer a conta - nesse exemplo linha igual
print('\n-----------------------------------------------------------------\n')
print('Duplicados no relatorio de vendas')
print(df1.duplicated().sum())

#agrupar clientes por cidade
print('\n-----------------------------------------------------------------\n')
clientePorCidade = dfConsolidado.groupby('Cidade')['Cliente'].nunique().sort_values(ascending=False)

print('Clientes por cidade\n')
print(clientePorCidade)


#NUmero de vendas por plano
print('\n-----------------------------------------------------------------\n')
print('Numero de vendas por plano')
vendasPorPlano = dfConsolidado['Plano Vendido'].value_counts()
print(vendasPorPlano)

#selecionar as 3 maiores cidades em numerod de clientes distintos
print('\n-----------------------------------------------------------------\n')
topTresCidades = clientePorCidade.head(3)
print('Top 3 cidades em vendas')
print(topTresCidades)


#Crie uma nova coluna chamda status com base no plano vendido
#Se o plano for enterprise o status sera premium, caso contrario sera padrao
#funcao lambda
#dfConsolidado['Status']  - cria colunna Status 
#apply - executa no panda a funcao lambda
print('\n-----------------------------------------------------------------\n')
dfConsolidado['Status'] =  dfConsolidado['Plano Vendido'].apply(lambda x: 'Premium' if x == 'Enterprise' else 'Padrao' )
#conta quantos registros há em cada tipo de status (premium e padrao)
statusDist = dfConsolidado['Status'].value_counts()
print('Distribuicao de status dos planos')
print(statusDist)

#salva dados em csv e xlsx
print('\n-----------------------------------------------------------------\n')
try:
    dfConsolidado.to_excel('dados_saida.xlsx', index=False)
    dfConsolidado.to_csv('dados_saida.csv', index=False)
    print('Arquivos foram gerados com sucesso')
except:
    print('Erro ao gerar os aqruivos, contate o adminstrador')


