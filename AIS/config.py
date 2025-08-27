'''
Autor: Joao
Data: 27-08-205
Versao: 1.0
'''

BD_PATH = 'bancodedadosAIS.db'
FLASK_DEBUG = True
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000

ROTAS = [
    '/',
    '/upload',
    '/consultar',
    '/graficos',
    '/editar_inadimplencia',
    '/correlacao',
    '/grafico3d',
    '/editar_selic'
    ]