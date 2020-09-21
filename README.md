# Amazônia Sufocada

Esse repositório contém o código fonte para os [mapas](#) e o [robô](https://twitter.com/botqueimadas) do [InfoAmazonia](https://twitter.com/InfoAmazoniaBR) que monitoram queimadas na Amazônia Legal.

## Como funciona?

O fluxo de trabalho deste repositório acontece da seguinte maneira.

1. Pré-processamos dados de queimadas da NASA/FIRMS e dos limites territoriais das áreas protegidas da Amazônia Legal.
2. Diariamente, atualizamos estes dados com informações novas que capturamos dos bancos de dados da NASA/FIRMS.
3. Com os dados atualizados, criamos arquivos GeoJSON e MbTiles que são, então, enviados para o Mapbox.
4. A partir dos dados e dos mapas criados no Mapbox, geramos os fios que são publicados no Twitter.

Ele foi testado em sistemas Ubuntu 18.04 e 20.04. Não há suporte oficial para Mac e Windows.

## Como reproduzir?

Para reproduzir o projeto na íntegra, você vai precisar de contas e acesso às APIs do [Mapbox](https://www.mapbox.com/) e do [Twitter](https://developer.twitter.com/en). Aviso: o serviço do Mapbox não é gratuito e você pode receber cobranças se executar os passas abaixo inadvertidamente.

### Pré-requisitos

- Antes de tudo, clone esse repositório para o seu computador.

- Primeiro, precisamos dos dados brutos de queimadas e dos limites territoriais para processar. Os arquivos são grandes demais para o GitHub, portanto estão disponíveis [neste link](https://drive.google.com/file/d/1wqCokvhoHcVgJ7QnmS-kIypwgDFkIJBr/view?usp=sharing). Baixe-os e extraia no diretório-raiz deste repositório.

- Agora, precisamos instalar os pré-requisitos para rodar o código-fonte. Vamos lá, passo-a-passo:
	1. Instale o Anaconda3, que pode ser baixado [neste link](https://www.anaconda.com/products/individual).
	2. Crie um ambiente virtual no Anaconda executando o comando `conda env create --file environment.yml`
	3. Já dentro do ambiente recém criado, instale a interface de linha de comando do Mapbox. Instruções [aqui](https://github.com/mapbox/mapbox-cli-py).
	4. Instale o tippecanoe, também do Mapbox, [conforme as instruções](https://github.com/mapbox/tippecanoe).
	5. Modifique os arquivos `setup.sh` e `update_data.sh` com os caminhos para sua instalação local do Anaconda e para o diretório em que você clonou o projeto.
	6. No diretório code, crie arquivos chamados `twitter_credentials.py` e `mapbox_credentials.py` com as suas chaves de acesso às APIs dos respectivos serviços.
		- Para o Twitter, defina as seguintes variáveis com as respectivas chaves: `consumer_key`, `consumer_secret`, `bearer_token`, `access_token`, `access_token_secret`
		- Para o Mapbox, defina uma variável `token` com a sua credencial para uso das APIs.
	7. No arquivo `prepare_tilesets.py`, substitua a variável `USERNAME` com o nome de usuário de sua conta no Mapbox.

### Executando o código

- Para criar o banco de dados pela primeira vez, execute o comando `bash setup.sh`. Os dados do diretório `input` serão processados e você verá surgir um diretório `output`.

- Sempre que quiser atualizar os dados, executa `bash update_data.sh`. Sugerimos que essa tarefa seja realizada todos os dias no início da noite, já que a varredura dos satélites acontece no final da tarde. Para nosso robô, atualizamos os dados todos os dias as 19h de Brasília. Esse script vai executar as seguintes tarefas, em ordem:
	1. Acessar os bancos de dados na NASA/FIRMS, baixar os dados das últimas 24h e agregar no formato necessário para alimentar os mapas e o robô do Twitter.
	2. Processar os dados salvos no passo 1 para o formato MbTiles, usando o tippecanoe. Esses arquivos são, em seguida, usados para atualizar tilesets publicados no Mapbox Studio.
	3. A partir dos tilesets acima, usamos a API de imagens estáticas do Mapbox para salvar arquivos JPEG dos mapas relevantes.
	4. Finalmente, usamos os dados e as imagens para criar e publicar informações no Twitter.

## Sério que você só vai falar dos shell scripts?
Caso você queira entender melhor como o código funciona, sinta-se a vontade para explorar os arquivos do diretório `code`, que estão relativamente bem documentados. Grosso modo, a divisão é a seguinte:

1. `prepare.py` executa o pré-processamento dos dados do diretório `input`. Só deve ser executado uma vez.
2. `process_data.py` format e atualiza os bancos de dados gerados por `prepare.py`
3. `process_susbsets.py` salva arquivos a partir de recortes específicos dos bancos de dados citados acima.
4. `process_tilesets.py` usa o tippecanoe e a API do Mapbox para salvar arquivos .mbtiles e atualizar tilesets no Mapbox Studio.
5. `process_tweet_variables.py` salva arquivos JSON com variáveis úteis a partir dos bancos de dados atualizados anteriormente.
6. `process_tweet_images.py` usa a API de imagens estáticas do Mapbox para gerar imagens de mapas que serão publicadas no Twitter.
7. `process_tweet_content.py` salva um novo arquivo JSON com a estrutura dos fios no formato `[{"text": "blablabla", "img": "path/to/img"}]`
8. `tweet.py`, finalmente, lê os JSONs gerados por `process_tweet_content.py` e envia para o Twitter usando a API.

Os arquivos `update_datasets.py` e `update_tweet_data.py` são, simplesmente, wrappers para os processos acima. O primeiro agrupa os passos 2 até 4. O segundo, os passos 5 até 8. 
