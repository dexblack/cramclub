"""
Wrapper for CallHub operations.
"""
from requests import get, put, post, delete
import json
from singleton.singleton import Singleton
from cramcfg import CramCfg
from cramconst import CUSTOM_FIELD_FEDERAL, CUSTOM_FIELD_STATE, CUSTOM_FIELD_CONTACTID


def missing_callhub_contacts(cram, club):
    """Remove callhub (club) entries found in CiviCRM (cram) list"""
    crmids = [crm_contact["id"] for crm_contact in cram]
    # This depends on the custom CallHub field "ContactID"
    return [ch_contact["id"] for ch_contact in club
            if ch_contact["ContactID"] not in crmids]


def make_callhub_contact_from(civicrm_url, crm_contact):
    """Extract and transform"""
    return {
        "contact": crm_contact["phone"],
        "mobile": crm_contact["phone"] if crm_contact["phone"][0:2] == "04" else "",
        "last_name": crm_contact["last_name"],
        "first_name": crm_contact["first_name"],
        "country_code": "AU",
        "email": crm_contact["email"],
        "address": crm_contact["street_address"],
        "city": crm_contact["city"],
        "state": crm_contact["state_province"],
        "company_name": crm_contact[""],
        "company_website": civicrm_url + "/" + crm_contact["contact_id"],
        "custom_fields": {
            CUSTOM_FIELD_FEDERAL: crm_contact[""],
            CUSTOM_FIELD_STATE: crm_contact[""],
            CUSTOM_FIELD_CONTACTID: crm_contact["contact_id"]}
        }


def gather_callhub_ids(id_map, callhub_contacts):
    for callhub_contact in callhub_contacts:
        if CUSTOM_FIELD_CONTACTID in callhub_contact["custom_fields"]:
            crm_id = callhub_contact["custom_fields"][CUSTOM_FIELD_CONTACTID]
            if not crm_id:
                continue
            # Assume a valid CiviCRM identifier in this custom field
            # and add it to the map
            id_map[crm_id] = callhub_contact["id"]


def missing_crm_contacts(cram, callhub_crm_map):
    """Return new list from cram that only has the contacts missing from club"""
    ch_ids = [elem["ch"] for elem in callhub_crm_map]
    missing = [crm_contact for crm_contact in cram
               if crm_contact["id"] in ch_ids]
    return missing



@Singleton
class CallHub(object):
    """
    CallHub API wrapper.
    Implements limited required functionality.
    """
    def __init__(self, *args, **kwargs):
        cram = CramCfg.instance()
        self.url = cram.cfg["callhub"]["url"]
        self.civicrm_url = cram.cfg["civicrm"]["url"]
        self.headers = {
            "Authorization": "Token " + cram.cfg["callhub"]["api_key"],
            }


    def contacts(self):
        """Retrieve an id {crm:ch_id} mapping of all contacts in CallHub"""
        all_contacts = self.url + "/contacts"

        response = get(url=all_contacts, headers=self.headers)
        content = json.loads(response.content)
        crm_ch_id_map = {}
        gather_callhub_ids(id_map=crm_ch_id_map, callhub_contacts=content)

        for page in range(2, int(int(content["count"])/10) + 2):
            response = get(all_contacts + "?page=%d" % page, self.headers)
            content = json.loads(response.content)
            gather_callhub_ids(id_map=crm_ch_id_map, callhub_contacts=content)

        return crm_ch_id_map


    def phonebook_clear(self, phonebook_id, contact_ids):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = "%s/%d/contacts" % [self.url, phonebook_id]
        if len(contact_ids) > 0:
            data = {"contact_ids": contact_ids}
            delete_result = delete(url=phonebook_contacts, headers=self.headers, data=data)
            return delete_result

        return {
            "url": self.url,
            "id": phonebook_id,
            "count": 0
            }


    def phonebook_clear_all(self, phonebook_id):
        """Retrieve all contacts, then build a delete all request"""
        phonebook_contacts = "%s/%d/contacts" % [self.url, phonebook_id]
        response = get(url=phonebook_contacts, headers=self.headers)
        contact_ids = [contact["contact"] for contact in response["results"]]
        delete_result = phonebook_clear(phonebook_id=phonebook_id, contact_ids=contact_ids)
        assert delete_result["count"] == "0"


    def phonebook_update(self, phonebook_id, crm_contacts, crm_ch_id_map):
        """Create all contacts and add them to phonebook"""

        # Remove contacts not in the new list
        remove_ch_contacts = missing_callhub_contacts(cram=crm_contacts,
                                                      club=all_ch_contacts)

        clear_result = phonebook_clear(phonebook_id=phonebook_id,
                                       contact_ids=remove_ch_contacts)

        phonebook_contacts = "%s/%d/contacts" % [self.url, phonebook_id]
        create_contact = self.url + "/contacts"

        # Identify new CRM contacts
        ## Note: Without the dict map this would be take order N squared time!
        new_contacts = [crm_contact in crm_contacts if crm_contacts["id"] in crm_ch_id_map]
        callhub_contacts = [make_callhub_contact_from(self.civicrm_url, contact)
                            for contact in new_contacts]
