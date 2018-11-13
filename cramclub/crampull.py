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

    def __init__(self):
        """
        Set up logger and keys from config.
        Load CiviCRM instance.
        """
        cram = CramCfg.instance() # pylint: disable-msg=E1101

        self.logger = CramLog.instance() # pylint: disable-msg=E1102
        self._api = CiviCRM(
            url = cram.cfg['civicrm']['url'],
            site_key = cram.cfg['civicrm']['site_key'],
            api_key = cram.cfg['civicrm']['api_key'],
            use_ssl = True,
            timeout = cram.cfg['timeout'])


    def contact(self, crm_id):
        """ Retrieve a single contact. """
        response = self._api.get('Contact', id=crm_id)
        contact = {}
        if response:
            contact = response[0]
            #self.logger.debug('Contact: {:s}'.format(str(contact)))
            fields = self._api.get('CustomValue', entity_id=crm_id)
            #self.logger.debug('Custom data: {:s}'.format(str(fields)))
            contact['custom'] = {}
            for field in fields:
                contact['custom'][field['id']] = field['latest']
        return contact


    def group(self, group_id):
        """ Retrieve all contacts in a group. """
        contacts = []
        try:
            contacts = self._api.get('Contact',
                                     group=[group_id],
                                     limit=5000,
                                     offset=0)

            self.logger.info('Contacts: {:d}'.format(len(contacts)))

        except ReadTimeout as err:
            self.logger.error(err)

        return contacts
