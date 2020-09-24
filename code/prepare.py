'''
Prepara os bancos de dados brutos
para que o programa seja executado
de forma otimizada.
'''

import geopandas as gpd
import pandas as pd
import os
import re
import shutil
import uuid
import warnings 

warnings.filterwarnings('ignore', message='.*initial implementation of Parquet.*') # Aviso de versão inicial do feather


###############
### Helpers ###
###############

def add_biomes(row, biomes):
    '''
    Adiciona dados sobre os biomas que interceptam
    cada um dos territórios.
    
    Parâmetros:
    
    > row: uma linha do dataframe, representando um território
    > biomes: o geodataframe de biomas
    '''
    
    # Um geodataframe com todos os biomas que intersectam o território
    intersecting_biomes = biomes[biomes.geometry.intersects(row.geometry)]
    
    # Transforma em array de nomes
    intersecting_biomes = intersecting_biomes.nome_bioma.tolist()
    
    # E, finalmente, em string separada por vírgulas
    intersecting_biomes = ", ".join(intersecting_biomes)
    
    # Retorna uma série
    return pd.Series({
        "biomas": intersecting_biomes
    })


def add_cities(row, cities):
    '''
    Adiciona dados sobre as cidades (e, consequentemente, estados)
    que intersectam cada território.
    
    Parâmetros:
    
    > row: uma linha do dataframe, representando um território
    > cities: o geodataframe de cidades
    '''
    
    # Um geodataframe com todos os biomas que intersectam o território
    intersecting_cities = cities[cities.geometry.intersects(row.geometry)]
    
    # Transforma em array de nomes
    intersecting_cities_arr = intersecting_cities.cidade.tolist()
    intersecting_states_arr = intersecting_cities.estado.unique().tolist()
    
    # E, finalmente, em string separada por vírgulas
    intersecting_cities_str = ", ".join(intersecting_cities_arr)
    intersecting_states_str = ", ".join(intersecting_states_arr)
    
    # Retorna uma série
    return pd.Series({
        "cities": intersecting_cities_str,
        "states": intersecting_states_str
    })


def shorten_name(row):
    '''
    Função apply para encurtar os nomes de Unidades de Conservação
    com base em abreviações de suas designações técnicas.
    '''
    # Coletânea de prefixos para substituir
    preffixes = {
        "Parque": "Pq.",
        "Parque Estadual": "Pq. Est.",
        "Refúgio de Vida Silvestre": "RDVS",
        "Parque Nacional": "Pq. Nac.",
        "Floresta": "Fl.",
        "Floresta Estadual": "Fl. Est",
        "Floresta Nacional": "Fl. Nac.",
        "Área de Proteção Ambiental": "APA",
        "Reserva de Desenvolvimento Sustentável":"RDS",
        "Reserva Extrativista": "Res. Ext.",
        "Reserva Particular do Patrimônio Natural": "RPPN",
        "Estação Ecológica": "Est. Eco.",
        "Reserva Biológica": "Res. Bio.",
        "Área de Relevante Interesse Ecológico": "ARIE",
        "Monumento Natural": "Mon. Nat."

    }

    # Salva o velho nome em uma variável
    old_name = row.nome_uc

    # O novo nome será 'transformado' aos poucos
    new_name = old_name

    # Coloca os prefixos de/do/da  e o conjuntivo e em minúscula
    new_name = re.sub("Do ", "do ", new_name)
    new_name = re.sub("Da ", "da ", new_name)
    new_name = re.sub("De ", "de ", new_name)
    new_name = re.sub("Dos ", "dos ", new_name)
    new_name = re.sub("Das ", "das ", new_name)
    new_name = re.sub("Das ", "das ", new_name)
    new_name = re.sub(" E ", " e ", new_name)


    # Troca 'Estadual' e 'Nacional' por abreviação
    new_name = re.sub("Estadual", "Est.", new_name)
    new_name = re.sub("Nacional", "Nac.", new_name)

    # Padroniza alguns erros de digitação
    new_name = re.sub("Sustentavel", "Sustentável", new_name)
    new_name = re.sub("Ecologica", "Ecológica", new_name)
    new_name = re.sub("Iii", "III", new_name)

    # Cria o prefixo novo
    old_prefix = row.cat_uc
    new_prefix = preffixes[old_prefix]

    new_name = re.sub(old_prefix, new_prefix,  new_name)

    return pd.Series({
        "new_name": new_name
    })


##########################
### Funções principais ###
##########################

def featherize_sources():
    '''
    Processa os dados estáticos na pasta input para que
    fiquem em um formato comum. Salva em formato feather
    para facilitar as operações de read/write.
    '''

    ##############################################
    ### Cria estrutura de diretórios de output ###
    ##############################################

    def handle_directories(dir_):
        '''
        Cria o diretório especificado. Se ele já existir,
        deleta e cria um novo
        '''
        if os.path.exists(dir_):
            shutil.rmtree(dir_)
        os.makedirs(dir_)

    base_path = "../output"
    for item in ["csvs", "feathers", "imgs", "jsons"]:

        if item == "csvs":
            for subitem in ["land_info", "logs", "tilesets"]:
                new_dir = f"{base_path}/{item}/{subitem}"
                handle_directories(new_dir)

        if item == "feathers":
            for subitem in ["land_info", "sources", "tilesets"]:
                new_dir = f"{base_path}/{item}/{subitem}"
                handle_directories(new_dir)

        if item == "imgs":
            for subitem in ["tweets"]:
                new_dir = f"{base_path}/{item}/{subitem}"
                handle_directories(new_dir)

        if item == "jsons":
            for subitem in ["alerts", "land_info", "recipes", "tilesets"]:
                new_dir = f"{base_path}/{item}/{subitem}"
                handle_directories(new_dir)


    ###################################################
    ### Detalhes sobre diretório de entrada e saída ###
    ###################################################

    in_path = "../input/"
    out_path = "../output/feathers/sources/"

    #################     
    ### Satélites ###
    #################

    dtype = {"acq_time": str, "acq_date": str}

    archive = pd.read_csv(f"{in_path}FIRMS_VIIRS_2020/fire_archive.csv", dtype=dtype)
    archive.to_feather(f"{out_path}fire_archive.feather")

    nrt = pd.read_csv(f"{in_path}FIRMS_VIIRS_2020/fire_nrt.csv", dtype=dtype)
    nrt.to_feather(f"{out_path}fire_nrt.feather")

    # Limites da Amazônia Legal
    legal_amazon = gpd.read_file(f"{in_path}limites_amazonia_legal")
    legal_amazon.to_feather(f"{out_path}limites_amazonia_legal.feather")

    # Salva os limites para cortar outros bancos estáticos
    amz_outline = legal_amazon.unary_union 

    
    ###############
    ### Cidades ###
    ###############

    cities = gpd.read_file(f"{in_path}cidades_amazonia_legal/")

    columns = {
        "CD_MUN": "cod_cidade",
        "NM_MUN": "cidade",
        "SIGLA_UF": "estado",
        "CD_UF": "cod_estado",
        "geometry": "geometry"
    }

    cities = cities.rename(columns=columns)
    cities = cities.drop([item for item in cities.columns if item not in columns.values()], axis=1)

    # Remove duplicatas existentes
    cities = cities.drop_duplicates()

    cities.to_feather(f"{out_path}cidades_amazonia_legal.feather")


    ##############
    ### Biomas ###
    ##############

    biomes = gpd.read_file(f"{in_path}biomas_amazonia_legal")

    # Remove colunas
    biomes = biomes[["NOM_BIOMA", "ID1", "geometry"]]

    # Renomeia campos para nosso padrão
    biomes = biomes.rename(columns={"ID1":"cod_bioma", "NOM_BIOMA": "nome_bioma"})

    # Transforma campo de id em string
    biomes["cod_bioma"] = biomes["cod_bioma"].astype(int).astype(str)

    # Renomeia alguns biomas para facilitar compreensão
    biomes.loc[0, "nome_bioma"] = "Amazônia"
    biomes.loc[1, "nome_bioma"] = "Massa D'Água Costeira"
    biomes.loc[2, "nome_bioma"] = "Massa D'Água Continental"

    biomes.to_feather(f"{out_path}biomas_amazonia_legal.feather")

    
    ###############################
    ### Unidades de conservação ###
    ###############################

    con_units = gpd.read_file(f"{in_path}unidades_de_conservacao", encoding='utf8')

    columns = {
        "NOME_UC1": "nome_uc",
        "ID_WCMC2": "cod_uc",
        "CATEGORI3": "cat_uc",
        "geometry": "geometry"
    }

    con_units = con_units.rename(columns=columns)
    con_units = con_units.drop([item for item in con_units.columns if item not in columns.values()], axis=1)
    con_units.nome_uc = con_units.nome_uc.str.title()

    # Adiciona um código identificador para unidades de conservação que não tem um
    con_units["cod_uc"] = con_units["cod_uc"].apply(lambda x: uuid.uuid4().hex if x is None else x)

    # Adiciona campos customizados
    con_units["nome_uc_curto"] = con_units.apply(shorten_name, axis=1)
    con_units["biomas"] = con_units.apply(add_biomes, args=(biomes,), axis=1)
    con_units[["cidade", "estado"]] = con_units.apply(add_cities, args=(cities,), axis=1)

    con_units.to_feather(f"{out_path}unidades_de_conservacao.feather")

    ########################
    ### Terras indígenas ###
    ########################

    ind_lands = gpd.read_file(f"{in_path}terras_indigenas/")

    columns = {
        "terrai_cod": "cod_ti",
        "terrai_nom": "nome_ti",
        "fase_ti": "fase_ti",
        "etnia_nome": "nome_etnia",
        "geometry": "geometry",
        "municipio_": "cidade",
        "uf_sigla": "estado"
    }

    ind_lands = ind_lands.rename(columns=columns)
    ind_lands = ind_lands.drop([item for item in ind_lands.columns if item not in columns.values()], axis=1)
    ind_lands = ind_lands[ind_lands.geometry.intersects(amz_outline)].reset_index(drop=True)

    # Mantém apenas terras que já tenham sido efetivamente delimitadas
    ind_lands = ind_lands[~ind_lands.fase_ti.isin(('Declarada', 'Em Estudo'))]

    # Adiciona campos customizados
    ind_lands["biomes"] = ind_lands.apply(add_biomes, args=(biomes,), axis=1)

    ind_lands.to_feather(f"{out_path}terras_indigenas.feather")


def main():
	featherize_sources()

if __name__ == "__main__":
	main()