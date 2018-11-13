"""
Configure the default logging setup.
"""
import os
import logging
import platform
from pathlib import PurePath
from singleton.singleton import Singleton

from cramconst import APP_NAME, dot_or_nothing


@Singleton
class CramLog(object):
    """Singleton logger object"""

    _DEFAULT_LOG_FILE = APP_NAME
    instance = None

    def __init__(self, *args, **kwargs):
        # Check for log directory defined by the environment
        if 'CRAMCLUB_LOG_DIR' in os.environ:
            self.log_dir = os.environ['CRAMCLUB_LOG_DIR']

        if 'instance' in kwargs:
            self.instance = kwargs['instance']

        # If none specified then use platform specific default location
        if not hasattr(self, 'log_dir'):
            if platform.system() == 'Linux':
                self.log_dir = PurePath('/') / 'var' / 'log' / APP_NAME
            elif platform.system() == 'Windows':
                if 'PROGRAMDATA' in os.environ:
                    self.log_dir = PurePath(os.environ['PROGRAMDATA']) / APP_NAME

        if not hasattr(self, 'log_dir'):
            raise RuntimeError('CramLog: Unsupported platform: ' + platform.system())

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.init_logger = logging.getLogger(APP_NAME + '.init')
        ich = logging.StreamHandler()
        ich.setLevel(logging.ERROR)
        ich.setFormatter(formatter)
        self.init_logger.addHandler(ich)

        print('Log output at: ' + self.log_dir.as_posix())

        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        self._logger = logging.getLogger(APP_NAME + '.engine')
        self._logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        log_path = self.log_dir / (self._DEFAULT_LOG_FILE + 
                                  dot_or_nothing(self.instance) + '.log')
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        # add the handlers to logger
        self._logger.addHandler(ch)
        self._logger.addHandler(fh)        


    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)


    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)


    def warn(self, msg, *args, **kwargs):
        self._logger.warn(msg, *args, **kwargs)


    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)


    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)
