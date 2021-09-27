from builtins import object
from typing import Pattern
import os
import uuid
import time
import subprocess
import psutil
import glob
import re

from rcon import Client


class ValveExe(object):
    def __init__(self, gameExe, gameDir, steamExe=None, appid=None):

        self.gameExe = gameExe
        self.gameDir = gameDir
        self.exeName = self.gameExe.split('\\')[-1]

        self.appid = appid
        self.steamExe = steamExe

        self.uuid = str(uuid.uuid4())

        self.logName = 'valve-exe-' + self.uuid + '.log'
        self.logPath = os.path.join(gameDir, self.logName)

        self._full_cleanup()

        self.rcon_enabled = None
        self.console = None
        self.hijacked = False

    def launch(self, *params):
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

    def run(self, command, *param):
        if self.console:
            self.console.run(command, *param)
        else:
            with self as console:
                console.run(command, *param)

    def quit(self):
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


class Logger(object):

    def __init__(self, logpath):
        '''
        Tracks console output by leveraging con_logfile.
        Supported in most source games (not l4d2)
        '''
        self.logPath = logpath
        self.logs = ''
        self.bookmark = 0

    def log_until(self, until=None):
        logs_since = ''  # all logs since the previous log_until()
        with open(self.logPath, mode='r') as f:
            f.seek(self.bookmark, 0)
            while not re.search(until, logs_since):
                time.sleep(0.5)
                for line in f.readlines():
                    self.logs += line
                    logs_since += line
                    self.bookmark = f.tell()

    def __del__(self):
        try:
            if os.path.exists(self.logPath):
                os.remove(self.logPath)
        except:
            pass


class VConsole(object):
    def run(self, command, *param):
        pass

    def __enter__(self):
        pass

    def __exit__(self):
        pass


class RconConsole(VConsole):
    '''
    Issues commands by leveraging RCON.
    this is supported by most multiplayer games
    '''

    def __init__(self, ip, port, passwd):
        self.client = Client(ip, port, passwd=passwd)

    def run(self, command, *params):
        return self.client.run(command, *params)

    def __enter__(self):
        self.client.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.__exit__(exc_type, exc_val, exc_tb)


class ExecConsole(VConsole):
    '''
    Issues commands by using the -hijack alongside a +exec statement.
    this is supported by games that support -hijack (not csgo)
    '''

    def __init__(self, gameExe, gameDir, uuid):
        self.gameExe = gameExe
        self.gameDir = gameDir
        self.cfgName = 'valve-exe-' + uuid + '.cfg'
        self.cfgPath = os.path.join(self.gameDir, 'cfg', self.cfgName)

    def run(self, command, *params):
        with open(self.cfgPath, "w+") as f:
            f.seek(0)
            f.write(command + ' ' + ' '.join(params))
            f.truncate()

        launch_params = [self.gameExe, '-hijack', '+exec', self.cfgName]
        self.process = subprocess.Popen(
            launch_params,
            creationflags=subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NEW_PROCESS_GROUP)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if os.path.exists(self.cfgPath):
                os.remove(self.cfgPath)
        except:
            pass
