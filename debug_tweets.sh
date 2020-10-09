source /root/anaconda3/etc/profile.d/conda.sh &&
conda activate amazonia_sufocada &&
cd /home/amazonia-sufocada/code/ &&
# python process_subsets.py &&
# python process_tilesets.py &&
python update_tweet_data.py &&
python tweet.py "/home/amazonia-sufocada/output/jsons/tweets/ucs_24h.json" &&
sleep 30m &&
python tweet.py "/home/amazonia-sufocada/output/jsons/tweets/tis_24h.json"
