"""
Retrieve CiviCRM group contact list data.
"""
import requests
import cramcfg


class crampull(object):
    """CiviCRM wrapper class"""
    def __init__(self, *args, **kwargs):
        self.api_key = cramcfg.civicrm_api_key
        self.site_key = cramcfg.civicrm_site_key

    def configure(self):
        pass

    def contacts(self):
        return []

    def group(self, id):
        return {}
