"""
Top level commands.
"""
from cramlog import CramLog
import crampull

def start():
    """
    Use the configuration and wait for scheduled update time or stop signal.
    """
    logger = CramLog.instance()
    logger.info('Starting')
    #print(args)


def stop():
    """
    Create the process stop signal.
    This is a just creating a file named 'stop' in the default configuration directory.
    """
    logger = CramLog.instance()
    logger.info('Stopping')
    #print(args)


def restart():
    stop()
    start()
