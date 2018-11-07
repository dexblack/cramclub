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
    #logger = CramLog.instance() # pylint: disable-msg=E1102
    #logger.info('Starting')
    #logger.info(args)
    cramio = CramIo()
    if cramio.stop_process():
        # Clean up from previous 'stop' command
        os.remove(cramio.cram.cfg['stop_file_path'])

    # Here is where the work really begins
    while not cramio.stop_process():
        if cramio.start_process():
            cramio.process_groups()
            if cramio.do_csv_only:
                break
        # Wait a minute before checking again
        time.sleep(RETRY_TIME)


def stop():
    """
    Create the process stop file.
    This creates a stop file in the default configuration directory.
    The running instance will see it within 1 minute and halt.
    """
    #logger = CramLog.instance() # pylint: disable-msg=E1102
    #logger.info('Stopping')
    #logger.info(args)
    cram = CramCfg.instance() # pylint: disable-msg=E1101
    with open(cram.cfg['stop_file_path'], 'w') as f:
        f.write('Stop CramClub instance "%s" running' % cram.cfg['instance'])


def restart():
    stop()
    # Wait long enough for the currently running instance to halt
    time.sleep(RETRY_TIME)
    start()
