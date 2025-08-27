import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import sqlite3
import datetime
from tabulate import tabulate
import math

#BeautifulSoup biblioteca para passear (analisar) HTML e extrair informações

#header para simular um navegador real (agums sites bloqueiam "bots" entao fingimo ser o Google Chrome)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0 Safari/537.36'
    
}

#baseRUL = 'https://www.adorocinema.com/filmes/melhores/'
baseURL = "https://www.sampaingressos.com.br/templates/ajax/lista_espetaculo.php"
shows = [] #Lista que vai armazenar os dados da coleta de cada filme
data_hoje = datetime.date.today().strftime('%d-%m-%Y')
agora = datetime.datetime.now()
paginaLimite = 2 #quantidade de paginas -1 para ser consultada
card_temp_min = 1
card_temp_max = 3
page_temp_min = 2
page_temp_max  = 5
bancoDados = 'C:/Users/integral/Desktop/Python2_Joao/banco_sampa_ingresso.db'
saidaCSV = f'shows_sampa_ingresso_{data_hoje}-{agora}.csv'

for pagina in range(1,paginaLimite +1 ):
    url = f'{baseURL}?page={pagina}&tipoEspetaculos=shows'#https://www.adorocinema.com/filmes/melhores/?page=2 coloca o numero da pagina
    print(f'Coletando dados da pagina {pagina} : {url}')
    resposta = requests.get(url, headers=headers) #pegar dados da pagina, baseado no headers - todo html esta aqui
    soup = BeautifulSoup(resposta.text, 'html.parser' ) # cria um objeto html e joga dentro de soup pagina inteira

    #se o site nao responder, pula para a proxima pagina
    if resposta.status_code != 200:
        print(f'Erro ao carregar a pagina {pagina}. Codigo do erro e: {resposta.status_code}')
        continue

    #cada filme aparece em uma div(card) com a classe abaixo
    #procure todas as "div" que tenho o nome class_="card entity-card entity-card-list cf - olha no inspecionar da pagina o card para esse sexmplo
    cards = soup.find_all('div', id='box_espetaculo') 
    #itereramos por cada card(div) de filme
    for card in cards:
        try:
            #capturar o titulo e link da pagina do filme
            titulo_tag = card.find('b', class_='titulo')
            local_tag = card.find('span', class_='local')
            horario_tag = card.find('span', class_='horario')

            titulo = titulo_tag.text.strip() if titulo_tag else 'N/A'
            local = local_tag.text.strip() if local_tag else 'N/A'
            horario = horario_tag.text.strip() if horario_tag else 'N/A'

            if titulo != 'N/A':
                shows.append({   
                        'Titulo': titulo,
                        'Local': local,
                        'Horario': horario})
            else:
                print('Card sem titulo (ignorado)')

            #aguardar um tempo aleatorio entre os parametros escolhido para nao sobrecarregar o site e nem revelar que sou um bot
            tempo = random.uniform(card_temp_min, card_temp_max)
            time.sleep(tempo)
        except Exception as e:
            print(f'Erro ao processar card. Erro: {e}')

    #esperar um tempo entre uma pagina e outra
    tempo = random.uniform(page_temp_min, page_temp_max)
    time.sleep(tempo)   

#converter os dados coletados para dataframe do pandas
df = pd.DataFrame(shows)
print(df.head())

df.to_csv(saidaCSV, index=False, encoding='utf-8-sig', quotechar="'", quoting=1)


#connectar um bando de dados SQLite (cria se nao existe)
conn = sqlite3.connect(bancoDados)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS shows(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Titulo TEXT,
        Local TEXT,
        Horario TEXT
    )
''')

# inserir cada filme coletado dentro da tabela do banco de dados

for evento in shows:
    try:
        cursor.execute('''
            INSERT INTO shows (Titulo, Local, Horario) VALUES (?,?,?)
        ''',(
            evento['Titulo'],
            evento['Local'],
            evento['Horario']
    ))
    except Exception as e:
        print(f"Erro ao inserir evento {evento['Titulo']} no banco de dados. Codigo de identificacao do erro {e}")
conn.commit()
conn = sqlite3.connect(bancoDados)

dfShows = pd.read_sql_query('SELECT * FROM shows', conn)
conn.close()

print('---------------------------------------------')
print(tabulate(dfShows, headers='keys', tablefmt='psql'))
print('----------------------------------------------')
print('---------------------------------------------')
print('Dados raspados e salvos com sucesso')
print(f'\n Arquivo salvo em: {saidaCSV} \n')
print('Obrigado por usar o sistema de Bot do Joao')
print(f"Finalizado em: {agora.strftime('%H:%M:%S')}")
print('----------------------------------------------')