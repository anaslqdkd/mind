# mind

## Installation

### 0. Clone the projet

```bash
git clone https://github.com/anaslqdkd/mind.git
```

### 1. System Dependencies

```bash
sudo apt update
sudo apt install build-essential gfortran pkg-config wget git python3.11 python3.11-dev python3.11-venv libblas-dev liblapack-dev
```

### 2. Install Ipopt with coinbrew

```bash
git clone https://github.com/coin-or/coinbrew.git
cd coinbrew
git config --global url."https://github.com/".insteadOf git@github.com:
./coinbrew fetch Ipopt ThirdParty-ASL ThirdParty-Mumps --no-prompt
./coinbrew build Ipopt --prefix=$HOME/ipopt-install --no-prompt
./coinbrew install Ipopt
```

Add the following to your `.bashrc` or `.zshrc`:

```bash
export PATH="$HOME/ipopt-install/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/ipopt-install/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$HOME/ipopt-install/lib/pkgconfig:$PKG_CONFIG_PATH"
source ~/.bashrc
```

Check Ipopt installation:

```bash
ipopt --version
```

### 3. Set up the Python environment

```bash
cd mind/mind
python3.11 -m venv env
source env/bin/activate
pip install -r requirements.txt
deactivate
chmod u+x test/command.sh
```
```
