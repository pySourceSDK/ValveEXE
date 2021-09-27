import os
import uuid
import time
import subprocess
import psutil
import glob

from rcon import Client

from valveexe.logger import Logger
from valveexe.console import RconConsole, ExecConsole


class ValveExe(object):
    def __init__(self, gameExe, gameDir, steamExe=None, appid=None):
        '''Defines a launchable source engine game to be interacted with.

        .. note:: Some games cannot be launched by their .exe alone \
        (ex:csgo, probably for anti-cheat related reasons). \
        Those games need to include the optional parameters :any:`steamExe` \
        and :any:`appid`. Those parameters are only to be used if \
        absolutely needed, they are a fallback and will downgrade ValveEXE \
        functionnality if present.

        :param gameExe: the path for the game executable.
        :type gameExe: path, str
        :param gameDir: The mod directory.
        :type gameDir: path, str
        :param steamExe: The path for the Steam executable.
        :type steamExe: optional, path, str
        :param appid: The `Steam AppID <https://developer.valvesoftware.com/wiki/Steam_Application_IDs>`_.
        :type appid: optional, int
        '''

        self.gameExe = gameExe
        self.gameDir = gameDir
        self.exeName = self.gameExe.split('\\')[-1]

        self.appid = appid
        self.steamExe = steamExe

        self.uuid = str(uuid.uuid4()).split('-')[-1]

        self.logName = 'valve-exe-' + self.uuid + '.log'
        self.logPath = os.path.join(gameDir, self.logName)

        self.console = None

        self.rcon_enabled = None
        self.hijacked = None

        self._full_cleanup()

    def launch(self, *params):
        '''Launches the game as specified in :any:`__init__` with the
        launch parameters supplied as arguments.

        :param \*params: The launch parameters to be supplied to the executable.
        :type \*params: str
        '''
        if self.steamExe and self.appid:
            self._terminate_process()  # Steam launches cannot be hijacked
            launch_params = [self.steamExe, '-applaunch', str(self.appid)]
        else:
            self.hijacked = bool(self._find_process())
            launch_params = [self.gameExe, '-hijack']

        launch_params.extend(['-game', self.gameDir])
        launch_params.extend(['+log', '0', '+sv_logflush', '1',
                              '+con_logfile', self.logName])

        if self._check_rcon_eligible() is not False:
            launch_params.extend(['-usercon', '+ip', '0.0.0.0',
                                  '+rcon_password', self.uuid])

        launch_params.extend(list(*params))
        self.process = subprocess.Popen(
            launch_params,
            creationflags=subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NEW_PROCESS_GROUP)

        while not os.path.exists(self.logPath):
            time.sleep(3)

        self.logger = Logger(self.logPath)

    def run(self, command, *params):
        '''Forwards a command with its parameters to the active :any:`VConsole`

        :param command: A Source Engine `console command \
        <https://developer.valvesoftware.com/wiki/Console_Command_List>`_.
        :type command: str
        :param \*params: The values to be included with the command.
        :type \*params: str
        '''

        if self.console:
            self.console.run(command, *params)
        else:
            with self as console:
                console.run(command, *params)

    def quit(self):
        '''Closes the game client'''
        process = self.process or self._find_process(self)
        if process:
            process.terminate()

    def _check_rcon_eligible(self):
        '''
        None: Unknown
        True: Eligible
        False: Not eligible
        '''
        process = self._find_process()
        if not process:
            # no process running
            return None
        elif self.gameDir not in process.cmdline():
            # wrong game open
            process.terminate()
            return None
        elif '-usercon' not in process.cmdline():
            # doesn't have rcon enabled
            return False
        else:
            # 'connections' confirms game is listening for rcon
            return bool(process.connections())

    def _find_process(self):
        return next((p for p in psutil.process_iter() if
                     p.name() == self.exeName), None)

    def _terminate_process(self):
        process = self._find_process()
        process and process.terminate()

    def __enter__(self):
        while self._check_rcon_eligible() is None:
            time.sleep(3)

        if self._check_rcon_eligible():
            self.console = RconConsole("127.0.0.1", 27015, self.uuid)
        else:
            self.console = ExecConsole(self.gameExe, self.gameDir, self.uuid)

        self.console.__enter__()
        return self.console

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.console.__exit__(exc_type, exc_val, exc_tb)
        self.console = None

    def __del__(self):
        try:
            self.run('con_logfile', '""')
        except:
            pass
        del self.logger

    def _full_cleanup(self):
        for f in glob.glob(self.gameDir + 'valve-exe-*.log'):
            try:
                os.remove(f)
            except:
                pass
