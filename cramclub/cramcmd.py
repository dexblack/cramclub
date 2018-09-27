"""
Top level commands.
"""
from cramlog import cramlog
import crampull

def start(args):
    """
    Read configuration and wait for scheduled update time or stop signal.
    """
    print('Starting')
    #print(args)


def stop(args):
    """
    Create the process stop signal.
    This is a just creating a file named 'stop' in the default configuration directory.
    """
    print('Stopping')
    #print(args)


def restart(args):
    stop(args)
    start(args)
