'''
Usa as apis do Mapbox e o Tippecanoe para
criar styles customizáveis no Mapbox Studio.

A maior parte da funcionalidade desse script
é simplesmente um wrappper para o utilitário
de linha de comando 'Tilesets CLI' e do Tippecanoe, 
desenvolvidos pela equipe do próprio Mapbox. 

Veja mais:

https://github.com/mapbox/tilesets-cli/
https://github.com/RodrigoMenegat/amazonia-sufocada
'''

import mapbox_credentials
import json
import os
import shutil
import subprocess
import time


abspath = os.path.abspath
dirname = os.path.dirname

###############
### Globals ###
###############

PROJECT_ROOT = dirname(abspath(dirname(__file__)))

CONDA_PREFIX = os.environ["CONDA_PREFIX"] # path to the environment-specific utilities

TIPPECANOE_PATH = abspath("/home/tippecanoe/tippecanoe")

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
        ("amzsufocada-grid-20km", f"{PROJECT_ROOT}/output/jsons/land_info/grid_20km.json"),
        ("amzsufocada-7d-grid-1", f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_1.json"),
        ("amzsufocada-7d-grid-2", f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_2.json"),
        ("amzsufocada-7d-grid-3", f"{PROJECT_ROOT}/output/jsons/tilesets/7d_grid_3.json")
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

        # O grid de 20km não sera passado ao tippecanoe. Usaremos o JSON puro.
        if source[0] == "amzsufocada-grid-20km":
            return

        # Se o output já existir, passa --force. Se não, não
        if source[0] in ["amzsufocada-24h-tis", "amzsufocada-24h-ucs", 
                         "amzsufocada-24h-ti-most-fire", "amzsufocada-24h-ucs-most-fire",
                         "amzsufocada-7d-grid-1", "amzsufocada-7d-grid-2", "amzsufocada-7d-grid-3",
                        ]:
                # Due to a weird bug, combining the --force and -r1 flags creates mbtiles files with zombie points. We will manually rename/remove the files
                # to avoid this.
                command = f"{TIPPECANOE_PATH} -zg -o {PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}_new.mbtiles -l {source[0]} {source[1]} -b0 -r1  --drop-densest-as-needed"

                print(command)
                result = subprocess.run(command, shell=True, capture_output=True, check=True)
                print(result.stdout)
                print(result.stderr)

                # Remove the old mbtiles
                if os.path.isfile(f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles"):
                    os.remove(f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles")

                # Rename the new one
                os.rename(f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}_new.mbtiles", f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles")

        elif source[0] in ["amzsufocada-terras-indigenas", "amzsufocada-unidades-conserv", "amzsufocada-biomas"]:
                # Tippecanoe needs a buffer to avoid lines in the tile boundaries of polygons
                command = f"{TIPPECANOE_PATH} -zg --force -o {PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles -l {source[0]} {source[1]}  --drop-densest-as-needed"

                print(command)
                result = subprocess.run(command, shell=True, capture_output=True, check=True)
                print(result.stdout)
                print(result.stderr)


        else:
                command = f"{TIPPECANOE_PATH} -zg --force -o {PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles -l {source[0]} {source[1]} -b0 --drop-densest-as-needed"


                print(command)
                result = subprocess.run(command, shell=True, capture_output=True, check=True)
                print(result.stdout)
                print(result.stderr)


def upload(source):
        '''
        Usa a API de uploads do InfoAmazônia para
        enviar os arquivos .mbtiles recém criados
        para o Mapbox Studio.

        Parâmetros:

        > source: o caminho do arquivo que deve ser enviado

        > tileset: o tileset que deve ser criado ou atualizado
        '''

        # O grid de 20km é em formato JSON. Os demais, mbtiles
        if source[0] == "amzsufocada-grid-20km":
            command =  [f"{CONDA_PREFIX}/bin/mapbox", "upload", f"{USERNAME}.{source[0]}", f"{PROJECT_ROOT}/output/jsons/land_info/grid_20km.json"]

        else:
            command = [f"{CONDA_PREFIX}/bin/mapbox", "upload", f"{USERNAME}.{source[0]}", f"{PROJECT_ROOT}/output/mbtiles/tilesets/{source[0]}.mbtiles"]

        print(command)
        result = subprocess.run(command, env={"MAPBOX_ACCESS_TOKEN": TOKEN}, capture_output=True, check=True)
        print(result.stdout)
        print(result.stderr)



################
### Execução ###
################

def main():

        directory = f"{PROJECT_ROOT}/output/mbtiles/tilesets"
        if not os.path.exists(directory):
                os.makedirs(directory)

        for source in SOURCES:
                tippecanoe(source)
                upload(source)


if __name__ == "__main__":
        main()
