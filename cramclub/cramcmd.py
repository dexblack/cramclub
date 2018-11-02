"""
Top level commands.
"""
import os
import time
from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from cramio import CramIo


def start():
    """
    Start doing the work.
    """
    logger = CramLog.instance() # pylint: disable-msg=E1102
    logger.info('Starting')
    #logger.info(args)
    cramio = CramIo()
    # Clean up from previous 'stop' command
    if cramio.start_process():
        os.remove(cramio.cfg['stop_file_path'])


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
    cram = CramCfg.instance() # pylint: disable-msg=E1101
    logger = CramLog.instance() # pylint: disable-msg=E1102
    logger.info('Stopping')
    #logger.info(args)
    with open(cram.cfg['stop_file_path'], 'w') as f:
        f.write('Stop CramClub instance running')


def restart():
    stop()
    # Wait long enough for the currently running instance to halt
    time.sleep(RETRY_TIME)
    start()
