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
        conn.commit()
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


@app.route(rotas[5])
def correlacao():
    with sqlite3.connect(caminhoBd) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)

    #realiza uma juncao entre dois dataframes usando a coluna de mes como chave de juncao
    merged  = pd.merge(inad_df, selic_df, on = 'mes')

    #calcula o coeficiente da corelação de peradon entre as duas varivais (inadimplencia e selic)
    #quero correlacionar a coluna inadimplencia com a selic
    correl = merged['inadimplencia'].corr(merged['selic_diaria'])

    #registrar as variaveis para a regressao linear onde x é a variaval independente (no caso selic_diaria campo)
    x = merged['selic_diaria']

    # y é a variavel dependente
    y = merged['inadimplencia']

    #calcula o coeficiente da reta de regressao linear onde 'm' é a inlinacao e 'b' é a interseção
    #realizar o calculo esse cauclo é feito pelo polyfit -  calcula a regreção
    #x independente y pentendete - indepentede depende da dependente - 1 polinomio
    m, b = np.polyfit(x, y, 1)


    # a partir daqui vamos gerar o grafico
    #eixo x recebe o x da selit diaria e y da indimpkencia
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = x,
        y = y,
        mode = 'markers',
        name = 'Inadimplencia X Selic',
        #marker  para alterar os mrcadores
        marker  = dict(
            color = 'rgba(0, 123, 255, 0.8)',
            size = 12,
            line = dict(width = 2, color = 'white'),
            symbol = 'circle'
            ),
        #hovertemplate - controla o que vao acontecer quando passa o mouse por cima do elemento
        hovertemplate = 'SELIC: %{x:.2f}%<br>Inadimplencia: %{y:.2f}%<extra></extra>'
        )
    )

    #adicionar a linha de tentencia de regreção linear
    fig.add_trace(go.Scatter(
        x = x, #mesmo eixo de dados do anterior
        y = m * x + b, # a equação de linha de tendencia 
        mode = 'lines',
        name = 'Linha de Tendencia',
        line = dict(
            color = 'rgba(255, 53, 69, 1)',
            width = 4,
            dash = 'dot' #tipo de linha
            )
        )
    )

    #formatar o grafico
    fig.update_layout(
        title = {
            'text':f'<b>Correlação entre Selic e Inadimplencia</b><br><span style="fonte-size:16px">Coeficiente de Correlação: {correl:.2f}</span>', 
            'y':0.95, #posicao vertical do titulo (95% da altura do grafico)
            'x':0.5, #posicao horizontal do titulo (50% da altura do grafico)
            'xanchor':'center', #alinha o titulo horizontal ao centro
            'yanchor':'top' # alinha o titulo verticalmente ao topo
        },
        xaxis_title = dict(
            text = 'SELIC Média Mensal (%)', #titulo do eixo x
            font = dict(
                size = 18,
                family = 'Arial',
                color = 'gray'
            )
        ),
        yaxis_title = dict(
            text = 'Inadimplencia (%)', #titulo do exixo y
            font = dict(
                size = 18,
                family = 'Arial',
                color = 'gray'
            )           
        ),
        xaxis = dict(
            tickfont = dict(
                size = 14,
                family = 'Arial',
                color = 'black',
            ),
            gridcolor = 'lightgray'
        ),
        yaxis = dict(
            tickfont = dict(
                size = 14,
                family = 'Arial',
                color = 'black',
            ),
            gridcolor = 'lightgray'
        ),
        font = dict(  #formatacao das fontes gerais a que eu nao formatei
            family = 'Arial',
            color = 'black'
        ),
        legend = dict(
            orientation = 'h',               #legenda horizontal
            yanchor = 'bottom',             #alinhamento vertical da legenda
            y = 1.05,                       #posição  da legenda um pouco acima do grafico
            xanchor = 'center',             #
            x = 0.5,                        # posicao horizonta da legenda
            bgcolor = 'rgba(0,0,0,0)',      # cor de fundo da legenda
            borderwidth = 0                 # largura da birda da legenda
        ),
        margin = dict(
            l = 60,
            r = 60,
            t = 120,
            b = 60
        ),
        plot_bgcolor = '#f8f9fa', #cor de fundo do grafico
        paper_bgcolor = 'white' #cor de fundo da area do grafico
    )

    #gera o html do grafico sem o codigo javascript necessário para o grafico funcionar (inclusão externa)
    graph_html = fig.to_html(
        full_html = False,
        include_plotlyjs = 'cdn'
    )
    #div classe 
    return render_template_string('''
        <html>
            <head>
                <title>Correlaçao SELIC VS e Inadimplencia</title>
                <style>
                    body{font-family:Arial; background-color:#ffffff, color=#333;}
                    .container{width: 90%; margin: auto; text-align:center;}             
                    h1{margin-top: 40px;}
                    a{text-decoration:none; color: #007bff;}
                    a:hover{text-decoration:underline;}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Correlaçao SELIC VS e Inadimplencia</h1>
                    <div>{{ grafico|safe }}</div>
                    <br>
                    <div><a href="{{voltar}}">Voltar</a></div>
                </div>
            </body>
        </html>
    ''', grafico = graph_html, voltar =  rotas[0])

@app.route(rotas[6])
def insights_3d():
    with sqlite3.connect(caminhoBd) as conn:
        inad_df = pd.read_sql_query('SELECT * FROM inadimplencia', conn)
        selic_df = pd.read_sql_query('SELECT * FROM selic', conn)
    
    #mescla os dois dataframes com base na coluna de mes ordenando do mais antigo para o mais novo
    merged = pd.merge(inad_df, selic_df, on = 'mes').sort_values('mes')
    merged['mes_idx'] = range(len(merged))

    #calcula a diferença da inadimplencia em relação ao mes anterior (nossa primeira derivada discreta)
    # fillna -> o metodo e usado para substituir valores NaN em uma serie ou coluna por 0 - nesse caso para o primeiro dado, nãp tem um anterior para calular
    # iria trazer um note a number NaN - preencho ele com 0
    merged['tend_inad'] = merged['inadimplencia'].diff().fillna(0)

    # calsseificar a tendencia como subir ou cair=u ou estavel com base na variação calculada
    trend_color = ['subiu' if x > 0 else 'caiu' if x < 0 else 'estavel' for x in merged['tend_inad']]

    # calcular as variaçoes mensais (derivadas discreta) da inadimplencia e da selic
    merged['var_inad'] = merged['inadimplencia'].diff().fillna(0)
    merged['var_selic'] = merged['selic_diaria'].diff().fillna(0)

    # seleciona as colunas numericas que serão usadas para agrupar os meses por similaridade
    features = merged[['selic_diaria', 'inadimplencia']].copy()
    # normalizador para pradonizar as variaveis (media = 0, devio = 1)
    scaler = StandardScaler()
    #aplica a normalização
    scaler_features = scaler.fit_transform(features)

    # executa o algoritimo do kmeans com 3 clusters (grupo)  distintos. Isso vai rotular cada mes com um numero de cluster, agrupando meses similares
    Kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    # adiciona as colunas com os clusters selecionados
    merged['cluster'] = Kmeans.fit_predict(scaler_features)

    #prepara os dados de entrada para o calculo de uma regressão linear multipla, a ideia e encontrar um plano que melhor se ajusta aos pontos 3d do grafico
    #matrix de entrada: tempo e selic
    x = merged[['mes_idx', 'selic_diaria']].values
    #vetor de saida
    y = merged['inadimplencia'].values

    # concatena uma coluna para permitir o calculo independente 
    # aplica o metodo minimo dos quadrados para resolver a *  coef = y
    a = np.c_[x, np.ones(x.shape[0])]

     # resultado: coef[0] = a, coef[2] = b, coef[2] = c
     # np.linalg.lstsq retorn 4 valores coeffs, _, _, _ - _ = nao irei utilizar os elementos
    coeffs, _, _, _ = np.linalg.lstsq(a, y, rcond=None)

    # criaremos aqui a malha de pontos 2d para desenhar a seperficie do plano de regtressão
    # 30 pontos entre  menor e o maior mes
    xi = np.linspace(
        merged['mes_idx'].min(),
        merged['mes_idx'].max(),
        30
        )
    # 30 pontos entre o menor e a maior  taxa selic
    yi = np.linspace(
        merged['selic_diaria'].min(),
        merged['selic_diaria'].max(),
        30
        )
    
    #gera todas as combinaçoes possiveis entre os valores da xi e xy
 
    # gera todas as combinações possiveis entre os valores de xi e yi
    xi, yi = np.meshgrid(xi,yi) 

    # aplica a equação do plano para gerar os valores z(inadimplencia)
    zi = coeffs[0] * xi + coeffs[1] * yi + coeffs[2]

    # crie o grafico 3d com as informações extras ao passar o mouse sobre os pontos

    #https://plotly.com/python/builtln-colorscales/
    scatter = go.Scatter3d(
        x = merged['mes_idx'],          #eixo x = tempo
        y = merged['selic_diaria'],     #eixo y = taxa selic
        z = merged['inadimplencia'],    #eixo z = inad
        mode = 'markers',                #apenas marcadores bolinhas
        marker = dict(
                size = 8,
                color = merged['cluster'],
                colorscale = 'Viridis',     #tema da paleta de cores padrão suave
                opacity = 0.9
        ),
        text = [ #conteudo que aparece ao passar o mouse sobre os pontos de dados
            #Quando utiilza f string posso utilizar html dentro
            #f'Mes: {mes}<br>Inadimplencia: {z:.2f}%<br>SELIC: {y:.2f}<br>Var Inadimplencia: {vi:.2f}<br>Variação Selic {vs:.2f}<br>Tendencia {t}'
            #quando o for estiver dentro do texto, ele pega os itens do texto conforme o form exemplo mes {m} com merged['mes]
            f'''
            Mes: {m}
            Inadimplencia: {z:.2f}%
            SELIC: {y:.2f}
            Var Inadimplencia: {vi:.2f}
            Variação Selic {vs:.2f}
            Tendencia {t}'
            '''
            for m, z, y, vi, vs, t in zip(
                merged['mes'],    #campos da tabela
                merged['inadimplencia'],
                merged['selic_diaria'],
                merged['var_inad'],
                merged['var_selic'],
                trend_color
            )  
        ],
        hovertemplate = '%{text}<extra></extra>'
    )

    #criar a superficie 3d do plano de regressão
    surface = go.Surface(
        # coordenadas de grade
        x = xi,
        y = yi,
        z = zi,
        showscale = False, # barra de cores
        colorscale = 'Reds', #paleta vermelha para o plano
        opacity = 0.5,
        name = 'Plano de Regressão' 
    )

    # junta os dois graficos (pontos de dados e plano de regressão) em uma unica visualização 3d
    fig = go.Figure( data = [scatter, surface])

    # foemat o layout da cena completa em 3d
    fig.update_layout(
        scene = dict(
            xaxis = dict(
                title = 'Tempo (Meses)',
                tickvals = merged['mes_idx'],
                ticktext = merged['mes']
            ),
            yaxis = dict(title = 'SELIC (%)'),
            zaxis = dict(title = 'Inadimplencia (%)')
        ),
        title = 'Insights Economicos 3D com Tenencias, Derivadas e Clusters',
        margin = dict(l=0, r=0, t=50, b=0),
        height = 800
    )
    graph_html = fig.to_html(
        full_html = False,
        include_plotlyjs = 'cdn'
    )



    return render_template_string('''   
        <html>
            <head>
                <title></title>
                <style>
                    body{font-familiy: Arial; background-color: #f8f9fa; color: #222; text-align: center;}
                    a{text-decoration: none; color: #007bff}
                    a:hover{text-decoration: underline;}
                </style>
            </head>
            <body>
                <div>
                    <h1>Grafico 3D com Insights Economicos</h1>
                    <p>Analise visual com cluster, tendencias e plano de regressão</p>
                    <div>{{ grafico|safe }}</div>
                    <br><div><a href="{{voltar}}">Voltar</a></div>
                </div>
            </body>
        </html>

    ''', grafico = graph_html, voltar = rotas[0])



if __name__ == '__main__':
    init_db()
    app.run(
        debug = config.FLASK_DEBUG,
        host = config.FLASK_HOST,
        port = config.FLASK_PORT
    )

