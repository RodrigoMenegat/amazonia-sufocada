'''
1. Atualiza os três arquivos do banco de dados:
- O banco de dados completo
- As últimas 48h
- As últimas 24h

2. Sobe os tilesets processados para o Mapbox Studio
'''

import process_data, process_subsets, process_tilesets

def main():

	process_data.main([])
	process_subsets.main()
	process_tilesets.main()


if __name__ == "__main__":
	main()