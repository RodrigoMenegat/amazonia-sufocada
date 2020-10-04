'''
Salva recortes específicos dos bancos de dados completos 
em formato GeoJSON. Eles serão usados para enviar ao Mapbox
recortes de dados menores, em que todos os pontos precisam
estar visíveis ao mesmo tempo para evitar dissonância na mensagem.
'''

import geopandas as gpd
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

def find_place_with_most_fire(df, code, position=1):
    '''
    Encontra qual é o território com mais fogo
    em um dataframe. Retorna o id do território.
    
    Parâmetros:
    
    df -> Um dataframe com focos de queimada em determinado recorte temporal.
    
    code -> O código do tipo de terra em que iremos contar os focos. Pode ser 'cod_uc', 'cod_ti' ou 'cod_bioma'.
    Caso nenhum tipo de terra seja especificado, conta todos os focos.
    
    position -> Com esse parâmetro, é possível selecionar outros locais que não o primeiro colocado em número
    de focos. Por exemplo, se especificarmos o valor 2, a função vai retornar dados sobre o segundo território
    em situação mais crítica.
    '''
    
    # Determina nomes de coluna de acordo com o tipo de terra
    
    
    df = df[~df[code].isna()]
    
    id_ = df.groupby(code).uuid.count().sort_values(ascending=False).reset_index().loc[position-1, code]
    
    return id_


def find_grid_with_most_fire(grid_df, time, position=1):
    '''
    Encontra qual é o retângulo do grid com mais fogo
    em um determinado recorte temporal. Retorna seu id.
    
    Parâmetros:

    grid_df -> Dataframe que representa o grid de quadrados de 20km quadrados já com informações sobre fogo.

    time -> String que representa o intervalo de agregação. Pode ser '24h', '7d' ou 'full_db'

    position -> Com esse parâmetro, é possível selecionar outros locais que não o primeiro colocado em número
    de focos. Por exemplo, se especificarmos o valor 2, a função vai retornar dados sobre o segundo território
    em situação mais crítica.
    '''

    # Seleciona o grid com mais fogo
    grid_most_fire = grid_df.sort_values(by=f"focos_{time}", ascending = False).reset_index().loc[position-1]
    
    # Pega as informações básicas
    id_ = grid_most_fire["cod_box"]

    return id_


################
### Execução ###
################

def main():
	
	# Lê os dados necessários
	points_24h = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/24h.feather")

	# Salva os recortes com dados de 24h
	inside_ucs = points_24h[~points_24h.cod_uc.isna()]
	inside_tis = points_24h[~points_24h.cod_ti.isna()]

	ti_most_fire_id = find_place_with_most_fire(points_24h, "cod_ti", position=1)
	ti_most_fire = points_24h[points_24h.cod_ti == ti_most_fire_id]

	uc_most_fire_id = find_place_with_most_fire(points_24h, "cod_uc", position=1)
	uc_most_fire = points_24h[points_24h.cod_uc == uc_most_fire_id]

	# Salva os recortes com dados de 7d
	grid = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/land_info/grid_20km.feather")
	points_7d = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/7d.feather")

	grid_most_fire_1_id = find_grid_with_most_fire(grid, time="7d", position=1)
	grid_most_fire_1 = points_7d[points_7d.cod_box == grid_most_fire_1_id]

	grid_most_fire_2_id = find_grid_with_most_fire(grid, time="7d", position=2)
	grid_most_fire_2 = points_7d[points_7d.cod_box == grid_most_fire_2_id]

	grid_most_fire_3_id = find_grid_with_most_fire(grid, time="7d", position=3)
	grid_most_fire_3 = points_7d[points_7d.cod_box == grid_most_fire_3_id]

	# Salva os recortes de 24h
	inside_tis.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/24h_tis.json", driver="GeoJSON")
	inside_ucs.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/24h_ucs.json", driver="GeoJSON")
	uc_most_fire.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/24h_uc_most_fire.json", driver="GeoJSON")
	ti_most_fire.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/24h_ti_most_fire.json", driver="GeoJSON")


	# Salva os recortes de 7d
	grid_most_fire_1.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_1.json", driver="GeoJSON")
	grid_most_fire_2.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_2.json", driver="GeoJSON")
	grid_most_fire_3.to_file(f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_3.json", driver="GeoJSON")



if __name__ == "__main__":
	main()
