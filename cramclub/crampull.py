"""
Retrieve CiviCRM group contact list data.
"""
from singleton.singleton import Singleton
from civicrm.civicrm import CiviCRM
from cramcfg import CramCfg
from cramlog import CramLog
from requests.exceptions import ReadTimeout


@Singleton
class CramPull(object):
    """
    CiviCRM API wrapper class.
    Restricted to pulling information only.
    """
    _api = None

    def __init__(self, *args, **kwargs):
        cram = CramCfg.instance()

        self._api = CiviCRM(
            url = cram.cfg["civicrm"]["url"],
            site_key = cram.cfg["civicrm"]["site_key"],
            api_key = cram.cfg["civicrm"]["api_key"],
            use_ssl = True,
            timeout = cram.cfg["timeout"])


    def contact(self, id):
        return self._api.get("Contact", id=id);


    def group(self, group_id):
        logger = CramLog.instance()
        contacts = []
        try:
            contacts = self._api.get("Contact", group=[group_id],
                                    limit=5000, offset=0);
            logger.info("Contacts: {:d}".format(len(contacts)))
        except ReadTimeout as ce:
            logger.error(ce)

        return contacts
