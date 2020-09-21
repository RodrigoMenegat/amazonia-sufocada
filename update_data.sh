source /root/anaconda3/etc/profile.d/conda.sh &&
conda activate amazonia_sufocada &&
cd /home/amazonia-sufocada/code/ &&
python update_datasets.py &&
python update_tweet_data.py &&
python tweet.py "../output/jsons/tweets/ucs_24h.json" &&
sleep 60m &&
python tweet.py "../output/jsons/tweets/tis_24h.json"
