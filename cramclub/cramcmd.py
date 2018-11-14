"""
Top level commands.
"""
import os
import time
from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from cramio import CramIo
import cramtest



def test():
    """
    Various tests to verify Web API behaviors.
    """
    cramtest.test_add_contact_to_callhub()


def start():
    """
    Start doing the work.
    """
    logger = CramLog.instance() # pylint: disable-msg=E1102
    logger.log(70, 'Starting')

    cramio = CramIo()
    # Clean up from previous 'stop' command
    if cramio.stop_process():
        os.remove(cramio.cram.cfg['stop_file_path'])

    # Here is where the work really begins
    while not cramio.stop_process():
        if cramio.start_process():
            cramio.process_groups()
        # Wait a minute before checking again
        time.sleep(RETRY_TIME)


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
