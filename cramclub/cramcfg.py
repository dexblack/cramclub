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


def load_configuration(file, logger):
    """ Base reader/writer for YAML configuration file. """
    cfg = {}
    with open(file) as stream:
        try:
            cfg = yaml.load(stream)
        except yaml.YAMLError as err:
            logger.critical(str(err))
    return cfg


def save_configuration(cfg, file):
    """ Just dump the YAML as text. """
    with open(file, 'w') as stream:
        yaml.dump(cfg, stream, default_flow_style=False)


class CramPath(object):
    """
    Construct all the various required file paths.
    """
    _path = None # Configuration directory.
    instance = None  # Name of the current running instance i.e. 'prod'.
    csv = None # CSV file path.
    groups = None # Group configuration file path.
    stop = None # Stop file path.
    defaults = None # Default values configuration file path.
    configuration = None # Instance configuration file path.


    def __init__(self, instance):
        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        self.instance = instance
        instance = dot_or_nothing(instance)

        # Override platform dependent configuration location.
        env_config_dir = os.getenv('CRAMCLUB_CFG_DIR')
        if env_config_dir:
            self._path = PurePath(env_config_dir)
        else:
            if platform.system() == 'Linux':
                xdg_cfg_home = os.environ['XDG_CONFIG_HOME']
                xdg_home = PurePath(xdg_cfg_home if xdg_cfg_home else '/etc')
                self._path = xdg_home / APP_NAME
            elif platform.system() == 'Windows':
                self._path = PurePath(os.getenv('PROGRAMDATA')) / APP_NAME
            else:
                raise RuntimeError('CramPaths Unsupported platform: ' + platform.system())

        self.logger.info('Configuration directory: ' + self._path.as_posix())

        self.csv = (self._path / (APP_NAME + instance + '.csv')).as_posix()
        self.stop = (self._path / (APP_NAME + instance + '.stop')).as_posix()
        self.groups = (self._path / (APP_NAME + '.groups' + instance + '.yaml')).as_posix()

        self.defaults = (self._path / ('defaults' + instance + '.yaml')).as_posix()

        # Build the correct configuration file name for this instance.
        self.configuration = (self._path / (APP_NAME + instance + '.yaml')).as_posix()



@Singleton
class CramCfg(object):
    """Singleton Configuration object."""

    def __init__(self, instance):
        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        self.paths = CramPath(instance)
        self.secure_keys = [
            ('civicrm', 'api_key'),
            ('civicrm', 'site_key'),
            ('callhub', 'api_key'),
        ]


        self.cfg = {
            'instance': self.paths.instance,
            'iv': None,
            'salt': None,
            'secured': False,
            'callhub': {},
            'civicrm': {},
            'rocket': {},
            'timeout': 20,
            'runat': "03:00",
            'stop_file_path': None
            }


        self.cfg['csv_file_path'] = self.paths.csv
        self.cfg['stop_file_path'] = self.paths.stop
        self.logger.log(70, 'Stop file path: ' + self.cfg['stop_file_path'])
        self.logger.log(70, 'Default configuration: ' + self.paths.defaults)
        self.logger.log(70, 'Configuration file path: ' + self.paths.configuration)
        self.logger.log(70, 'Groups file path: ' + self.paths.groups)

        if os.path.exists(self.paths.defaults):
            self.cfg.update(load_configuration(self.paths.defaults, self.logger))

        if not os.path.exists(self.paths.configuration):
            raise RuntimeError('Missing configuration file: ' + self.paths.configuration)
        self.cfg.update(load_configuration(self.paths.configuration, self.logger))

        if os.path.exists(self.paths.groups):
            self.cfg.update(load_configuration(self.paths.groups, self.logger))


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
            else:
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
        instance = self.cfg['instance']
        self.logger.debug('Instance configuration: "%s"' % (instance or ''))
        assert from_args.instance == instance
