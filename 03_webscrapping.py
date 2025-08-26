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

baseRUL = 'https://www.adorocinema.com/filmes/melhores/'
filmes = [] #Lista que vai armazenar os dados da coleta de cada filme
data_hoje = datetime.date.today().strftime('%d-%m-%Y')
agora = datetime.datetime.now()
paginaLimite = 2 #quantidade de paginas -1 para ser consultada
card_temp_min = 1
card_temp_max = 3
page_temp_min = 2
page_temp_max  = 5
bancoDados = 'C:/Users/integral/Desktop/Python2_Joao/banco_filmes.db'
saidaCSV = f'filmes_adorocinema_{data_hoje}-{data_hoje}.csv'

for pagina in range(1,paginaLimite+1):
    url = f'{baseRUL}?page={pagina}'#https://www.adorocinema.com/filmes/melhores/?page=2 coloca o numero da pagina
    print(f'Coletando dados da pagina {pagina} : {url}')
    resposta = requests.get(url, headers=headers) #pegar dados da pagina, baseado no headers
    soup = BeautifulSoup(resposta.text, 'html.parser' ) # cria um objeto html e joga dentro de soup pagina inteira

    #se o site nao responder, pula para a proxima pagina
    if resposta.status_code != 200:
        print(f'Erro ao carregar a pagina {pagina}. Codigo do erro e: {resposta.status_code}')
        continue

    #cada filme aparece em uma div(card) com a classe abaixo
    #procure todas as "div" que tenho o nome class_="card entity-card entity-card-list cf - olha no inspecionar da pagina o card para esse sexmplo
    cards = soup.find_all('div', class_='card entity-card entity-card-list cf') 
    #itereramos por cada card(div) de filme
    for card in cards:
        try:
            #capturar o titulo e link da pagina do filme
            titulo_tag = card.find('a', class_='meta-title-link')
            titulo = titulo_tag.text.strip() if titulo_tag else 'N/A' #se titulo false, ele mostra NA
            link = 'https://www.adorocinema.com' + titulo_tag['href'] if titulo_tag else None #pegar link da tag

            #capturar a nota do filme
            nota_tag = card.find('span', class_='stareval-note') #span - tag nota se chama class_='stareval-note
            nota = nota_tag.text.strip().replace(',','.') if nota_tag else 'N/A'

            #Caso exita o link, acessar a pagina individual do site
            if link:
                filme_resposta = requests.get(link, headers=headers)
                filme_soup = BeautifulSoup(filme_resposta.text, 'html.parser') 
            
                # capturar o diretor do filme
                diretor_tag = filme_soup.find('div', class_= 'meta-body-item meta-body-direction meta-body-oneline')
                if diretor_tag:
                    #vamos higienizar o texto do diretor
                    diretor = diretor_tag.text.strip().replace('Direção:','').replace(',','').replace('|','').strip()
                else:
                    diretor = 'N/A'
                diretor = diretor.replace('\n','').replace('\r','').strip()

            #captura do generos
            #pagina do filme filme_soup
            genero_block = filme_soup.find('div', class_='meta-body-info')
            if genero_block:
                generos_links = genero_block.find_all('a')
                generos = [g.text.strip() for g in generos_links]
                #junta em categoria e me traz so 3 generos da lista
                categoria = ', '.join(generos[:3]) if generos else 'N/A'
            else:
                categoria = 'N/A'
            
            #captura o ano de lancamanto
            #dica a tag e um 'span e o nome da classe é 'date'
            ano_tag = genero_block.find('span', class_='date') if genero_block else None
            ano = ano_tag.text.strip() if ano_tag else 'N/A'

            #mso adiciona o filma se todos os dados principais exitirem
            if titulo != 'N/A' and link != 'N/A' and nota != 'N/A':
                filmes.append(
                    {'Titulo': titulo,
                        'Direcao': diretor,
                        'Nota': nota,
                        'Link': link,
                        'Ano': ano,
                        'Categoria': categoria
                })
            else:
                print(f'Fime incompleto ou erro na coleta de dados {titulo}.')

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
df = pd.DataFrame(filmes)
print(df.head())

df.to_csv(saidaCSV, index=False, encoding='utf-8-sig', quotechar="'", quoting=1)


#connectar um bando de dados SQLite (cria se nao existe)
conn = sqlite3.connect(bancoDados)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS filmes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Titulo TEXT,
        Direcao TEXT,
        Nota REAL,
        Link TEXT,
        Ano TEXT,
        Categoria TEXT
               )
''')

# inserir cada filme coletado dentro da tabela do banco de dados

for filme in filmes:
    try:
        cursor.execute('''
            INSERT INTO filmes (Titulo, Direcao, Nota, Link, Ano, Categoria) VALUES (?,?,?,?,?,?)
        ''',(
            filme['Titulo'],
            filme['Direcao'],
            float(filme['Nota']) if filme['Nota'] != 'N/A' else None,
            filme['Link'],
            filme['Ano'],
            filme['Categoria']
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