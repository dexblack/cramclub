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

    def __init__(self, **kwargs):
        # Check for log directory defined by the environment
        if 'CRAMCLUB_LOG_DIR' in os.environ:
            self.log_dir = os.environ['CRAMCLUB_LOG_DIR']

        self.instance = 'test'
        if 'instance' in kwargs:
            self.instance = kwargs['instance']

        self.default_log_level = logging.DEBUG if self.instance == 'test' else logging.ERROR
        if 'loglevel' in kwargs:
            self.default_log_level = kwargs['loglevel']

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

        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)
        print('Log output at: ' + self.log_dir.as_posix())

        self._logger = logging.getLogger(APP_NAME + '.engine')
        self._logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        log_path = self.log_dir / (
            self._DEFAULT_LOG_FILE + dot_or_nothing(self.instance) + '.log')
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(self.default_log_level)
        # create console handler with a higher log level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        # add the handlers to logger
        self._logger.addHandler(console_handler)
        self._logger.addHandler(file_handler)


    def critical(self, msg, *args, **kwargs): # pylint: disable-msg=C0111
        self._logger.critical(msg, *args, **kwargs)


    def error(self, msg, *args, **kwargs): # pylint: disable-msg=C0111
        self._logger.error(msg, *args, **kwargs)


    def warn(self, msg, *args, **kwargs): # pylint: disable-msg=C0111
        self._logger.warn(msg, *args, **kwargs)


    def info(self, msg, *args, **kwargs): # pylint: disable-msg=C0111
        self._logger.info(msg, *args, **kwargs)


    def debug(self, msg, *args, **kwargs): # pylint: disable-msg=C0111
        self._logger.debug(msg, *args, **kwargs)

    def log(self, level, msg, *arg, **kwargs): # pylint: disable-msg=C0111
        self._logger.log(level, msg, *arg, **kwargs)
