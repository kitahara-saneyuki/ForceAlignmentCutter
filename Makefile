git_user_name="kitahara-saneyuki"
git_user_email="edwarddwarf1999@gmail.com"

init_debian:
	-sudo apt-get -y update
	-sudo apt-get -y upgrade
	git config --global user.name $(git_user_name)
	git config --global user.email $(git_user_email)

init_mac:
	brew update
	brew upgrade
	git config --global user.name $(git_user_name)
	git config --global user.email $(git_user_email)

conda_create:
	conda env create -f environment.yml

conda_update:
	conda env update -f environment.yml --prune

conda_remove:
	conda remove -y -n ForceAlignmentCutter --all

run_server:
	conda run --no-capture-output -n ForceAlignmentCutter gunicorn -k uvicorn.workers.UvicornWorker src.main:app

miniconda_debian:
	curl https://repo.anaconda.com/pkgs/misc/gpgkeys/anaconda.asc | gpg --dearmor > conda.gpg
	sudo install -o root -g root -m 644 conda.gpg /usr/share/keyrings/conda-archive-keyring.gpg
	gpg --keyring /usr/share/keyrings/conda-archive-keyring.gpg --no-default-keyring --fingerprint 34161F5BF5EB1D4BFBBB8F0A8AEB4F8B29D82806
	echo "deb [arch=amd64 signed-by=/usr/share/keyrings/conda-archive-keyring.gpg] https://repo.anaconda.com/pkgs/misc/debrepo/conda stable main" | sudo tee -a /etc/apt/sources.list.d/conda.list
	sudo apt update
	sudo apt install conda
	rm conda.gpg
	echo "source /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

miniconda_mac:
	echo "export http_proxy=http://127.0.0.1:7890" >> ~/.zprofile
	echo "export https_proxy=http://127.0.0.1:7890" >> ~/.zprofile
	source ~/.zprofile
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	echo "eval '$(/usr/local/bin/brew shellenv)'" >> ~/.zprofile
	source ~/.zprofile
	brew install --cask anaconda
	echo "export PATH='/usr/local/anaconda3/bin:$PATH'" >> ~/.zprofile
	sudo chmod -R 775 ~/.conda/

cuda:
	wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
	sudo dpkg -i cuda-keyring_1.1-1_all.deb
	sudo apt-get update
	sudo apt-get -y install cuda-toolkit-12-9
	rm cuda-keyring_1.1-1_all.deb
