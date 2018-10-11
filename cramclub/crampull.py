"""
Retrieve CiviCRM group contact list data.
"""
from singleton.singleton import Singleton
from civicrm import *
from cramcfg import CramCfg 


@Singleton
class CramPull(object):
    """CiviCRM API wrapper class"""
    _api = None

    def __init__(self, *args, **kwargs):
        cfg = CramCfg.instance()

        self._api = CiviCRM(
            url = cfg.civicrm.url,
            site_key = cfg.civicrm.site_key,
            api_key = cfg.civicrm.api_key,
            use_ssl = True,
            timeout = cfg.timeout)

    def contact(self, id):
        return self._api.get('Contact', { 'id': id });

    def group(self, id):
        return self._api.get('Group', { 'id': id });
