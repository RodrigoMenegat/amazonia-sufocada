'''
Prepara os bancos de dados brutos
para que o programa seja executado
de forma otimizada.
'''

import geopandas as gpd
import numpy as np
import pandas as pd
import os
import re
import shutil
import uuid
import warnings 

warnings.filterwarnings('ignore', message='.*initial implementation of Parquet.*') # Aviso de versão inicial do feather


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


def extract_name_without_category(row):
    '''
    Adiciona o nome da unidade de conservação sem
    o tipo de local. Exemplo: 'Parque Florestal Lorem Ipsum'
    vira apenas 'Lorem Ipsum'
    
    Parâmetros:
    
    > row: uma linha do dataframe, representando um território

    '''
    
    # Coloca tudo em lower para padronizar análise
    full_name = row.nome_uc.lower().strip()
    category = row.cat_uc.lower().strip()
    
    # Padroniza alguns erros de digitação
    full_name = re.sub("sustentavel", "sustentável", full_name).strip()
    category = re.sub("sustentavel", "sustentável", category).strip()
    
    full_name = re.sub("ecologica", "ecológica", full_name).strip()
    category = re.sub("ecologica", "ecológica", category).strip()
    
    full_name = re.sub("ecologico", "ecológico", full_name).strip()
    category = re.sub("ecologico", "ecológico", category).strip()
    
    full_name = re.sub("estacao", "estação", full_name).strip()
    category = re.sub("estacao", "estação", category).strip()
    
    full_name = re.sub("area", "área", full_name).strip()
    category = re.sub("area", "área", category).strip()
    
    full_name = re.sub("protecao", "proteção", full_name).strip()
    category = re.sub("protecao", "proteção", category).strip()

    # Remove a categoria
    name_no_cat = full_name.replace(category, "").strip()
    
    # Remove algumas exceções
    name_no_cat = name_no_cat.replace("natural municipal", "").strip()
    name_no_cat = name_no_cat.replace("área de relevante interesse ecológica", "").strip()
    
    
    # Remove sobras causadas pelo erro
    for substring in ["estadual", "nacional", "do ", "de ", "da ", "das ", "dos "]:
        if name_no_cat.startswith(substring):
            name_no_cat = re.sub(f'^\s?{substring}', '', name_no_cat)
            name_no_cat = name_no_cat.strip()
            
            
    # Title case
    name_no_cat = name_no_cat.title()
            
            
    # Coloca os prefixos de/do/da  e o conjuntivo e em minúscula
    name_no_cat = re.sub("Do ", "do ", name_no_cat)
    name_no_cat = re.sub("Da ", "da ", name_no_cat)
    name_no_cat = re.sub("De ", "de ", name_no_cat)
    name_no_cat = re.sub("Dos ", "dos ", name_no_cat)
    name_no_cat = re.sub("Das ", "das ", name_no_cat)
    name_no_cat = re.sub("Das ", "das ", name_no_cat)
    name_no_cat = re.sub(" E ", " e ", name_no_cat)
    
    # Padroniza alguns edge cases
    name_no_cat = re.sub("Sustentavel", "Sustentável", name_no_cat)
    name_no_cat = re.sub("Ecologica", "Ecológica", name_no_cat)
    name_no_cat = re.sub("Iii", "III", name_no_cat)
    
    return pd.Series({
        "name_no_cat": name_no_cat
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

    in_path = abspath(f"{PROJECT_ROOT}/input/")
    out_path = abspath(f"{PROJECT_ROOT}/output/feathers/sources/")

    #################     
    ### Satélites ###
    #################

    dtype = {"acq_time": str, "acq_date": str}

    archive = pd.read_csv(f"{in_path}/FIRMS_VIIRS_2020/fire_archive.csv", dtype=dtype)
    archive.to_feather(f"{out_path}/fire_archive.feather")

    nrt = pd.read_csv(f"{in_path}/FIRMS_VIIRS_2020/fire_nrt.csv", dtype=dtype)
    nrt.to_feather(f"{out_path}/fire_nrt.feather")

    # Limites da Amazônia Legal
    legal_amazon = gpd.read_file(f"{in_path}/limites_amazonia_legal")
    legal_amazon.to_feather(f"{out_path}/limites_amazonia_legal.feather")

    # Salva os limites para cortar outros bancos estáticos
    amz_outline = legal_amazon.unary_union 

    
    ###############
    ### Cidades ###
    ###############

    cities = gpd.read_file(f"{in_path}/cidades_amazonia_legal/")

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

    cities.to_feather(f"{out_path}/cidades_amazonia_legal.feather")


    ##############
    ### Biomas ###
    ##############

    biomes = gpd.read_file(f"{in_path}/biomas_amazonia_legal")

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

    # Remove biomas de Massa D'Água
    biomes = biomes[~biomes.nome_bioma.isin(["Massa D'Água Costeira", "Massa D'Água Continental"])]
    biomes = biomes.reset_index(drop=True)

    biomes.to_feather(f"{out_path}/biomas_amazonia_legal.feather")

    
    ###############################
    ### Unidades de conservação ###
    ###############################

    # Base de dados do MMA com todas as unidades de conservação do país
    # http://mapas.mma.gov.br/i3geo/datadownload.htm
    con_units = gpd.read_file(f"{in_path}/unidades_de_conservacao")

    # Mantém apenas o que está nos contornos da Amazônia Legal
    con_units = con_units[con_units.geometry.intersects(amz_outline)]

    # Corta para remover partes de UCs que estão fora da Amazônia Legal
    con_units["geometry"] = gpd.clip(con_units.geometry.buffer(0), amz_outline)

    columns = {
        "NOME_UC1": "nome_uc",
        "ID_UC0": "cod_uc",
        "CATEGORI3": "cat_uc",
        "geometry": "geometry",
        "ESFERA5": "esfera",
        "ANO_CRIA6": "ano_criacao"
    }

    # Renomeia e mantém colunas relevantes
    con_units = con_units.rename(columns=columns)
    con_units = con_units.drop([item for item in con_units.columns if item not in columns.values()], axis=1)
    
    # Coloca campos em titlecase
    con_units["nome_uc"] = con_units.nome_uc.str.title()
    con_units["esfera"] = con_units.esfera.str.title()


    # Adiciona um código identificador para unidades de conservação que não tem um
    con_units["cod_uc"] = con_units["cod_uc"].apply(lambda x: uuid.uuid4().hex if x is None else x)

    # Adiciona campos customizados
    con_units["nome_uc_curto"] = con_units.apply(shorten_name, axis=1)
    con_units["nome_uc_sem_cat"] = con_units.apply(extract_name_without_category, axis=1)
    con_units["biomas"] = con_units.apply(add_biomes, args=(biomes,), axis=1)
    con_units[["cidade", "estado"]] = con_units.apply(add_cities, args=(cities,), axis=1)


    # Reseta índice
    con_units = con_units.reset_index(drop=True)

    # Salva
    con_units.to_feather(f"{out_path}/unidades_de_conservacao.feather")

    ########################
    ### Terras indígenas ###
    ########################

    ind_lands = gpd.read_file(f"{in_path}/terras_indigenas/")

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

    # Mantém apenas terras que já tenham sido efetivamente delimitadas -- a não ser que elas estejam marcadas com 'restrição de uso'
    ind_lands = ind_lands[~(ind_lands.fase_ti.isin(('Declarada', 'Em Estudo'))) | (ind_lands.nome_ti.str.contains("restrição"))]

    # Adiciona campos customizados
    ind_lands["biomes"] = ind_lands.apply(add_biomes, args=(biomes,), axis=1)

    ind_lands["nome_etnia"] = ind_lands["nome_etnia"].str.replace(",", ", ")
    ind_lands["cidade"] = ind_lands["cidade"].str.replace(",", ", ")
    ind_lands["estado"] = ind_lands["estado"].str.replace(",", ", ")

    ind_lands.to_feather(f"{out_path}/terras_indigenas.feather")


    ########################################
    ### Quadrados da divisão da Amazônia ###
    ########################################

    def find_territories(row):
        '''
        Encontra todas as cidades, estados, biomas, TIs e UCs
        que fazem interseção com a área destacada. Essa função
        deve ser aplicada (df.apply) no dataframe que contém 
        toda a região da Amazônia Legal dividida em pequenos quadrados.
        
        Parâmetros:
        
        > row: uma linha do dataframe, representando um território
        '''
        
        box = row.geometry
        
        # Terras indígenas que fazem interseção
        ti_intersection = ind_lands[ind_lands.intersects(box)]

        nome_ti = ti_intersection["nome_ti"].tolist()
        nome_ti = ", ".join(nome_ti)

        cod_ti = ti_intersection["cod_ti"].astype(str).tolist()
        cod_ti = ", ".join(cod_ti)
        
        # Biomas que fazem interseção
        biome_intersection = biomes[biomes.intersects(box)]

        nome_bioma = biome_intersection["nome_bioma"].tolist()
        nome_bioma = ", ".join(nome_bioma)

        cod_bioma = biome_intersection["cod_bioma"].astype(str).tolist()
        cod_bioma = ", ".join(cod_bioma)
        
        # Unidades de conservação que fazem interseção
        uc_intersection = con_units[con_units.intersects(box)]

        nome_uc = uc_intersection["nome_uc"].tolist()
        nome_uc = ", ".join(nome_uc)

        cod_uc = uc_intersection["cod_uc"].astype(str).tolist()
        cod_uc = ", ".join(cod_uc)
        
        # Cidades e estados que fazem interseção
        city_intersection = cities[cities.intersects(box)]
        
        estado = city_intersection["estado"].unique().tolist()
        estado = ", ".join(estado)
        
        cidade = city_intersection["cidade"].tolist()
        cidade = ", ".join(cidade)
        
        return pd.Series({
            "cidade": cidade,
            "cod_bioma": cod_bioma,
            "cod_ti": cod_ti,
            "cod_uc": cod_uc,
            "estado": estado,
            "nome_bioma": nome_bioma,
            "nome_ti": nome_ti,
            "nome_uc": nome_uc
        })

    grid = gpd.read_file(f"{in_path}/amazonia_legal_grid_20km")

    # Torna o id inteiro
    grid["id"] = grid.id.astype(int).astype(str)

    # Transforma para o CRS correto (estava em conical equal area)
    grid = grid.to_crs(cities.crs)

    # Adiciona dados dos locais com interseção
    grid[["cidade", "cod_bioma", "cod_ti", "cod_uc", "estado", "nome_bioma", "nome_ti", "nome_uc"]] = grid.apply(find_territories, axis=1)

    # Preenche espaços vazios com NaNs
    grid = grid.applymap(lambda x: np.nan if x == "" else x)

    # O geopandas retira o CRS depois de uma função apply.
    # Precisamos adicionar novamente.
    # Transforma para o CRS correto (estava em conical equal area)
    grid.crs = cities.crs

    # Renomeia e remove colunas
    grid = grid.drop(["left", "top", "right", "bottom"], axis=1)
    grid = grid.rename(columns={"id": "cod_box"})

    print("Crs is", grid.crs)

    grid.to_feather(f"{out_path}/grid_20km.feather")

def main():
	featherize_sources()

if __name__ == "__main__":
	main()