"""
Top level commands.
"""
import os
import time
from cramcfg import CramCfg
from cramlog import CramLog
from cramconst import RETRY_TIME
from cramio import process_groups

def start():
    """
    Start a thread to do the work.
    """
    logger = CramLog.instance()
    logger.info('Starting')
    #logger.info(args)
    cram = CramCfg.instance()
    if os.path.exists(cram.cfg["stop_file_path"]):
        os.remove(cram.cfg["stop_file_path"])

    # Here is where the work really begins
    process_groups()


def stop():
    """
    Create the process stop signal.
    This creates a stop file in the default configuration directory.
    The running instance will see it within 1 minute and halt.
    """
    cram = CramCfg.instance()
    logger = CramLog.instance()
    logger.info('Stopping')
    #logger.info(args)
    with open(cram.cfg["stop_file_path"], "w") as f:
        f.write("Stop CramClub process running")


def restart():
    stop()
    # Wait long enough for the currently running instance to halt
    time.sleep(RETRY_TIME)
    start()
