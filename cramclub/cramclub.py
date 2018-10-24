"""
CiviCRM / CallHub integration utility.

Purpose:
Update CallHub phone books based upon a list of matching CiviCRM smart group identifiers.


Notes:
Configurable to update on a schedule. See command line arguments 'at'.
CallHub contacts have a custom ContactID field corresponding to the CiviCRM contact.
Multiple instances may be executed on the same server controlled by
different configurations via the --instance 'name' parameter.
"""
import sys
import argparse
import cramcmd
from cramlog import CramLog
from cramcfg import CramCfg


def get_args(prog, argv):
    """
    Parse command line and execute the required operation.
    """
    parser = argparse.ArgumentParser(
        description='CiviCRM smart groups to CallHub phonebooks updater.')

    parser.add_argument('--version', action='version', version='%(prog)s 0.2')

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid sub-commands')

    parser_start = subparsers.add_parser('start',description='Execute the updater using the configured schedule')
    parser_start.add_argument('--civicrm_site_key', help='[env] CiviCRM Site key')
    parser_start.add_argument('--civicrm_api_key', help='[env] CiviCRM API key')
    parser_start.add_argument('--callhub_api_key', help='[env] CallHub API key')
    parser_start.add_argument('--timeout', type=int, help='REST API call timeout in seconds')
    parser_start.add_argument('--runat', help='Time of day to run the job. [env] CRAMCLUB_RUNAT')
    parser_start.add_argument('--instance', help='Which configuration to use; e.g. "state" => cramclub.state.yaml', default='')
    parser_start.set_defaults(cmd=cramcmd.start)

    parser_stop = subparsers.add_parser('stop', description='Halt a running updater')
    parser_stop.set_defaults(cmd=cramcmd.stop)

    parser_restart = subparsers.add_parser('restart', description='Halt a running updater')
    parser_restart.set_defaults(cmd=cramcmd.restart)

    args = parser.parse_args(argv)
    return args


def main(prog, argv):
    """
    Determine the action to take and execute it.
    """
    args = get_args(prog, argv)
    CramLog.initialize(instance=args.instance)
    CramCfg.initialize(instance=args.instance)
    config = CramCfg.instance()
    config.update(args)

    if "cmd" in args:
        args.cmd()


# MAIN script execution begins here
if __name__ == "__main__":
    # execute only if run as a script
    main(prog=sys.argv[0], argv=sys.argv[1:])
