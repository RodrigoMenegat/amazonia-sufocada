'''
Atualiza apenas o banco de dados de
terras, sem alterar os dados de focos
de fogo salvos anteriormente
'''

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

from process_data import *
import geopandas as gpd

def main():
	
	df_24h = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/24h.feather")
	df_7d = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/7d.feather")
	full_db = gpd.read_feather(f"{PROJECT_ROOT}/output/feathers/tilesets/bd_completo.feather")

	# Cria arquivos com os dados estáticos sobre terras indígenas e unidades de conservação
	print("> Creating land databases")
	update_land_datasets(df_24h, df_7d, full_db)


if __name__ == "__main__":
	main()