source /root/anaconda3/etc/profile.d/conda.sh &&
conda activate amazonia_sufocada &&
cd /home/amazonia-sufocada/code &&
python prepare.py &&
python process_data.py setup
