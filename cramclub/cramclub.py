"""
CiviCRM / CallHub integration utility.

Purpose:
Update CallHub phone books based upon a list of matching CiviCRM smart group identifiers.


Notes:
Configurable to update on a schedule. See command line arguments 'at'.
CallHub contacts have a custom ContactID field corresponding to the CiviCRM contact.
"""
import sys
import argparse


def get_args(prog, argv):
    """
    Parse command line and execute the required operation.
    """
    parser = argparse.ArgumentParser(
        description='CiviCRM smart groups to CallHub phonebooks updater.')

    parser.add_argument('--version', action='version', version='%(prog)s 0.1')

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid sub-commands')

    parser_start = subparsers.add_parser('start',
                                         description='Execute the updater using the configured schedule')
    parser_start.add_argument('--civicrm-site-key', required=True,
                        help='CiviCRM Site Key')
    parser_start.add_argument('--civicrm-api-key', required=True,
                        help='CiviCRM API Key')
    parser_start.add_argument('--callhub-api-key', required=True,
                        help='CallHub API Key')
    parser_start.add_argument('--timeout', type=int, default=5,
                        help='REST API call timeout in seconds')
    parser_start.set_defaults(cmd=start)

    parser_stop = subparsers.add_parser('stop', description='Halt a running updater')
    parser_stop.set_defaults(cmd=stop)

    parser_restart = subparsers.add_parser('restart', description='Halt a running updater')
    parser_restart.set_defaults(cmd=restart)

    return parser.parse_args(argv)


def start(args):
    print('Starting')
    print(args)


def stop(args):
    print('Stopping')
    print(args)


def restart(args):
    stop(args)
    start(args)


def main(prog, argv):
    """
    Determine the action to take and execute it.
    """
    args = get_args(prog, argv)
    args.cmd(args)

if __name__ == "__main__":
    # execute only if run as a script
    main(prog=sys.argv[0], argv=sys.argv[1:])
