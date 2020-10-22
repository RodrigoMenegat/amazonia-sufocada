'''
Esse script lê os dados e imagens salvos
por process_tweet_variables.py e process_tweet_images.py
e salva arquivos JSON com os fios que serão publicados por tweet.py
'''

from datetime import datetime, timedelta
import json
import os


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


###############
### Helpers ###
###############

def read_variables(time):
    '''
    Lê o arquivo JSON com as variáveis
    salvas para o período de tempo desejado
    e retorna como um dicionário do Python.

    Parâmetros:

    > time: O intervalo de tempo desejado. Pode ser
    '24h' ou '7d'.
    '''

    with open(f"{PROJECT_ROOT}/output/jsons/alerts/{time}.json") as f:
        data = json.load(f)

    return data


##########################
### Funções principais ###
##########################

def build_thread_most_fire_indigenous_land(data):
    '''
    Acessa as variáveis criadas por find_values
    para montar a thread diária sobre terras indígenas
    que será publicada no Twitter.
    
    O fio é estruturado em um array do objetos com um campo
    para o texto e um para o caminho de uma eventual foto.
    '''

    # Cria timestamps para garantir unicidade

    # Cria correspondências curtas para as variáveis,
    # tornando o texto do fio mais fácil de acompanhar.



    # Campos usados para evitar repetição exagerada
    day = datetime.now().strftime("%d/%m/%Y")
    total_geral = data["total_focos_amazonia_legal_2020"]
    total_fogo = data["terras_indigenas"]["total_focos_24h"]


    # Números

    a = data["terras_indigenas"]["areas_com_fogo_24h"]

    b = data["terras_indigenas"]["areas_mais_fogo_24h"]["1"]["nome"]
    c = data["terras_indigenas"]["areas_mais_fogo_24h"]["1"]["n_focos"]
    d = data["terras_indigenas"]["areas_mais_fogo_24h"]["1"]["porcentagem"]
    e = data["terras_indigenas"]["areas_mais_fogo_24h"]["1"]["dias_consecutivos"]
    estados_1 = data["terras_indigenas"]["areas_mais_fogo_24h"]["1"]["estados"]

    f = data["terras_indigenas"]["areas_mais_fogo_24h"]["2"]["nome"]
    g = data["terras_indigenas"]["areas_mais_fogo_24h"]["2"]["n_focos"]
    h = data["terras_indigenas"]["areas_mais_fogo_24h"]["2"]["porcentagem"]
    estados_2 = data["terras_indigenas"]["areas_mais_fogo_24h"]["2"]["estados"]

    i = data["terras_indigenas"]["areas_mais_fogo_24h"]["3"]["nome"]
    j = data["terras_indigenas"]["areas_mais_fogo_24h"]["3"]["n_focos"]
    k = data["terras_indigenas"]["areas_mais_fogo_24h"]["3"]["porcentagem"]
    estados_3 = data["terras_indigenas"]["areas_mais_fogo_24h"]["3"]["estados"]

    
    tweets = [ ]
    
    # Abertura
    tweet = {
        "text": (f"Olá! Hoje, {day}, nossa análise detectou {a} terras indígenas da Amazônia Legal com fogo ativo nas últimas 24h. Veja mais informações no fio 👇"),
        "img": None
    }
    tweets.append(tweet)
    
    # Chamada para imagem retirada da API do Mapbox.
    tweet = {
        "text": (f"Este mapa mostra todos os focos de calor em terras indígenas em {day}. As áreas roxas são as {a} terras indígenas onde foram registrados os focos. Cada ponto representa uma área de 0,14 km² em que o satélite detectou  atividade de fogo."),
        "img": "../output/imgs/tweets/ti_24h_todos_os_focos.jpg"
    }
    tweets.append(tweet)
    
    # Destaca a terra indígena com mais focos de fogo nas últimas 24h.
    tweet = { "text": f"A situação mais crítica acontece na Terra Indígena {b} ({estados_1}), cujos {c} focos são {d}% do total registrado em terras indígenas nas últimas 24h. Além disso, lá existem áreas com fogo há {e} dias seguidos. Veja no mapa.",
         "img": "../output/imgs/tweets/ti_24h_local_mais_focos.jpg"
    }
    tweets.append(tweet)
    
    
    tweet =  { 
                "text": (f"Ela, porém, não é a única que sofre. As outras duas terras com mais fogo no último dia foram estas:\n\n"
					f"- {f} ({estados_2}): {h}% do total, com {g} focos\n"
					f"- {i} ({estados_3}): {k}% do total, com {j} focos\n"),
                "img": None
            }
    tweets.append(tweet)
    
    
    tweet = { "text": f"Atenção para a metodologia! 📈 Nossa análise usa dados do satélite S-NPP, da NASA, que não é o mesmo que o INPE usa como referência desde 2002. Cada um dos {total_fogo} focos mostrados representa uma área de 0,14 km² com brilho e calor compatíveis com atividade de fogo.",
         "img": None
    }
    tweets.append(tweet)
    

    tweet = { "text": f"Você pode ver detalhes sobre a situação da Amazônia Legal na página especial do Amazônia Sufocada e navegar pelo mapa interativo com todos os {total_geral} focos de calor registrados na região em 2020. \n\nhttps://infoamazonia.org/sufocada",
         "img": None
    }
    tweets.append(tweet)
    

    # Não podemos aceitar nenhum tuíte com mais de 280 toques
    tweets_over_280_chars = [len(tweet["text"]) >= 280 for tweet in tweets]
    print([len(tweet["text"]) for tweet in tweets])
    assert not any(tweets_over_280_chars), "tuítes acima do limite de caracteres detectados"

    return tweets



def build_thread_most_fire_conservation_units(data):
    '''
    Acessa as variáveis criadas por find_values
    para montar a thread diária sobre unidades de conservação
    que será publicada no Twitter.
    
    O fio é estruturado em um array do objetos com um campo
    para o texto e um para o caminho de uma eventual foto.
    '''

    # Campos usados para evitar repetição exagerada
    day = datetime.now().strftime("%d/%m/%Y")
    total_geral = data["total_focos_amazonia_legal_2020"]
    total_fogo = data["unidades_de_conservacao"]["total_focos_24h"]

    # Cria correspondências curtas para as variáveis,
    # tornando o texto do fio mais fácil de acompanhar.

    a = data["unidades_de_conservacao"]["areas_com_fogo_24h"]

    b = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["1"]["nome"]
    c = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["1"]["n_focos"]
    d = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["1"]["porcentagem"]
    e = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["1"]["dias_consecutivos"]
    estados_1 = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["1"]["estados"]


    f = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["2"]["nome"]
    g = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["2"]["n_focos"]
    h = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["2"]["porcentagem"]
    estados_2 = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["2"]["estados"]


    i = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["3"]["nome"]
    j = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["3"]["n_focos"]
    k = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["3"]["porcentagem"]
    estados_3 = data["unidades_de_conservacao"]["areas_mais_fogo_24h"]["3"]["estados"]


    
    tweets = [ ]
    
    # Abertura
    tweet = {
        "text": (f"Oi! Nossa análise descobriu que há {a} unidades de conservação na Amazônia Legal com fogo ativo no último dia, {day}. Mais detalhes no fio 👇"),
        "img": None
    }
    tweets.append(tweet)
    
    # Chamada para imagem retirada da API do Mapbox.
    tweet = {
        "text": (f"No mapa abaixo, as áreas verdes são unidades de conservação com focos de calor em {day}. Cada ponto representa 0,14 km² em que o satélite detectou atividade de fogo."),
        "img": f"{PROJECT_ROOT}/output/imgs/tweets/uc_24h_todos_os_focos.jpg"
        
    } 
    tweets.append(tweet)
    
    # Destaca a terra indígena com mais focos de fogo nas últimas 24h.
    tweet = { "text": f"Nas últimas 24h, a maior quantidade de focos aconteceu na unidade {b} ({estados_1}), que teve {c} pontos de fogo ({d}% do total). Essa área está queimando há {e} dias. Veja no mapa:",

         "img": f"{PROJECT_ROOT}/output/imgs/tweets/uc_24h_local_mais_focos.jpg"

    }
    tweets.append(tweet)
    
    
    tweet =  { 
                "text": (f"As outras duas unidades de conservação com mais fogo no últimos dia foram estas:\n\n"
                    f"- {f} ({estados_2}): {h}% do total, com {g} focos\n"
                    f"- {i} ({estados_3}): {k}% do total, com {j} focos\n"),

                "img": None
              
            }
    tweets.append(tweet)
    
    
    tweet = { "text": f"Atenção para a metodologia! 📈 A análise usa dados do satélite S-NPP, da NASA, que tem mais resolução que a referência utilizada pelo Inpe e capta maior número de focos. Cada um dos {total_fogo} focos representa uma área de 0,14 km² que pode conter várias ou uma única frente de fogo.",
         "img": None
    }
    tweets.append(tweet)
    

    tweet = { "text": f"Você pode ver mais detalhes sobre a situação da Amazônia Legal na página especial Amazônia Sufocada e navegar pelo mapa interativo com todos os {total_geral} focos de calor registrados na região em 2020. \n\nhttps://infoamazonia.org/sufocada",
         "img": None
    }
    tweets.append(tweet)


    # Não podemos aceitar nenhum tuíte com mais de 280 toques
    tweets_over_280_chars = [len(tweet["text"]) >= 280 for tweet in tweets]
    print([len(tweet["text"]) for tweet in tweets])
    assert not any(tweets_over_280_chars), "tuítes acima do limite de caracteres detectados"
    
    return tweets


def build_thread_7d_grid(data):
    '''
    Acessa as variáveis criadas por find_values
    para montar a thread semanal com base nos grids de
    20 km quadrados que será publicada no Twitter.
    
    O fio é estruturado em um array do objetos com um campo
    para o texto e um para o caminho de uma eventual foto.
    '''

    # Definição de variáveis

    # Datas
    today = datetime.now()
    last_week_date = today - timedelta(days=7) # O cálculo é sempre para sete dias antes, então
                                               # o texto dos tweets só estará correto na data
                                               # de publicação, que acontece nas segundas-feiras,
                                               # mas com dados de domingo.


    # Formato DD/MM/YY
    today = today.strftime("%d/%m/%Y")
    last_week_date = last_week_date.strftime("%d/%m/%Y")

    # Gerais

    total_geral = data["total_focos_amazonia_legal_2020"]
    total_semana = data["total_focos_7d"]
    total_focos_7d_uc = data["total_focos_7d_uc"]
    total_focos_7d_uc_pp = round(total_focos_7d_uc / total_semana * 100)
    total_focos_7d_ti = data["total_focos_7d_ti"] 
    total_focos_7d_ti_pp = round(total_focos_7d_ti / total_semana * 100)



    # Destaque 1
    grid_1_n_focos = data["grid"]["areas_mais_fogo_7d"]["1"]["n_focos"]
    grid_1_dias_consecutivos = data["grid"]["areas_mais_fogo_7d"]["1"]["dias_consecutivos"]
    grid_1_cidade = data["grid"]["areas_mais_fogo_7d"]["1"]["cidade"]
    grid_1_estado = data["grid"]["areas_mais_fogo_7d"]["1"]["estado"]
    grid_1_bioma = data["grid"]["areas_mais_fogo_7d"]["1"]["nome_bioma"]
    grid_1_ti = data["grid"]["areas_mais_fogo_7d"]["1"]["nome_ti"]
    grid_1_uc = data["grid"]["areas_mais_fogo_7d"]["1"]["nome_uc_curto"]


    # Destaque 2
    grid_2_n_focos = data["grid"]["areas_mais_fogo_7d"]["2"]["n_focos"]
    grid_2_dias_consecutivos = data["grid"]["areas_mais_fogo_7d"]["2"]["dias_consecutivos"]
    grid_2_cidade = data["grid"]["areas_mais_fogo_7d"]["2"]["cidade"]
    grid_2_estado = data["grid"]["areas_mais_fogo_7d"]["2"]["estado"]
    grid_2_bioma = data["grid"]["areas_mais_fogo_7d"]["2"]["nome_bioma"]
    grid_2_ti = data["grid"]["areas_mais_fogo_7d"]["2"]["nome_ti"]
    grid_2_uc = data["grid"]["areas_mais_fogo_7d"]["2"]["nome_uc_curto"]


    # Destaque 3
    grid_3_n_focos = data["grid"]["areas_mais_fogo_7d"]["3"]["n_focos"]
    grid_3_dias_consecutivos = data["grid"]["areas_mais_fogo_7d"]["3"]["dias_consecutivos"]
    grid_3_cidade = data["grid"]["areas_mais_fogo_7d"]["3"]["cidade"]
    grid_3_estado = data["grid"]["areas_mais_fogo_7d"]["3"]["estado"]
    grid_3_bioma = data["grid"]["areas_mais_fogo_7d"]["3"]["nome_bioma"]
    grid_3_ti = data["grid"]["areas_mais_fogo_7d"]["3"]["nome_ti"]
    grid_3_uc = data["grid"]["areas_mais_fogo_7d"]["3"]["nome_uc_curto"]


    # Conteúdo do fio
    tweets = [ ]
    
    # Abre
    tweet = {
        "text": (f"Olá! Chegou o dia do nosso relatório semanal, em que falamos sobre as regiões da Amazônia Legal que mais tiveram focos de calor na semana passada, entre o domingo de {last_week_date} e ontem. Acompanhe no fio 👇"),
        "img": None
    }
    tweets.append(tweet)

    # Quantas estão em regiões protegidas?
    tweet = {
        "text": (f"De todos os focos de fogo registrados nos últimos sete dias, {total_focos_7d_ti_pp}% aconteceram dentro de terras indígenas e {total_focos_7d_uc_pp}% aconteceram em unidades de conservação."),
        "img": None
    }
    tweets.append(tweet)


    # Destaque das áreas
    tweet = {
        "text": (f"No mapa abaixo, cada quadrado representa uma região de 400km² com ao menos um foco de calor registrado na semana. Quanto mais roxo ele estiver, mais focos de calor aconteceram lá dentro."),
        "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_todas_as_areas.jpg"
    }
    tweets.append(tweet)


    # Área de destaque 1
    if not grid_1_ti and not grid_1_uc:
        tweet = {
            "text": (f"A região com mais fogo está em destaque no mapa, com focos de calor em amarelo. Ela fica nos arredores de {grid_1_cidade}, {grid_1_estado}, e faz parte do bioma {grid_1_bioma}. Essa área está queimando há {grid_1_dias_consecutivos} dias consecutivos."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_1.jpg"
        }
        tweets.append(tweet)

    elif grid_1_ti and not grid_1_uc:
        tweet = {
            "text": (f"A região com mais fogo está em destaque no mapa, com focos de calor em amarelo. Ela fica nos arredores de {grid_1_cidade}, {grid_1_estado}. Essa área está queimando há {grid_1_dias_consecutivos} dias consecutivos. Ao menos parte dela está na terra indígena {grid_1_ti}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_1.jpg"
        }
        tweets.append(tweet)

    elif not grid_1_ti and grid_1_uc:
        tweet = {
            "text": (f"Veja no mapa a região com mais fogo, nos arredores de {grid_1_cidade}, {grid_1_estado}. Essa área está queimando há {grid_1_dias_consecutivos} dias consecutivos. Ao menos parte dela está na unidade de conservação {grid_1_uc}. Pontos amarelos representam focos de calor."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_1.jpg"
        }
        tweets.append(tweet)

    elif grid_1_ti and grid_1_uc:
        tweet = {
            "text": (f"Veja no mapa a região com mais fogo, perto de {grid_1_cidade}, {grid_1_estado}. Essa área queima há {grid_1_dias_consecutivos} dias consecutivos. Ao menos parte dela está na unidade de conservação {grid_1_uc} e na terra indígena {grid_1_ti}. Pontos amarelos são focos de calor."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_1.jpg"
        }
        tweets.append(tweet)


    # Área de destaque 2
    if not grid_2_ti and not grid_2_uc:
        tweet = {
            "text": (f"Outras áreas também estão em situação crítica. A 2ª região que mais queima fica no município de {grid_2_cidade}, {grid_2_estado}, e faz parte do bioma {grid_2_bioma}. Essa área está queimando há {grid_2_dias_consecutivos} dias consecutivos."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_2.jpg"
        }
        tweets.append(tweet)

    elif grid_2_ti and not grid_2_uc:
        tweet = {
            "text": (f"Outras áreas também estão em situação crítica. A 2ª região que mais queima fica no município de {grid_2_cidade}, {grid_2_estado}. Essa área está queimando há {grid_2_dias_consecutivos} dias consecutivos. Ao menos parte dela fica na terra indígena {grid_2_ti}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_2.jpg"
        }
        tweets.append(tweet)

    elif not grid_2_ti and grid_2_uc:
        tweet = {
            "text": (f"Outras áreas também estão em situação crítica. A 2ª região que mais queima fica no município de {grid_2_cidade}, {grid_2_estado}. Essa área está queimando há {grid_2_dias_consecutivos} dias consecutivos. Ao menos parte dela fica na unidade de conservação {grid_2_uc}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_2.jpg"
        }
        tweets.append(tweet)

    elif grid_2_ti and grid_2_uc:
        tweet = {
            "text": (f"Outras áreas também estão em situação crítica. A 2ª área que mais queima está no município de {grid_2_cidade}, {grid_2_estado}. Essa área queima há {grid_2_dias_consecutivos} dias consecutivos. Partes dela ficam na undidade de conservação {grid_2_uc} e na terra indígena {grid_2_ti}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_2.jpg"
        }
        tweets.append(tweet)


    # Área de queimada 3
    if not grid_3_ti and not grid_3_uc:
        tweet = {
            "text": (f"Por fim, a 3ª área com mais focos de calor fica em {grid_3_cidade}, {grid_3_estado} e faz parte do bioma {grid_3_bioma}. Há registro de fogo na região faz {grid_3_dias_consecutivos} dias seguidos."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_3.jpg"
        }
        tweets.append(tweet)

    elif grid_3_ti and not grid_3_uc:
        tweet = {
            "text": (f"Por fim, a 3ª área com mais focos de calor fica em {grid_3_cidade}, {grid_3_estado}. Há registro de fogo na região faz {grid_3_dias_consecutivos} dias seguidos. Ao menos parte dessa área fica na terra indígena {grid_3_ti}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_3.jpg"
        }
        tweets.append(tweet)

    elif not grid_3_ti and grid_3_uc:
        tweet = {
            "text": (f"Por fim, a 3ª área que mais queima fica em {grid_3_cidade}, {grid_3_estado}. Há registro de fogo na região faz {grid_3_dias_consecutivos} dias seguidos. Ao menos parte dessa área está na unidade de conservação {grid_3_uc}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_3.jpg"
        }
        tweets.append(tweet)

    elif grid_3_ti and grid_3_uc:
        tweet = {
            "text": (f"Por fim, a 3ª área que mais queima está no município de {grid_3_cidade}, {grid_3_estado}. Essa área queima há {grid_3_dias_consecutivos} dias consecutivos. Partes dela ficam na unidade de conservação {grid_3_uc} e na terra indígena {grid_3_ti}."),
            "img": f"{PROJECT_ROOT}/output/imgs/tweets/grid_7d_mais_fogo_3.jpg"
        }
        tweets.append(tweet)


    # Metodologia
    tweet = {
            "text": (f"Para identificar as áreas listadas, dividimos o território da Amazônia Legal em uma grade de quadrados de cerca de 20km de lado. As áreas com mais fogo são aquelas que tiveram mais focos de calor detctados pelo satélite S-NPP, da NASA, entre ontem e o domingo anterior, {last_week_date}."),
            "img": None
        }
    tweets.append(tweet)

    tweet = {
            "text": (f"Esse satélite não é o mesmo que o INPE usa como referência desde 2002. Cada um dos {total_semana} focos registrados nessa semana representa uma área de 0,14km² com brilho e calor compatíveis com atividade de fogo."),
            "img": None
        }
    tweets.append(tweet)


    # Link out
    tweet = {
            "text": (f"Você pode ver mais detalhes na página especial do Amazônia Sufocada e navegar pelo mapa interativo com todos os {total_geral} focos de calor registrados na região em 2020.\n\nhttps://infoamazonia.org/sufocada"),
            "img": None
        }
    tweets.append(tweet)



    # Checagem de tamanho
    tweets_over_280_chars = [len(tweet["text"]) >= 280 for tweet in tweets]
    print([len(tweet["text"]) for tweet in tweets])
    assert not any(tweets_over_280_chars), "tuítes acima do limite de caracteres detectados"
    
    return tweets

################
### Execução ###
################

def main():


    # Verifica se o diretório de tweets de fato existe
    directory = f"{PROJECT_ROOT}/output/jsons/tweets/"
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Lê os dados das variáveis de 24h
    data_24h = read_variables("24h")

    # Terras indígenas, 24h
    with open(f"{PROJECT_ROOT}/output/jsons/tweets/tis_24h.json", "w+") as f:
        content = build_thread_most_fire_indigenous_land(data_24h)
        json.dump(content, f, indent=2)

    # Unidades de conservação, 24h
    with open(f"{PROJECT_ROOT}/output/jsons/tweets/ucs_24h.json", "w+") as f:
        content = build_thread_most_fire_conservation_units(data_24h)
        json.dump(content, f, indent=2)


    # Lê os dados das variáveis de 7 dias
    data_7d = read_variables("7d")
    with open(f"{PROJECT_ROOT}/output/jsons/tweets/grid_7d.json", "w+") as f:
        content = build_thread_7d_grid(data_7d)
        json.dump(content, f, indent=2)

if __name__ == "__main__":
	main()
