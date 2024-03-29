# CRaM CalLhUB.

## CiviCRM to CallHub smart group phonebook updater.

Generates updated contact lists within existing CallHub phonebooks.
This is based upon a mapping configuration of CiviCRM smart group identifiers
to corresponding CallHub Phonebook identifiers.

Configuration location is either:
Linux:  $XDG_CONFIG_HOME default /etc/cramclub/
windows: $PROGRAMDATA/cramclub/

Alternatively you can define `CRAMCLUB_CFG_DIR` in the environment and override the default loation.


Configuration files:

### Usage
	python cramclub.py --help

	usage: cramclub.py [-h] [--version] [--loglevel {CRITICAL,ERROR,WARNING,INFO,DEBUG,NOTSET}] {secure,start,stop,restart} ...

CiviCRM smart groups to CallHub phonebooks updater.

Optional arguments:
	-h, --help            show this help message and exit
	--version             show program's version number and exit

subcommands:
  valid sub-commands

  {secure,start,stop,restart}

#### Securing
Secure the updater's configuration files

	cramclub.py secure -i INSTANCE

#### Starting
Execute the updater using the configured schedule

	cramclub.py start --help
	
	usage: python cramclub.py start --help
	usage: python cramclub.py start --instance INSTANCE
		[--civicrm_site_key CIVICRM_SITE_KEY]
		[--civicrm_api_key CIVICRM_API_KEY]
		[--callhub_api_key CALLHUB_API_KEY]
		[--timeout TIMEOUT]
		[--runat RUNAT]

	--instance INSTANCE, -i INSTANCE
		Which configuration to use;e.g. "INSTANCE" =>
		cramclub.INSTANCE.yaml

Optional arguments:

*NB: Command line arguments override configuration file values.*

	-h, --help  show this help message and exit
	
	--civicrm_site_key CIVICRM_SITE_KEY
		[env] CiviCRM Site key
	--civicrm_api_key CIVICRM_API_KEY
		[env] CiviCRM API key
	--callhub_api_key CALLHUB_API_KEY
		[env] CallHub API key
	--timeout TIMEOUT, -t TIMEOUT
		REST API call timeout in seconds
	--runat RUNAT, -r RUNAT
		Time of day to run the job. [env] CRAMCLUB_RUNAT

    e.g. python cramclub.py -l WARNING start -i prod --runat 03:00 --timeout 30

#### Stopping
Halt a running updater

	python cramclub.py stop --help

	usage: cramclub.py stop -h | --help
	usage: cramclub.py stop --instance INSTANCE

    e.g. python cramclub.py -l NOTSET stop -i prod

#### Restarting
Restarting a running updater

	cramclub.py restart --help

	usage: cramclub.py restart -h | --help
	usage: cramclub.py restart --instance INSTANCE
