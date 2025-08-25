from flask import Flask, request, render_template, render_template_string
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.io as pio
import random
    
regioes = {
        "Europa":['France','Germany','Italy','Spain','Portugal'],
        "Asia":['China','Japan','India','Thailand'],
        "Africa":['Angola','Nigeria','Egypt','Algeria'],
        "Americas":['USA','Brazil','Canada','Argentina','Mexico']
    }
dados = []
with sqlite3.connect(r"C:\Users\integral\Desktop\Python2_Joao\bancodados.db") as conn:
    #item percore os valores internos da variavel regioes - na variavel paises, coloca todos os paises da linha
    for regiao, paises in regioes.items():
        #criando a lista de placeholders para os paises dessa regiao no fomato pais1, pais2,....
        #isso vai ser utilizado na conulta sql para filtrar os paises da região. PlaceHolder = jucao
        placeholders = ','.join([f'"{p}"' for p in paises])
        query = f'''
            SELECT SUM(total_litres_of_pure_alcohol) AS total from bebidas
            WHERE country IN ({placeholders})
        '''
        #como a consulta vai retornasr um unico valor (soma) pegamos o primeiro valor usando [0] se o resultado for none (sem dados) retornaremos o para evitar
        #erros
        total = pd.read_sql_query(query, conn).iloc[0,0]
        # adicionar o resultado ao dicionaro 'dados', para cada regiao com o consumo total calculado
        dados.append({'Regiao': regiao, 'Consumo Total': total})
        print(total)
dfRegioes = pd.DataFrame(dados)
dfRegioes.to_excel('dados_saida123.xlsx', index=False)

print(dfRegioes)

#This result is a Pandas Series, which by default prints the Name and dtype, and that might be causing formatting or integration issues.

#✅ How to fix it

#You want to extract the actual number (float) from the result and avoid printing the Series metadata.

#Assuming you do something like:

#result = pd.read_sql_query(query, conn)
#total = result.iloc[0, 0]   # Get the value directly from DataFrame
#print(total)