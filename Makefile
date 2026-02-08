git_user_name="kitahara-saneyuki"
git_user_email="edwarddwarf1999@gmail.com"

init:
	-sudo apt-get -y update
	-sudo apt-get -y upgrade
	git config --global user.name $(git_user_name)
	git config --global user.email $(git_user_email)
	sudo apt install ffmpeg

conda_create:
	conda env create -f environment.yml
	conda run --no-capture-output -n ForceAlignmentCutter mfa model download dictionary mandarin_china_mfa
	conda run --no-capture-output -n ForceAlignmentCutter mfa model download acoustic mandarin_mfa

conda_update:
	conda env update -f environment.yml --prune

conda_remove:
	conda remove -y -n ForceAlignmentCutter --all

run_api:
	./start_server.sh

run_api_dev:
	conda run --no-capture-output -n ForceAlignmentCutter uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

run_server:
	conda run --no-capture-output -n ForceAlignmentCutter gunicorn -k uvicorn.workers.UvicornWorker src.main:app

miniconda:
	curl https://repo.anaconda.com/pkgs/misc/gpgkeys/anaconda.asc | gpg --dearmor > conda.gpg
	sudo install -o root -g root -m 644 conda.gpg /usr/share/keyrings/conda-archive-keyring.gpg
	gpg --keyring /usr/share/keyrings/conda-archive-keyring.gpg --no-default-keyring --fingerprint 34161F5BF5EB1D4BFBBB8F0A8AEB4F8B29D82806
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/conda-archive-keyring.gpg] https://repo.anaconda.com/pkgs/misc/debrepo/conda stable main" | sudo tee -a /etc/apt/sources.list.d/conda.list
	sudo apt update
	sudo apt install conda
	rm conda.gpg
	echo "source /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

cuda:
	wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
	sudo dpkg -i cuda-keyring_1.1-1_all.deb
	sudo apt-get update
	sudo apt-get -y install cuda-toolkit-12-9
	rm cuda-keyring_1.1-1_all.deb
