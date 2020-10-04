'''
Esse script salva as variáveis necessárias para gerar
os tweets que serão publicados no robô monitor do InfoAmazônia.
Elas são salvas em formato JSON para que sejam lidas posteriormente
pelo script que faz a publicação no Twitter.
'''
import pandas as pd
import geopandas as gpd
import os
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
GRID_FIRE_DATA = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/grid_20km.feather")

CITIES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/cidades_amazonia_legal.feather")
CONSERVATION_UNITS =  gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/unidades_de_conservacao.feather")
INDIGENOUS_LAND = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/terras_indigenas.feather")
LEGAL_AMAZON = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/limites_amazonia_legal.feather")
BIOMES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/biomas_amazonia_legal.feather")
GRID = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/grid_20km.feather")

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
    estados = look_up(source, code, id_, "estado")
    
    
    return {
        "id": id_,
        "nome": nome,
        "n_focos": n_focos,
        "porcentagem": porcentagem,
        "dias_consecutivos": dias_consecutivos,
        "estados": estados
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
    estados = result["estado"]
    
    
    # Verifica se há 'empates'
    is_draw = df[df["dias_consecutivos"] == result["dias_consecutivos"]].shape[0] > 1
        
    return {
        "id": id_,
        "nome": nome,
        "dias_consecutivos": dias_consecutivos,
        "is_draw": is_draw,
        "estados": estados

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

def find_values_24h():
    '''
    Faz consulta aos bancos de dados para gerar todas as
    variáveis necessárias para a elaboração dos fios
    que são publicados a cada 24h no Twitter.
    Eles resumem o estado 
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
    


    return {
        "total_focos_amazonia_legal_2020": DF_FULL.shape[0],
    	"terras_indigenas": terras_indigenas,
    	"unidades_de_conservacao": unidades_de_conservacao
    }


def find_values_7d():
    '''
    Faz consulta aos bancos de dados para gerar todas as
    variáveis necessárias para a elaboração do fio no
    Twitter.
    '''

    ###############
    ### Helpers ###
    ###############

    def find_rects_with_fire_in_proteced_areas(n, time):
        '''
        Descobre, dos n grids com mais fogo, quantos estão
        em Terras Indígenas e Unidades de Conservação.

        Parâmetros:

        n -> Inteiro que representa quantidade de grids que devem ser considerados nessa conta. 
        time -> String que representa o intervalo de agregação. Pode ser '24h', '7d' ou 'full_db'
        '''

        # Seleciona os dez grids com mais foco
        grids_most_fire = GRID_FIRE_DATA.sort_values(by=f"focos_{time}").head(n)

        # Quantos desses estão em terras indígenas?
        grids_ind_land = grids_most_fire[~grids_most_fire.cod_ti.isna()].shape[0]

        # Quantos desses estão em unidades de conservação?
        grids_conservation_unit = grids_most_fire[~grids_most_fire.cod_uc.isna()].shape[0]

        grids_protected_areas = grids_most_fire[(~grids_most_fire.cod_uc_isna()) | ~grids_most_fire.cod_ti.isna()].shape[0]


        return {
            "em_tis": grids_ind_land,
            "em_ucs": grids_conservation_unit,
            "total": grids_protected_areas
        }



    def find_grid_with_most_fire(time, total_fires, position=1):
        '''
        Encontra qual é o retângulo do grid com mais fogo
        em um determinado recorte temporal. Retorna, também,
        informações detalhadas sobre ele.
        
        Parâmetros:

        time -> String que representa o intervalo de agregação. Pode ser '24h', '7d' ou 'full_db'

        total_fires -> O número de focos de incêndio total registrados em áreas do mesmo tipo. É usado
        para calcular qual o percentual que os focos registrados em cada terra representam do total.

        position -> Com esse parâmetro, é possível selecionar outros locais que não o primeiro colocado em número
        de focos. Por exemplo, se especificarmos o valor 2, a função vai retornar dados sobre o segundo território
        em situação mais crítica.
        '''
        
        # Seleciona o grid com mais fogo
        grid_most_fire = GRID_FIRE_DATA.sort_values(by=f"focos_{time}", ascending = False).reset_index().loc[position-1]
        
        # Pega as informações básicas
        id_ = grid_most_fire["cod_box"]
        n_focos = int(grid_most_fire[f"focos_{time}"])

        porcentagem = round(n_focos / total_fires * 100)
        dias_consecutivos = grid_most_fire["dias_consecutivos"]
        
        # Vamos escolher apenas um dos vários territórios que intersectam a área para garantir que o tuíte seja sucinto
        cidade = grid_most_fire["cidade"].split(",")[0].strip() if grid_most_fire["cidade"] else None
        estado = grid_most_fire["estado"].split(",")[0].strip() if grid_most_fire["estado"] else None
        nome_ti = grid_most_fire["nome_ti"].split(",")[0].strip() if grid_most_fire["nome_ti"] else None
        cod_ti = grid_most_fire["cod_ti"].split(",")[0].strip() if grid_most_fire["cod_ti"] else None
        nome_uc = grid_most_fire["nome_uc"].split(",")[0].strip() if grid_most_fire["nome_uc"] else None
        cod_uc = grid_most_fire["cod_uc"].split(",")[0].strip() if grid_most_fire["cod_uc"] else None
        nome_bioma = grid_most_fire["nome_bioma"].split(",")[0].strip() if grid_most_fire["nome_bioma"] else None

        # Pega o nome curto, pré-formatado, da UC
        if cod_uc:
            nome_uc_curto = CONSERVATION_UNITS[CONSERVATION_UNITS.cod_uc == cod_uc].reset_index().loc[0, "nome_uc_curto"]
        else:
            nome_uc_curto = None
        
        
        return {
            "id": id_,
            "n_focos": n_focos,
            "porcentagem": porcentagem,
            "dias_consecutivos": dias_consecutivos,
            "cidade": cidade,
            "estado": estado,
            "nome_ti": nome_ti,
            "nome_uc": nome_uc,
            "nome_uc_curto": nome_uc_curto,
            "nome_bioma": nome_bioma
        }



    # Áreas do grid com mais fogo
    grid = {}

    # Das dez áreas com mais fogo, quantas são em UCs e TIs?
    grid["fogo_em_areas_protegidas"] = find_rects_with_fire_in_proteced_areas(10, "7d")

    # Grids com mais focos de foco nos últimos 7d e detalhes sobre eles
    grid["areas_mais_fogo_7d"] = { }
    for i in range(1, 4):
        grid["areas_mais_fogo_7d"][f"{i}"] = find_grid_with_most_fire("7d", DF_7D.shape[0], i)

    return {
        "total_focos_amazonia_legal_2020": DF_FULL.shape[0],
        "total_focos_7d": DF_7D.shape[0],
        "grid": grid,
    }

################
### Execução ###
################

def main():

    data = find_values_24h()
    with open(f"{PROJECT_ROOT}/output/jsons/alerts/24h.json", "w+") as f:
        json.dump(data, f, indent=4)

    data = find_values_7d()
    with open(f"{PROJECT_ROOT}/output/jsons/alerts/7d.json", "w+") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
	main()
