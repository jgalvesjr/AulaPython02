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
for regiao, paises in regioes.items():
    placeholders = ','.join([f'"{p}"' for p in paises])
    print(placeholders)
    dados.append({'Regiao': regiao})

    print(' ')
    print(dados)

with sqlite3.connect(r"C:\Users\integral\Desktop\Python2_Joao\bancodados.db") as conn:
            query = f'''
                SELECT SUM(total_litres_of_pure_alcohol) AS total from bebidas
                WHERE country IN ({placeholders})
            '''
            total = pd.read_sql_query(query, conn).iloc[0]
            print(total)
dfRegioes = pd.DataFrame(dados)

print(dfRegioes)
