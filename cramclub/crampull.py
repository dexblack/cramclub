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

        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        self._api = CiviCRM(
            url = cram.cfg['civicrm']['url'],
            site_key = cram.cfg['civicrm']['site_key'],
            api_key = cram.cfg['civicrm']['api_key'],
            use_ssl = True,
            timeout = cram.cfg['timeout'])


    def contact(self, id):
        response = self._api.get('Contact', id=id);
        contact = {}
        if response:
            contact = response[0]
            self.logger.debug('Contact: {:s}'.format(str(contact)))
            custom = self._api.get('CustomValue', entity_id=id)
            self.logger.debug('Custom data: {:s}'.format(str(custom)))
            fields = {}
            if custom['is_error'] != 0 and custom['count'] == 1:
                fields = custom['values'][0]
            contact['custom_fields'] = fields
        return contact


    def group(self, group_id):
        contacts = []
        try:
            contacts = self._api.get('Contact',
                                     group=[group_id],
                                     limit=5000,
                                     offset=0);

            self.logger.info('Contacts: {:d}'.format(len(contacts)))

        except ReadTimeout as ce:
            self.logger.error(ce)

        return contacts
