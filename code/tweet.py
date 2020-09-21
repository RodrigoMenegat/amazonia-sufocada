'''
Esse script usa o Tweepy e os dados e imagens que já processamos
para fazer uma thread no Twitter.
'''

import json
import time
import tweepy
import twitter_credentials
import sys

# Inicia uma sessão
AUTH = tweepy.OAuthHandler(twitter_credentials.consumer_key, twitter_credentials.consumer_secret)
AUTH.set_access_token(twitter_credentials.access_token, twitter_credentials.access_token_secret)

API = tweepy.API(AUTH)


###############
### Helpers ###
###############

def post_thread(tweets):
	'''
	Publica uma série de tweets, um em resposta ao
	outro, criando um fio.

	Parâmetros:

	> tweets: um array json-like com os
	tweets que devem ser publicados, em ordem.
	'''

	# De início, não estamos respondendo ninguém.
	reply_to = None

	for tweet in tweets:

		time.sleep(5)


		# Se o tuíte contém media, prepara o upload usando o endpoint adequado
		media = tweet["img"]
		if tweet["img"]:
			img = API.media_upload(media)
			img = [img.media_id]
		else:
			img = []

		# Publica o tuíte, responendo ao anterior (ou a None, caso seja o primeiro da série)
		status = API.update_status(tweet["text"], 
			in_reply_to_status_id=reply_to,
			 media_ids=img,
			 place_id="Amazônia Legal")

		# O próximo tweet deve responder este aqui
		reply_to = status.id


################
### Execução ###
################

def main(argv):

	if len(argv) != 2:
		print("Usage: python tweet.py path/to/json-with-tweets.json")
		sys.exit(1)


	# Lê o arquivo JSON contendo os tweets que devem ser publicados agora
	with open(argv[1]) as f:
		tweets = json.load(f)

	post_thread(tweets)

if __name__ == "__main__":
	main(sys.argv)