"""
Wrapper for CallHub operations.
"""
import json
from requests import get, post, delete
from singleton.singleton import Singleton

from cramlog import CramLog
from cramcfg import CramCfg
from cramconst import CUSTOM_FIELDS, CUSTOM_FIELD_FEDERAL, \
                      CUSTOM_FIELD_STATE, CUSTOM_FIELD_CONTACTID


def missing_callhub_contacts(ch_contacts, crm_contacts, crm_ch_id_map):
    """Gather callhub entries not found in CiviCRM id map"""
    ch_ids = [crm_ch_id_map[crm_contact['contact_id']]
              for crm_contact in crm_contacts]
    
    missing = [ch_contact['id'] for ch_contact in ch_contacts
               if ch_contact['id'] not in ch_ids]

    return missing


def gather_callhub_ids(id_map, callhub_contacts):
    """Examine CallHub contact details for CiviCRM id"""
    for callhub_contact in callhub_contacts:
        if (CUSTOM_FIELDS in callhub_contact and
            callhub_contact[CUSTOM_FIELDS] and
            CUSTOM_FIELD_CONTACTID in callhub_contact[CUSTOM_FIELDS]):
            # Gather the contact id
            custom_fields = json.loads(callhub_contact[CUSTOM_FIELDS].replace("'", '"').replace('u"','"'))
            crm_id = custom_fields[CUSTOM_FIELD_CONTACTID]
            if not crm_id:
                continue
            # Assume a valid CiviCRM identifier in this custom field
            # and add it to the map. As string everywhere.
            id_map[crm_id] = str(callhub_contact['id'])


def missing_crm_contacts(crm_contacts, crm_ch_id_map):
    """Return new list from cram that only has the contacts missing from club"""
    # Another O(N) operation dodged with dict lookup.
    missing, remainder = ([], []) # This is the return value
    for crm_contact in crm_contacts:
        if crm_contact['id'] in crm_ch_id_map:
            remainder.append(crm_contact)
        else:
            missing.append(crm_contact)
    return (missing, remainder)



@Singleton
class CallHub(object):
    """
    CallHub API wrapper.
    Implements limited required functionality.
    """
    def __init__(self, *args, **kwargs):
        cram = CramCfg.instance() # pylint: disable-msg=E1101
        self.url = cram.cfg['callhub']['url']
        self.civicrm_url = cram.cfg['civicrm']['url']
        self.rocket_url = cram.cfg['rocket']['url']
        self.headers = {
            'Authorization': 'Token ' + cram.cfg['callhub']['api_key'],
            }
        self.logger = CramLog.instance() # pylint: disable-msg=E1102


    def contacts(self):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""
        all_contacts = self.url + '/contacts'

        crm_ch_id_map = {}
        gather_callhub_ids(id_map=crm_ch_id_map, callhub_contacts=content['results'])

        for page in range(2, int(int(content['count']) / 10) + 2):
            get_response = get(url=all_contacts + '?page=%d' % page, headers=self.headers)
            response_content = json.loads(get_response.content)
            gather_callhub_ids(id_map=crm_ch_id_map, callhub_contacts=response_content['results'])

        return crm_ch_id_map


    def phonebook_get_contacts(self, phonebook_id):
        """Retrieve all contacts in a phonebook"""
        phonebook_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        response = get(url=phonebook_contacts, headers=self.headers)
        return response.results


    def phonebook_clear(self, phonebook_id, contact_ids):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        if contact_ids:
            data = {'contact_ids': contact_ids}
            delete_result = delete(url=phonebook_contacts,
                                   headers=self.headers,
                                   data=data)
            return delete_result

        return {
            'url': self.url,
            'id': phonebook_id,
            'count': 0
            }


    def phonebook_clear_all(self, phonebook_id):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        response = get(url=phonebook_contacts, headers=self.headers)
        contact_ids = [contact['contact'] for contact in response['results']]
        delete_result = self.phonebook_clear(phonebook_id=phonebook_id, contact_ids=contact_ids)
        assert delete_result['count'] == '0'


    def make_callhub_contact_from(self, crm_contact):
        """Extract and transform"""
        return {
            'contact': crm_contact['phone'],
            'mobile': crm_contact['phone'] if crm_contact['phone'][0:2] == '04' else '',
            'last_name': crm_contact['last_name'],
            'first_name': crm_contact['first_name'],
            'country_code': 'AU',
            'email': crm_contact['email'],
            'address': crm_contact['street_address'],
            'city': crm_contact['city'],
            'state': crm_contact['state_province'],
            'company_name': crm_contact[''],
            'company_website': '%s/%s' % (self.rocket_url, crm_contact['contact_id']),
            CUSTOM_FIELDS: {
                CUSTOM_FIELD_FEDERAL: crm_contact[''],
                CUSTOM_FIELD_STATE: crm_contact[''],
                CUSTOM_FIELD_CONTACTID: crm_contact['contact_id']}
            }


    def phonebook_create_new_contact(self, phonebook_id, ch_contact):
        phonebook_create_contact = '%s/phonebooks/%s/create_contact' % (self.url, phonebook_id)
        response = post(url=phonebook_create_contact,
                        headers=self.headers,
                        data=ch_contact)
        self.logger.info(
            'Phonebook: "%s" New contact: "%s"' %
            (phonebook_id, ch_contact[CUSTOM_FIELDS][CUSTOM_FIELD_CONTACTID]))
        if response.ok:
            self.logger.info(response.content)
        else:
            self.logger.debug(response)
        return response


    def phonebook_add_existing(self, phonebook_id, ch_contact_ids):
        phonebook_add_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        response = post(url=phonebook_create_contact,
                        headers=self.headers,
                        data={'contact_ids': ch_contact_ids})
        self.logger.info(
            'Phonebook: "%s" Add existing contact: "%s"' %
            (phonebook_id, ch_contact[CUSTOM_FIELDS][CUSTOM_FIELD_CONTACTID]))
        if response.ok:
            self.logger.info(response.content)
        else:
            self.logger.debug(response)
        return response



    def phonebook_update(self, phonebook_id, crm_contacts, crm_ch_id_map):
        """Create all contacts and add them to phonebook"""

        # Remove contacts not in the crm_contacts list
        missing = missing_callhub_contacts(
            ch_contacts=self.phonebook_get_contacts(phonebook_id),
            crm_contacts=crm_contacts,
            crm_ch_id_map=crm_ch_id_map)

        clear_result = self.phonebook_clear(
            phonebook_id=phonebook_id,
            contact_ids=missing)

        assert ('count' in clear_result and
                clear_result['count'] == len(ch_contacts) - len(remove_ch_contacts))


        # Identify new CRM contacts
        ## Note: Without the dict map this would be O(N*N)!
        missing, remainder = missing_crm_contacts(crm_contacts, crm_ch_id_map)
        
        # Create missing contacts in the phonebook
        for crm_contact in missing:
            self.phonebook_create_new_contact(
                phonebook_id,
                self.make_callhub_contact_from(crm_contact))

        # Add the remaining existing contacts to the phonebook
        self.phonebook_add_existing(
                phonebook_id,
                [crm_ch_id_map[crm_contact['contact_id']]
                 for crm_contact in remainder])
