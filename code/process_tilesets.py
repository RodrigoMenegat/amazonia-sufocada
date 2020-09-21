'''
Usa o Mapbox Tilling Service (MTS)
para criar layers customizáveis
via Mapbox Studio.

A maior parte da funcionalidade desse script
é simplesmente um wrappper para o utilitário
de linha de comando 'Tilesets CLI', desenvol-
vido pela equipe do próprio Mapbox. Veja mais:

https://github.com/mapbox/tilesets-cli/
'''

import mapbox_credentials
import json
import os
import subprocess
import time


abspath = os.path.abspath
dirname = os.path.dirname

###############
### Globals ###
###############

PROJECT_ROOT = dirname(abspath(dirname(__file__)))

CONDA_PREFIX = os.environ["CONDA_PREFIX"] # path to the environment-specific utilities

TOKEN = mapbox_credentials.token

USERNAME = "infoamazonia"

SOURCES = [
	("amzsufocada-24h", f"{PROJECT_ROOT}/output/jsons/tilesets/24h.json"),
	("amzsufocada-24h-tis", f"{PROJECT_ROOT}/output/jsons/tilesets/24h_tis.json"),
	("amzsufocada-24h-ucs", f"{PROJECT_ROOT}/output/jsons/tilesets/24h_ucs.json"),
	("amzsufocada-24h-ti-most-fire", f"{PROJECT_ROOT}/output/jsons/tilesets/24h_ti_most_fire.json" ),
	("amzsufocada-24h-ucs-most-fire", f"{PROJECT_ROOT}/output/jsons/tilesets/24h_uc_most_fire.json"),
	("amzsufocada-7d", f"{PROJECT_ROOT}/output/jsons/tilesets/7d.json"),
	("amzsufocada-bd-completo", f"{PROJECT_ROOT}/output/jsons/tilesets/bd_completo.json"),
    ("amzsufocada-terras-indigenas", f"{PROJECT_ROOT}/output/jsons/land_info/terras_indigenas.json"),
    ("amzsufocada-unidades-conserv", f"{PROJECT_ROOT}/output/jsons/land_info/unidades_de_conservacao.json"),
    ("amzsufocada-biomas", f"{PROJECT_ROOT}/output/jsons/land_info/biomas.json"),
]


###############
### Helpers ###
###############

def tippecanoe(source):
	'''
	Passa os arquivos de GeoJSON selecionados para o
	tippecanoe através da linha de comando. O output
	é salvo como um arquivo .mbtiles no caminho de destino

	Parâmetros:	


	> source: uma tupla no formato (nome-camada, caminho). Exemplo: ("amzsufocada-24h", "../output/jsons/tilesets/24h.json")
	'''

	# Se o output já existir, passa --force. Se não, não

	if source[0] in ["amzsufocada-24h-tis", "amzsufocada-24h-ucs", "amzsufocada-24h-ti-most-fire", "amzsufocada-24h-uc-most-fire"]:
		command = f"tippecanoe -zg --force -o {PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles -l {source[0]} {source[1]} -b0 -r1 --drop-densest-as-needed"


	else:
		command = f"tippecanoe -zg --force -o {PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles -l {source[0]} {source[1]} -b0 --drop-densest-as-needed"


	print(command)
	subprocess.run(command, shell=True)


def upload(source):
	'''
	Usa a API de uploads do InfoAmazônia para
	enviar os arquivos .mbtiles recém criados
	para o Mapbox Studio.

	Parâmetros:

	> source: o caminho do arquivo que deve ser enviado

	> tileset: o tileset que deve ser criado ou atualizado
	'''

	command = [f"{CONDA_PREFIX}/bin/mapbox", "upload", f"{USERNAME}.{source[0]}", f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles"]

	print(command)
	subprocess.run(command, env={"MAPBOX_ACCESS_TOKEN": TOKEN})





################
### Execução ###
################

def main():

	directory = "../output/mbtiles/tilesets"
	if not os.path.exists(directory):
		os.makedirs(directory)

	for source in SOURCES:
		tippecanoe(source)
		upload(source)
	

if __name__ == "__main__":
	main()

