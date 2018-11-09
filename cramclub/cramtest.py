from cramlog import CramLog
from callhub import CallHub
from crampull import CramPull


def test_add_contact_to_callhub():
    """
    Checking what happens when we create the same contact twice.
    Do we get the same CallHub contact id back?
    Is it then the equivalent of an update operation?
    """
    logger = CramLog.instance()
    crampull = CramPull.instance()
    club = CallHub.instance()

    crm_id = '287831'
    crm_contact = crampull.contact(crm_id)
    if not crm_contact:
        logger.error('Failed to retrieve CRM contact: ' + crm_id)
        return

    ch_contact = club.make_callhub_contact_from(crm_contact)


    result1 = club.phonebook_create_new_contact(phonebook_id, ch_contact)
    result2 = club.phonebook_create_new_contact(phonebook_id, ch_contact)
