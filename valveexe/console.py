import os
import time
import subprocess

from rcon import Client


class VConsole():
    '''An abstract definition for the different types of console
    implementations. All implementation are intended to receive
    commands via the :any:`run` function
    '''

    def run(self, command, *params):
        '''Runs a specified command with it's parameters

        :param command: A Source Engine `console command \
        <https://developer.valvesoftware.com/wiki/Console_Command_List>`_.
        :type command: str
        :param \*params: The values to be included with the command.
        :type \*params: str
        '''
        pass

    def __enter__(self):
        pass

    def __exit__(self):
        pass


class RconConsole(VConsole):
    '''
    Issues commands by leveraging RCON.
    This is supported by most multiplayer games.
    '''

    def __init__(self, ip, port, passwd):
        '''
        :param ip: The IP the game client is listening on (usually "127.0.0.1").
        :type ip: str
        :param port: The port the game client is listening on (usually 27015).
        :type port: int
        :param passwd: The Rcon password to be used to issue commands.
        :type passwd: str'''
        self.client = Client(ip, port, passwd=passwd)

    def run(self, command, *params):
        return self.client.run(command, *params)

    def __enter__(self):
        self.client.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.__exit__(exc_type, exc_val, exc_tb)


class ExecConsole(VConsole):
    '''
    Issues commands by using the -hijack launch parameters alongside a +exec statement.
    This is supported by games that support -hijack (not csgo).
    '''

    def __init__(self, gameExe, gameDir, uuid):
        '''
        :param gameExe: The path to the game executable.
        :type gameExe: path, str
        :param gameDir: The path to the mod folder.
        :type gameDir: path, str
        :param uuid: A unique identifier for the config name.
        :type uuid: str'''

        self.gameExe = gameExe
        self.gameDir = gameDir
        self.cfgName = 'valve-exe-' + uuid + '.cfg'
        self.cfgPath = os.path.join(self.gameDir, 'cfg', self.cfgName)

    def run(self, command, *params):
        with open(self.cfgPath, "w") as f:
            f.seek(0)
            f.write(command + ' ' + ' '.join(params))
            f.truncate()

        launch_params = [self.gameExe, '-hijack', '+exec', self.cfgName]
        self.process = subprocess.Popen(
            launch_params,
            creationflags=subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NEW_PROCESS_GROUP)

        time.sleep(1) # leaves time for the game to read the command

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            os.remove(self.cfgPath)
        except:
            pass
