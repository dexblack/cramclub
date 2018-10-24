"""
Configuration values.
"""
import os
import platform
import yaml
from singleton.singleton import Singleton
from pathlib import PurePath
from cramlog import CramLog
from cramconst import APP_NAME, dot_or_nothing


@Singleton
class CramCfg(object):
    """Singleton Configuration object."""

    _CFG_FILE_NAME = APP_NAME

    def __init__(self, *args, **kwargs):
        self.logger = CramLog.instance()

        self.cfg = {
            'instance': (kwargs['instance'] if 'instance' in kwargs else None),
            'dir': None,
            'callhub': {},
            'civicrm': {},
            'timeout': 0,
            'runat': None,
            'stop_file_path': None
            }

        # Override platform dependent configuration location.
        if 'CRAMCLUB_CFG_DIR' in os.environ:
            self.cfg['dir'] = PurePath(os.environ['CRAMCLUB_CFG_DIR'])

        if not self.cfg['dir']:
            if platform.system() == 'Linux':
                self.cfg['dir'] = PurePath('/') / 'etc' / APP_NAME
            elif platform.system() == 'Windows':
                self.cfg['dir'] = PurePath(os.environ['PROGRAMDATA']) / APP_NAME

        if not self.cfg['dir']:
            raise RuntimeError('CramCfg: Unsupported platform: ' + platform.system())

        self.logger.info('Configuration directory: ' + self.cfg['dir'].as_posix())

        self.cfg['stop_file_path'] = (self.cfg['dir'] / (
            'cramclub' + dot_or_nothing(self.cfg['instance']) + '.stop')).as_posix()
        print('Stop file path: ' + self.cfg['stop_file_path'])

        self.defaults_path = self.cfg['dir'] / (
            'defaults' + dot_or_nothing(self.cfg['instance']) + '.yaml')

        print('Default configuration: ' + self.defaults_path.as_posix())
        if os.path.exists(self.cfg['dir']):
            # Build the correct configuration file name for this instance.
            self.cfg_path = self.cfg['dir'] / (
                self._CFG_FILE_NAME + dot_or_nothing(self.cfg['instance']) + '.yaml')

            print('Configuration file path: ' + self.cfg_path.as_posix())

        if os.path.exists(self.defaults_path.as_posix()):
            with open(self.defaults_path.as_posix()) as stream:
                try: 
                    self.cfg = yaml.load(stream)
                except yaml.YAMLError as e:
                    self.logger.critical(str(e))

        if os.path.exists(self.cfg_path.as_posix()):
            with open(self.cfg_path.as_posix()) as stream:
                try: 
                    self.cfg.update(yaml.load(stream))
                except yaml.YAMLError as e:
                    self.logger.critical(str(e))
        else:
            raise RuntimeError('Missing configuration file: ' + self.cfg_path.as_posix())

        # Environment values override configuration values
        if 'CIVICRM_SITE_KEY' in os.environ:
            self.cfg['civicrm']['site_key'] = os.environ['CIVICRM_SITE_KEY']

        if 'CIVICRM_API_KEY' in os.environ:
            self.cfg['civicrm']['api_key'] = os.environ['CIVICRM_API_KEY']

        if 'CALLHUB_API_KEY' in os.environ:
            self.cfg['callhub']['api_key'] = os.environ['CALLHUB_API_KEY']

        if 'CRAMCLUB_RUNAT' in os.environ:
            self.cfg['runat'] = os.environ['CRAMCLUB_RUNAT']

        # Remove trailing slash from URLs
        assert 'civicrm' in self.cfg and 'url' in self.cfg['civicrm']
        if self.cfg['civicrm']['url'][-1:] == '/':
            self.cfg['civicrm']['url'] = self.cfg['civicrm']['url'][0:-1]

        assert 'callhub' in self.cfg and 'url' in self.cfg['callhub']
        if self.cfg['callhub']['url'][-1:] == '/':
            self.cfg['callhub']['url'] = self.cfg['callhub']['url'][0:-1]

        assert 'rocket' in self.cfg and 'url' in self.cfg['rocket']
        if self.cfg['rocket']['url'][-1:] == '/':
            self.cfg['rocket']['url'] = self.cfg['rocket']['url'][0:-1]

        #self.logger.info(self.cfg)


    def update(self, from_args):
        """Command line arguments override everything"""
        if 'civicrm_site_key' in from_args and from_args.civicrm_site_key:
            self.cfg['civicrm']['site_key'] = from_args.civicrm_site_key

        if 'civicrm_api_key' in from_args and from_args.civicrm_api_key:
            self.cfg['civicrm']['api_key'] = from_args.civicrm_api_key

        if 'callhub_api_key' in from_args and from_args.callhub_api_key:
            self.cfg['callhub']['api_key'] = from_args.callhub_api_key

        if 'timeout' in from_args and from_args.timeout:
            self.cfg['timeout'] = from_args.timeout

        if 'runat' in from_args and from_args.runat:
            self.cfg['runat'] = from_args.runat

        # A simple check to validate the configuration was not copied
        # by mistake and used for the wrong purpose.
        # Internal 'instance' identifier must match the command line.
        self.logger.info('Instance command line: "' + from_args.instance + '"')
        self.logger.info('Instance configuration: ' +
                         ('"' + self.cfg['instance'] + '"' if self.cfg['instance'] else 'null'))
        assert from_args.instance == self.cfg['instance']
