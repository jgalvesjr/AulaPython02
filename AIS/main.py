from flask import Flask, request, jsonify, render_template_string
import pandas as pd
import sqlite3
import os
import plotly.graph_objects as go
from dash import Dash, html, dcc
import numpy as np
import config
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
#pip install scikit-learn
#pip list

app = Flask(__name__)
caminhoBd = config.BD_PATH
rotas = config.ROTAS

def init_db():
    with sqlite3.connect(caminhoBd) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inadimplencia(
                mes TEXT PRIMARY KEY,
                inadimplencia REAL
            )

        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS selic(
                mes TEXT PRIMARY KEY,
                selic_diaria REAL
            )

        ''')
        conn.commit()
vazio = 0

@app.route(rotas[0])
def index():
    return render_template_string(f'''
        <h1>Upload de dados Economicos</h1>
        <form action="{rotas[1]}" method="POST" enctype="multipart/form-data">
            <label for="campo_inadimplencia">Arquivo de Inadimplencia (CSV)</<label>
            <input name="campo_inadimplencia" type="file" required><br>
            <label for="campo_selic">Arquivo de Taxa Selic (CSV)</<label>
            <input name="campo_selic" type="file" required><br>
            <input type="submit" value="Fazer Upload">
        </form>
        <br><br>
        <hr>
        <a href="{rotas[2]}">Consultar dados Armazenados</a><br>
        <a href="{rotas[3]}">Visualizar Graficos</a><br>
        <a href="{rotas[4]}">Editar dados de Inadimplencia</a><br>
        <a href="{rotas[5]}">Analisar Correlacao</a><br> 
        <a href="{rotas[6]}">Observabiliade em 3D</a><br>
        <a href="{rotas[7]}">Editar Selic</a><br>
    ''')

@app.route(rotas[1], methods=['POST', 'GET'])
def upload():
    #request pegar texto que venha de fora
    inad_file = request.files.get('campo_inadimplencia')
    selic_file = request.files.get('campo_selic')

    if not inad_file or not selic_file:
        #retornar log in json, com isso posso pegar erros de outros lugares para usar
        #Dentro da chave crio o meu json
        return jsonify({"Erro":"Ambos os arquivos devem ser enviados"})
    
    #colocar no pandas para manupular arquivos
    #sel = separador do arquivo, se nao colocar pega o padrão que é ;
    #nomes = colunas
    #header = cabeçalho
    inad_df = pd.read_csv(
        inad_file,
        sep =  ';',
        names = ['data','inadimplencia'],
        header = 0
    )
    selic_df = pd.read_csv(
        selic_file,
        sep = ';',
        names = ['data', 'selic_diaria'],
        header = 0
    )

    #datas pode estar em formatos distintos, padronizar as datas
    #pego a data arrumo e coloco de volta
    inad_df['data'] = pd.to_datetime(
        inad_df['data'],
        format = "%d/%m/%Y"
    )

    selic_df['data'] = pd.to_datetime(
        selic_df['data'],
        format = "%d/%m/%Y"
    )

    #Pegar do dia mes ano somente o mes
    inad_df['mes'] = inad_df['data'].dt.to_period('M').astype(str)

    selic_df['mes'] = selic_df['data'].dt.to_period('M').astype(str)

    #Remover meses repetidos
    inad_mensal = inad_df[["mes","inadimplencia"]].drop_duplicates()

    #agrupar por mes o campo selic diaria metodo de agrupamento media e tirar indece
    selic_mensal = selic_df.groupby('mes')['selic_diaria'].mean().reset_index()

    with sqlite3.connect(caminhoBd) as conn:
        inad_df.to_sql(
            'inadimplencia',
            conn,
            if_exists = 'replace',
            index = False
        )
        selic_df.to_sql(
            'selic',
            conn,
            if_exists =  'replace',
            index = False
        )
    return jsonify({"Mensagem":"Dados cadastrador com sucesso!"})

@app.route(rotas[2], methods = ['GET', 'POST'])
def consultar():

    if request.method == 'POST':
        #quando o que vem do campo tabela da seleção se se for post. Ira vir no exemplo inadimplencia ou selic
        tabela = request.form.get('campo_tabela')
        if tabela not in ['inadimplencia', 'selic']:
            #jsonify envia o erro e o codigo de erro nesse caso 
            return  jsonify({"Erro":"Tabela Invalida"}),400
        with sqlite3.connect(caminhoBd) as conn:
            df = pd.read_sql_query(f'SELECT * FROM {tabela}', conn)
        return df.to_html(index=False)

    return render_template_string(f'''
        <h1>Consulta de Tabelas</h1>
        <form method="POST">
            <label for = "campo_tabela">Escolha uma tabela</label>
            <select name="campo_tabela">
                <option value="inadimplencia">Inadimplencia</option>
                <option value="selic">Taxa Selic</option>
            </select>                   
            <input type="submit" value="Consultar">
        </form>
        <br><a href="{rotas[0]}"> Voltar </a>
    ''')

@app.route(rotas[3])
def graficos():
    with sqlite3.connect(caminhoBd) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)


    ###### Aqui criei um grafico para inadimplencia
    #variavel figura herdou tudo do go.Figure() do gráfico
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x = inad_df['mes'],
        y = inad_df['inadimplencia'],
        mode = 'lines+markers',
        name = 'Inadimplencia'
        )
    )
    # 'ggplot2', 'seaborn', 'simple_whit', 'ploty', 'ploty_white', 'ploty_dark', 'presentation', 'xgridoff', 'ygridoff', 'none'
    fig1.update_layout(
        title = 'Evolucao da Inadimplencia',
        xaxis_title = 'Mês',
        yaxis_title = '%',
        template = 'plotly_dark'
    )

    #Exercicio de media mensal selic
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x = selic_df['mes'],
        y = selic_df['selic_diaria'],
        mode = 'lines+markers',
        name = 'selic'
    )
    )
    fig2.update_layout(
        title = 'Media mensal da Selic',
        xaxis_title =  'Mês',
        yaxis_title = 'Taxa',
        template = 'plotly_dark'
    )

    #exibir grafico
    grafico_html1 = fig1.to_html(
        full_html = False, #nao carrega todo o html
        include_plotlyjs = 'cdn' #incluir java script da cdn u do google quando puxa fica no codigo
        )

    grafico_html2 = fig2.to_html(
        full_html = False, #nao carrega todo o html
        include_plotlyjs = False
        )

    return render_template_string('''
        <html>
            <head>
                <title>sGraficos Economicos </title>
                <style>
                    .container{
                        display:flex;
                        justify-content:space-around;
                    }
                    .graph{
                        width: 48%;
                    }

                </style>
            </head>
            <body>
                <h1>
                    <marquee> Graficos Economicos </marquee>
                </h1>
                <div class="container">
                    <div class="graph">{{ reserva01|safe}}</div> 
                    <div class="graph">{{ reserva02|safe }}</div>
                </div>
            </body>
        </html><br><a href="{{ voltar }}"> Voltar </a>
    ''', reserva01 = grafico_html1, reserva02 = grafico_html2, voltar = rotas[0])

#|safe quem interpreta o nosso html e o broser e nao o python

@app.route(rotas[4], methods = ['POST', 'GET'])
def editar_inadimplencia():
   #Etrou na pagina e pediu para recarregar por POST
   if request.method == "POST":
        mes = request.form.get('campo_mes')
        novo_valor = request.form.get('campo_valor')
        if not mes or not novo_valor:
            return jsonify({"Erro":"Infomrme a data e o valor"}),400
        
        try:
           novo_valor = float(novo_valor.replace(',','.'))
        except ValueError as e:
           return jsonify({"Erro":"Valor invalido"}),e
        with sqlite3.connect(caminhoBd) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE inadimplencia 
                SET inadimplencia = ?
                WHERE mes = ?
            ''', (novo_valor, mes))
            conn.commit()    
        return jsonify({"Mensagem":f"Valor da Inadinplencia para o {mes} atualizado para {novo_valor}"})
   
   return render_template_string(f'''
        <h1> Editar Inadimplencia </h1>
        <form method="POST" action="{rotas[4]}">
        <label for="campo_mes"> Mes (AAAA-MM) </label>
        <input type="text" name="campo_mes" ><br>

        <label for="campo_valor">Novo valor de Inadimplencia </label>
        <input type="text" name="campo_valor"><br>

        <input type="submit" value="Atualizar Dados"><br>
        </form>
        <br>
        <a href="{rotas[0]}"> Voltar </a>
    ''')

@app.route(rotas[7], methods = ['POST', 'GET'])
def editar_selic():
    if request.method == 'POST':
        mes = request.form.get('campo_mes')
        novo_valor = request.form.get('campo_valor')
        if not mes or not novo_valor:
            return jsonify({"Erro":"Infomrme a data e o valor"}),400
        try:
            novo_valor = float(novo_valor.replace(',','.'))
        except ValueError as e:
            return jsonify({"Erro":"Valor invalido"}),e

        with sqlite3.connect(caminhoBd) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE selic
                SET selic_diaria = ?
                WHERE mes = ?
            ''', (novo_valor, mes))
            conn.commit()
        return jsonify({"Mensagem":f"Valor da Selic para o {mes} atualizado para {novo_valor}"})
       
    return render_template_string(f'''
        <h1> Editar Selic </h1>
        <form method="POST" action="{rotas[7]}">
        <label for="campo_mes"> Mes (AAAA-MM) </label>
        <input type="text" name="campo_mes" placeholder="2025-01"><br>

        <label for="campo_valor"> Novo valor de Taxa Selic </label>
        <input type="text" name="campo_valor" placeholder="12.5"><br>

        <input type="submit" value="Atualizar Dados"><br>
        </form>
        <br>
        <a href="{rotas[0]}"> Voltar </a>
    ''')


if __name__ == '__main__':
    init_db()
    app.run(
        debug = config.FLASK_DEBUG,
        host = config.FLASK_HOST,
        port = config.FLASK_PORT
    )

