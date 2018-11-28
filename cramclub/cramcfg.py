"""
Configuration values.
"""
import os
import platform
from pathlib import PurePath
import yaml
from singleton.singleton import Singleton
from cramlog import CramLog
from cramconst import APP_NAME, dot_or_nothing


@Singleton
class CramCfg(object):
    """Singleton Configuration object."""

    def __init__(self, *args, **kwargs):
        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        assert not args
        self.cfg = {
            'instance': (kwargs['instance'] if 'instance' in kwargs else None),
            'dir': os.getenv('CRAMCLUB_CFG_DIR'),
            'callhub': {},
            'civicrm': {},
            'rocket': {},
            'timeout': 20,
            'runat': "03:00",
            'stop_file_path': None
            }

        # Override platform dependent configuration location.
        if self.cfg['dir']:
            self.cfg['dir'] = PurePath(self.cfg['dir'])
        else:
            if platform.system() == 'Linux':
                xdg_cfg_home = os.environ['XDG_CONFIG_HOME']
                xdg_home = PurePath(xdg_cfg_home if xdg_cfg_home else '/etc')
                self.cfg['dir'] = xdg_home / APP_NAME
            elif platform.system() == 'Windows':
                self.cfg['dir'] = PurePath(os.getenv('PROGRAMDATA')) / APP_NAME
            else:
                raise RuntimeError('CramCfg: Unsupported platform: ' + platform.system())

        self.logger.info('Configuration directory: ' + self.cfg['dir'].as_posix())

        instance = dot_or_nothing(self.cfg['instance'])
        self.cfg['csv_file_path'] = (self.cfg['dir'] / (APP_NAME + instance + '.csv')).as_posix()
        self.cfg['stop_file_path'] = (self.cfg['dir'] / (APP_NAME + instance + '.stop')).as_posix()
        self.logger.log(70, 'Stop file path: ' + self.cfg['stop_file_path'])

        self.defaults_path = self.cfg['dir'] / ('defaults' + instance + '.yaml')
        self.logger.log(70, 'Default configuration: ' + self.defaults_path.as_posix())

        if os.path.exists(self.cfg['dir']):
            # Build the correct configuration file name for this instance.
            self.cfg_path = self.cfg['dir'] / (
                APP_NAME + instance + '.yaml')

            self.logger.log(70, 'Configuration file path: ' + self.cfg_path.as_posix())

        if os.path.exists(self.defaults_path.as_posix()):
            with open(self.defaults_path.as_posix()) as stream:
                try:
                    self.cfg.update(yaml.load(stream))
                except yaml.YAMLError as err:
                    self.logger.critical(str(err))

        if os.path.exists(self.cfg_path.as_posix()):
            with open(self.cfg_path.as_posix()) as stream:
                try:
                    self.cfg.update(yaml.load(stream))
                except yaml.YAMLError as err:
                    self.logger.critical(str(err))
        else:
            raise RuntimeError('Missing configuration file: ' + self.cfg_path.as_posix())

        def override_with_env(cfg, name, subkey=None):
            '''
            Environment values override configuration values.
            Value names are constructed
            i.e. app name prefixed, uppercased and underscore separated.
            Assignment is to either name or name+subkey depending.
            '''
            env_var = '%s_%s%s' % (
                APP_NAME,
                name.upper(),
                ('_' + subkey.upper()) if subkey else '')
            env_val = os.getenv(env_var)
            if env_val:
                if subkey:
                    cfg[name][subkey] = env_val
                else:
                    cfg[name] = env_val

        override_with_env(self.cfg, name='civicrm', subkey='site_key') # CRAMCLUB_CIVICRM_SITE_KEY
        override_with_env(self.cfg, name='civicrm', subkey='api_key') # CRAMCLUB_CIVICRM_API_KEY
        override_with_env(self.cfg, name='callhub', subkey='api_key') # CRAMCLUB_CALLHUB_API_KEY
        override_with_env(self.cfg, name='runat') # CRAMCLUB_RUNAT

        def trim_slash(url):
            """Remove trailing slash from URLs"""
            return url[0:-1] if url[-1:] == '/' else url

        assert 'url' in self.cfg['civicrm']
        self.cfg['civicrm']['url'] = trim_slash(self.cfg['civicrm']['url'])

        assert 'url' in self.cfg['callhub']
        self.cfg['callhub']['url'] = trim_slash(self.cfg['callhub']['url'])

        assert 'rocket' in self.cfg and 'url' in self.cfg['rocket']
        self.cfg['rocket']['url'] = trim_slash(self.cfg['rocket']['url'])


    def arg_or_cfg(self, from_args, name=None, subkey=None):
        """
        Update self.cfg using from_args and cope with the None value properly.
        Uses `name` or `name_subkey` as attribute name for from_args.
        NB: Handles the special case where name == section and no key.
        """
        arg = getattr(from_args, '%s%s' % (name, '_' + subkey if subkey else ''), None)
        if arg:
            if subkey:
                self.cfg[name][subkey] = arg
            elif not subkey:
                self.cfg[name] = arg


    def update(self, from_args):
        """Command line arguments override everything"""

        self.arg_or_cfg(from_args, 'civicrm', 'site_key')
        self.arg_or_cfg(from_args, 'civicrm', 'api_key')
        self.arg_or_cfg(from_args, 'callhub', 'api_key')
        self.arg_or_cfg(from_args, 'timeout')
        self.arg_or_cfg(from_args, 'runat')

        # A simple check to validate the configuration was not copied
        # by mistake and used for the wrong purpose.
        # Internal 'instance' identifier must match the command line.
        self.logger.debug('Instance command line: "%s"' % from_args.instance)
        inst = self.cfg['instance']
        self.logger.debug('Instance configuration: "%s"' % (inst or ''))
        assert from_args.instance == inst
