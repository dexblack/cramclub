"""
Wrapper for CallHub operations.
"""
import re
import json
from requests import get, post, put, delete, exceptions
from singleton.singleton import Singleton

from cramlog import CramLog
from cramcfg import CramCfg
from cramconst import CUSTOM_FIELDS, CUSTOM_FIELD_CONTACTID
# unused CUSTOM_FIELD_FEDERAL, CUSTOM_FIELD_STATE


def sanitised_callhub_contact(ch_contact):
    """Customer privacy protection for log output."""
    return 'id: %s, url: %s, custom: %s' % (
        ch_contact.get('pk_str', ''),
        ch_contact.get('url', ''),
        ch_contact[CUSTOM_FIELDS].replace(CUSTOM_FIELD_CONTACTID, 'ContactID')
    )


def sanitise_crm_contact(rocket_url, crm_contact):
    """Privacy protection for contact data in logs"""
    return 'crm_id: %s, url: %s' % (
        crm_contact['contact_id'],
        '%s/%s' % (rocket_url, crm_contact['contact_id']),
    )


def mark_duplicates(crm_contacts, ch_contacts, logger):
    """Ensure crm_contacts have unique contact numbers."""

    def standardise(country_code, region_code, phone_number):
        """
        I tried so hard to avoid having to write this.
        Alas, inadequacies in the CallHub API forced it upon me.
        This an approximation of the full algorithm they use internally
        when creating a new contact.
        """
        phn = phone_number.replace(' ', '')
        if len(phn) == 12 and phn[0:3] == (country_code + '0'): # 610?????????
            phn = country_code + phn[3:]
        if (len(phn) == 11 and phn[0:3] == (country_code + region_code)) or (
                len(phn) == 11 and phn[0:3] == (country_code + '4')):
            return phn  # 612???????? landline or 614????????  mobile number
        if phn[0:1] == '0':
            phn = phn[1:]
        if len(phn) == 9 and phn[0:1] == '4': # 4????????  mobile number
            return country_code + phn
        if len(phn) == 9 and phn[0:1] == region_code:
            phn = phn[1:]  # 2???????? landline
        if len(phn) == 10 and phn[0:2] == country_code:
            phn = phn[2:]  # 61???????? landline
        if len(phn) == 9 and phn[0:1] == region_code: # 2????????
            phn = phn[1:]
        if len(phn) == 9 and phn[0:1] == '4': # 4????????  mobile number
            phn = country_code + phn
        if len(phn) == 8: # ???????? landline
            phn = country_code + region_code + phn
        return phn
    count = 0
    phone_numbers = [c['contact'] for c in ch_contacts]
    # Collect CiviCRM ContactID fields from existing contacts in the phone-book.
    get_contact_id = lambda c: json.loads(
        c[CUSTOM_FIELDS].replace("'", '"').replace('u"', '"')).get(CUSTOM_FIELD_CONTACTID)
    crm_ids = [get_contact_id(c) for c in ch_contacts if CUSTOM_FIELDS in c]

    for crm_contact in crm_contacts:
        # Don't count contacts already in the phone-book as duplicates.
        # Also skip empty phone numbers.
        if crm_contact['contact_id'] in crm_ids:
            continue
        phone_number = standardise('61', '2', crm_contact['phone'])
        if not phone_number:
            continue
        duplicate = phone_number in phone_numbers
        crm_contact['duplicate'] = duplicate
        if duplicate:
            count = count + 1
            logger.debug('Duplicate phone number. CiviCRM contact %s.' % \
                crm_contact['contact_id'])
        else:
            phone_numbers.append(phone_number)
    return count


def missing_callhub_contacts(ch_contacts, crm_contacts, crm_ch_id_map):
    """Gather CallHub contacts not found in CiviCRM id map."""
    if not ch_contacts:
        return ([], [])

    missing = []
    existing = []
    for crm_contact in crm_contacts:
        ch_id = crm_ch_id_map.get(crm_contact.get('contact_id'))
        if ch_id:
            existing.append(ch_id)

    remainder = []
    for ch_contact in ch_contacts:
        contact_id = ch_contact['pk_str'] # id as a string value
        if contact_id in existing:
            remainder.append(ch_contact)
        else:
            missing.append(contact_id)

    return (missing, remainder)


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
    """
    Return a new list CRM contacts missing from CallHub,
    and the CallHub ids of the existing CallHub entries.
    """
    # Another O(NxN) operation dodged with dict lookup.
    missing, existing = ([], []) # This is the return value
    for crm_contact in crm_contacts:
        if crm_contact.get('duplicate'):
            continue

        ch_id = crm_ch_id_map.get(crm_contact.get('contact_id'))
        if ch_id:
            existing.append(ch_id)
        else:
            missing.append(crm_contact)
    return (missing, existing)



@Singleton
class CallHub(object):
    """
    CallHub API wrapper.
    Implements limited required functionality.
    """
    def __init__(self, crypter):
        """
        Set up configured URLs, API keys and field identifiers.
        """
        cram = CramCfg.instance() # pylint: disable-msg=E1101
        self.url = cram.cfg['callhub']['url']
        self.civicrm_url = cram.cfg['civicrm']['url']
        self.rocket_url = cram.cfg['rocket']['url']
        self.crm_custom = cram.cfg['civicrm']['custom'] \
            if 'custom' in cram.cfg['civicrm'] else {}

        authtoken = crypter.decrypt(cram.cfg['callhub']['api_key'])
        self.headers = {
            'Authorization': 'Token ' + authtoken,
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
        response = post(
            url=create_contact,
            headers=self.headers,
            data=ch_contact)
        #self.logger.info(
        #    'New contact: "%s"' % ch_contact[CUSTOM_FIELDS][CUSTOM_FIELD_CONTACTID])
        content = {}
        if response.ok:
            content = response.json()
            self.logger.info('Created Contact: %s' % sanitised_callhub_contact(content))

        elif response.status_code == 400:
            self.logger.warn('Create Contact bad request: HTTP Error %d' % response.status_code)
            response2 = response.json()
            non_field_errors = response2.get('non_field_errors')
            email_error = response2.get('email')
            if non_field_errors:
                self.logger.warn(str(non_field_errors))
            elif email_error:
                self.logger.warn(str(email_error))
            else:
                # Contact already existed. Returns the one found.
                self.logger.warn(response2.get('detail', 'no error detail provided'))
                content = response2.get('contact', {})
        else:
            self.logger.error('Create Contact %s failed: HTTP Error %d' % (
                ch_contact.get(CUSTOM_FIELDS).replace(CUSTOM_FIELD_CONTACTID, 'ContactID'),
                response.status_code))
        return content


    def update_contact(self, ch_id, ch_contact):
        """Use 'ch_contact' fields to update CallHub contact 'ch_id'."""
        update_contact = self.url + '/contacts/%s/' % ch_id
        response = put(
            url=update_contact,
            data=ch_contact,
            headers=self.headers)
        content = {}
        if response.ok:
            content = response.json()
            self.logger.info('Updated Contact: %s' % sanitised_callhub_contact(content))
        else:
            self.logger.debug('Update Contact failed: %s. %s' % (response.reason, response.text))
        return content


    def contacts(self):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""

        crm_ch_id_map = {}
        try:
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
                page += 1
                gather_callhub_ids(
                    id_map=crm_ch_id_map,
                    callhub_contacts=response_content['results'])

        except exceptions.ConnectionError as conn_err:
            self.logger.error(str(conn_err))

        return crm_ch_id_map


    def delete_contact(self, ch_id):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""
        next_page = self.url + ('/contacts/%s/' % ch_id)
        del_response = delete(url=next_page, headers=self.headers)
        if del_response.status_code != 200:
            self.logger.critical('Failed to delete CallHub Contact %s' % ch_id)


    def phonebook_get_contacts(self, phonebook_id):
        """Retrieve all contacts in a phonebook"""
        contacts = []
        next_url = '%s/phonebooks/%s/contacts/' % (self.url, phonebook_id)
        while next_url:
            retry_count = 0
            while retry_count < 3:
                try:
                    response = get(url=next_url, headers=self.headers)
                    break
                except ConnectionError as conn_err:
                    if retry_count < 3:
                        self.logger.warn('%s. Retrying... %d' % (str(conn_err), retry_count))
                    else:
                        self.logger.error(str(conn_err))
                    retry_count += 1

            if response.ok:
                content = response.json()
                contacts.extend(content['results'])
                next_url = content['next']
            else:
                next_url = None
        return contacts


    def phonebook_clear(self, phonebook_id, contact_ids):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = '%s/phonebooks/%s/contacts/' % (self.url, phonebook_id)
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
            'last_name': crm_contact['last_name'],
            'first_name': crm_contact['first_name'],
            'country_code': 'AU',
            'email': crm_contact.get('email', ''),
            'address': crm_contact.get('street_address', ''),
            'city': crm_contact.get('city', ''),
            'state': crm_contact.get('state_province', ''),
            'company_website': '%s/%s' % (self.rocket_url, crm_contact['contact_id']),
            CUSTOM_FIELDS: custom_fields
        }


    def phonebook_add_existing(self, phonebook_id, ch_contact_ids):
        """Add a list of contacts to a phonebook."""
        phonebook_contacts = '%s/phonebooks/%s/contacts/' % (self.url, phonebook_id)
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
            content = response.json()
        else:
            sanitised_error = re.sub("Phonenumber:'([0-9][0-9][0-9])[0-9]+'", \
                r"Phonenumber:'\1????????'", response.text)
            content = {
                'url': '%s/phonebooks/%s/' % (self.url, phonebook_id),
                'id': int(phonebook_id),
                'owner': '',
                'name': '',
                'description': '',
                'count': '+1',
                'error': sanitised_error
                }
            #self.logger.log(80, 'KILL THIS LINE %s' % response.text)

        return content


    def phonebook_update(self, phonebook_id, crm_contacts, crm_ch_id_map):
        """Create all contacts and add them to phonebook"""
        ch_contacts = self.phonebook_get_contacts(phonebook_id)
        mark_duplicates(crm_contacts, ch_contacts, self.logger)

        # Remove contacts not in the crm_contacts list
        missing_callhub, remaining = missing_callhub_contacts(
            ch_contacts=ch_contacts,
            crm_contacts=crm_contacts,
            crm_ch_id_map=crm_ch_id_map)

        if missing_callhub:
            clear_content = self.phonebook_clear(
                phonebook_id=phonebook_id,
                contact_ids=missing_callhub)
            self.logger.debug('Removed %d contacts from phonebook: %s. %d/%d remaining.' % \
                (len(missing_callhub), phonebook_id, int(clear_content['count']), len(ch_contacts)))

        # Identify new CRM contacts.
        ## Note: `existing` is a list of CallHub ids.
        missing, existing = missing_crm_contacts(crm_contacts, crm_ch_id_map)

        # Skip adding contacts that are already in the phonebook.
        for ch_contact in ch_contacts:
            callhub_id = ch_contact['pk_str']
            if callhub_id in existing:
                existing.remove(callhub_id)

        # Extract contact numbers from the ones remaining in the phonebook.
        contact_numbers = [x['contact'] for x in remaining]

        # Create missing contacts.
        for crm_contact in missing:
            if not crm_contact['phone']:
                self.logger.warn('Missing phone number: %s' % \
                    sanitise_crm_contact(self.rocket_url, crm_contact))
                continue

            if crm_contact['duplicate']:
                continue

            ch_contact = self.make_callhub_contact_from(crm_contact)
            new_contact = self.create_contact(ch_contact)
            if not new_contact:
                self.logger.warn('Failed to create or retrieve contact: %s' % \
                    sanitised_callhub_contact(ch_contact))
                continue

            # Prevent adding two entries with the same contact number!
            # Surprisingly common for two people to share a mobile phone.
            if new_contact['contact'] not in contact_numbers:
                existing.append(new_contact['pk_str']) # id as a string

        if not existing:
            # We're done here.
            return

        # Update the phonebook with all these CallHub contact ids.
        result = self.phonebook_add_existing(
            phonebook_id=phonebook_id, ch_contact_ids=existing)
        if result.get('count') == '+1': # Special value to indicate failure.
            self.logger.error('CallHub.phonebook_update(): ' + \
                'Failed to add to phonebook %s: %s' % (
                    phonebook_id, result.get('error', 'no error message')))
        else:
            assert int(result.get('count', '-1')) >= len(existing)
