# CRaM CalLhUB.

## CiviCRM to CallHub smart group phonebook updater.

Generates updated contact lists within existing CallHub phonebooks.
This is based upon a mapping configuration of CiviCRM smart group identifiers
to corresponding CallHub Phonebook identifiers.

Configuration location is either:
Linux:  $XDG_CONFIG_HOME default /etc/cramclub/
windows: $PROGRAMDATA/cramclub/

Configuration files:
groups.cfg : Tab separated list of [CiviCRM smart group id, CallHub phonebook id].
schedule.cfg : Time(s) of day to initiate the update.