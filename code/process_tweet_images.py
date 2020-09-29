from datetime import datetime
import pandas as pd
import geopandas as gpd
import json
import mapbox_credentials
import matplotlib.pyplot as plt
import os
from pprint import pprint
import random
import re
import requests
import shutil


###########################
### Rename os functions ###
### for readability     ###
###########################

abspath = os.path.abspath
dirname = os.path.dirname

###############
### Globals ###
###############

PROJECT_ROOT = dirname(abspath(dirname(__file__)))

##################################
### Dados sobre fogo por terra ###
##################################

TIS_INFO = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/terras_indigenas.feather")
UCS_INFO = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/unidades_de_conservacao.feather")

#######################
### Token de acesso ###
#######################

TOKEN = mapbox_credentials.token
USERNAME = "infoamazonia"

###############
### Helpers ###
###############

def handle_cache(url, style_id):
    '''
    Solução 'hack' para driblar o cache do mapbox:
    altera levemente o tamanho da imagem estática
    requerida, em comparação com a última requisição
    que foi feita. Isso é necessário pois pode demorar
    até 12h para que alterações feitas nos styles aparecem
    nas URLs estáticas.

    Parâmetros:

    > url: a url que será levemente modificada
    > style_id: o id do estilo do Mapbox para o qual queremos gerar uma imagem estática
    '''

    file = f"{PROJECT_ROOT}/output/jsons/requests/last-request-{style_id}.json"
    
    # Essa condição só sera ativada na primeira execução do script
    if not os.path.isfile(file):
        return url

    # Lê o arquivo com dados da última requisição enviada para o estilo
    with open(file) as f:
        data = json.load(f)

    # Descobre qual foi a última requisição enviada
    last_url = data["url"]

    # Caso a última url tenha sido 800x800, substituímos.
    # Caso contrário, basta manter como está
    if "800x800" in last_url:
        url = url.replace("800x800", "801x801")

    return url


def read_variables(time):
    '''
    Lê o arquivo JSON com as variáveis
    salvas para o período de tempo desejado
    e retorna como um dicionário do Python.

    Parâmetros:
​
    > time: O intervalo de tempo desejado. Pode ser
    '24h' ou '7d'.
    '''

    with open(f"{PROJECT_ROOT}/output/jsons/alerts/{time}.json") as f:
        data = json.load(f)

    return data


def save_request_info(url, style_id):
    '''
    Salva informações sobre o horário e a URL em que uma requisição
    foi feita.
    '''
    
    directory = f"{PROJECT_ROOT}/output/jsons/requests"
    if not os.path.exists(directory):
        os.makedirs(directory)

    data = {
        "url": url,
        "datetime": datetime.now().strftime("%m/%d/%Y,%H:%M:%S")
    }

    with open(f"{directory}/last-request-{style_id}.json", "w+") as f:
        json.dump(data, f)

######################
### Main functions ###
######################

def make_maps(time, land_type):
    '''
    Desenha e salva os mapas usando no fio
    do Twitter para as últimas 24h, usando o
    Python.
    
    Parâmetros:

    > time: O intervalo de tempo desejado. Pode ser
    24h' ou '7d'.
    
    > land_type: para que tipo de terra vamos fazer
    as análises. Pode ser 'tis' (terras indígenas) ou 'ucs'
    (unidades de conservação)
    '''
    
    # Lê os dados corretos
    data = read_variables(time)
    
    # Define parâmetros para o mapa
    figsize=(24,12)
    
    if land_type == "tis":
        data = data["terras_indigenas"]
        column_name = "cod_ti"
        land = TIS_INFO.copy()
        bgcolor =  "#edddd4"
        mapcolor = "#edddd4"
        landcolor = "#E9B6AF"
        edgecolor = "#000"
        firecolor = "#E01600"


    elif land_type == "ucs":
        data = data["unidades_de_conservacao"]
        column_name = "cod_uc"
        land = UCS_INFO.copy()
        bgcolor = "#FFEFD6"
        mapcolor = "#FFEFD6"
        landcolor = "#FFE4AD"
        edgecolor = "#000"
        firecolor = "#E01600"       

    # 1. Mapa com todos os focos de fogo que ocorreram
    # sobre o território do tipo determinado

    # Seleciona os focos de fogo que ocorreram sobre esse tipo de terra
    fires = FOGOS[time] 
    fires = fires[~fires[column_name].isna()]

    # Seleciona os territórios que tiveram algum fogo nas últimas 24h
    land = land[~land[f"focos_{time}"].isna()]

    # Plota e salva
    fig, ax = plt.subplots(facecolor=bgcolor, figsize=figsize)
    ESTADOS.plot(color=mapcolor, edgecolor="#000", ax=ax)
    land.plot(color=landcolor, edgecolor=edgecolor, alpha=1, ax=ax)
    fires.plot(color=firecolor, markersize=1, alpha=.5, ax=ax)
    ax.axis('off')

    fig.savefig(f"../output/imgs/tweets/{land_type}_{time}_todos_os_focos.png", 
                facecolor=fig.get_facecolor(), 
                transparent=True, 
                bbox_inches='tight',
                pad_inches = 0)

    
    # 2. Mapa com o território que sofre com mais fogo
    id_mais_fogo = data[f"areas_mais_fogo_{time}"]["1"]["id"]

    # Seleciona os focos de fogo do território específico
    fires = fires[fires[column_name]==id_mais_fogo]

    # Seleciona os limites do território
    land = land[land[column_name]==id_mais_fogo]


    # Plota e salva
    fig, ax = plt.subplots(facecolor=bgcolor, figsize=figsize)
    ESTADOS.plot(color=mapcolor, edgecolor="#000", ax=ax)
    land.plot(color=landcolor, edgecolor=edgecolor, alpha=1, ax=ax)
    fires.plot(color=firecolor, markersize=1, alpha=.5, ax=ax)
    ax.axis('off')

    fig.savefig(f"{PROJECT_ROOT}/output/imgs/tweets/{land_type}_{time}_local_mais_focos.png", 
            facecolor=fig.get_facecolor(), 
            transparent=True, 
            bbox_inches='tight', 
            pad_inches = 0)


def get_static_images(path, time, land_type):
    '''
    Usa a API do Mapbox para gerar
    imagens estáticas dos mapas desejados.

    Parâmetros:

    > path: o nome do arquivo em que a imagem deve ser salva
    > time: o recorte temporal que deve ser usado para gerar a imagem.
    Por enquanto, apenas '24h' foi implementado.
    > land_type: pode ser 'ucs' ou 'tis'. Determina
    qual imagem será requisita para a API.
    '''

    # Lê as variáveis do twitter
    twitter_vars = read_variables("24h")

    # Ids dos estilos em que queremos gerar o mapa
    style_ids = {
        "uc": "ckfa0tb682xcy19ntjuscr9sz",
        "ti": "cke3lwj1o092919m9dmiri8h7"
    }

    # Seleciona o id adequado
    style_id = style_ids[land_type]    

    # 1. Salvar mapa com todos os focos e terras em chamas

    # Monta a query 
    url =f"https://api.mapbox.com/styles/v1/{USERNAME}/{style_id}/static/-59.1764,-6.55711,4.2,0/800x800@2x?access_token={TOKEN}"
    # Adapta a url conforme necessário
    url = handle_cache(url, style_id)
    # Salva dados para aplicar o 'dibre' no cache
    save_request_info(url, style_id)



    r = requests.get(url, stream=True,  headers={'Cache-Control': "no-cache"})
    
    if r.status_code == 200:
        print(url)
        fpath = path + f"/{land_type}_{time}_todos_os_focos.jpg"
        with open(fpath, 'wb+') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        print(r.text)
        raise Exception(r.status_code)     

    # 2. Salvar o mapa com zoom na terra que mais teve fogo

    # Seleciona o overlay geojson que queremos colocar na imagem
    if land_type == "uc":
        overlay = UCS_INFO.copy()
        vars_key = "unidades_de_conservacao"
    elif land_type == "ti":
        overlay = TIS_INFO.copy()
        vars_key = "terras_indigenas"

    # Filtra o geodf para manter apenas a terra com mais focos
    most_fires_id = twitter_vars[vars_key]["areas_mais_fogo_24h"]["1"]["id"]
    overlay = overlay[overlay[f"cod_{land_type}"] ==  most_fires_id]
    
    assert overlay.shape[0] == 1, "ambiguous land id"

    # Transforma em um arquivo GeoJSON
    overlay = json.loads(
        overlay.head(1).geometry.simplify(.05).to_json() # Isso é uma string simples em formato json
    )

    # Adiciona geojson customizado no padrão simplestyle-spec do Mapbox
    # https://github.com/mapbox/simplestyle-spec/tree/master/1.1.0
    for feature in overlay["features"]:

        if land_type == "ti":

            feature["properties"] = {
                "fill":"%23551636",
                "stroke": "%23702341",
                "stroke-width": 3,
                "fill-opacity":.5,
            }

        elif land_type == "uc":

            feature["properties"] = {
                "fill":"%23195c53",
                "stroke": "%2327867b",
                "stroke-width": 3,
                "fill-opacity":.5,
            }

    # Transforma em string novamente
    overlay = json.dumps(overlay)

    # Altera o style do id para acessar os pontos corretos
    style_ids = {
        "uc": "ckfalqxwq1tce19qtb0tkg6cv",
        "ti": "ckfakmyg63j8m19lne8hkfe86"
    }

    style_id = style_ids[land_type]

    if land_type == "uc":
        layer_id = "ucs"
    elif land_type == "ti":
        layer_id = "ti"    


    # Constrói a URL
    url =f"https://api.mapbox.com/styles/v1/{USERNAME}/{style_id}/static/geojson({overlay})/auto/800x800@2x?access_token={TOKEN}&before_layer=amzsufocada-24h-{layer_id}-most-fire"
    url = handle_cache(url, style_id)
    save_request_info(url, style_id)
    print(url)

    # Envia requisição e salva o retorno
    r = requests.get(url, stream=True,  headers={'Cache-Control': "no-cache"})
    if r.status_code == 200: # Se a resposta for bem sucedida
        fpath = path + f"/{land_type}_{time}_local_mais_focos.jpg"
        with open(fpath, 'wb+') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
    else:
        print(r.text)
        raise Exception(r.status_code)     



################
### Execução ###
################

def main():
    
    times = ["24h"]
    land_types = ["uc", "ti"]
    
    for time in times:
        for land_type in land_types:
            path = f"{PROJECT_ROOT}/output/imgs/tweets/"
            get_static_images(path, time, land_type)

if __name__ == "__main__":
    main()
