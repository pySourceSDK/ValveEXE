import os
import uuid
import time
import logging
import subprocess
import psutil
import glob

from rcon import Client

from valveexe.utils import find_process, terminate_process
from valveexe.logger import Logger
from valveexe.console import RconConsole, ExecConsole

log = logging.getLogger(__name__)

#: Drive the game by relaunching it with ``-hijack +exec <cfg>``. Works
#: wherever hijacking works, which is everywhere except a Steam-launched game.
EXEC = 'exec'
#: Drive the game over RCON. Needed for games that cannot be hijacked (csgo),
#: and costs a listen server, an ip binding and an rcon password to set up.
RCON = 'rcon'
#: Pick :any:`EXEC` where the game can be hijacked, :any:`RCON` where it
#: cannot.
AUTO = 'auto'
#: Every console mode :any:`ValveExe` accepts.
CONSOLES = (EXEC, RCON, AUTO)

#: Seconds to wait for the game to start writing its console log.
LAUNCH_TIMEOUT = 120
#: Seconds to wait for a launched game to become reachable by a console.
CONSOLE_TIMEOUT = 120
#: Seconds a game is given to close after ``quit`` before it is killed.
QUIT_TIMEOUT = 30


def remove(path):
    '''Deletes a file if it is there, and shrugs if it is not.'''
    try:
        os.remove(path)
    except OSError:
        pass


class GameNotRunning(RuntimeError):
    '''The game could not be reached: it never came up, or it went away
    before a console could be opened on it.'''


class ValveExe(object):
    def __init__(self, gameExe, gameDir, steamExe=None, appid=None,
                 console=EXEC, lan=True):
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
        :param console: Which console backend drives the game: :any:`EXEC`
            (default), :any:`RCON`, or :any:`AUTO` to pick by capability.
            Stated rather than detected, so a run behaves the same every time.
        :type console: optional, str
        :param lan: Launches with ``sv_lan 1``, so a listen server never asks
            Steam to validate the client's own auth ticket. A Steam client
            left holding a stale ticket (from a game that was killed or
            crashed) otherwise kicks every later session with "Invalid STEAM
            UserID Ticket" until Steam is restarted. Turn off only when the
            game has to host or join a real, Steam-authenticated server.
        :type lan: optional, bool
        '''
        if console not in CONSOLES:
            raise ValueError('console must be one of {}, got {!r}'.format(
                ', '.join(CONSOLES), console))
        self.consoleMode = console
        self.lan = lan

        self.gameExe = gameExe
        self.gameDir = gameDir
        self.exeName = self.gameExe.split('\\')[-1]

        self.appid = appid
        self.steamExe = steamExe

        self.uuid = str(uuid.uuid4()).split('-')[-1]

        self.logName = 'valve-exe-' + self.uuid + '.log'
        self.logPath = os.path.join(gameDir, self.logName)

        self.console = None
        self.process = None
        self.logger = None

        self.rcon_enabled = None
        self.hijacked = None

        self._cleaned = False

        self._full_cleanup()

    def launch(self, *params):
        '''Launches the game as specified in :any:`__init__` with the
        launch parameters supplied as arguments.

        :param \*params: The launch parameters to be supplied to the executable.
        :type \*params: str
        '''
        if self.steamExe and self.appid:
            # Steam launches cannot be hijacked
            terminate_process(self.exeName)
            launch_params = [self.steamExe, '-applaunch', str(self.appid)]
        else:
            self.hijacked = bool(find_process(self.exeName))
            launch_params = [self.gameExe, '-hijack']

        launch_params.extend(['-game', self.gameDir])
        launch_params.extend(['+log', '0', '+sv_logflush', '1',
                              '+con_logfile', self.logName])
        # Ahead of the caller's params, so it is set before any +map loads.
        if self.lan:
            launch_params.extend(['+sv_lan', '1'])

        # -usercon stands up a listen server with an ip binding and an rcon
        # password. Nothing needs that when ExecConsole is driving, and asking
        # for it has been seen to cost the client its own Steam auth ticket.
        log.debug("console mode: %s (rcon=%s)", self.consoleMode,
                  self._uses_rcon())
        if self._uses_rcon():
            launch_params.extend(['-usercon', '+ip', '0.0.0.0',
                                  '+rcon_password', self.uuid])

        launch_params.extend(list(*params))
        self.process = subprocess.Popen(
            launch_params,
            creationflags=subprocess.DETACHED_PROCESS |
            subprocess.CREATE_NEW_PROCESS_GROUP)

        log.debug("log path exists: %s", os.path.exists(self.logPath))
        deadline = time.time() + LAUNCH_TIMEOUT
        while not os.path.exists(self.logPath):
            if time.time() >= deadline:
                raise GameNotRunning(
                    '{} never started writing its console log; waited {}s '
                    'for {}'.format(self.exeName, LAUNCH_TIMEOUT, self.logPath))
            log.debug("waiting for log file: %s", self.logPath)
            time.sleep(0.5)

        self.logger = Logger(self.logPath)

    def run(self, command, *params):
        '''Forwards a command with its parameters to the active :any:`VConsole`

        :param command: A Source Engine `console command \
        <https://developer.valvesoftware.com/wiki/Console_Command_List>`_.
        :type command: str
        :param \*params: The values to be included with the command.
        :type \*params: str
        '''
        if not self.process:
            return
        if self.console:
            self.console.run(command, *params)
        else:
            with self as console:
                console.run(command, *params)

    def quit(self):
        '''Closes the game client.

        Asks it to ``quit`` first, and only kills it if it is still up after
        :any:`QUIT_TIMEOUT`. A killed game never ends its Steam session: the
        Steam client keeps the dead game's auth ticket, and every game started
        after that is kicked with "Invalid STEAM UserID Ticket" until Steam
        itself is restarted.
        '''
        process = self._our_process()
        if process:
            try:
                self.run('quit')
            except Exception:
                log.debug("quit: could not send quit", exc_info=True)
            try:
                process.wait(QUIT_TIMEOUT)
            except psutil.TimeoutExpired:
                log.debug("quit: game still up after %ss, terminating",
                          QUIT_TIMEOUT)
                process.terminate()
            except psutil.NoSuchProcess:
                pass
        self.process = None

    def _can_hijack(self):
        """Whether this game can be driven with ``-hijack +exec``.

        Everything can, except a game that had to be started through Steam
        (csgo): those cannot be hijacked, which is the only reason RCON exists
        here. Deciding by that capability rather than by whether the game
        happened to have its rcon port open yet makes the choice of console
        the same on every run -- it used to be a race, and the two backends
        fail in completely different ways.

        :rtype: bool
        """
        return not (self.steamExe and self.appid)

    def _uses_rcon(self):
        """Whether this instance drives the game over RCON.

        :rtype: bool
        """
        if self.consoleMode == RCON:
            return True
        if self.consoleMode == AUTO:
            return not self._can_hijack()
        return False

    def _our_process(self):
        '''The running game this instance is driving, or None.

        A game whose command line does not carry our ``-game`` dir belongs to
        somebody else -- a plain Steam launch, another mod, another tool's
        session. It is never ours to command, and never ours to kill.

        :rtype: psutil.Process, None
        '''
        process = find_process(self.exeName)
        if not process:
            return None
        try:
            cmdline = process.cmdline()
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            return None
        if self.gameDir in cmdline or self.gameDir.split(os.sep)[-1] in cmdline:
            return process
        log.debug("%s is running, but not with -game %s",
                  self.exeName, self.gameDir)
        return None

    def _check_rcon_eligible(self):
        '''
        None: Unknown -- no game of ours is running to inspect
        True: Eligible
        False: Not eligible
        '''
        process = self._our_process()
        if not process:
            log.debug("rcon check: no game of ours running for %s",
                      self.exeName)
            return None

        try:
            if '-usercon' not in process.cmdline():
                # doesn't have rcon enabled
                log.debug("rcon check: -usercon not present, rcon unavailable")
                return False
            # 'connections' confirms game is listening for rcon
            connections = getattr(process, 'net_connections', None)                 or process.connections
            return bool(connections())
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            log.debug("rcon check: process went away or is unreadable")
            return False

    def __enter__(self):
        log.debug("entering console context, waiting for the game")
        deadline = time.time() + CONSOLE_TIMEOUT
        while self._our_process() is None:
            if time.time() >= deadline:
                raise GameNotRunning(
                    'no {} running with -game {} after {}s; cannot open a '
                    'console'.format(self.exeName, self.gameDir,
                                     CONSOLE_TIMEOUT))
            time.sleep(1)

        if self._uses_rcon():
            log.debug("using RconConsole")
            self.console = RconConsole("127.0.0.1", 27015, self.uuid)
        else:
            log.debug("using ExecConsole")
            self.console = ExecConsole(self.gameExe, self.gameDir, self.uuid)

        log.debug("opening console")
        self.console.__enter__()
        return self.console

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.console:
            self.console.__exit__(exc_type, exc_val, exc_tb)
        self.console = None

    def cleanup(self, quitGame=None):
        '''Undoes everything this instance did, and leaves nothing running.

        Resets ``con_logfile`` while the game can still hear it, closes the
        console, removes the config and log files this instance created, and
        closes a game it launched.

        Safe to call more than once, from a failure path, or after the game
        has already gone: it never waits on a process that is not there, and
        never touches a game this instance did not launch.

        :param quitGame: Whether to close the game. Defaults to closing it
            only when this instance launched it, never when it hijacked one
            that was already running.
        :type quitGame: optional, bool
        '''
        if self._cleaned:
            return
        self._cleaned = True

        if quitGame is None:
            quitGame = not self.hijacked

        process = self._our_process()
        log.debug("cleanup: running=%s quitGame=%s", bool(process), quitGame)

        # Only worth resetting on a game that is alive and staying alive.
        if process and not quitGame:
            try:
                self.run('con_logfile', '""')
            except Exception:
                log.debug("cleanup: could not reset con_logfile", exc_info=True)

        if self.console:
            try:
                self.console.__exit__(None, None, None)
            except Exception:
                log.debug("cleanup: closing the console failed", exc_info=True)
            self.console = None

        if quitGame and process:
            self.quit()
        self.process = None

        if self.logger:
            # Logger.__del__ removes the log file it was reading.
            self.logger = None

        remove(self.logPath)
        remove(os.path.join(self.gameDir, 'cfg',
                            'valve-exe-' + self.uuid + '.cfg'))

    def __del__(self):
        try:
            self.cleanup()
        except BaseException:
            pass

    def _full_cleanup(self):
        '''Sweeps up after earlier runs that never got to clean up: their
        console logs and exec configs would otherwise pile up in the game
        folder forever.'''
        stale = glob.glob(os.path.join(self.gameDir, 'valve-exe-*.log'))
        stale += glob.glob(os.path.join(self.gameDir, 'cfg',
                                        'valve-exe-*.cfg'))
        for f in stale:
            remove(f)
