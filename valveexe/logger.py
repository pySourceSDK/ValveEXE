import os
import re
import time


class Logger():
    '''Tracks console output by leveraging the `con_logfile` command.
    Supported in most source games (except l4d2)
    '''

    def __init__(self, logpath):
        '''
        :param logpath: The path to the log file
        :type logpath: path, str
         '''
        self.logPath = logpath

        self.logs = ''  #: :type: (str) - all the logs accumulated so far
        self._bookmark = 0

    def log_ingest(self):
        '''
        Will resume reading the logs from where it last left off until the end
        and return all logs since

        :rtype: str
        '''
        logs_since_bookmark = ''
        with open(self.logPath, mode='r') as f:
            f.seek(self._bookmark, 0)
            for line in f.readlines():
                self.logs += line
                logs_since_bookmark += line
                self._bookmark = f.tell()
        return logs_since_bookmark

    def log_until(self, until=None):
        '''
        Will :any:`log_ingest()<log_ingest>` until a specified regex is
        found within the logs.

        :param until: A regex string to match against the logs
        :type until: str
         '''
        logs_since_until = ''  # all logs since the previous log_until()
        with open(self.logPath, mode='r') as f:

            while not re.search(until, logs_since_until):
                time.sleep(0.5)
                logs_since_until += self.log_ingest()
                if not until:
                    break
        return logs_since_until

    def __del__(self):
        try:
            os.remove(self.logPath)
        except:
            pass
