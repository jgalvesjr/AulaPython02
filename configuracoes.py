# __     __  _         _    
# \ \   / / / \       / \   
#  \ \ / / / _ \     / _ \  
#   \ V / / ___ \ _ / ___ \ 
#    \_(_)_/   \_(_)_/   \_\
# Autor: Joao Alves
# Versao: 0.0.1v 2025
# https://www.asciiart.eu/text-to-ascii-art


#caminho banco de dados
DB_PATH =  "C:/Users/integral/Desktop/Python2_Joao/bancodados.db"

#caminho html
inicioPath = "C:/Users/integral/Desktop/Python2_Joao/inicio.html"

#--------------------
#Consultas SQL
#--------------------

# Seleciona e traz todos os dados da tabela vingadores
consulta01 = "SELECT * FROM vingadores"

# Seleciona o dados para gerar grafico 1
consulta02 = '''
            SELECT country, total_litres_of_pure_alcohol FROM bebidas
            ORDER BY total_litres_of_pure_alcohol DESC
            LIMIT 10
        '''

# Exclui a tabela vingadores se ela existir
consulta03 = "DROP TABLE IF EXISTS vingadores"