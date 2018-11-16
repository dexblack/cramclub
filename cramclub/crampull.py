"""
Retrieve CiviCRM group contact list data.
"""
from requests.exceptions import ReadTimeout, ConnectionError
from singleton.singleton import Singleton

from civicrm.civicrm import CiviCRM
from cramcfg import CramCfg
from cramlog import CramLog



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
        self.rocket_url = cram.cfg['rocket']['url']
        self._api = CiviCRM(
            url=cram.cfg['civicrm']['url'],
            site_key=cram.cfg['civicrm']['site_key'],
            api_key=cram.cfg['civicrm']['api_key'],
            use_ssl=True,
            timeout=cram.cfg['timeout'])


    def sanitise_crm_contact(self, crm_contact):
        """Privacy protection for contact data in logs"""
        return 'contact_id: %s, url: %s' % (
            crm_contact['contact_id'],
            '%s/%s' % (self.rocket_url, crm_contact['contact_id']),
        )


    def contact(self, crm_id):
        """ Retrieve a single contact. """
        response = self._api.get('Contact', id=crm_id)
        contact = {}
        if response:
            contact = response[0]
            #self.logger.debug('Contact: {:s}'.format(self.sanitise_crm_contact(contact)))
            fields = self._api.get('CustomValue', entity_id=crm_id)
            #self.logger.debug('Custom data: {:s}'.format(str(fields)))
            contact['custom'] = {}
            for field in fields:
                contact['custom'][field['id']] = field['latest']
        return contact


    def group(self, group_id):
        """ Retrieve all contacts in a group. """
        contacts = []
        retry_count = 0
        while retry_count < 3:
            try:
                contacts = self._api.get(
                    'Contact',
                    group=[group_id],
                    limit=5000,
                    offset=0)

                self.logger.info('Contacts: {:d}'.format(len(contacts)))
                break

            except ReadTimeout as err:
                if retry_count == 2:
                    self.logger.critical(str(err))
                else:
                    self.logger.warn(str(err) + ' Retrying...' + str(retry_count))
                retry_count += 1

            except ConnectionError as conn_err:
                # 'Connection aborted.', ConnectionResetError
                # 10054, 'An existing connection was forcibly closed by the remote host', None, 10054, None
                if retry_count == 2:
                    self.logger.critical(str(conn_err))
                else:
                    self.logger.warn(str(conn_err) + ' Retrying... ' + str(retry_count))
                retry_count += 1

        return contacts
