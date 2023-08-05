Welcome to ValveEXE's documentation!
====================================

.. License
.. image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: https://github.com/pySourceSDK/ValveEXE/blob/master/LICENSE.txt

.. Python versions
.. image:: https://img.shields.io/pypi/pyversions/valveexe.svg
   :target: https://pypi.python.org/pypi/valveexe/

.. Pypi versions
.. image:: https://badge.fury.io/py/valveexe.svg
   :target: https://pypi.python.org/pypi/valveexe/

ValveEXE is a python library to interact with Source Engine game clients. It provides ways to input console commands as well as ways to read console output. It is primarily intended to assist in creating modding build tools that involves the game client but what you make out of it is up to you.

.. Note:: This library is completely VAC safe. It does not interact with memory in any way that might be frowned upon by anti-cheat. Console commands are issued either via RCON or by launch parameters. The console output is read from the disk, in log files provided by the game.

.. warning:: ValveEXE does not currently support Left 4 Dead 2 due to some engine differences.


User Guides
-----------

Get yourself up and running quickly.

.. toctree::
   :maxdepth: 2

   quickstart

API
---

.. toctree::
   :maxdepth: 2

   api_ref

Contributing
------------

Few things to know before diving in the code.

.. toctree::
   :maxdepth: 2

   contributing
