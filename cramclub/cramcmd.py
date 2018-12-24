"""
Top level commands.
"""
import os
import time
from base64 import b64encode, b64decode
from cramcfg import CramCfg, load_configuration, save_configuration
from cramlog import CramLog
from cramconst import APP_NAME, RETRY_TIME
from cramio import CramIo
from cramcrypt import CramCrypt, get_random_bytes
import cramtest



def test():
    """
    Various tests to verify Web API behaviors.
    """
    #cramtest.test_add_contact_to_callhub()
    cramtest.test_crypto()


def secure():
    """
    Read configuration file(s), encrypt any API keys and write them back.
    """
    cram = CramCfg.instance()
    # Default configuration file.
    cfg_defaults = load_configuration(cram.paths.defaults, cram.logger)
    secured = cfg_defaults.get('secured', None)
    if secured: # Don't do this twice.
        return

    assert 'passphrase' not in cfg_defaults
    assert 'iv' not in cfg_defaults
    assert 'salt' not in cfg_defaults

    crypter = CramCrypt(None, None)
    # iv & salt are auto-generated and only saved in 'defaults.instance.yaml'
    cfg_defaults['iv'] = b64encode(crypter.iv).decode("ascii")
    cfg_defaults['salt'] = b64encode(crypter.salt).decode("ascii")

    def secure_keys(cram, crypter, cfg):
        """ Encrypt the list of key values if present. """
        for (key, subkey) in cram.secure_keys:
            if key in cfg and subkey in cfg[key]:
                cfg[key][subkey] = crypter.encrypt(cfg[key][subkey])
        # Every configuration that has had this run on it will be marked as 'secured'
        # TBD: Hash any secure values and write that result as well so the app
        # can detect modified secure values.
        cfg['secured'] = True


    secure_keys(cram, crypter, cfg_defaults)
    save_configuration(cfg_defaults, cram.paths.defaults, cram.logger)

    # Instance configuration file
    cfg_instance = load_configuration(cram.paths.configuration, cram.logger)
    secure_keys(cram, crypter, cfg_instance)
    save_configuration(cfg_instance, cram.paths.configuration, cram.logger)


def start():
    """
    Start doing the work.
    """
    cram = CramCfg.instance()
    cram.logger.log(70, 'Starting')

    if not cram.cfg['secured']:
        cram.logger.critical('You must first run> python {0}{1}{0}.py secure -i {2}'.format(
            APP_NAME, os.sep, cram.cfg['instance']))
        return

    # Prompts the user for the pass phrase and configures encryption
    cramio = CramIo(
        CramCrypt(
            initial_value=b64decode(cram.cfg['iv'].encode('ascii')),
            salt=b64decode(cram.cfg['salt'].encode('ascii'))
        )
    )

    # Clean up from previous 'stop' command
    if cramio.stop_process():
        os.remove(cramio.cram.cfg['stop_file_path'])

    # Here is where the work really begins
    while not cramio.stop_process():
        if cramio.start_process():
            cramio.process_groups()
        # Wait a minute before checking again
        time.sleep(RETRY_TIME)
    cram.logger.log(70, 'Stopped')


def stop():
    """
    Create the process stop file.
    This creates a stop file in the default configuration directory.
    The running instance will see it within 1 minute and halt.
    """
    logger = CramLog.instance() # pylint: disable-msg=E1102
    logger.log(70, 'Stopping')

    cram = CramCfg.instance() # pylint: disable-msg=E1101
    with open(cram.cfg['stop_file_path'], 'w') as stop_file:
        stop_file.write('Stop CramClub instance "%s" running' % cram.cfg['instance'])


def restart():
    """Stops other running instance and then starts running itself."""
    stop()
    # Wait long enough for the currently running instance to halt
    time.sleep(RETRY_TIME)
    start()
