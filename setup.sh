source /root/anaconda3/etc/profile.d/conda.sh &&
conda activate amazonia_sufocada &&
cd /home/amazonia-sufocada/code &&
python prepare.py &&
python process_data.py setup &&
python process_subsets.py &&
python process_tilesets.py &&
python process_tweet_variables.py &&
python process_tweet_images.py &&
python process_tweet_content.py &&
cd ..
cp -r -f -T /home/amazonia-sufocada/output /home/amazonia-sufocada-static-output

