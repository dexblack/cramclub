"""
Configuration values.
"""
import os
import platform
import yaml
from singleton.singleton import Singleton
from pathlib import PurePath
from cramlog import CramLog
import cramconst

@Singleton
class CramCfg(object):
    """Singleton Configuration object."""

    _CFG_FILE_NAME = cramconst.APP_NAME + ".yaml"

    def __init__(self, *args, **kwargs):
        logger = CramLog.instance()

        self.cfg = {}

        if "CRAMCLUB_CFG_DIR" in os.environ:
            self.cfg_dir = os.environ["CRAMCLUB_CFG_DIR"]

        if not hasattr(self, "cfg_dir"):
            if platform.system() == "Linux":
                self.cfg_dir = PurePath("/") / "etc" / cramconst.APP_NAME
            elif platform.system() == "Windows":
                self.cfg_dir = PurePath(os.environ["PROGRAMDATA"]) / cramconst.APP_NAME

        if not hasattr(self, "cfg_dir"):
            raise RuntimeError("CramCfg: Unsupported platform: " + platform.system())

        print("Configuration directory: " + self.cfg_dir.as_posix())

        self.defaults_path = self.cfg_dir / 'defaults.yaml'
        print("Default configuration: " + self.defaults_path.as_posix())
        if os.path.exists(self.cfg_dir):
            self.cfg_path = self.cfg_dir / self._CFG_FILE_NAME
            print("Configuration file path: " + self.cfg_path.as_posix())

        if os.path.exists(self.cfg_dir / 'defaults.yaml'):
            with open((self.cfg_dir / 'defaults.yaml').as_posix()) as stream:
                try: 
                    self.cfg = yaml.load(stream)
                except yaml.YAMLError as e:
                    logger.critical(str(e))

        if os.path.exists(self.cfg_path.as_posix()):
            with open(self.cfg_path.as_posix()) as stream:
                try: 
                    self.cfg = yaml.load(stream)
                except yaml.YAMLError as e:
                    logger.critical(str(e))

        # Environment values override configuration values
        if "CIVICRM_SITE_KEY" in os.environ:
            self.cfg["civicrm"]["site_key"] = os.environ["CIVICRM_SITE_KEY"]
        if "CIVICRM_API_KEY" in os.environ:
            self.cfg["civicrm"]["api_key"] = os.environ["CIVICRM_API_KEY"]
        if "CALLHUB_API_KEY" in os.environ:
            self.cfg["callhub"]["api_key"] = os.environ["CALLHUB_API_KEY"]

        #print(self.cfg)


    def update(self, from_args):
        """Command line arguments override everything"""
        args = { "civicrm": {}, "callhub": {} }
        if "civicrm_site_key" in from_args:
            args["civicrm"]["site_key"] = from_args.civicrm_site_key
        if "civicrm_api_key" in from_args:
            args["civicrm"]["api_key"] = from_args.civicrm_api_key
        if "callhub_api_key" in from_args:
            args["callhub"]["api_key"] = from_args.callhub_api_key
        self.cfg.update(args)
