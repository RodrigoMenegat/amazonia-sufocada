'''
Atualiza o conteúdo dos tuítes que devem ser publicados
com os dqeow mais recentes.
'''


import process_tweet_variables, process_tweet_images, process_tweet_content
def main():

	process_tweet_variables.main()
	process_tweet_images.main()
	process_tweet_content.main()

if __name__ == "__main__":
	main()