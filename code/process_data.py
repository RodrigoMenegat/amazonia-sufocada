import datetime
from distutils.dir_util import copy_tree
from functools import reduce
import geopandas as gpd
import os
import pandas as pd
from shapely.geometry import Point
import sys
import uuid
import warnings; warnings.filterwarnings('ignore', message='.*initial implementation of Parquet.*')

gpd.options.use_pygeos = True


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


########################
### Dados constantes ###
########################

BIOMES = BIOMES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/biomas_amazonia_legal.feather")
CITIES = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/cidades_amazonia_legal.feather")
CONSERVATION_UNITS =  gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/unidades_de_conservacao.feather")
GRID = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/grid_20km.feather")
INDIGENOUS_LAND = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/terras_indigenas.feather")
LEGAL_AMAZON = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/sources/limites_amazonia_legal.feather")

# Conversão de CRS
GRID.crs = LEGAL_AMAZON.crs
CONSERVATION_UNITS.crs = LEGAL_AMAZON.crs

###############
### Helpers ###
###############

def calculate_date_difference(df):
    '''
    Extrai a diferença em dias entre 
    a maior data do banco de dados
    e a data em que cada uma das entradas
    foi registrada.
    '''
    
    max_date = df.data.max()
    max_date = pd.to_datetime(max_date)
        
    df["date_diff"] = max_date - df["data"]
    df["date_diff"] = df["date_diff"].dt.days
    
    return df


def clip_over_amazon(gdf, rtree=True):
    '''
    Filtra os dados geográficos de um geodataframe
    para manter apenas aquelas que estão dentro
    da área da Amazônia Legal.
    '''

    print(">> Clipping over amazon")

    assert gdf.crs == LEGAL_AMAZON.crs

    gdf = gpd.sjoin(gdf, LEGAL_AMAZON, how='left', op='within').dropna(subset=['index_right'])

    gdf = gdf.dropna(subset=['index_right'])

    gdf = gdf.drop(["index_right", "SPRAREA", "SPRPERIMET", "SPRCLASSE"], axis=1)

    gdf = gdf.reset_index()
                
    return gdf


def df_to_gdf(df, lat_col="latitude", lon_col="longitude"):
    '''
    Transforma um dataframe normal em um geodataframe
    usando as colunas de latitude e longitude para isso
    '''

    print(">> Converting to GDF")

    points = df.apply(lambda row: Point (row[lon_col], row[lat_col]), axis=1)

    gdf = gpd.GeoDataFrame(df, geometry=points)

    # Padroniza o CRS para usar Sirgas 2000, como nas constantes
    gdf.crs = LEGAL_AMAZON.crs

    return gdf


def get_consecutive_days(gpby):
    '''
    Função que recebe um dataframe
    com fogos de fogo agrupado
    por terra indígena ou unidade
    de conservação e calcula a quantos
    dias consecutivos cada uma delas está
    queimando.
    '''

    def gen_prior_date(start_date):
        '''
        Uma função geradora que sempre reduz
        a data passada como argumento em
        um dia a cada chamada'''

        yield start_date

        while True:

            start_date -= datetime.timedelta(days=1)
            yield start_date
        
    def count_consec_dates(dates, start_date):
        '''
        Uma função que conta os dias consecutivos
        em que uma observação ocorre no DataFrame,
        de forma regresssiva, a partir de uma data
        especificada.
        '''
        
        dates = pd.to_datetime(dates.values).date

        dates_set = set(dates) # O(1) vs O(n) lookup times

        back_in_time = gen_prior_date(start_date)

        tally = 0

        while next(back_in_time) in dates_set:  # jump out on first miss
            tally += 1

        return tally

    start_date = pd.to_datetime("today").date()
        
    gpby = gpby.data

    gpby = gpby.apply(lambda x: count_consec_dates(x, start_date))
    
    gpby = gpby.to_frame().reset_index().rename(columns={"data":"dias_consecutivos"})

    return gpby


def fill_data(datapoints):
    '''
    Adiciona dados de localização aos arquivos
    que contém a localização dos focos de incêndio
    ''' 

    print(">> Making spatial joins")

    # Extrai dados sobre pertencimento a terra indígena,
    # área de preservação e cidade e município
    how = 'left'
    op = 'within'

    # Mantém apenas algumas colunas especificas dos bancos de dados estáticos
    indigen_cols = ["cod_ti", "nome_ti", "nome_etnia", "geometry"]
    conserv_cols = ["nome_uc", "cod_uc", "cat_uc", "ano_criacao", "esfera", "geometry"]
    grid_cols = ["cod_box", "geometry"]

    datapoints = gpd.sjoin(datapoints, CITIES, how=how, op=op).drop("index_right", axis=1)
    
    datapoints = gpd.sjoin(datapoints, INDIGENOUS_LAND[indigen_cols], how=how, op=op).drop("index_right", axis=1)
    
    datapoints = gpd.sjoin(datapoints, CONSERVATION_UNITS[conserv_cols], how=how, op=op).drop("index_right", axis=1)
    
    datapoints = gpd.sjoin(datapoints, BIOMES, how=how, op=op).drop("index_right", axis=1)

    datapoints = gpd.sjoin(datapoints, GRID[grid_cols], how=how, op=op).drop("index_right", axis=1)

    # Remove as entradas de fogo duplicadas. São poucas, causadas por problemas de sobreposição
    # no shapefile de unidades de conservação, que fazem um ponto estar contido em duas UCs ao mesmo tempo.
    # datapoints = datapoints.drop_duplicates(subset="uuid")

    # Renomeia as colunas 'left'
    datapoints = datapoints.rename(columns={
        "cidade_left": "cidade",
        "estado_left": "estado"
    })

    return datapoints


def save_csv(df, fname):
    '''
    Salva um dataframe como
    arquivo csv
    '''

    print(">> Saving as CSV")

    df.to_csv(fname, index=False)


def save_feather(df, fname):
    '''
    Salva um dataframe ou geodatrame
    como arquivo feather
    '''

    print(">> Saving as feather")

    if "data" in df.columns:
        df["data"] = df.data.astype(str)

    if "hora" in df.columns:
        df["hora"] = df.hora.astype(str)

    df.to_feather(fname)


def save_geojson(gdf, fname): 
    '''
    Salva um geodataframe como
    arquivo geojson para enviar
    ao Mapbox.
    '''

    print(">> Saving as GeoJSON")

    if "data" in gdf.columns:
        gdf["data"] = gdf.data.astype(str)


    if "hora" in gdf.columns:
        gdf["hora"] = gdf.hora.astype(str)

    gdf.to_file(fname, driver="GeoJSON")


def sanitize_duplicates(df, logfile):
    '''
    Remove duplicatas que decorrem de polígonos
    com sobreposição no momento de fazer o spatial
    join. Salva uma descrição dos itens afetados em um
    arquivo com um log de erros.
    '''

    print(">> Handling duplicates (due to spatial joins)")
    # Marca as segundas ocorrência
    dup_entries = df[df.duplicated(subset="uuid", keep='last')]

    if logfile == "24h" or logfile == "7d":

        # Salva as entradas duplicadas em um arquivo CSV para controle
        save_csv(dup_entries, f"../output/csvs/logs/{logfile}.csv")

    elif logfile == "bd_completo":

        # Adiciona novas entradas ao log de duplicados
        dup_entries.to_csv(f"../output/csvs/logs/bd_completo.csv", mode='a', header=False)

    # Mantém as primeiras ocorrências
    df = df.drop_duplicates(subset="uuid", keep="first").reset_index(drop=True)

    return df


def sanitize_api_duplicates(df, logfile):
    '''
    O funcionamento dessa função é semelhante ao da função acima,
    mas ela é chamada apenas quando as APIs de 24h e 7d da NASA são
    acessadas para atualizar o banco de dados completo. Como a API da NASA
    nem sempre retorna os dados mais atualizados (por motivos que ainda estou
    investigando), há algumas entradas de alguns horários que acabam duplicadas.
    Essa função previne esse comportamento.
    '''

    print(">> Handling duplicates (due to API behavior")
    dup_entries = df[df.duplicated(subset=["data", "hora", "latitude", "longitude"], keep='last')]

    if logfile == "bd_completo":
        dup_entries.to_csv(f"../output/csvs/logs/api_bd_completo.csv", mode='a', header=False)


    elif logfile == "24h" or logfile == "7d":
        save_csv(dup_entries, f"../output/csvs/logs/api_{logfile}.csv")


    # Mantém as primeiras ocorrências
    df = df.drop_duplicates(subset=["data", "hora", "latitude", "longitude"], keep="first").reset_index(drop=True)

    return df


def time_format(df): 
    '''
    Altera as colunas de data e hora dos arquivos da NASA
    para um formato padronizado.
    '''

    print(">> Formatting time")

    # Renomeia os campos de data e hora
    df = df.rename(columns={
        "acq_date": "data",
        "acq_time": "hora"
        })

    # Formato o horário para fazer sentido
    df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d")
    df["hora"] = pd.to_datetime(df["hora"], format="%H%M").dt.time
    df["dia"] =  df.data.dt.day
    df["mes"] =  df.data.dt.month
    df["ano"] =  df.data.dt.year

    return df


def uuid_fires(df):
    '''
    Função aplicada via apply em um dataframe
    que gera um item único para cada foco de fogo.
    Ela assume que os focos de fogos são únicos
    e que não há duplicatas.
    '''

    print(">> Adding fire uuids")

    df["uuid"] = [uuid.uuid4().hex for i in range(df.shape[0])]

    return df



##################
### Main tasks ###
##################

def build_original_database():
    '''
    Lê os arquivos baixados manualmente do site da NASA
    e salva o dataframe resultante. Retorna dois dataframes:
    um já sem duplicatas, para plotar os tilesets do total de fogo
    em toda a Amazônia, e outro com as duplicatas, que serão usadas para 
    computar o total de focos de fogo em cada território. 
    Essas duplicatas existem porque alguns territórios tem áreas que se sobrepõem,
    então é possível que um foco esteja em dois territórios do mesmo tipo ao mesmo
    tempo.
    '''

    # Lê arquivos com campos em um tipo específico
    archive = pd.read_feather("../output/feathers/sources/fire_archive.feather")
    nrt = pd.read_feather("../output/feathers/sources/fire_nrt.feather")

    # Reúne os dados de near real time com os dados de padrão científico
    df = pd.concat((archive, nrt))

    # Adiciona um id único para cada fogo
    df = uuid_fires(df)

    # Renomeia os campos de data e hora
    df = time_format(df)

    # Calcula a diferença de dias entre cada ponto e data de última atualização
    df = calculate_date_difference(df)

    # Transforma em gdf
    df = df_to_gdf(df)

    # Mantém apenas os pontos que estão sobre a Amazônia
    df = clip_over_amazon(df)

    # Reúne com dados de terras indígenas, cidades e unidades de conservação
    df = fill_data(df)

    # Mantém apenas as colunas relevantes
    df = df[[
                "uuid", "data", "hora", "dia", "mes", "ano", "date_diff", "latitude", "longitude",
                "cod_cidade", "cidade", "cod_estado", "estado",
                "cod_ti", "nome_ti", "nome_etnia",
                "cod_bioma", "nome_bioma",
                "bright_ti4", "bright_ti5", "frp",
                "nome_uc", "cod_uc", "geometry",
                "cod_box"
            ]]

    # Mantém um banco de dados com as duplicatas para calcular os tilesets de terra posteriormente
    df_dups = df.copy()

    df = sanitize_duplicates(df, "bd_completo")

    # Salva como CSV
    save_csv(df, f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo.csv")

    # Salva como Feather
    save_feather(df,  f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo.feather")
    save_feather(df_dups, f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo_com_duplicatas.feather")


    # Salva como GeoJSON
    save_geojson(df,  f"{PROJECT_ROOT}/output/jsons/tilesets/bd_completo.json")
    #save_geojson(df_dups, f"{PROJECT_ROOT}/output/jsons/tilesets/bd_completo_com_duplicatas.json")


    return df, df_dups


def fetch_recent_data():
    '''
    Acessa, salva e retorna dataframes com os
    dados da NASA para as últimas 24h e 7d
    '''

    # Dicionário para armazenar cada dataframe
    dfs = { }
    
    for time in ("24h", "7d"):

        # Lê os dados a partir da URL
        url = f"https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_South_America_{time}.csv"
        df = pd.read_csv(url, dtype={"acq_time": str})

        df = uuid_fires(df)

        # Renomeia os campos de data e hora
        df = time_format(df)

        # Calcula a diferença de dias entre cada ponto e data de última atualização
        df = calculate_date_difference(df)

        # Transforma em gdf
        df = df_to_gdf(df)

        # Mantém apenas os pontos que estão sobre a Amazônia
        df = clip_over_amazon(df)

        # Reúne com dados de terras indígenas, cidades e unidades de conservação
        df = fill_data(df)

        # Renomeia colunas para manter padrão
        df = df.rename(columns={
            "cidade_left": "cidade", 
            "estado_left": "estado"
        })

        # Mantém apenas as colunas relevantes
        df = df[[
                    "uuid", "data", "hora", "dia", "mes", "ano", "date_diff", "latitude", "longitude",
                    "cod_cidade", "cidade", "cod_estado", "estado",
                    "cod_ti", "nome_ti", "nome_etnia",
                    "cod_bioma", "nome_bioma",
                    "bright_ti4", "bright_ti5", "frp",
                    "nome_uc", "cod_uc", "geometry",
                    "cod_box"
                ]]

        # Lida com duplicatas

        # Mantém um banco de dados com as duplicatas para calcular os tilesets de terra posteriormente
        df_dups = df.copy()

        df = sanitize_duplicates(df, time)

        # Adiciona dados ao dicionário
        dfs[time] = df
        dfs[f"{time}_dups"] = df_dups

        # Salva como CSV
        save_csv(df, f"{PROJECT_ROOT}/output/csvs/tilesets/{time}.csv")

        # Salva como Feather
        save_feather(df, f"{PROJECT_ROOT}/output/feathers/tilesets/{time}.feather")
        save_feather(df_dups, f"{PROJECT_ROOT}/output/feathers/tilesets/{time}_com_duplicatas.feather")


        # Salva como GeoJSON
        save_geojson(df, f"{PROJECT_ROOT}/output/jsons/tilesets/{time}.json")

    # Retorna os dataframes para usar no resto dos processos
    return dfs["24h"], dfs["24h_dups"], dfs["7d"], dfs["7d_dups"]


def update_original_database(new_data, new_data_dups):

    '''
    Adiciona os dados das últimas 24h 
    ao banco completo de fogo NRT
    '''


    # Lê o banco de dados original em formato feather
    gdf = gpd.read_feather( f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo.feather")
    gdf_dups = gpd.read_feather( f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo_com_duplicatas.feather")


    for datapoints, updates, label in zip([gdf, gdf_dups], 
                                          [new_data, new_data_dups],
                                          ["clean", "duplicated"]):

        # Concatena com os novos dados
        datapoints = pd.concat((datapoints, updates))


        # Mantém apenas os dados do último ano
        year = datetime.datetime.now().year

        datapoints["datetime"] = pd.to_datetime(datapoints.data)
        datapoints = datapoints[datapoints.datetime.dt.year == year]
        datapoints = datapoints.drop("datetime", axis=1)

        # Reindexa
        datapoints = datapoints.reset_index(drop=True)

        # Salva como CSV
        if label == "clean":
            
            datapoints = sanitize_api_duplicates(datapoints, "bd_completo")

            save_csv(datapoints, f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo.csv")
            save_feather(datapoints,  f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo.feather")
            save_geojson(datapoints,  f"{PROJECT_ROOT}/output/jsons/tilesets/bd_completo.json")

            # Salva os dados sem duplicatas em uma variável
            gdf = datapoints.copy()

        elif label == "duplicated":
            
            #save_csv(datapoints, f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo_com_duplicatas.csv")
            save_feather(datapoints, f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo_com_duplicatas.feather")
            #save_geojson(datapoints, f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo_com_duplicatas.geojson")

            gdf_dups = datapoints.copy()

    return gdf, gdf_dups


# Atualiza os bancos de dados estáticos de terras indígenas e unidades de conservação
def update_land_datasets(df_24h, df_7d, full_db):
    
    # Por quais colunas vamos agregar?
    # Cada resultado vai ser salvo em um arquivo diferente
    columns = ["cod_ti", "cod_uc", "cod_bioma", "cod_box", "cod_cidade"]

    # Essas são as agregações temporais que faremos
    # e seus respectivos dataframes
    labels = ["db_completo", "7d", "24h"]
    dfs = [full_db, df_7d, df_24h]

    for column in columns:

        # Os dataframes de cada recorte temporal são salvos aqui e depois
        # passam por um merge para criar uma única tabela
        gpbys = [ ]
        
        for label, df in zip(labels, dfs):

            gpby = df.groupby(column)["geometry"].count().to_frame().reset_index().rename(columns={"geometry":f"focos_{label}"})

            gpbys.append(gpby)
            
        # Adiciona também um dado de focos de fogo consecutivo            
        gpby = full_db.groupby(column)

        gpby = get_consecutive_days(gpby)

        gpbys.append(gpby)

        # Reúne os dados do array usando reduce
        gpby = reduce(lambda a,b: pd.merge(a,b,on=column, how='left'), gpbys)
    
        # Reúne os dados com o banco de dados original e salva em vários formatos
        if column == "cod_ti":
            
            gpby = INDIGENOUS_LAND.merge(gpby, on=column, how="left")
            
            save_feather(gpby, f"{PROJECT_ROOT}/output/feathers/land_info/terras_indigenas.feather")
            save_csv(gpby, f"{PROJECT_ROOT}/output/csvs/land_info/terras_indigenas.csv")
            save_geojson(gpby, f"{PROJECT_ROOT}/output/jsons/land_info/terras_indigenas.json")
        
        elif column == "cod_uc":
            
            gpby = CONSERVATION_UNITS.merge(gpby, on=column, how="left")
            
            save_feather(gpby, f"{PROJECT_ROOT}/output/feathers/land_info/unidades_de_conservacao.feather")
            save_csv(gpby, f"{PROJECT_ROOT}/output/csvs/land_info/unidades_de_conservacao.csv")
            save_geojson(gpby, f"{PROJECT_ROOT}/output/jsons/land_info/unidades_de_conservacao.json")
            
        elif column == "cod_bioma":
            
            gpby = BIOMES.merge(gpby, on=column, how="left")

            save_feather(gpby, f"{PROJECT_ROOT}/output/feathers/land_info/biomas.feather")
            save_csv(gpby, f"{PROJECT_ROOT}/output/csvs/land_info/biomas.csv")
            save_geojson(gpby, f"{PROJECT_ROOT}/output/jsons/land_info/biomas.json")

        elif column == "cod_box":
            
            gpby = GRID.merge(gpby, on=column, how="left")

            save_feather(gpby, f"{PROJECT_ROOT}/output/feathers/land_info/grid_20km.feather")
            save_csv(gpby, f"{PROJECT_ROOT}/output/csvs/land_info/grid_20km.csv")
            save_geojson(gpby, f"{PROJECT_ROOT}/output/jsons/land_info/grid_20km.json")

        elif column == "cod_cidade":


            gpby = CITIES.merge(gpby, on=column, how="left")

            save_feather(gpby, f"{PROJECT_ROOT}/output/feathers/land_info/cidades.feather")
            save_csv(gpby, f"{PROJECT_ROOT}/output/csvs/land_info/cidades.csv")
            save_geojson(gpby, f"{PROJECT_ROOT}/output/jsons/land_info/cidades.json")


#################
### Execution ###
#################

# Gerar um arquivo JSON com informações para montar os alertas do dia
def main(argv):

    # Essa flag é usada para determinar se o banco de dados está sendo
    # atualizado pela primeira vez ou não.
    if len(argv) > 1:
        if argv[1] == "setup":
            setup = True
        else:
            print("Invalid command line argument. Can only be 'setup'")
            sys.exit(1)
    else:
        setup = False

    
    # Cria um backup para manter os dados sempre ativos
    print("> Backuping data")
    copy_tree(f"{PROJECT_ROOT}/output/", f"{PROJECT_ROOT}/output_bkp")
   
    # Atualiza o banco de dados, sabendo que uma enormidade de coisas podem dar errado (conexão, por exemplo)
    try:
        
        # Caso o banco de dados completo não exista, cria.
        db_path = f"{PROJECT_ROOT}/output/csvs/tilesets/bd_completo.csv"

        db_exists = os.path.isfile(db_path)
        if not db_exists:
            print("> Creating main database")
            full_db, full_db_dups = build_original_database()

        # Acessa e salva os arquivos recentes
        print("> Creating recent datasets")
        df_24h, df_24h_dups, df_7d, df_7d_dups = fetch_recent_data()

        # Adiciona os dados das últimas 24h ao banco de dados e salva
        if not setup:
            print("> Updating main database")
            full_db, full_db_dups = update_original_database(df_24h, df_24h_dups)

        # TO DO: filtra os dados de full_db para manter apenas entradas do ano corrente

        # Cria arquivos com os dados estáticos sobre terras indígenas e unidades de conservação
        print("> Creating land databases")
        update_land_datasets(df_24h_dups, df_7d_dups, full_db_dups)
        
    except Exception as e:
        
        print(f"Exception {e} detected. Restoring files to previous state")
        
        # Se quebrar, podemos colocar o backup de volta no diretório de dados
        copy_tree(f"{PROJECT_ROOT}/output_bkp", f"{PROJECT_ROOT}/output/")


if __name__ == "__main__":
    main(sys.argv)
