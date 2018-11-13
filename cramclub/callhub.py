"""
Wrapper for CallHub operations.
"""
import json
from requests import get, post, put, delete
from singleton.singleton import Singleton

from cramlog import CramLog
from cramcfg import CramCfg
from cramconst import CUSTOM_FIELDS, CUSTOM_FIELD_CONTACTID
# unused CUSTOM_FIELD_FEDERAL, CUSTOM_FIELD_STATE


def missing_callhub_contacts(ch_contacts, crm_contacts, crm_ch_id_map):
    """Gather CallHub contacts not found in CiviCRM id map."""
    missing = []
    if not ch_contacts:
        return missing

    ch_ids = []
    for crm_contact in crm_contacts:
        if crm_contact['contact_id'] in crm_ch_id_map:
            ch_ids.append(crm_ch_id_map[crm_contact['contact_id']])

    for ch_contact in ch_contacts:
        contact_id = ch_contact['pk_str'] # id as a string value
        if contact_id not in ch_ids:
            missing.append(contact_id)

    return missing


def gather_callhub_ids(id_map, callhub_contacts):
    """Examine CallHub contact details for CiviCRM id."""
    for callhub_contact in callhub_contacts:
        if (CUSTOM_FIELDS in callhub_contact and
                callhub_contact[CUSTOM_FIELDS] and
                CUSTOM_FIELD_CONTACTID in callhub_contact[CUSTOM_FIELDS]):
            # Gather the contact id
            custom_fields = json.loads(
                callhub_contact[CUSTOM_FIELDS].replace("'", '"').replace('u"', '"'))
            crm_id = custom_fields[CUSTOM_FIELD_CONTACTID]
            if not crm_id:
                continue
            # Assume a valid CiviCRM identifier in this custom field
            # and add it to the map. As string everywhere.
            id_map[crm_id] = callhub_contact['pk_str'] # id as a string


def missing_crm_contacts(crm_contacts, crm_ch_id_map):
    """Return new list from cram that only has the contacts missing from club"""
    # Another O(N) operation dodged with dict lookup.
    missing, remainder = ([], []) # This is the return value
    for crm_contact in crm_contacts:
        if crm_contact['id'] in crm_ch_id_map:
            remainder.append(crm_ch_id_map[crm_contact['id']])
        else:
            missing.append(crm_contact)
    return (missing, remainder)



@Singleton
class CallHub(object):
    """
    CallHub API wrapper.
    Implements limited required functionality.
    """
    def __init__(self):
        """
        Set up configured URLs, API keys and field identifiers.
        """
        cram = CramCfg.instance() # pylint: disable-msg=E1101
        self.url = cram.cfg['callhub']['url']
        self.civicrm_url = cram.cfg['civicrm']['url']
        self.rocket_url = cram.cfg['rocket']['url']
        self.crm_custom = (cram.cfg['civicrm']['custom']
                           if 'custom' in cram.cfg['civicrm'] else {})
        self.headers = {
            'Authorization': 'Token ' + cram.cfg['callhub']['api_key'],
            }
        self.logger = CramLog.instance() # pylint: disable-msg=E1102


    def get_contact_fields(self):
        """
        Return field id and names.
        Essentially useless unless you're building a CSV import mapping,
        except it does not list custom field identifiers; for that you must
        go to the appropriate Web UI Settings page.
        NB: The names DO NOT match the actual fields used in the requests!
        """
        contact_fields = '%s/contacts/fields/' % self.url
        response = get(url=contact_fields, headers=self.headers)
        return response.content


    def create_contact(self, ch_contact):
        """
        Before adding this data the 'contact' number field is standardised
        and a lookup performed. If a matching record is found that is returned.
        NB: The provided details are NOT updated into the existing record!
        However, it MAY update the custom_fields; This needs further confirmation,
        and the behaviour may also change if CallHub make their API work correctly.
        """
        create_contact = self.url + '/contacts/'
        response = post(url=create_contact,
                        headers=self.headers,
                        data=ch_contact)
        #self.logger.info(
        #    'New contact: "%s"' % ch_contact[CUSTOM_FIELDS][CUSTOM_FIELD_CONTACTID])
        content = {}
        if response.ok:
            content = response.json()
            self.logger.info('Created Contact: ' + str(content))
        elif response.status_code == 400:
            response2 = response.json()
            content = response2['contact']
            self.logger.warn('Create Contact bad request: HTTP Error %d' % response.status_code)
            self.logger.warn('Create Contact bad request: %s' % response2['detail'])
        else:
            self.logger.error('Create Contact failed: HTTP Error %d' % response.status_code)
        return content


    def update_contact(self, ch_id, ch_contact):
        """Use 'ch_contact' fields to update CallHub contact 'ch_id'."""
        update_contact = self.url + '/contacts/%s/' % ch_id
        response = put(
            url=update_contact,
            data=ch_contact,
            headers=self.headers)
        #self.logger.info(
        #    'New contact: "%s"' % ch_contact[CUSTOM_FIELDS][CUSTOM_FIELD_CONTACTID])
        content = {}
        if response.ok:
            content = response.json()
            self.logger.info('Updated Contact: %s' % str(content))
        else:
            self.logger.debug('Update Contact failed: %s. %s' % (response.reason, response.text))
        return content


    def contacts(self):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""

        crm_ch_id_map = {}
        page = 1
        next_page = self.url + '/contacts?page=%d' % page
        while next_page:
            get_response = get(url=next_page, headers=self.headers)
            if get_response.status_code != 200:
                self.logger.critical('Failed to retrieve CallHub Contacts page %d' % page)
                next_page = None
                continue

            response_content = get_response.json()
            next_page = response_content['next']
            page = page + 1
            gather_callhub_ids(id_map=crm_ch_id_map, callhub_contacts=response_content['results'])

        return crm_ch_id_map


    def delete_contact(self, ch_id):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""
        next_page = self.url + '/contacts?' + ch_id
        del_response = delete(url=next_page, headers=self.headers)
        if del_response.status_code != 200:
            self.logger.critical('Failed to delete CallHub Contact ' + ch_id)


    def phonebook_get_contacts(self, phonebook_id):
        """Retrieve all contacts in a phonebook"""
        contacts = []
        next_url = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        while next_url:
            response = get(url=next_url, headers=self.headers)
            if response.ok:
                content = response.json()
                contacts.extend(content['results'])
                next_url = content['next']
            else:
                next_url = None
        return contacts


    def phonebook_clear(self, phonebook_id, contact_ids):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        if contact_ids:
            headers = {'Content-Type': 'application/json'}
            headers.update(self.headers)
            delete_result = delete(
                url=phonebook_contacts,
                headers=headers,
                data=json.dumps({'contact_ids': contact_ids}))
            if delete_result.ok:
                return delete_result.json()
        # Consistent return result makes calling code cleaner.
        return {
            'url': self.url,
            'id': phonebook_id,
            'count': -1,
            'error': delete_result.text
            }


    def phonebook_clear_all(self, phonebook_id):
        """Retrieve all contacts, then build a delete all request"""
        contacts = self.phonebook_get_contacts(phonebook_id=phonebook_id)
        if contacts:
            contact_ids = [contact['contact'] for contact in contacts]
            delete_result = self.phonebook_clear(phonebook_id=phonebook_id, contact_ids=contact_ids)
            assert delete_result['count'] == '0'


    def make_callhub_contact_from(self, crm_contact):
        """
        Extract CiviCRM contact data and transform into a CallHub contact.
        NB: CiviCRM UI calculates the State and Federal electorates at runtime.
        That data is not  available from the CiviCRM API to update CallHub.
        """
        def fmt(key, value):
            return '"%s": "%s"' % (key, value)

        fields = [
            # fmt(CUSTOM_FIELD_FEDERAL, (
            #     crm_contact['custom'][self.crm_custom['federal']]
            #     if (self.crm_custom and
            #         self.crm_custom['federal'] in crm_contact['custom'])
            #     else '')),
            # fmt(CUSTOM_FIELD_STATE, crm_contact['state_province'] + ' - ' + '?'),
            fmt(CUSTOM_FIELD_CONTACTID, crm_contact['contact_id'])
        ]
        custom_fields = '{%s}' % ','.join(fields)

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
            'company_name': '',
            'company_website': '%s/%s' % (self.rocket_url, crm_contact['contact_id']),
            CUSTOM_FIELDS: custom_fields
            }


    def phonebook_add_existing(self, phonebook_id, ch_contact_ids):
        """Add a list of contacts to a phonebook."""
        phonebook_contacts = '%s/phonebooks/%s/contacts' % (self.url, phonebook_id)
        headers = {'Content-Type': 'application/json'}
        headers.update(self.headers)
        response = post(
            url=phonebook_contacts,
            headers=headers,
            data=json.dumps({'contact_ids': ch_contact_ids}))
        content = {}
        if response.ok:
            self.logger.info(
                'Phonebook: "%s" Add existing contacts: "%s"' %
                (phonebook_id, str(ch_contact_ids)))
            #self.logger.debug(response.content)
            content = response.json()
        else:
            self.logger.error(response.text)
        return content


    def phonebook_update(self, phonebook_id, crm_contacts, crm_ch_id_map):
        """Create all contacts and add them to phonebook"""
        # Remove contacts not in the crm_contacts list
        ch_contacts = self.phonebook_get_contacts(phonebook_id)
        missing = missing_callhub_contacts(
            ch_contacts=ch_contacts,
            crm_contacts=crm_contacts,
            crm_ch_id_map=crm_ch_id_map)

        if missing:
            clear_content = self.phonebook_clear(
                phonebook_id=phonebook_id,
                contact_ids=missing)
            assert int(clear_content['count']) == len(ch_contacts) - len(missing)

        # Identify new CRM contacts
        ## Note: existing is a list of CallHub ids.
        missing, existing = missing_crm_contacts(crm_contacts, crm_ch_id_map)
        assert len(missing) + len(existing) == len(crm_contacts)

        # Create missing contacts in the phonebook
        for crm_contact in missing:
            if not crm_contact['phone']:
                self.logger.warn('Missing phone number: %s' % str(crm_contact))
                continue
            ch_contact = self.make_callhub_contact_from(crm_contact)
            new_contact = self.create_contact(ch_contact)
            if not new_contact:
                self.logger.warn('Failed to create or retrieve contact: %s' % str(ch_contact))
            else:
                existing.append(new_contact['id'])

        # Update the phonebook with all these CallHub contact ids
        result = self.phonebook_add_existing(phonebook_id=phonebook_id, ch_contact_ids=existing)
        if int(result['count']) < len(existing):
            self.logger.warn('CallHub.phonebook_update():' + \
            'Failed to add to phonebook %s: %s' % (phonebook_id, str(existing)))
