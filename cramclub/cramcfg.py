"""
Configuration values.
"""
import os
import platform
from pathlib import PurePath
from singleton import Singleton
from cramlog import cramlog


class CramCfg(object):
    __metaclass__ = Singleton

    logger_name = "cramclub"
    _DEFAULT_LOG_FILE = _DEFAULT_LOGGER_NAME + ".log"

    def __init__():
        logger = CramCfg()

        self.cfg_dir = os.environ("CRAMCLUB_CFG_DIR")
        self.log_dir = os.environ("CRAMCLUB_LOG_DIR")

        if not self.log_dir:
            if platform.system() == "Linux":
                self.log_dir = PurePath("/") / "var" / "log" . _DEFAULT_LOGGER_NAME

        if not self.log_dir:
            error_msg = "No log output directory available."
            logger.init_logger.critical(error_msg)
            raise RuntimeError(error_msg)

        if not os.path.exists(self.log_dir):
            os.mkdir(self.log_dir)

        self.civicrm_site_key = os.environ.get("CRAMCLUB_CIVI_SITE")
        self.civicrm_api_key = os.environ.get("CRAMCLUB_CIVI_API")
        self.callhub_api_key = os.environ.get("CRAMCLUB_CALLHUB_API")
