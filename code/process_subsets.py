'''
Salva recortes específicos dos bancos de dados completos 
em formato GeoJSON. Eles seram usados para enviar ao Mapbox
recortes de dados menores, em que todos os pontos precisam
estar visíveis ao mesmo tempo para evitar dissonância na mensagem.
'''

import geopandas as gpd


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

################
### Execução ###
################

def main():
	
	# Lê os dados necessários
	points_24h = gpd.read_feather("../output/feathers/tilesets/24h.feather")

	# Salva os recortes
	inside_ucs = points_24h[~points_24h.cod_uc.isna()]

	inside_tis = points_24h[~points_24h.cod_ti.isna()]

	ti_most_fire_id = find_place_with_most_fire(points_24h, "cod_ti", position=1)
	ti_most_fire = points_24h[points_24h.cod_ti == ti_most_fire_id]

	uc_most_fire_id = find_place_with_most_fire(points_24h, "cod_uc", position=1)
	uc_most_fire = points_24h[points_24h.cod_uc == uc_most_fire_id]

	# Save it 
	inside_tis.to_file("../output/jsons/tilesets/24h_tis.json", driver="GeoJSON")
	inside_ucs.to_file("../output/jsons/tilesets/24h_ucs.json", driver="GeoJSON")
	uc_most_fire.to_file("../output/jsons/tilesets/24h_uc_most_fire.json", driver="GeoJSON")
	ti_most_fire.to_file("../output/jsons/tilesets/24h_ti_most_fire.json", driver="GeoJSON")


if __name__ == "__main__":
	main()