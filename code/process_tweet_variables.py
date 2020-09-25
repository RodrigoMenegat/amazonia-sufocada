'''
Esse script salva as variáveis necessárias para gerar
os tweets que serão publicados no robô monitor do InfoAmazônia.
Elas são salvas em formato JSON para que sejam lidas posteriormente
pelo script que faz a publicação no Twitter.
'''
import pandas as pd
import geopandas as gpd
import json
from pprint import pprint

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

######################
### DATA CONSTANTS ###
######################

DF_24H = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/24h.feather")
DF_7D = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/7d.feather")
DF_FULL = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo.feather")

CONSERVATION_UNITS_FIRE_DATA = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/unidades_de_conservacao.feather")
INDIGENOUS_LAND_FIRE_DATA = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/terras_indigenas.feather")
BIOMES_FIRE_DATA = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/biomas.feather")

CITIES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/cidades_amazonia_legal.feather")
CONSERVATION_UNITS =  gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/unidades_de_conservacao.feather")
INDIGENOUS_LAND = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/terras_indigenas.feather")
LEGAL_AMAZON = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/limites_amazonia_legal.feather")
BIOMES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/biomas_amazonia_legal.feather")

###############
### Helpers ###
###############

def look_up(df, lookup_column, lookup_value, result_column):
    '''
    Retorna um nome de campo com base em um código identificador.
    Assegura-se que apenas um resultado positivo é possível.
    A funcionalidade é semelhante ao vlookup do Excel.
    
    Parâmetros:
    
    df -> Um dataframe
    
    lookup_column -> Em que coluna devemos fazer a busca
    
    lookup_value -> Que valor devemos procurar
    
    result_column -> A coluna com o valor que deve ser retornado
    
    Fonte:
    https://stackoverflow.com/questions/46371391/lookup-first-match-in-pandas-dataframe
    '''
    
    # Faza busca
    s = df.loc[df[lookup_column]==lookup_value, result_column]
    
    # Sem resultado? Levantar exceção.
    if s.empty:
        raise ValueError("Nenhum resultado encontrado")
    
    # Se a busca encontrar apenas um valor, está correta
    elif len(s) == 1:
        return s.item()
    
    # Diferente de 1? Levantar exceção.
    else:
        raise ValueError("Mais de um resultado encontrado. Assegure-se que o código para busca não é ambíguo.")

def find_places_with_fire(df, code):
    '''
    Conta quantas unidades do tipo de terra selecionado
    tiveram ao menos um registro de foco no dataframe.
    
    Parâmetros:
    
    df -> Um dataframe com focos de queimada em determinado recorte temporal.
    
    code -> O código do tipo de terra em que iremos verificar se há fogo. Pode ser 'cod_uc', 'cod_ti' ou 'cod_bioma'.
    '''
    
    # Pega todos os focos de calor que ocorreram no tipo de área especificado
    focos_em_terras = df[~df[code].isna()]

    # Conta os ids únicos dessas terras
    terras_com_fogo = focos_em_terras[code].unique().shape[0]


    return terras_com_fogo

def find_place_with_most_fire(df, code, total_fires, position=1):
    '''
    Encontra qual é o território com mais fogo
    em um dataframe. Retorna um dicionário com
    os seguintes dados: id, nome do território,
    número de focos de fogo e dias consecutivos
    de queima.
    
    Parâmetros:
    
    df -> Um dataframe com focos de queimada em determinado recorte temporal.
    
    code -> O código do tipo de terra em que iremos contar os focos. Pode ser 'cod_uc', 'cod_ti' ou 'cod_bioma'.
    Caso nenhum tipo de terra seja especificado, conta todos os focos.
    
    position -> Com esse parâmetro, é possível selecionar outros locais que não o primeiro colocado em número
    de focos. Por exemplo, se especificarmos o valor 2, a função vai retornar dados sobre o segundo território
    em situação mais crítica.

    total_fires -> O número de focos de incêndio total registrados em áreas do mesmo tipo. É usado
    para calcular qual o percentual que os focos registrados em cada terra representam do total.
    '''
    
    # Determina nomes de coluna de acordo com o tipo de terra
    
    if code == 'cod_ti':
        source = INDIGENOUS_LAND_FIRE_DATA
        result_column = "nome_ti"
        
    elif code == 'cod_uc':
        source = CONSERVATION_UNITS_FIRE_DATA
        result_column = "nome_uc_curto" 
        
    elif code == 'cod_bioma':
        source = BIOMES_FIRE_DATA
        result_column = "nome_bioma"
        
    
    df = df[~df[code].isna()]
    
    id_ = df.groupby(code).uuid.count().sort_values(ascending=False).reset_index().loc[position-1, code]
    nome = look_up(source, code, id_, result_column)
    n_focos = int(look_up(source, code, id_, "focos_24h"))
    porcentagem = round(n_focos / total_fires * 100)
    dias_consecutivos = int(look_up(source, code, id_, "dias_consecutivos"))
    
    
    return {
        "id": id_,
        "nome": nome,
        "n_focos": n_focos,
        "porcentagem": porcentagem,
        "dias_consecutivos": dias_consecutivos
    }

def burning_for_the_longest(df, code, position=1):
    '''
    Essa função encontra a unidade de território
    que está queimando a mais dias consecutivos.
    Ao informar um valor para o parâmetro 'position',
    é possível escolher, por exemplo, a segunda terra
    que mais queima (position=2).
    
    Parâmetros:
    
    df -> Um dataframe com dados sobre queimadas em uma modalidade de terra.
    
    code -> O código do tipo de terra em que iremos contar os focos. Pode ser 'cod_uc', 'cod_ti' ou 'cod_bioma'.
    
    position -> Com esse parâmetro, é possível selecionar outros locais que não o primeiro colocado em número
    de focos. Por exemplo, se especificarmos o valor 2, a função vai retornar dados sobre o segundo território
    em situação mais crítica.
    '''
    
    # Determina nomes de coluna de acordo com o tipo de terra
    if code == 'cod_ti':
        name_column = "nome_ti"
        
    elif code == 'cod_uc':
        name_column = "nome_uc_curto" 
        
    elif code == 'cod_bioma':
        name_column = "nome_bioma"
    
    # Pega a quantidade de dias consecutivos em que o território em primeiro lugar está queimando,
    # assim como detalhes sobre ele.
    result = df.sort_values(by='dias_consecutivos', ascending=False).reset_index().loc[position-1]
    id_ = str(result[code])
    nome = result[name_column]
    dias_consecutivos = int(result['dias_consecutivos'])
    
    
    # Verifica se há 'empates'
    is_draw = df[df["dias_consecutivos"] == result["dias_consecutivos"]].shape[0] > 1
        
    return {
        "id": id_,
        "nome": nome,
        "dias_consecutivos": dias_consecutivos,
        "is_draw": is_draw
    }


def total_fires(df, code):
    '''
    Encontra o total de focos de calor
    observados no tipo de território.

    Parâmetros:

    df -> Um dataframe com focos de queimada em determinado recorte temporal.
    
    code -> O código do tipo de terra em que iremos contar os focos. Pode ser 'cod_uc', 'cod_ti' ou 'cod_bioma'.
    Caso nenhum tipo de terra seja especificado, conta todos os focos.
    '''

    total_fires = df[~df[code].isna()].shape[0]

    return total_fires

##########################
### Funções principais ###
##########################

def find_values():
    '''
    Faz consulta aos bancos de dados para gerar todas as
    variáveis necessárias para a elaboração do fio no
    Twitter.
    '''
    
    # 1. Thread de terras indígenas nas últimas 24h
    terras_indigenas = {}

    # Total de focos de fogo nas últimas 24h
    terras_indigenas["total_focos_24h"] = total_fires(DF_24H, "cod_ti")
    
    # Total de terras indígenas com fogo nas últimas 24h
    terras_indigenas["areas_com_fogo_24h"] = find_places_with_fire(DF_24H, "cod_ti")

    # Terras indígena com mais focos de fogo nas últimas 24h e detalhes sobre elas
    terras_indigenas["areas_mais_fogo_24h"] = { }
    for i in range(1, 4):
        terras_indigenas["areas_mais_fogo_24h"][f"{i}"] = find_place_with_most_fire(DF_24H, "cod_ti", terras_indigenas["total_focos_24h"], i)

    # Terra indígena que está queimando faz mais tempo e detalhes sobre ela
    terras_indigenas["areas_fogo_mais_dias"] = { }
    for i in range(1,4):
        terras_indigenas["areas_fogo_mais_dias"][f"{i}"] = burning_for_the_longest(INDIGENOUS_LAND_FIRE_DATA, 'cod_ti', i)
        

    # 2. Thread de unidades de conservação nas últimas 24h

    unidades_de_conservacao = {}

    # Total de focos de fogo nas últimas 24h
    unidades_de_conservacao["total_focos_24h"] = total_fires(DF_24H, "cod_uc")

    # Total de unidades de conservação com fogo nas últimas 24h
    unidades_de_conservacao["areas_com_fogo_24h"] = find_places_with_fire(DF_24H, "cod_uc")

    # Unidade de conservação com mais focos de fogo nas últimas 24h e detalhes sobre ela
    unidades_de_conservacao["areas_mais_fogo_24h"] = { }
    for i in range(1, 4):
        unidades_de_conservacao["areas_mais_fogo_24h"][f"{i}"] = find_place_with_most_fire(DF_24H, "cod_uc", unidades_de_conservacao["total_focos_24h"], i)
                
    # Unidade de conservação que está queimando faz mais tempo e detalhes sobre ela
    unidades_de_conservacao["areas_fogo_mais_dias"] = { }
    for i in range(1,4):
        unidades_de_conservacao["areas_fogo_mais_dias"][f"{i}"] = burning_for_the_longest(CONSERVATION_UNITS_FIRE_DATA, 'cod_uc', i)


    # 3. O total de fogos na Amazônia Legal e
    


    return {
        "total_focos_amazonia_legal_2020": DF_FULL.shape[0],
    	"terras_indigenas": terras_indigenas,
    	"unidades_de_conservacao": unidades_de_conservacao
    }


################
### Execução ###
################

def main():

	data = find_values()
	with open(f"{PROJECT_ROOT}/output/jsons/alerts/24h.json", "w+") as f:
		json.dump(data, f, indent=4)


if __name__ == "__main__":
	main()