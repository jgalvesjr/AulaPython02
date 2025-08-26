import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import sqlite3
import datetime
from tabulate import tabulate
import math


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
    
}


baseURL = 'https://www.sampaingressos.com.br/espetaculos/shows'
#baseurl = "https://www.sampaingressos.com.br/templates/ajax/lista_espetaculo.php"
filmes = []
data_hoje = datetime.date.today().strftime('%d-%m-%Y')
agora = datetime.datetime.now()
paginaLimite = 2 #quantidade de paginas -1 para ser consultada
card_temp_min = 1
card_temp_max = 3
page_temp_min = 2
page_temp_max  = 5
bancoDados = 'C:/Users/integral/Desktop/Python2_Joao/banco_sampa_ingresso.db'
saidaCSV = f'filmes_sampaingresso_{data_hoje}-{data_hoje}.csv'

for pagina in range(1,paginaLimite+1):
    url = f'{baseURL}?pagina={pagina}'
    print(f'Coletando dados da pagina {pagina} : {url}')
    resposta = requests.get(url, headers=headers)  #pegar dados da pagina, baseado no headers
    soup = BeautifulSoup(resposta.text, 'html.parser' ) # cria um objeto html e joga dentro de soup pagina inteira
    print('SOUP')
    print(soup)

    #se o site nao responder, pula para a proxima pagina
    if resposta.status_code != 200:
        print(f'Erro ao carregar a pagina {pagina}. Codigo do erro e: {resposta.status_code}')
        continue

    #cada filme aparece em uma div(card) com a classe abaixo
    #procure todas as "div" que tenho o nome class_="card entity-card entity-card-list cf - olha no inspecionar da pagina o card para esse sexmplo
    cards = soup.find_all('div', id='box_espetaculo') #melhor pegar semrpe a class
    #'div' '_class' pego da pagina https://www.sampaingressos.com.br/espetaculos/shows?pagina=2 inspecionar 
    #itereramos por cada card(div) de filme
    for card in cards:
        try:
            #capturar o titulo e link da pagina do filme
            titulo_tag = card.find('b', class_='titulo')
            titulo = titulo_tag.text.strip() if titulo_tag else 'N/A' #se titulo false, ele mostra NA
            print('Titulo')
            print(titulo)

            #mso adiciona o filma se todos os dados principais exitirem
            if titulo != 'N/A':
                filmes.append({'Titulo': titulo})
            else:
                print(f'Fime incompleto ou erro na coleta de dados {titulo}.')
        except Exception as e:
            print(f'Erro ao processar o filme {titulo}. Erro: {e}')

            #aguardar um tempo aleatorio entre os parametros escolhido para nao sobrecarregar o site e nem revelar que sou um bot
            tempo = random.uniform(card_temp_min, card_temp_max)
            time.sleep(tempo)
            tempo_ajustado = math.ceil(tempo)
            print(f'Tempo de espera: {tempo_ajustado} seg')
        except Exception as e:
            print(f'Erro ao processar o filme {titulo}. Erro: {e}')
    #esperar um tempo entre uma pagina e outra
    tempo = random.uniform(page_temp_min, page_temp_max)
    time.sleep(tempo)   

    #converter os dados coletados para dataframe do pandas

print(filmes)
df = pd.DataFrame(filmes)
print('LISTA TITULO')
print(df.head())

df.to_csv(saidaCSV, index=False, encoding='utf-8-sig', quotechar="'", quoting=1)

#connectar um bando de dados SQLite (cria se nao existe)
conn = sqlite3.connect(bancoDados)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS filmes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Titulo TEXT
               )
''')

for filme in filmes:
    try:
        cursor.execute('''
            INSERT INTO filmes (Titulo) VALUES (?)
        ''',(
            filme['Titulo']
    ))
    except Exception as e:
        print(f"Erro ao inserir filme {filme['Titulo']} no banco de dados. Codigo de identificacao do erro {e}")
conn.commit()
conn = sqlite3.connect(bancoDados)

dfFilmes = pd.read_sql_query('SELECT * FROM filmes', conn)
conn.close()

print('---------------------------------------------')
print(tabulate(dfFilmes, headers='keys', tablefmt='psql'))
print('----------------------------------------------')
print('---------------------------------------------')
print('Dados raspados e salvos com sucesso')
print(f'\n Arquivo salvo em: {saidaCSV} \n')
print('Obrigado por usar o sistema de Bot do Joao')
print(f"Finalizado em: {agora.strftime('%H:%M:%S')}")
print('----------------------------------------------')