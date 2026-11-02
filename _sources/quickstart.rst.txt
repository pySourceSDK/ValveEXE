Quickstart
==========

Get yourself up and running quickly.

Installation
------------

PyPI
~~~~
ValveEXE is available on the Python Package Index. This makes installing it with pip as easy as:

.. code-block:: bash

   pip3 install valveexe

Git
~~~

If you want the latest code or even feel like contributing, the code is available on GitHub.

You can easily clone the code with git:

.. code-block:: bash

   git clone git://github.com/pySourceSDK/ValveEXE.git

and install it from the repo directory with:

.. code-block:: bash

   python3 setup.py install

Usage
-----

Here's a few example usage of ValveEXE

Sending a command to the client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsing can be done by creating an instance of Exe with a path.

.. code-block:: python

   > from valveexe import ValveExe
   > tf2 = ValveExe('C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\hl2.exe', # exe path
                    'C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf') # mod dir

   > tf2.launch('-windowed', '-novid', '+map', 'ctf_2fort')
   > tf2.run('nav_generate') # will run the command "nav_generate"
   > tf2.logger.log_until("\.nav' saved\.") # will wait until the log matches the provided regex string
   > tf2.quit() # exits the game


Sending multiple commands to the client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you wish to perform multiple commands without ValveEXE reconnecting to RCON each time, The previous example could be reimplemented using the 'with' keyword.

.. code-block:: python

   > from valveexe import ValveExe
   > tf2 = ValveExe('C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\hl2.exe', # exe path
                    'C:\Program Files (x86)\Steam\steamapps\common\Team Fortress 2\tf') # mod dir

   > tf2.launch('-windowed', '-novid')
   > with tf2 as console:
   >   console.run('map', 'ctf_2fort') # Will load the map
   >   tf2.logger.log_until('Redownloading all lightmaps') # Map is done loading
   >   console.run('nav_generate') # will run the command "nav_generate"
   >   tf2.logger.log_until("\.nav' saved\.") # nav is done generating
   >   console.run('disconnect') # exits the map
   > tf2.quit() # exits the game
