"""
Configure the default logging setup.
"""
import logging
from cramcfg import CramCfg
from singleton import Singleton


class CramLog(object):
    """Default logger object configuration"""
    __metaclass__ = Singleton

    def __init__(self, *args, **kwargs):
        self.init_logger = logging.getLogger(CramCfg.logger_name + ".init")
        ich = logging.StreamHandler()
        ich.setLevel(logging.ERROR)
        self.init_logger.addHandler(ich)

        self._logger = logging.getLogger(CramCfg.logger_name)
        self._logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(_DEFAULT_LOG_FILE)
        fh.setLevel(logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
