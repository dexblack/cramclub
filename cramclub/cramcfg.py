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

        self.cfg = {
            "dir": None,
            "callhub": {},
            "civicrm": {},
            "timeout": 0,
            "runat": None,
            "stop_file_path": None
            }

        # Override platform dependent configuration location.
        if "CRAMCLUB_CFG_DIR" in os.environ:
            self.cfg["dir"] = PurePath(os.environ["CRAMCLUB_CFG_DIR"])

        if not self.cfg["dir"]:
            if platform.system() == "Linux":
                self.cfg["dir"] = PurePath("/") / "etc" / cramconst.APP_NAME
            elif platform.system() == "Windows":
                self.cfg["dir"] = PurePath(os.environ["PROGRAMDATA"]) / cramconst.APP_NAME

        if not self.cfg["dir"]:
            raise RuntimeError("CramCfg: Unsupported platform: " + platform.system())

        logger.info("Configuration directory: " + self.cfg["dir"].as_posix())

        self.cfg["stop_file_path"] = (self.cfg["dir"] / "cramclub.stop").as_posix()

        self.defaults_path = self.cfg["dir"] / 'defaults.yaml'
        print("Default configuration: " + self.defaults_path.as_posix())
        if os.path.exists(self.cfg["dir"]):
            self.cfg_path = self.cfg["dir"] / self._CFG_FILE_NAME
            print("Configuration file path: " + self.cfg_path.as_posix())

        if os.path.exists(self.cfg["dir"] / 'defaults.yaml'):
            with open((self.cfg["dir"] / 'defaults.yaml').as_posix()) as stream:
                try: 
                    self.cfg = yaml.load(stream)
                except yaml.YAMLError as e:
                    logger.critical(str(e))

        if os.path.exists(self.cfg_path.as_posix()):
            with open(self.cfg_path.as_posix()) as stream:
                try: 
                    self.cfg.update(yaml.load(stream))
                except yaml.YAMLError as e:
                    logger.critical(str(e))

        # Environment values override configuration values
        if "CIVICRM_SITE_KEY" in os.environ:
            self.cfg["civicrm"]["site_key"] = os.environ["CIVICRM_SITE_KEY"]

        if "CIVICRM_API_KEY" in os.environ:
            self.cfg["civicrm"]["api_key"] = os.environ["CIVICRM_API_KEY"]

        if "CALLHUB_API_KEY" in os.environ:
            self.cfg["callhub"]["api_key"] = os.environ["CALLHUB_API_KEY"]

        if "CRAMCLUB_RUNAT" in os.environ:
            self.cfg["runat"] = os.environ["CRAMCLUB_RUNAT"]

        # Remove trailing slash from URLs
        if cram.cfg["civicrm"]["url"][-1:] == '/':
            cram.cfg["civicrm"]["url"] = cram.cfg["civicrm"]["url"][0:-1]

        if cram.cfg["callhub"]["url"][-1:] == '/':
            cram.cfg["callhub"]["url"] = cram.cfg["callhub"]["url"][0:-1]

        #logger.info(self.cfg)


    def update(self, from_args):
        """Command line arguments override everything"""
        if "civicrm_site_key" in from_args and from_args.civicrm_site_key:
            self.cfg["civicrm"]["site_key"] = from_args.civicrm_site_key

        if "civicrm_api_key" in from_args and from_args.civicrm_api_key:
            self.cfg["civicrm"]["api_key"] = from_args.civicrm_api_key

        if "callhub_api_key" in from_args and from_args.callhub_api_key:
            self.cfg["callhub"]["api_key"] = from_args.callhub_api_key

        if "timeout" in from_args and from_args.timeout:
            self.cfg["timeout"] = from_args.timeout

        if "runat" in from_args and from_args.runat:
            self.cfg["runat"] = from_args.runat
