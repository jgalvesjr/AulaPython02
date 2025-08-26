from flask import Flask, request, render_template, render_template_string
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.io as pio
import random
import configuracoes as config

menuInicio = config.inicioPath
caminhoBanco = config.DB_PATH
queryVerVingadores = config.consulta01
queryGrafico1 = config.consulta02
dropVingadores = config.consulta03

#configurar o ploty para abrir os arquivos no navegador por padrao
pio.renderers.default = 'browser'

#carregar o arquivos drinks.csv
#r na frente - raw string - python para de interpretar as barras
dfDrinks = pd.read_csv(r"C:\Users\integral\Desktop\Python2_Joao\drinks.csv")
dfAvengers = pd.read_csv(r"C:\Users\integral\Desktop\Python2_Joao\avengers.csv", encoding='latin1')

#criar o banco de dados em SQL e popular com os dados do csv
#criar conexao com o baco 0 no exemplo cria um banco chamado consumo_alcool.db
conn = sqlite3.connect(caminhoBanco)

#cria a tabela bebidas e a tabela vingadores no banco de dados bancodedados.db (conn herda sqlite3)
dfDrinks.to_sql('bebidas', conn, if_exists='replace', index=False)
dfAvengers.to_sql('vingadores', conn, if_exists='replace', index=False)
conn.commit()
conn.close()


#iniciar o flask
#__name__ é o nome da nossa aplicacao - herdar tudo do flask
app = Flask(__name__)

#render_template_string reinderiza o html para mostrar na rota
@app.route('/')
def index():
    return render_template('inicio.html')

@app.route('/grafico1')
def grafico1():
    #outra forma de conectar usando o with poderia usar o conn do inicio - com o with tenho que terminar com : 
    # + query
    with sqlite3.connect(caminhoBanco) as conn: 
        df = pd.read_sql_query(queryGrafico1, conn)

    #Criar grafico 
    #bar - grafico barras
    figuraGrafico01 = px.bar(
        df, 
        x ="country",
        y="total_litres_of_pure_alcohol",
        title="Top 10 paises com maior consumo de alcool"
    )
    return figuraGrafico01.to_html() + "<br><a href='/'>Voltar</a>"

@app.route('/grafico2')
def grafico2():
    with sqlite3.connect(caminhoBanco) as conn:
        #faz um select mudando o nome do campos 
        df = pd.read_sql_query('''
            SELECT AVG(beer_servings) AS cerveja, AVG(spirit_servings) AS destilado, AVG(wine_servings) AS vinhos FROM bebidas
        ''', conn)

    #Comentario instrutor - transforma as colunas (cerveja, destilados, vinhos) em linhas criando duas colunas
    #Uma chamada bebidas com os nomes originas das colunas
    #e outra chamada media de porcoes com os valores correspondentes
    #junta os dados da tabela, pega as bebidas exemplo cerveja, destilado, etc e colocam em Bebidas. Sabe que é uma média colocar em Media de Porcoes
    df_melted = df.melt(var_name='Bebidas', value_name='Media de Porcoes')
    figuraGRafico02 = px.bar(
        df_melted,
        x="Bebidas",
        y = "Media de Porcoes",
        title = "Media de consumo global por tipo"
    )
    return figuraGRafico02.to_html()

#grafico 3, consumo por região
@app.route('/grafico3')
def grafico3():
    regioes = {
        "Europa":['France','Germany','Italy','Spain','Portugal'],
        "Asia":['China','Japan','India','Thailand'],
        "Africa":['Angola','Nigeria','Egypt','Algeria'],
        "Americas":['USA','Brazil','Canada','Argentina','Mexico']
    }
    dados = []
    with sqlite3.connect(caminhoBanco) as conn:
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
    dfRegioes = pd.DataFrame(dados)
    figuraGrafico3 = px.pie(
        dfRegioes,
        names = 'Regiao',
        values = 'Consumo Total',
        title = 'Consumo total por regiao'
    )
    return figuraGrafico3.to_html() + "<br>< a href='/'>Voltar</a>"

#criando grafico 4 comprativo tipos bebidas
@app.route('/grafico4')
def grafico4():
    with sqlite3.connect(caminhoBanco) as conn:
        df = pd.read_sql_query('''
        SELECT beer_servings, spirit_servings, wine_servings FROM bebidas
         ''', conn)
        medias = df.mean().reset_index()
        medias.columns = ['Tipo','Media'] #gerando coluna
    figuraGrafico4 = px.pie(
        medias,
        names='Tipo',
        values='Media',
        title='Proporcao media entre tipos de bebidas'
    )
    return figuraGrafico4.to_html() +  "<br><a href='/'>Voltar</a>"

@app.route('/comparar', methods=['GET', 'POST'])
def comparar():
    opcoes = ['beer_servings', 'spirit_servings', 'wine_servings', 'total_litres_of_pure_alcohol']

    if request.method == 'POST':
        #logica para mostrar o grafico quando tem POST ao acessar a página
        eixo_x = request.form.get('eixo_x')
        eixo_y = request.form.get('eixo_y')
        if eixo_x == eixo_y:
            return "<h3>Selecione campos diferentes!</h3>"

        conn = sqlite3.connect(caminhoBanco)
        #colocar o que foi selecionado no eixo_x e no eixo_y em {} {} respectivamente
        df = pd.read_sql_query("SELECT country, {}, {} FROM bebidas".format(eixo_x,eixo_y), conn) 
        conn.close()
        figuraComparar = px.scatter(
            df,
            x = eixo_x,
            y = eixo_y,
            title = f'Comparacao entre {eixo_y} e {eixo_y}'
        )
        figuraComparar.update_traces(textposition =  'top center')
        return figuraComparar.to_html() +  "<br><a href='/'>Voltar</a>"

        

    #aqui e a pagina sem post, ou seja, a primeira vez que o usuario entrar na pagina
    return render_template_string('''
        <h2>Comparar Campos</h2>
        <form method="POST">
            <label>Eixo X:</label>
            <select name="eixo_x">
                {% for opcao in opcoes %}
                    <option value="{{opcao}}">{{opcao}}</option>     
                {% endfor %}          
            </select>
            <br><br>
            <label>Eixo Y:</label>
            <select name="eixo_y">
                {% for opcao in opcoes %}
                    <option value="{{opcao}}">{{opcao}}</option>     
                {% endfor %}                     
            </select>
            <br><br>
            <input type="submit" value="-- Comparar --">
        </form>
        ''', opcoes = opcoes) #opcoes vem de fora opcao variavel = recebe opcao lista

@app.route('/upload_avengers', methods=['GET', 'POST'])
def upload_avengers():
    if request.method == 'POST':
        #recebi um arquivos, entao vamos cadastrar no banco
        #se tem arquivo tem o base64 do arquivo no recebido
        recebido = request.files['arquivo']
        if not recebido:
            return "<h3>Nenhum arquivo recebido</h3><br><a href='/'>Voltar</a>"
        dfAvengers = pd.read_csv(recebido, encoding='latin1')
        conn = sqlite3.connect(caminhoBanco)
        dfAvengers.to_sql('vingadores', conn, if_exists='replace', index=False)
        conn.commit()
        conn.close()
        return "<h3>Arquivo inserido com sucesso! </h3><br><a href='/'>Voltar</a>"

    
    #acessar a rota pela primeira vez (sem post) cai nesse html
    #enctype="multipart/form-data" - upload arquivo em html e padroa isso
    return '''
        <h2>Upload da tabela Avengers</h2>
        <form method="POST" enctype="multipart/form-data"> 
            <input type="file" name="arquivo" accepet=".csv"><br>
            <input type="submit" value="-- Enviar --">
        </form>

    '''
@app.route('/ver_vingadores')
def ver_vingadores():
    conn = sqlite3.connect(caminhoBanco)
    try:
        dfAvengers = pd.read_sql_query(queryVerVingadores, conn)
    except Exception as erro:
        conn.close()
        return f"<h3>Erro ao consultar a tabela {str(erro)}</h3><br><a href='/'>Voltar</a>"
    if dfAvengers.empty:
        return "<h3>A tabela vingadores esta vazia ou nao existe!</h3><br><a href='/'>Voltar</a>"
    return dfAvengers.to_html(index=False) + "<br><a href='/'>Voltar</a>"

@app.route('/apagar_vingadores')
def apagar_vingadores():
    conn = sqlite3.connect(caminhoBanco)
    cursor = conn.cursor()
    try:
        cursor.execute(dropVingadores)
        conn.commit()
        mensagem = "<h3>Tabela vingadores apagado com sucesso !</h3>"
    except Exception as erro:
        mensagem = "<h3>Erro ao apagar a tabela</h3>"
    conn.close()
    return mensagem + "<br><a href='/'>Voltar</a>"
    
@app.route('/documentacao')
def documentacao():
    return render_template('documentacao.html') + "<br><a href='/'>Voltar</a>"

#niciar o servidor
if __name__ == '__main__':
    app.run(debug=True)
