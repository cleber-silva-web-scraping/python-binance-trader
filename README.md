## Bot for trader crypto currency in Binance

# Requirementes

    * Python 3.x
    * TA-Lib

# Install TA-Lib

- download from https://mrjbq7.github.io/ta-lib/install.html

```
$ cd /../ta-lib
$ ./configure --prefix=/usr
$ make
$ sudo make install
$ sudo apt upgrade
$ pip install ta-lib or pip install TA-Lib
```

# Setup enviroment

```
$ python3 -m venv env
$ source ./env/bin/activate
$ pip install --upgrade pip
$ pip install -r requirements

```

# Config

- copy file `config-example.py` to `config.py`
- update `config.py` with your data

# Running

```
python app.py
```

# Running in docker

docker build -t cryptob:1 .

docker build -t cryptoapp -f DockerfileApp

docker run -itd cryptoapp

# More

I still working .....
