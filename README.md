[![GPLv3 license](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/pySourceSDK/ValveEXE/blob/master/LICENSE.txt)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/valveexe.svg)](https://pypi.python.org/pypi/valveexe/)
[![PyPI version fury.io](https://badge.fury.io/py/valveexe.svg)](https://pypi.python.org/pypi/valveexe/)

# ValveEXE

ValveEXE is a python library to interact with Source Engine game clients. It provides ways to input console
commands as well as ways to read console output. It is primarily intended to assist in creating modding tools.

Full documentation: https://pysourcesdk.github.io/ValveEXE/

> This library is completely VAC safe. It does not interact with memory in any way that might be
> frowned upon by anti-cheat. Console commands are issued either via RCON or by launch parameters.
> The console output is read from the disk, in log files provided by the game.

## Installation

### PyPI

ValveEXE is available on the Python Package Index. This makes installing it with pip as easy as:

```bash
pip3 install valveexe
```

### Git

If you want the latest code or even feel like contributing, the code is available on GitHub.

You can easily clone the code with git:

```bash
git clone git@github.com:pySourceSDK/ValveEXE.git
```

and install it with:

```bash
python3 setup.py install
```
