# MIND: Python Optimization Software for Process Design Membranes
## Requirements

- Python3.10

## Installation
```bash
git clone https://github.com/anaslqdkd/mind.git
cd mind
chmod +x setup.sh
./setup.sh
```
### 2. Install Ipopt Using coinbrew (optional)

Ipopt is required for optimization tasks. Install it as follows:

```bash
git clone https://github.com/coin-or/coinbrew.git
cd coinbrew
git config --global url."https://github.com/".insteadOf git@github.com:
./coinbrew fetch Ipopt ThirdParty-ASL ThirdParty-Mumps --no-prompt
./coinbrew build Ipopt --prefix=$HOME/ipopt-install --no-prompt
./coinbrew install Ipopt
```

#### Update Your Shell Configuration

Add these lines to your `.bashrc` or `.zshrc` to ensure your environment can find Ipopt:

```bash
export PATH="$HOME/ipopt-install/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/ipopt-install/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$HOME/ipopt-install/lib/pkgconfig:$PKG_CONFIG_PATH"
```

Apply the changes:

```bash
source ~/.bashrc  # or source ~/.zshrc
```
#### Verify Ipopt Installation

```bash
ipopt --version
```

## 3. Running the Project
```bash
source env/bin/activate
python3 main.py
```
